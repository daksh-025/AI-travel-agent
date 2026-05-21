import logging
from datetime import datetime
import uuid
from typing import List, Dict, Any, Optional
from langchain.agents import AgentExecutor, create_openai_functions_agent, create_react_agent
from langchain.schema import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool, StructuredTool
from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import BaseTool
import asyncio
from app.chat.models import ChatRequest, ToolResult, SerpAPIHotelsInput, SerpAPIOneHotelInput, TavilyWebSearchInput, PineconeRetrieveInput, ApifyBookingInput
from app.chat.response_models import StructuredChatResponse, HotelSearchResponse, HotelResult, HotelPosition, WebSearchResponse, WebSearchImage, ExtraPrice
from app.chat.tools import SerpAPIHotelsTool, SerpAPIOneHotelTool, TavilyWebSearchTool, ApifyBookingTool
from app.core.config import settings

logger = logging.getLogger(__name__)

class ToolUsageCallback(BaseCallbackHandler):
    """Callback to track tool usage during agent execution"""
    
    def __init__(self):
        self.tools_used = []
        self.tool_inputs = {}
        self.tool_outputs = {}
    
    def on_tool_start(self, serialized, input_str, **kwargs):
        """Called when a tool starts"""
        tool_name = serialized.get("name", "unknown")
        self.tools_used.append(tool_name)
        self.tool_inputs[tool_name] = input_str
        logger.info(f"🔧 Tool started: {tool_name}")
        logger.info(f"🔧 Tool input: {input_str[:100]}...")
    
    def on_tool_end(self, output, **kwargs):
        """Called when a tool ends"""
        # The last tool used will be the one that just ended
        if self.tools_used:
            tool_name = self.tools_used[-1]
            
            # Store outputs as list to support multiple calls to same tool
            if tool_name not in self.tool_outputs:
                self.tool_outputs[tool_name] = []
            self.tool_outputs[tool_name].append(output)
            
            logger.info(f"🔧 Tool ended: {tool_name} (call #{len(self.tool_outputs[tool_name])})")
            logger.info(f"🔧 Tool output type: {type(output)}")
            logger.info(f"🔧 Tool output length: {len(str(output)) if output else 0}")
            if output:
                logger.info(f"🔧 Tool output preview: {str(output)[:200]}...")
    
    def get_tool_usage_info(self):
        """Get summary of tool usage"""
        return {
            "tools_used": self.tools_used,
            "serpapi_hotels_used": "serpapi_hotels" in self.tools_used,
            "serpapi_one_hotel_used": "serpapi_one_hotel" in self.tools_used,
            "tavily_web_search_used": "tavily_web_search" in self.tools_used,
            "pinecone_retrieve_used": "pinecone_retrieve" in self.tools_used,
            "total_tools_used": len(self.tools_used),
            "tool_inputs": self.tool_inputs,
            "tool_outputs": self.tool_outputs,
        }


class SimpleAgentToolCallback:
    """Callback to track tool usage in SimpleAgent execution"""
    
    def __init__(self):
        self.tools_used = []
        self.tool_inputs = {}
        self.tool_outputs = {}
    
    def on_tool_start(self, tool_name: str, tool_args: dict):
        """Called when a tool starts"""
        self.tools_used.append(tool_name)
        self.tool_inputs[tool_name] = tool_args
        logger.info(f"🔧 Tool started: {tool_name}")
        logger.info(f"🔧 Tool input: {str(tool_args)[:100]}...")
    
    def on_tool_end(self, tool_name: str, output: str):
        """Called when a tool ends"""
        # Store outputs as list to support multiple calls to same tool
        if tool_name not in self.tool_outputs:
            self.tool_outputs[tool_name] = []
        self.tool_outputs[tool_name].append(output)
        
        logger.info(f"🔧 Tool ended: {tool_name} (call #{len(self.tool_outputs[tool_name])})")
        logger.info(f"🔧 Tool output type: {type(output)}")
        logger.info(f"🔧 Tool output length: {len(str(output)) if output else 0}")
        if output:
            logger.info(f"🔧 Tool output preview: {str(output)[:200]}...")
    
    def get_tool_usage_info(self):
        """Get summary of tool usage"""
        return {
            "tools_used": self.tools_used,
            "serpapi_hotels_used": "serpapi_hotels" in self.tools_used,
            "serpapi_one_hotel_used": "serpapi_one_hotel" in self.tools_used,
            "tavily_web_search_used": "tavily_web_search" in self.tools_used,
            "pinecone_retrieve_used": "pinecone_retrieve" in self.tools_used,
            "apify_booking_used": "apify_booking" in self.tools_used,
            "total_tools_used": len(self.tools_used),
            "tool_inputs": self.tool_inputs,
            "tool_outputs": self.tool_outputs,
        }


class RealProgressCallback(SimpleAgentToolCallback):
    """Enhanced callback that provides real-time progress updates"""
    
    def __init__(self, progress_update_callback=None):
        super().__init__()
        self.current_tool = None
        self.progress_callback = progress_update_callback
        self.phase_progress = {
            "starting": 5,
            "analyzing": 15,
            "tool_execution": 30,
            "processing_results": 70,
            "generating_response": 85,
            "completing": 100
        }
    
    async def _send_progress(self, phase, message, percentage):
        """Send progress update if callback is set"""
        if self.progress_callback:
            from app.chat.streaming_models import ProgressUpdate, ProgressPhase
            try:
                # Map phase names to ProgressPhase enum
                phase_map = {
                    "starting": ProgressPhase.STARTING,
                    "analyzing": ProgressPhase.THINKING_PREFERENCES,
                    "searching_hotels": ProgressPhase.SEARCHING_BOOKING,
                    "searching_web": ProgressPhase.CHECKING_GOOGLE,
                    "processing": ProgressPhase.ANALYZING_SITES,
                    "matching": ProgressPhase.MATCHING_OPTIONS,
                    "generating": ProgressPhase.GENERATING_RESPONSE,
                    "completing": ProgressPhase.COMPLETE
                }
                
                progress_phase = phase_map.get(phase, ProgressPhase.ANALYZING_SITES)
                
                progress_update = ProgressUpdate(
                    phase=progress_phase,
                    message=message,
                    percentage=percentage,
                    details=f"Real-time: {phase}"
                )
                
                await self.progress_callback(progress_update)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")
    
    def _schedule_progress_update(self, phase, message, percentage):
        """Schedule a progress update to be sent (handles sync callback context)"""
        if self.progress_callback:
            # Store the progress update to be sent later
            if not hasattr(self, '_pending_progress'):
                self._pending_progress = []
            
            from app.chat.streaming_models import ProgressUpdate, ProgressPhase
            
            # Map phase names to ProgressPhase enum
            phase_map = {
                "starting": ProgressPhase.STARTING,
                "analyzing": ProgressPhase.THINKING_PREFERENCES,
                "searching_hotels": ProgressPhase.SEARCHING_BOOKING,
                "searching_web": ProgressPhase.CHECKING_GOOGLE,
                "processing": ProgressPhase.ANALYZING_SITES,
                "matching": ProgressPhase.MATCHING_OPTIONS,
                "generating": ProgressPhase.GENERATING_RESPONSE,
                "completing": ProgressPhase.COMPLETE
            }
            
            progress_phase = phase_map.get(phase, ProgressPhase.ANALYZING_SITES)
            
            progress_update = ProgressUpdate(
                phase=progress_phase,
                message=message,
                percentage=percentage,
                details=f"Real-time: {phase}"
            )
            
            self._pending_progress.append(progress_update)
    
    async def _send_pending_progress(self):
        """Send all pending progress updates"""
        if hasattr(self, '_pending_progress') and self._pending_progress:
            for progress_update in self._pending_progress:
                try:
                    await self.progress_callback(progress_update)
                    await asyncio.sleep(0.1)  # Small delay between updates
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")
            self._pending_progress = []
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        """Called when LLM starts processing"""
        self._schedule_progress_update(
            "analyzing", 
            "AI is analyzing your request...", 
            self.phase_progress["analyzing"]
        )
    
    def on_tool_start(self, tool_name: str, tool_args: dict):
        """Called when a tool starts (SimpleAgent interface)"""
        super().on_tool_start(tool_name, tool_args)
        self.current_tool = tool_name
        
        # Send real progress based on actual tool being used
        if tool_name == "serpapi_hotels":
            self._schedule_progress_update(
                "searching_hotels",
                "Searching hotel databases (Booking.com, Google Hotels)...",
                35
            )
        elif tool_name == "tavily_web_search":
            self._schedule_progress_update(
                "searching_web",
                "Searching web for current information...",
                40
            )
        elif tool_name == "pinecone_retrieve":
            self._schedule_progress_update(
                "processing",
                "Searching knowledge base for relevant information...",
                45
            )
        else:
            self._schedule_progress_update(
                "processing",
                f"Using {tool_name} to gather information...",
                50
            )
    
    def on_tool_end(self, tool_name: str, output: str):
        """Called when a tool ends (SimpleAgent interface)"""
        super().on_tool_end(tool_name, output)
        if self.current_tool:
            
            # Check if tool was successful
            success = output and not str(output).lower().startswith("error")
            
            if self.current_tool == "serpapi_hotels" and success:
                self._schedule_progress_update(
                    "processing",
                    "Processing hotel search results...",
                    65
                )
            elif self.current_tool == "tavily_web_search" and success:
                self._schedule_progress_update(
                    "processing",
                    "Processing web search results...",
                    60
                )
            elif success:
                self._schedule_progress_update(
                    "processing",
                    f"Processing {self.current_tool} results...",
                    55
                )
            else:
                self._schedule_progress_update(
                    "processing",
                    f"Completed {self.current_tool}, continuing...",
                    50
                )
            
            self.current_tool = None
    
    def on_tool_error(self, error, **kwargs):
        """Called when a tool errors"""
        if self.current_tool:
            self._schedule_progress_update(
                "processing",
                f"Issue with {self.current_tool}, trying alternatives...",
                45
            )
            self.current_tool = None
    
    def on_agent_finish(self, finish, **kwargs):
        """Called when agent finishes processing"""
        self._schedule_progress_update(
            "matching",
            "Matching results to your preferences...",
            75
        )
    
    def on_llm_end(self, response, **kwargs):
        """Called when LLM completes generation"""
        if not self.tools_used:  # Simple text generation
            self._schedule_progress_update(
                "generating",
                "Generating response...",
                self.phase_progress["generating"]
            )
        else:  # Had tools, so this is final response generation
            self._schedule_progress_update(
                "generating",
                "Creating personalized response...",
                self.phase_progress["generating"]
            )
    
    def get_tool_usage_info(self):
        """Get summary of tool usage (compatible with existing code)"""
        return {
            "tools_used": self.tools_used,
            "serpapi_hotels_used": "serpapi_hotels" in self.tools_used,
            "tavily_web_search_used": "tavily_web_search" in self.tools_used,
            "pinecone_retrieve_used": "pinecone_retrieve" in self.tools_used,
            "apify_booking_used": "apify_booking" in self.tools_used,
            "total_tools_used": len(self.tools_used),
            "tool_inputs": self.tool_inputs,
            "tool_outputs": self.tool_outputs,
        }

class SimpleAgentState:
    """Simple state management without LangGraph dependencies."""
    
    def __init__(self):
        self.messages: List[Any] = []
        self.todos: List[Dict[str, str]] = []
        self.files: Dict[str, str] = {}
    
    def add_message(self, message: Any):
        self.messages.append(message)
    
    def get_conversation_history(self) -> List[Any]:
        return self.messages
    
    def update_files(self, new_files: Dict[str, str]):
        self.files.update(new_files)
    
    def get_files(self) -> Dict[str, str]:
        return self.files


class AsyncSimpleAgent:
    """
    Optimized async agent implementation with parallel tool execution.
    
    Key optimizations:
    - Direct async tool execution (no thread pools)
    - Parallel tool calls via asyncio.gather()
    - 40-80ms faster per tool
    - 50-70% faster for multi-tool queries
    """
    
    def __init__(self, model, tools: List, system_prompt: str, max_iterations: int = 10, callback=None):
        self.model = model
        self.tools = {tool.name: tool for tool in tools}
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self.callback = callback
        
        # Bind tools to model (for schema only)
        self.model_with_tools = model.bind_tools(self._get_tool_schemas())
    
    def _get_tool_schemas(self) -> List[StructuredTool]:
        """Get tool schemas for LLM without wrapping execution"""
        schema_map = {
            "serpapi_hotels": SerpAPIHotelsInput,
            "serpapi_one_hotel": SerpAPIOneHotelInput,
            "tavily_web_search": TavilyWebSearchInput,
            "pinecone_retrieve": PineconeRetrieveInput,
            "apify_booking": ApifyBookingInput
        }
        
        schemas = []
        for tool in self.tools.values():
            args_schema = schema_map.get(tool.name)
            schema = StructuredTool.from_function(
                func=lambda: None,  # Dummy - execution handled separately
                name=tool.name,
                description=tool.description,
                args_schema=args_schema
            )
            schemas.append(schema)
        
        return schemas
    
    async def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main async agent execution loop with parallel tool calling"""
        messages = self._prepare_messages(input_data)
        iteration = 0
        
        self.max_iterations = 2
        logger.info(f"🚀 AsyncSimpleAgent starting (max_iterations={self.max_iterations})")
        
        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"📍 Iteration {iteration}/{self.max_iterations}")
            
            # Get AI response with tools (async)
            response = await self.model_with_tools.ainvoke(messages)
            messages.append(response)
            
            # Check if AI wants to use tools
            if hasattr(response, 'tool_calls') and response.tool_calls:
                logger.info(f"🔧 AI requested {len(response.tool_calls)} tool(s)")
                
                # 🚀 ENHANCED PARALLEL tool execution with serpapi_one_hotel optimization
                tool_results = await self._execute_tools_with_serpapi_optimization(response.tool_calls)
                
                # Add all results to messages
                for tool_call, result in zip(response.tool_calls, tool_results):
                    if isinstance(result, Exception):
                        content = f"Error: {str(result)}"
                        logger.error(f"❌ Tool {tool_call['name']} error: {result}")
                    else:
                        content = str(result)
                    
                    messages.append(ToolMessage(
                        content=content,
                        tool_call_id=tool_call["id"]
                    ))
            else:
                logger.info(f"✅ Agent finished - no more tools needed")
                break
        
        if iteration >= self.max_iterations:
            logger.warning(f"⚠️ Max iterations reached ({self.max_iterations})")
        
        return self._format_output(messages)
    
    async def _execute_tools_with_serpapi_optimization(self, tool_calls: List[Dict]) -> List[str]:
        """
        Execute tools with special optimization for parallel serpapi_one_hotel calls.
        
        This method detects when multiple serpapi_one_hotel calls are made and
        executes them in parallel to reduce latency significantly.
        """
        # Count serpapi_one_hotel calls for optimization
        serpapi_one_hotel_count = sum(1 for tc in tool_calls if tc["name"] == "serpapi_one_hotel")
        
        if serpapi_one_hotel_count > 1:
            logger.info(f"🚀 DETECTED {serpapi_one_hotel_count} serpapi_one_hotel calls - optimizing for parallel execution")
        
        # Execute all tools in parallel using asyncio.gather
        tool_tasks = [self._execute_tool_async(tc) for tc in tool_calls]
        
        start_time = asyncio.get_event_loop().time()
        tool_results = await asyncio.gather(*tool_tasks, return_exceptions=True)
        duration = asyncio.get_event_loop().time() - start_time
        
        # Enhanced logging for serpapi optimization
        if serpapi_one_hotel_count > 1:
            logger.info(f"✅ PARALLEL OPTIMIZATION: {serpapi_one_hotel_count} serpapi_one_hotel calls completed in {duration:.2f}s")
            logger.info(f"📊 Total tools executed: {len(tool_tasks)} in {duration:.2f}s")
        else:
            logger.info(f"✅ All {len(tool_tasks)} tools completed in {duration:.2f}s")
        
        return tool_results
    
    async def _execute_tool_async(self, tool_call: Dict) -> str:
        """Execute a single tool asynchronously - NO THREAD POOL"""
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        
        if tool_name not in self.tools:
            error_msg = f"Tool '{tool_name}' not found"
            logger.error(error_msg)
            return error_msg
        
        try:
            if self.callback:
                self.callback.on_tool_start(tool_name, tool_args)
            
            logger.info(f"🔧 Executing {tool_name}")
            start_time = asyncio.get_event_loop().time()
            
            # 🚀 Direct async execution - NO THREAD!
            tool = self.tools[tool_name]
            result = await tool.execute(tool_args)
            
            duration = asyncio.get_event_loop().time() - start_time
            logger.info(f"✅ {tool_name} completed in {duration:.2f}s")
            logger.info(f"📊 Result type: {type(result)}, has result attr: {hasattr(result, 'result')}")
            logger.info(f"📊 Result preview: {str(result.result)[:200] if hasattr(result, 'result') else 'N/A'}...")
            
            if self.callback:
                self.callback.on_tool_end(tool_name, result.result)  # ✅ FIX: Use result.result, not str(result)
            
            return result.result
            
        except Exception as e:
            error_msg = f"Error executing tool {tool_name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            if self.callback:
                self.callback.on_tool_end(tool_name, error_msg)
            
            return error_msg
    
    def _prepare_messages(self, input_data: Dict[str, Any]) -> List:
        """Convert input data to LangChain message format"""
        messages = [SystemMessage(content=self.system_prompt)]
        
        if "messages" in input_data:
            for msg in input_data["messages"]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
                elif msg["role"] == "tool":
                    messages.append(ToolMessage(
                        content=msg["content"],
                        tool_call_id=msg.get("tool_call_id", "")
                    ))
        
        return messages
    
    def _format_output(self, messages: List) -> Dict[str, Any]:
        """Convert messages back to simple format"""
        simple_messages = []
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                continue
            elif isinstance(msg, HumanMessage):
                simple_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                simple_messages.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, ToolMessage):
                simple_messages.append({
                    "role": "tool",
                    "content": msg.content,
                    "tool_call_id": msg.tool_call_id
                })
        
        return {
            "messages": simple_messages,
            "todos": [],
            "files": {}
        }


class SimpleAgent:
    """Simple agent implementation without LangGraph that uses model's built-in tool calling."""
    
    def __init__(self, model, tools: List[BaseTool], system_prompt: str, max_iterations: int = 10, callback=None):
        self.model = model
        self.tools = {tool.name: tool for tool in tools}
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self.callback = callback
        
        # Bind tools to the model - convert to LangChain-compatible tools
        langchain_tools = []
        for tool in self.tools.values():
            if hasattr(tool, '_create_langchain_function'):
                langchain_tools.append(tool._create_langchain_function())
            else:
                langchain_tools.append(tool)
        
        self.model_with_tools = model.bind_tools(langchain_tools)
    
    def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main agent execution loop using model's built-in tool calling."""
        messages = []
        
        # Add system prompt
        messages.append(SystemMessage(content=self.system_prompt))
        
        # Add conversation history (all messages, not just the latest user message)
        if "messages" in input_data:
            for msg in input_data["messages"]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
                elif msg["role"] == "tool":
                    messages.append(ToolMessage(
                        content=msg["content"],
                        tool_call_id=msg.get("tool_call_id", "")
                    ))
        
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            
            # Get AI response with tools
            response = self.model_with_tools.invoke(messages)
            messages.append(response)
            
            # Check if AI wants to use tools
            if hasattr(response, 'tool_calls') and response.tool_calls:
                # Execute tool calls
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    
                    if tool_name in self.tools:
                        try:
                            # Notify callback of tool start
                            if self.callback:
                                self.callback.on_tool_start(tool_name, tool_args)
                            
                            # For tools that work without injected parameters
                            tool = self.tools[tool_name]
                            
                            # For all tools, call normally since they don't need injected parameters
                            result = tool.invoke(tool_args)
                            
                            # Notify callback of tool end
                            if self.callback:
                                self.callback.on_tool_end(tool_name, str(result))
                            
                            # Add tool result message
                            tool_message = ToolMessage(
                                content=str(result),
                                tool_call_id=tool_call["id"]
                            )
                            messages.append(tool_message)
                            
                        except Exception as e:
                            error_msg = f"Error executing tool {tool_name}: {str(e)}"
                            
                            # Notify callback of tool end with error
                            if self.callback:
                                self.callback.on_tool_end(tool_name, error_msg)
                            
                            tool_message = ToolMessage(
                                content=error_msg,
                                tool_call_id=tool_call["id"]
                            )
                            messages.append(tool_message)
                    else:
                        error_msg = f"Tool '{tool_name}' not found"
                        tool_message = ToolMessage(
                            content=error_msg,
                            tool_call_id=tool_call["id"]
                        )
                        messages.append(tool_message)
            else:
                # No tool calls, conversation is complete
                break
        
        # Convert messages back to simple format
        simple_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                continue  # Skip system messages in output
            elif isinstance(msg, HumanMessage):
                simple_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                simple_messages.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, ToolMessage):
                simple_messages.append({"role": "tool", "content": msg.content, "tool_call_id": msg.tool_call_id})
        
        return {
            "messages": simple_messages,
            "todos": [],
            "files": {}
        }


class HotelChatAgent:
    """LangChain agent for hotel-related chat functionality"""
    
    def __init__(self, db=None, hybrid_memory=None):
        self.db = db
        self.hybrid_memory = hybrid_memory
        self.llm = None
        self.simple_agent = None
        self.tools = []
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize all available tools"""
        
        # Initialize SerpAPI Hotels tool if API key is available
        # if hasattr(settings, 'serpapi_api_key') and settings.serpapi_api_key:
        #     self.tools.append(SerpAPIHotelsTool())
        
        # Initialize SerpAPI One Hotel tool if API key is available
        if hasattr(settings, 'serpapi_api_key') and settings.serpapi_api_key:
            self.tools.append(SerpAPIOneHotelTool())
            # self.tools.append(NewSerpAPIOneHotelTool())
        
        # Disable Tavily Web Search tool to ensure a single GPT-5 call per request
        
        # Initialize Apify Booking tool if API token is available
        # if hasattr(settings, 'apify_token') and settings.apify_token:
        #     self.tools.append(ApifyBookingTool())
        
    
    async def _initialize_llm(self):
        """Initialize the language model"""
        if self.llm is None and settings.openai_api_key:
            self.llm = ChatOpenAI(
                model=settings.open_api_model_name,
                temperature=0.5,
                openai_api_key=settings.openai_api_key
            )
        elif self.llm is None:
            # Fallback to a simple response generator
            logger.warning("OpenAI API key not configured. Using fallback response generator.")
            self.llm = self._create_fallback_llm()
    
    def _create_fallback_llm(self):
        """Create a fallback LLM when OpenAI is not available"""
        class FallbackLLM:
            async def ainvoke(self, messages, **kwargs):
                # Simple fallback response
                return AIMessage(content="I'm here to help with your hotel inquiries! Please ask me about hotels, bookings, amenities, or travel information.")
        return FallbackLLM()
    
    async def _create_simple_agent(self, system_prompt: str, callback=None):
        """Create the SimpleAgent with tools and system prompt"""
        if self.simple_agent is None:
            await self._initialize_llm()
            
            # Check if we should use the optimized async agent
            use_async_agent = settings.use_async_agent if hasattr(settings, 'use_async_agent') else True
            
            if use_async_agent:
                # 🚀 Use optimized AsyncSimpleAgent (parallel tool execution)
                logger.info("🚀 Using optimized AsyncSimpleAgent with parallel tool execution")
                enabled_tools = [tool for tool in self.tools if tool.is_enabled()]
                
                self.simple_agent = AsyncSimpleAgent(
                    model=self.llm,
                    tools=enabled_tools,  # Direct tools, no conversion needed!
                    system_prompt=system_prompt,
                    max_iterations=settings.max_iteration_agent,
                    callback=callback
                )
            else:
                # Use old SimpleAgent (for backward compatibility)
                logger.info("⚠️ Using legacy SimpleAgent (sequential execution)")
                langchain_tools = []
                for tool in self.tools:
                    if tool.is_enabled():
                        langchain_tools.append(self._convert_to_langchain_tool(tool))
                
                self.simple_agent = SimpleAgent(
                    model=self.llm,
                    tools=langchain_tools,
                    system_prompt=system_prompt,
                    max_iterations=settings.max_iteration_agent,
                    callback=callback
                )
    
    def _convert_to_langchain_tool(self, tool):
        """Convert our custom tool to LangChain tool format"""
        
        if tool.name == "serpapi_hotels":
            def serpapi_function(**kwargs):
                # Convert kwargs to dict
                input_dict = kwargs
                
                # Run the async execute method synchronously
                try:
                    # Check if we're already in an event loop
                    loop = asyncio.get_running_loop()
                    # If we're in a running loop, we need to use a different approach
                    import concurrent.futures
                    import threading
                    
                    # Create a new event loop in a separate thread
                    def run_in_thread():
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            return new_loop.run_until_complete(tool.execute(input_dict))
                        finally:
                            new_loop.close()
                    
                    # Run in a separate thread to avoid event loop conflicts
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_in_thread)
                        result: ToolResult = future.result()
                    
                except RuntimeError:
                    # No running loop, safe to use run_until_complete
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result: ToolResult = loop.run_until_complete(tool.execute(input_dict))
                    finally:
                        loop.close()
                
                return result.result
            
            return StructuredTool.from_function(
                func=serpapi_function,
                name=tool.name,
                description=tool.description,
                args_schema=SerpAPIHotelsInput
            )
        
        elif tool.name == "pinecone_retrieve":
            def pinecone_function(**kwargs):
                # Convert kwargs to dict
                input_dict = kwargs
                
                # Run the async execute method synchronously
                try:
                    # Check if we're already in an event loop
                    loop = asyncio.get_running_loop()
                    # If we're in a running loop, we need to use a different approach
                    import concurrent.futures
                    import threading
                    
                    # Create a new event loop in a separate thread
                    def run_in_thread():
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            return new_loop.run_until_complete(tool.execute(input_dict))
                        finally:
                            new_loop.close()
                    
                    # Run in a separate thread to avoid event loop conflicts
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_in_thread)
                        result: ToolResult = future.result()
                    
                except RuntimeError:
                    # No running loop, safe to use run_until_complete
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result: ToolResult = loop.run_until_complete(tool.execute(input_dict))
                    finally:
                        loop.close()
                
                return result.result
            
            return StructuredTool.from_function(
                func=pinecone_function,
                name=tool.name,
                description=tool.description,
                args_schema=PineconeRetrieveInput
            )
        
        elif tool.name == "tavily_web_search":
            def tavily_function(**kwargs):
                # Convert kwargs to dict
                input_dict = kwargs
                
                # Run the async execute method synchronously
                try:
                    # Check if we're already in an event loop
                    loop = asyncio.get_running_loop()
                    # If we're in a running loop, we need to use a different approach
                    import concurrent.futures
                    import threading
                    
                    # Create a new event loop in a separate thread
                    def run_in_thread():
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            return new_loop.run_until_complete(tool.execute(input_dict))
                        finally:
                            new_loop.close()
                    
                    # Run in a separate thread to avoid event loop conflicts
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_in_thread)
                        result: ToolResult = future.result()
                    
                except RuntimeError:
                    # No running loop, safe to use run_until_complete
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result: ToolResult = loop.run_until_complete(tool.execute(input_dict))
                    finally:
                        loop.close()
                
                return result.result
            
            return StructuredTool.from_function(
                func=tavily_function,
                name=tool.name,
                description=tool.description,
                args_schema=TavilyWebSearchInput
            )
        
        elif tool.name == "apify_booking":
            def apify_function(**kwargs):
                # Convert kwargs to dict
                input_dict = kwargs
                
                # Run the async execute method synchronously
                try:
                    # Check if we're already in an event loop
                    loop = asyncio.get_running_loop()
                    # If we're in a running loop, we need to use a different approach
                    import concurrent.futures
                    import threading
                    
                    # Create a new event loop in a separate thread
                    def run_in_thread():
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            return new_loop.run_until_complete(tool.execute(input_dict))
                        finally:
                            new_loop.close()
                    
                    # Run in a separate thread to avoid event loop conflicts
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_in_thread)
                        result: ToolResult = future.result()
                    
                except RuntimeError:
                    # No running loop, safe to use run_until_complete
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result: ToolResult = loop.run_until_complete(tool.execute(input_dict))
                    finally:
                        loop.close()
                
                return result.result
            
            return StructuredTool.from_function(
                func=apify_function,
                name=tool.name,
                description=tool.description,
                args_schema=ApifyBookingInput
            )
        
        else:
            # Fallback for other tools
            def tool_function(input_str: str):
                # Handle different input types
                import json
                if isinstance(input_str, dict):
                    # Already a dictionary, use it directly
                    input_data = input_str
                else:
                    # Try to parse as JSON string
                    try:
                        input_data = json.loads(input_str)
                    except (json.JSONDecodeError, TypeError):
                        # Fallback to string input for backward compatibility
                        input_data = input_str
                
                # Run the async execute method synchronously
                try:
                    # Check if we're already in an event loop
                    loop = asyncio.get_running_loop()
                    # If we're in a running loop, we need to use a different approach
                    import concurrent.futures
                    import threading
                    
                    # Create a new event loop in a separate thread
                    def run_in_thread():
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            return new_loop.run_until_complete(tool.execute(input_data))
                        finally:
                            new_loop.close()
                    
                    # Run in a separate thread to avoid event loop conflicts
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_in_thread)
                        result: ToolResult = future.result()
                    
                except RuntimeError:
                    # No running loop, safe to use run_until_complete
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result: ToolResult = loop.run_until_complete(tool.execute(input_data))
                    finally:
                        loop.close()
                
                return result.result
            
            return Tool(
                name=tool.name,
                description=tool.description,
                func=tool_function
            )
    def get_current_date(self):
        """Get the current date"""
        return "Current date is: " + datetime.now().strftime("%Y-%m-%d") + " (UTC) and it is " + datetime.now().strftime("%A")

    def _get_system_prompt(self, user_context: dict = None) -> str:
        """Get the system prompt for the hotel chat agent"""
        from datetime import datetime
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_day = datetime.now().strftime("%A")
        
        # Build comprehensive personalization context if available
        personalization_context = ""
        if user_context and user_context.get("travel_preferences"):
            from app.services.traveller_type_service import TravellerTypeService
            preferences = user_context["travel_preferences"]
            traveller_type = preferences.traveller_type
            
            # Check if traveller_type is not None before accessing its value
            if traveller_type:
                description = TravellerTypeService.get_traveller_type_description(traveller_type)
                recommendations = TravellerTypeService.get_traveller_type_recommendations(traveller_type)
                
                # Log personalization for debugging
                logger.info(f"Personalizing response for traveller type: {traveller_type.value}")
                
                # Build detailed preference context for the prompt
                personalization_context = f"""
PERSONALIZATION CONTEXT:
USER TRAVELLER TYPE: {traveller_type.value.replace('_', ' ').title()}
DESCRIPTION: {description}

PERSONALIZED RECOMMENDATIONS FOR THIS USER:
{chr(10).join(f"• {rec}" for rec in recommendations)}

HOTEL SEARCH PERSONALIZATION RULES:
When using serpapi_hotels tool, ALWAYS apply these preferences:

HOTEL CLASS PREFERENCES:
- {traveller_type.value.replace('_', ' ').title()}: {self._get_hotel_class_guidance(traveller_type)}

AMENITY PREFERENCES:
- {traveller_type.value.replace('_', ' ').title()}: {self._get_amenity_guidance(traveller_type)}

CRITICAL PERSONALIZATION RULES:
- ALWAYS include relevant amenity codes in serpapi_hotels calls based on traveller type
- ALWAYS set appropriate hotel_class parameter based on traveller type
- ALWAYS set appropriate guest counts based on travel_crew preferences (adults/children parameters)
- ALWAYS explain WHY recommendations match their traveller type and travel crew
- Use their specific preferences to filter and rank all recommendations

EXAMPLE: If they're a "Luxury Seeker" travelling as "Couple", always include hotel_class: "5", adults: 2, children: 0, and amenities: "10,8,22,35,52" (spa, restaurant, room service, wifi, all-inclusive).
"""
            else:
                # Log when traveller_type is None
                logger.info("Traveller type is None - using default recommendations")
        else:
            # Log when no traveller type is available
            logger.info("No traveller type found - using default recommendations")
        
        # Build the system prompt in parts to avoid f-string nesting issues
        base_prompt = f"""You are Staicey, an Australian AI travel buddy with a warm, witty personality. You're like a boutique hotel concierge with humor who helps users find perfect accommodations.

Current date: {current_date} ({current_day})
{personalization_context}

PERSONALITY & STYLE:
- Warm, witty, organized friend who finds the best deals
- Use Australian slang naturally, inject humor and gentle sass
- Plain text only (no markdown/emojis), brief summaries
- Australian English, AUD currency

CORE RULES:
1. NEVER HALLUCINATE - Only use verified information from tools
2. USE TOOLS ONLY WHEN NEEDED - Don't call tools for general conversation or questions you can answer directly
3. AUTO-CALCULATE dates from relative expressions ("next weekend" = Friday-Sunday)
4. DEFAULT DATES: Use THIS WEEKEND if user says "no dates", "any dates", or "flexible dates"
5. ASK FOR CLARIFICATION if missing location/guests details
6. PERSONALIZE everything based on user's traveller type - explain WHY recommendations fit their style

TOOL USAGE GUIDELINES:
- serpapi_hotels: ONLY when user asks for hotel/accommodation searches, bookings, or property recommendations
- tavily_web_search: ONLY for real-time information, current events, weather, local attractions, restaurants, or recent news
- NO TOOLS needed for: one specific hotel inqury, greetings, general travel advice, explanations, follow-up questions, or conversation

WHEN TO USE EACH TOOL:
- Hotel searches: "Find hotels in Sydney", "Book accommodation", "5-star hotels near beach"
- Web search: "What's the weather like?", "Best restaurants in Melbourne", "Current events in Brisbane"
- General chat: "Hello", "Tell me about Australia", "What should I pack?" - NO TOOLS NEEDED

RESPONSE FLOW:
1. If user needs hotel search → Use serpapi_hotels tool, Do not include any hotel info including price, amenities, location and etc in response message
2. If user needs best price for one specific hotel, find recent blogs from booking.com & expedia, kayak and respond correctly using citation
3. If user needs real-time info → Use tavily_web_search tool  
4. If general conversation → Respond directly without tools
5. When use serpapi tool, do not include any hotel info including price, amenities, location and etc in response message
6. Mention calculated dates when using relative expressions
7. Personalize recommendations and explain why they fit the user's travel style
8. Use language that resonates with their traveller type

Remember: You're Staicey - the organized, funny friend who finds the best deals!"""

        return base_prompt
    
    def _get_hotel_class_guidance(self, traveller_type) -> str:
        """Get hotel class guidance for a traveller type"""
        if not traveller_type:
            return "Use hotel_class: '' (default)"
            
        guidance = {
            "business_traveller": "Use hotel_class: '' ()",
            "family_holidaymaker": "Use hotel_class: '' (family-friendly range)",
            "luxury_seeker": "Use hotel_class: '4, 5' (4, 5-star only for luxury)",
            "couples_on_getaways": "Use hotel_class: '3,4,5' (romantic 3,4,5 star)",
            "budget_conscious_traveller": "Use hotel_class: '' (budget to mid-range)",
            "adventure_outdoor_enthusiast": "Use hotel_class: '' (mid-range for adventure)",
            "cultural_culinary_traveller": "Use hotel_class: '' (range for cultural experiences)",
            "solo_explorer": "Use hotel_class: '' ()",
            "event_goer": "Use hotel_class: '' ()",
            "group_trip_planner": "Use hotel_class: '' ()",
            "frequent_short_tripper": "Use hotel_class: '' ()"
        }
        return guidance.get(traveller_type.value, "Use hotel_class: '' (default range)")
    
    def _get_amenity_guidance(self, traveller_type) -> str:
        """Get amenity guidance for a traveller type"""
        if not traveller_type:
            return "Use amenities: '' ()"
            
        guidance = {
            "business_traveller": "Use amenities: '35,22' (WiFi, room service)",
            "family_holidaymaker": "Use amenities: '12,6' (child-friendly, pool)",
            "luxury_seeker": "Use amenities: '10,22,52' (spa, room service, all-inclusive)",
            "couples_on_getaways": "Use amenities: '10,15' (spa, bar)",
            "budget_conscious_traveller": "Use amenities: '' (breakfast)",
            "adventure_outdoor_enthusiast": "Use amenities: '7,1' (fitness, parking)",
            "cultural_culinary_traveller": "Use amenities: '8,35,15' (restaurant, WiFi, bar)",
            "solo_explorer": "Use amenities: '35,7,15' (WiFi, fitness, bar)",
            "event_goer": "Use amenities: '15,22' (bar, room service)",
            "group_trip_planner": "Use amenities: '8,6' (restaurant, pool)",
            "frequent_short_tripper": "Use amenities: '1' (parking)"
        }
        return guidance.get(traveller_type.value, "Use amenities: '' ()")
    
    def _format_travel_crew_list(self, travel_crew_list) -> str:
        """Format travel crew list for display in system prompt"""
        if not travel_crew_list:
            return "Not specified"
        
        formatted_crews = []
        for crew in travel_crew_list:
            formatted_crews.append(crew.value.replace('_', ' ').title())
        
        return ", ".join(formatted_crews)
    
    def _get_guest_count_guidance(self, travel_crew_list) -> str:
        """Get guest count guidance based on travel crew preferences"""
        if not travel_crew_list:
            return "Use adults: 2, children: 0 (default)"
        
        # Use the first travel crew type as primary preference
        primary_crew = travel_crew_list[0]
        
        guidance = {
            "solo": "Use adults: 1, children: 0 (solo traveler)",
            "couple": "Use adults: 2, children: 0 (couple)",
            "family": "Use adults: 2, children: 2 (typical family with children)",
            "group": "Use adults: 4, children: 0 (group of friends)",
            "business": "Use adults: 1, children: 0 (business traveler)"
        }
        
        return guidance.get(primary_crew.value, "Use adults: 2, children: 0 (default)")
    
    def _get_default_guest_counts(self, travel_crew_list) -> tuple[int, int]:
        """Get default adult and children counts based on travel crew preferences"""
        if not travel_crew_list:
            return (2, 0)  # Default
        
        # Use the first travel crew type as primary preference
        primary_crew = travel_crew_list[0]
        
        defaults = {
            "solo": (1, 0),
            "couple": (2, 0),
            "family": (2, 2),
            "group": (4, 0),
            "business": (1, 0)
        }
        
        return defaults.get(primary_crew.value, (2, 0))
    
    async def _get_chat_history(self, session_id: str) -> List:
        """
        Retrieve chat history for the session
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of LangChain BaseMessage objects
        """
        if self.hybrid_memory:
            try:
                return await self.hybrid_memory.get_conversation_history(session_id)
            except Exception as e:
                logger.error(f"Error retrieving chat history for session {session_id}: {e}")
                return []
        return []
    
    async def _get_user_context(self, request: ChatRequest) -> dict:
        """Get user context including traveller type and full preferences if available"""
        user_context = {}
        
        # Try to get user's travel preferences
        if hasattr(request, 'context') and request.context and request.context.get('user_id'):
            try:
                from app.services.travel_preferences_service import TravelPreferencesService
                from app.database import get_database
                
                db = await get_database()
                service = TravelPreferencesService(db)
                preferences = await service.get_user_travel_preferences(request.context['user_id'])
                
                if preferences:
                    user_context['traveller_type'] = preferences.traveller_type
                    user_context['travel_preferences'] = preferences
                else:
                    # Provide default traveller type when user has no preferences
                    from app.models.travel_preferences import TravellerType
                    user_context['traveller_type'] = TravellerType.FREQUENT_SHORT_TRIPPER
                    user_context['travel_preferences'] = None
                    logger.info(f"Using default traveller type for user {request.context['user_id']}")
                    
            except Exception as e:
                logger.warning(f"Could not retrieve user travel preferences: {e}")
                # Provide default traveller type on error
                from app.models.travel_preferences import TravellerType
                user_context['traveller_type'] = TravellerType.FREQUENT_SHORT_TRIPPER
                user_context['travel_preferences'] = None
        
        return user_context
    
    async def process_message(self, request: ChatRequest) -> StructuredChatResponse:
        """Process a chat message and return a structured response"""
        try:
            from datetime import datetime
        
            current_date = datetime.now().strftime("%Y-%m-%d")
            current_day = datetime.now().strftime("%A")
            # Generate session ID if not provided
            session_id = request.session_id or str(uuid.uuid4())
            
            # Get user context (traveller type and preferences) if available
            user_context = await self._get_user_context(request)
            
            # Retrieve chat history for context
            chat_history = await self._get_chat_history(session_id)
            
            # Create callback to track tool usage
            tool_callback = SimpleAgentToolCallback()
            
            # Generate personalized system prompt for this user
            system_prompt = self._get_system_prompt(user_context)
            
            NEW_INSTRUCTIONS = f"""
Your name is Staicey - the organized, funny friend who finds the best deals!
You are a AI travel assistant for focusing Australia accomadation with access to web search capabilities.
You can search for current information and think through problems.

Current date: {current_date} ({current_day})

<Task>
Your job is to use tools to gather information about the user's input topic.
You can use any of the tools provided to you to find resources that can help answer the research question. You can call these tools in series or in parallel, your research is conducted in a tool-calling loop.
After the research is done, You have to use serpapi_one_hotel tool to get the detailed info of each hotel from hotel names in response from web search.
</Task>

<Available Tools>
You have access to two main tools:
1. **tavily_search**: For conducting web searches to gather information
2. **think_tool**: For reflection and strategic planning during research
3. **serpapi_one_hotel**: After research is done, for the detailed information of hotel from hotel names in response from web search - (Only use this hotel info for hotel card, Do not include this info in response text)
Do not include this info in response.
**IMPORTANT**: When you find multiple hotel names, call serpapi_one_hotel for ALL of them in PARALLEL to reduce latency. Don't call with same name if previous one was successful.

**CRITICAL: Use think_tool after each search to reflect on results and plan next steps**
</Available Tools>

<Instructions>
Think like a human researcher with limited time. Follow these steps:

1. **Read the question carefully** - What specific information does the user need?
2. **Start with broader searches** - Use broad, comprehensive queries first
3. **After each search, pause and assess** - Do I have enough to answer? What's still missing?
4. **Execute narrower searches as you gather information** - Fill in the gaps
4. **If there are multiple hotel names in response, call serpapi_one_hotel for ALL of them in PARALLEL** - This reduces latency significantly
6. **Stop when you can answer with detaild hotel info confidently** - Don't keep searching for perfection
7. **If you have called 4 successful serpapi_one_hotel, Stop calling serpapi_one_hotel.**
</Instructions>

<Hard Limits>
**Tool Call Budgets** (Prevent excessive searching):
- **Simple queries**: Use 1-2 search tool calls maximum
- **Normal queries**: Use 2-3 search tool calls maximum
- **Very Complex queries**: Use up to 4 search tool calls maximum
- **Always stop**: After 3 search tool calls if you cannot find the right sources

**Stop Immediately When**:
- You can answer the user's question comprehensively
- You have 3+ relevant examples/sources for the question
- Your last 2 searches returned similar information
</Hard Limits>

<Show Your Thinking>
After each search tool call, use think_tool to analyze the results:
- What key information did I find?
- What's missing?
- Do I have enough to answer the question comprehensively?
- Should I search more or provide my answer?
</Show Your Thinking>

<Clear format>
different format for hotel name only and description.
make hotel name bold d.g. **Brisbane hotel**
</Clear format>

"""
            
            # Create simple agent with callback
            await self._create_simple_agent(NEW_INSTRUCTIONS, tool_callback)
            
            # Convert chat history to simple format for SimpleAgent
            simple_messages = []
            for msg in chat_history:
                if hasattr(msg, 'type'):
                    if msg.type == 'human':
                        simple_messages.append({"role": "user", "content": msg.content})
                    elif msg.type == 'ai':
                        simple_messages.append({"role": "assistant", "content": msg.content})
            
            # Add current user message
            simple_messages.append({"role": "user", "content": request.message})
            
            # Process with SimpleAgent (async if using AsyncSimpleAgent)
            if isinstance(self.simple_agent, AsyncSimpleAgent):
                response = await self.simple_agent.invoke({"messages": simple_messages})
            else:
                response = self.simple_agent.invoke({"messages": simple_messages})
            
            # Get tool usage information
            tool_usage_info = tool_callback.get_tool_usage_info()
            
            serpapi_used = tool_usage_info["serpapi_hotels_used"]
            tavily_used = tool_usage_info["tavily_web_search_used"]
            pinecone_used = tool_usage_info["pinecone_retrieve_used"]
            serpapi_one_hotel_used = tool_usage_info["serpapi_one_hotel_used"]
            
            # Debug logging for tool usage
            logger.info(f"Tool usage info: {tool_usage_info}")
            logger.info(f"SerpAPI hotels used: {serpapi_used}")
            logger.info(f"SerpAPI one_hotel used: {serpapi_one_hotel_used}")
            logger.info(f"Tavily used: {tavily_used}")
            logger.info(f"Tavily used: {tavily_used}")
            
            # Generate suggestions for the user's next message
            # Avoid extra LLM calls for suggestions: provide static, context-light suggestions
            suggestions = [
                "Find nearby attractions",
                "Show me luxury resorts",
                "Is there any transport to the hotel?"
            ]
            
            if serpapi_used:
                # Try to extract and format hotel search results
                hotel_search_raw_list = tool_usage_info["tool_outputs"].get("serpapi_hotels", [])
                # Get the last result if it's a list, otherwise use as-is
                hotel_search_raw = hotel_search_raw_list[-1] if isinstance(hotel_search_raw_list, list) and hotel_search_raw_list else hotel_search_raw_list
                
                logger.info(f"Hotel search raw output: {hotel_search_raw}")
                logger.info(f"Tool outputs keys: {list(tool_usage_info['tool_outputs'].keys())}")

                if hotel_search_raw:
                    # Parse the SerpAPI JSON output into HotelSearchResponse format
                    hotel_search = await self.parse_serpapi_hotel_results(hotel_search_raw)
                    
                    # Extract the latest assistant message from SimpleAgent response
                    assistant_messages = [msg for msg in response["messages"] if msg["role"] == "assistant"]
                    latest_response = assistant_messages[-1]["content"] if assistant_messages else "No response generated"
                    
                    return StructuredChatResponse(
                        message=latest_response,
                        hotelSearch=hotel_search,
                        session_id=session_id,
                        suggestions=suggestions,
                        metadata={
                            "model": settings.open_api_model_name if settings.openai_api_key else "fallback",
                            "history_length": len(chat_history)
                        }
                    )
            
            elif tavily_used or serpapi_one_hotel_used:
                # Handle both web search and hotel search results
                web_search = None
                hotel_search = None
                
                # Get web search results if tavily was used
                if tavily_used:
                    tavily_search_raw_list = tool_usage_info["tool_outputs"].get("tavily_web_search", [])
                    # Get the last result if it's a list, otherwise use as-is
                    tavily_search_raw = tavily_search_raw_list[-1] if isinstance(tavily_search_raw_list, list) and tavily_search_raw_list else tavily_search_raw_list
                    if tavily_search_raw:
                        web_search = await self.parse_tavily_web_search_results(tavily_search_raw)
                        logger.info(f"✅ Parsed web search results: {web_search.resultsTitle if web_search else None}")
                
                # Get hotel search results if serpapi_one_hotel was used
                if serpapi_one_hotel_used:
                    serpapi_one_hotel_raw_list = tool_usage_info["tool_outputs"].get("serpapi_one_hotel", [])
                    logger.info(f"🔍 Found {len(serpapi_one_hotel_raw_list)} serpapi_one_hotel result(s)")
                    logger.info(f"🔍 Raw list type: {type(serpapi_one_hotel_raw_list)}")
                    if serpapi_one_hotel_raw_list:
                        logger.info(f"🔍 First result preview: {str(serpapi_one_hotel_raw_list[0])[:300]}...")
                    
                    if serpapi_one_hotel_raw_list:
                        # Parse all results
                        parsed_results = []
                        for idx, raw_result in enumerate(serpapi_one_hotel_raw_list):
                            logger.info(f"🔍 Parsing serpapi_one_hotel result #{idx+1}/{len(serpapi_one_hotel_raw_list)}")
                            logger.info(f"🔍 Raw output preview: {raw_result[:200] if raw_result else None}...")
                            parsed = await self.parse_serpapi_one_hotel_results(raw_result)
                            if parsed:
                                parsed_results.append(parsed)
                                logger.info(f"✅ Parsed: {parsed.resultsTitle} with {len(parsed.results)} hotel(s)")
                        
                        # Merge all parsed results into one
                        hotel_search = await self.merge_multiple_hotel_results(parsed_results)
                        logger.info(f"✅ Final merged hotel search: {hotel_search.resultsTitle}")
                        logger.info(f"✅ Total hotels in merged result: {len(hotel_search.results)}")

                logger.info(f"🔍 Tool outputs keys: {list(tool_usage_info['tool_outputs'].keys())}")
                logger.info(f"🏨 HOTEL hotel_search is None: {hotel_search is None}")
                logger.info(f"🌐 WEB web_search is None: {web_search is None}")
                
                # Extract the latest assistant message from SimpleAgent response
                assistant_messages = [msg for msg in response["messages"] if msg["role"] == "assistant"]
                latest_response = ""
                last_index = -1
                while latest_response == "" and abs(last_index) < len(assistant_messages):
                    latest_response = assistant_messages[last_index]["content"] if assistant_messages else "No response generated"
                    last_index -= 1
                
                return StructuredChatResponse(
                    message=latest_response,
                    webSearch=web_search,
                    hotelSearch=hotel_search,
                    session_id=session_id,
                    suggestions=suggestions,
                    metadata={
                        "model": settings.open_api_model_name if settings.openai_api_key else "fallback",
                        "history_length": len(chat_history)
                    }
                )
            
            # Return regular chat response
            # Extract the latest assistant message from SimpleAgent response
            assistant_messages = [msg for msg in response["messages"] if msg["role"] == "assistant"]
            latest_response = assistant_messages[-1]["content"] if assistant_messages else "No response generated"
            
            return StructuredChatResponse(
                message=latest_response,
                hotelSearch=None,
                webSearch=None,
                session_id=session_id,
                suggestions=suggestions,
                metadata={
                    "model": settings.open_api_model_name if settings.openai_api_key else "fallback",
                    "history_length": len(chat_history)
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            # Generate fallback suggestions even on error
            try:
                suggestions = await self.generate_suggestions(request.message, [])
            except:
                suggestions = [
                    "Find hotels in Sydney CBD",
                    "Show me luxury resorts", 
                    "What's the best time to visit?"
                ]
            
            return StructuredChatResponse(
                message="I apologize, but I encountered an error processing your request. Please try again.",
                hotelSearch=None,
                webSearch=None,
                session_id=request.session_id or str(uuid.uuid4()),
                suggestions=suggestions,
                metadata={"error": str(e)}
            )
    
    async def process_message_with_progress(self, request: ChatRequest, progress_callback) -> StructuredChatResponse:
        """Process a chat message with real-time progress updates"""
        try:
            # Generate session ID if not provided
            session_id = request.session_id or str(uuid.uuid4())
            
            # Get user context (traveller type and preferences) if available
            user_context = await self._get_user_context(request)
            
            # Retrieve chat history for context
            chat_history = await self._get_chat_history(session_id)
            
            # Create REAL progress callback that tracks actual agent execution
            real_progress_callback = RealProgressCallback(progress_callback)
            
            # Send initial progress
            await real_progress_callback._send_progress(
                "starting", 
                "Starting AI processing...", 
                5
            )
            
            # Generate personalized system prompt for this user
            system_prompt = self._get_system_prompt(user_context)
            
            # Create simple agent with progress callback
            await self._create_simple_agent(system_prompt, real_progress_callback)
            
            # Convert chat history to simple format for SimpleAgent
            simple_messages = []
            for msg in chat_history:
                if hasattr(msg, 'type'):
                    if msg.type == 'human':
                        simple_messages.append({"role": "user", "content": msg.content})
                    elif msg.type == 'ai':
                        simple_messages.append({"role": "assistant", "content": msg.content})
            
            # Add current user message
            simple_messages.append({"role": "user", "content": request.message})
            
            await real_progress_callback._send_progress(
                "generating",
                "Searching Web...",
                25
            )
            
            # Process with SimpleAgent (async if using AsyncSimpleAgent)
            if isinstance(self.simple_agent, AsyncSimpleAgent):
                response = await self.simple_agent.invoke({"messages": simple_messages})
            else:
                response = self.simple_agent.invoke({"messages": simple_messages})
            
            # Send any pending progress updates that were collected during execution
            await real_progress_callback._send_pending_progress()
            
            # Send progress for suggestion generation
            await real_progress_callback._send_progress(
                "generating",
                "Generating follow-up suggestions...",
                90
            )
            
            # Get tool usage information
            tool_usage_info = real_progress_callback.get_tool_usage_info()
            
            serpapi_used = tool_usage_info["serpapi_hotels_used"]
            tavily_used = tool_usage_info["tavily_web_search_used"]
            pinecone_used = tool_usage_info["pinecone_retrieve_used"]
            serpapi_one_hotel_used = tool_usage_info["serpapi_one_hotel_used"]
            
            # Generate suggestions for the user's next message
            suggestions = await self.generate_suggestions(request.message, chat_history)
            
            # Send completion progress
            await real_progress_callback._send_progress(
                "completing",
                "Complete!",
                100
            )
            
            if serpapi_used:
                # Try to extract and format hotel search results
                hotel_search_raw_list = tool_usage_info["tool_outputs"].get("serpapi_hotels", [])
                # Get the last result if it's a list, otherwise use as-is
                hotel_search_raw = hotel_search_raw_list[-1] if isinstance(hotel_search_raw_list, list) and hotel_search_raw_list else hotel_search_raw_list

                if hotel_search_raw:
                    # Parse the SerpAPI JSON output into HotelSearchResponse format
                    hotel_search = await self.parse_serpapi_hotel_results(hotel_search_raw)
                    
                    # Extract the latest assistant message from SimpleAgent response
                    assistant_messages = [msg for msg in response["messages"] if msg["role"] == "assistant"]
                    latest_response = assistant_messages[-1]["content"] if assistant_messages else "No response generated"
                    
                    return StructuredChatResponse(
                        message=latest_response,
                        hotelSearch=hotel_search,
                        session_id=session_id,
                        suggestions=suggestions,
                        metadata={
                            "model": settings.open_api_model_name if settings.openai_api_key else "fallback",
                            "history_length": len(chat_history),
                            "real_progress": True
                        }
                    )
            
            elif tavily_used or serpapi_one_hotel_used:
                # Handle both web search and hotel search results
                web_search = None
                hotel_search = None
                
                # Get web search results if tavily was used
                if tavily_used:
                    tavily_search_raw_list = tool_usage_info["tool_outputs"].get("tavily_web_search", [])
                    # Get the last result if it's a list, otherwise use as-is
                    tavily_search_raw = tavily_search_raw_list[-1] if isinstance(tavily_search_raw_list, list) and tavily_search_raw_list else tavily_search_raw_list
                    if tavily_search_raw:
                        web_search = await self.parse_tavily_web_search_results(tavily_search_raw)
                
                # Get hotel search results if serpapi_one_hotel was used
                if serpapi_one_hotel_used:
                    serpapi_one_hotel_raw_list = tool_usage_info["tool_outputs"].get("serpapi_one_hotel", [])
                    logger.info(f"🔍 Found {len(serpapi_one_hotel_raw_list)} serpapi_one_hotel result(s) [with progress]")
                    logger.info(f"🔍 Raw list type: {type(serpapi_one_hotel_raw_list)}")
                    if serpapi_one_hotel_raw_list:
                        logger.info(f"🔍 First result preview: {str(serpapi_one_hotel_raw_list[0])[:300]}...")
                    
                    if serpapi_one_hotel_raw_list:
                        # Parse all results
                        parsed_results = []
                        for idx, raw_result in enumerate(serpapi_one_hotel_raw_list):
                            logger.info(f"🔍 Parsing serpapi_one_hotel result #{idx+1}/{len(serpapi_one_hotel_raw_list)}")
                            parsed = await self.parse_serpapi_hotel_results(raw_result)
                            if parsed:
                                parsed_results.append(parsed)
                                logger.info(f"✅ Parsed: {parsed.resultsTitle} with {len(parsed.results)} hotel(s)")
                        
                        # Merge all parsed results into one
                        hotel_search = await self.merge_multiple_hotel_results(parsed_results)
                        logger.info(f"✅ Final merged hotel search: {hotel_search.resultsTitle}")
                        logger.info(f"✅ Total hotels in merged result: {len(hotel_search.results)}")

                logger.info(f"🔍 Tool outputs keys: {list(tool_usage_info['tool_outputs'].keys())}")
                logger.info(f"🏨 HOTEL hotel_search: {hotel_search}")
                logger.info(f"🌐 WEB web_search: {web_search}")
                
                # Extract the latest assistant message from SimpleAgent response
                assistant_messages = [msg for msg in response["messages"] if msg["role"] == "assistant"]
                latest_response = assistant_messages[-1]["content"] if assistant_messages else "No response generated"
                
                return StructuredChatResponse(
                    message=latest_response,
                    webSearch=web_search,
                    hotelSearch=hotel_search,
                    session_id=session_id,
                    suggestions=suggestions,
                    metadata={
                        "model": settings.open_api_model_name if settings.openai_api_key else "fallback",
                        "history_length": len(chat_history),
                        "real_progress": True
                    }
                )
            
            # Return regular chat response
            # Extract the latest assistant message from SimpleAgent response
            assistant_messages = [msg for msg in response["messages"] if msg["role"] == "assistant"]
            latest_response = assistant_messages[-1]["content"] if assistant_messages else "No response generated"
            
            return StructuredChatResponse(
                message=latest_response,
                hotelSearch=None,
                webSearch=None,
                session_id=session_id,
                suggestions=suggestions,
                metadata={
                    "model": settings.open_api_model_name if settings.openai_api_key else "fallback",
                    "history_length": len(chat_history),
                    "real_progress": True
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing chat message with progress: {e}")
            # Send error progress
            if progress_callback:
                from app.chat.streaming_models import ProgressUpdate, ProgressPhase
                await progress_callback(ProgressUpdate(
                    phase=ProgressPhase.COMPLETE,
                    message=f"Error: {str(e)[:50]}...",
                    percentage=100,
                    details="Error occurred during processing"
                ))
            
            # Generate fallback suggestions even on error
            try:
                suggestions = await self.generate_suggestions(request.message, [])
            except:
                suggestions = [
                    "Find hotels in Sydney CBD",
                    "Show me luxury resorts", 
                    "What's the best time to visit?"
                ]
            
            return StructuredChatResponse(
                message="I apologize, but I encountered an error processing your request. Please try again.",
                hotelSearch=None,
                webSearch=None,
                session_id=request.session_id or str(uuid.uuid4()),
                suggestions=suggestions,
                metadata={"error": str(e), "real_progress": True}
            )
    
    async def generate_ai_note_for_hotel(self, hotel_data: dict) -> str:
        """
        Generate an AI note for a hotel using the LLM based on available hotel data
        
        Args:
            hotel_data: Dictionary containing hotel information
            
        Returns:
            String containing the AI-generated note
        """
        try:
            await self._initialize_llm()
            
            # Extract relevant hotel information
            name = hotel_data.get("name", "")
            rating = hotel_data.get("overall_rating")
            reviews = hotel_data.get("reviews")
            stars = hotel_data.get("extracted_hotel_class")
            amenities = hotel_data.get("amenities", [])
            price = hotel_data.get("rate_per_night", {}).get("lowest") if hotel_data.get("rate_per_night") else None
            description = hotel_data.get("description", "")
            
            # Create a prompt for the LLM
            prompt = f"""
            As a helpful hotel assistant, create a brief, personalized note explaining why this hotel might be the best choice for the traveller.
            
            Hotel Information:
            - Name: {name}
            - Rating: {rating}/5 if available
            - Number of reviews: {reviews} if available
            - Star rating: {stars} stars if available
            - Amenities: {', '.join(amenities) if amenities else 'Not specified'}
            - Price: ${price} per night if available
            - Description: {description}
            
            Create a personalized note that explains a key reason why this hotel stands out. Focus on:
            - Value for money (if price is competitive)
            - Outstanding reviews/ratings (if significantly high)
            - Premium amenities (if luxury features present)
            - Location advantages (if mentioned in description)
            - Unique selling points
            
            Make it sound like a personal recommendation from a friend. Examples:
            - "This trendy spot offers refined rooms with a bar/restaurant and complimentary breakfast. It's a great deal at $XXX per night, which is XX% less than usual. It's a short walk to the Museum, perfect for a romantic stroll."
            - "This contemporary high-rise hotel offers farm-to-table dining, a gym, and a cafe. It's priced at $XXX, a fantastic XX% off its usual rate. Located near the Royal Botanic Gardens, it's ideal for a relaxing day out."
            
            Keep it 4 sentences, unique (without greeting), and focus on several key reasons why this hotel is special, replace hotel name into this hotel or this one.
            Use Australian spelling.
            """
            
            # Generate the note using the LLM
            response = await self.llm.ainvoke([SystemMessage(content=prompt)])
            ai_note = response.content.strip()
            
            # Fallback if LLM response is too long or empty
            # if not ai_note or len(ai_note) > 150:
            if not ai_note:
                ai_note = "This looks like a solid choice!"
            
            return ai_note
            
        except Exception as e:
            logger.warning(f"Error generating AI note for hotel {hotel_data.get('name', 'Unknown')}: {e}")
            return "This looks like a solid choice!"

    async def merge_multiple_hotel_results(self, hotel_results_list: list) -> HotelSearchResponse:
        """
        Merge multiple HotelSearchResponse objects into one
        
        Args:
            hotel_results_list: List of HotelSearchResponse objects
            
        Returns:
            Single HotelSearchResponse with all hotels combined
        """
        if not hotel_results_list:
            return HotelSearchResponse(resultsTitle="Hotel Search Results", results=[])
        
        if len(hotel_results_list) == 1:
            return hotel_results_list[0]
        
        # Merge all results
        all_hotels = []
        for hotel_response in hotel_results_list:
            if hotel_response and hotel_response.results:
                all_hotels.extend(hotel_response.results)
        
        # Use the first title or create a generic one
        title = hotel_results_list[0].resultsTitle if hotel_results_list else "Hotel Search Results"
        
        logger.info(f"✅ Merged {len(hotel_results_list)} hotel search results into {len(all_hotels)} total hotels")
        
        return HotelSearchResponse(
            resultsTitle=title,
            results=all_hotels
        )
    
    async def parse_serpapi_hotel_results(self, serpapi_json_str: str) -> HotelSearchResponse:
        """
        Parse SerpAPI hotel search results JSON string into HotelSearchResponse format
        
        Args:
            serpapi_json_str: JSON string from SerpAPI hotel search
            
        Returns:
            HotelSearchResponse object with parsed hotel data
        """
        try:
            # Parse the JSON string
            import json
            data = json.loads(serpapi_json_str) if isinstance(serpapi_json_str, str) else serpapi_json_str
            
            # Extract search parameters for context
            search_params = data.get("search_parameters", {})
            query = search_params.get("q", "hotel search")
                        
            # Create results title
            results_title = f"Hotels in {query.split(' in ')[-1] if ' in ' in query else 'your search area'}"
            
            # Parse hotel properties
            properties = data.get("properties", [])
            
            # 🚀 OPTIMIZATION: Generate ALL AI notes in parallel
            logger.info(f"🔧 Generating AI notes for {len(properties)} hotels in parallel")
            start_time = asyncio.get_event_loop().time()
            
            ai_note_tasks = [self.generate_ai_note_for_hotel(prop) for prop in properties]
            ai_notes = await asyncio.gather(*ai_note_tasks, return_exceptions=True)
            
            duration = asyncio.get_event_loop().time() - start_time
            logger.info(f"✅ All AI notes generated in {duration:.2f}s (parallel)")
            
            # Build hotel results with pre-generated AI notes
            hotel_results = []
            
            for prop, ai_note in zip(properties, ai_notes):
                try:
                    # Handle errors in AI note generation
                    if isinstance(ai_note, Exception):
                        logger.warning(f"AI note generation failed for {prop.get('name')}: {ai_note}")
                        ai_note = "This looks like a solid choice!"
                    
                    # Extract basic info
                    name = prop.get("name")
                    description = prop.get("description")
                    link = prop.get("link")
                    rating = prop.get("overall_rating") or prop.get("rating")
                    reviews = prop.get("reviews")
                    stars = prop.get("extracted_hotel_class") or prop.get("stars")
                    
                    logger.info(f"🏨 Agent parsing - Hotel: {name}, Stars: {stars}, Overall rating: {rating}, Reviews: {reviews}")
                    
                    # Extract address and phone
                    address = prop.get("address", None)
                    phone = prop.get("phone", None)
                    
                    # Extract pricing - use actual price from data
                    rate_info = prop.get("rate_per_night", {})
                    price = rate_info.get("lowest") if rate_info else None
                    price_label = "Best Price"  # Default label
                    
                    # If main price is null, try to get price from extra_prices
                    if price is None:
                        extra_prices_data = prop.get("extra_prices", [])
                        if extra_prices_data and len(extra_prices_data) > 0:
                            # Get the first available price from extra_prices
                            first_extra_price = extra_prices_data[0].get("price")
                            if first_extra_price is not None:
                                price = first_extra_price
                    
                    # Use actual price from data, no fallbacks
                    if price is not None:
                        # Convert to string if it's a number
                        if isinstance(price, (int, float)):
                            price = f"${int(price)}"
                        else:
                            price = str(price)
                    
                    logger.info(f"🏨 Agent parsing - Hotel: {name}, Price: {price}, Rate info: {rate_info}, Extra prices: {prop.get('extra_prices', [])}")
                    
                    # Extract room type and source
                    room_type = None  # Default
                    source = prop.get("source")
                    source_url = prop.get("source_url")
                    
                    # Extract image URLs properly - handle both formats
                    image_urls = []
                    
                    # First try to get imageUrls directly (from cached data)
                    direct_image_urls = prop.get("imageUrls", [])
                    if direct_image_urls and isinstance(direct_image_urls, list):
                        image_urls.extend(direct_image_urls)
                    
                    # Then try to get images array (from SERP API)
                    images = prop.get("images", [])
                    for image in images:
                        if isinstance(image, dict):
                            # Handle dict format with original_image field
                            image_url = image.get("thumbnail") or image.get("original_image") or image.get("url")
                            if image_url:
                                image_urls.append(image_url)
                        elif isinstance(image, str):
                            # Handle direct string URL
                            image_urls.append(image)
                    
                    logger.info(f"🏨 Agent parsing - Hotel: {name}, Image URLs: {len(image_urls)} images")
                    logger.info(f"🏨 Agent parsing - Direct imageUrls: {len(direct_image_urls)}, Images array: {len(images)}")
                    
                    # Extract amenities
                    amenities = prop.get("amenities", [])
                    
                    # Extract coordinates
                    gps = prop.get("gps_coordinates", {})
                    lat = gps.get("latitude")
                    lng = gps.get("longitude")
                    
                    # Extract extra_prices
                    extra_prices_data = prop.get("extra_prices", [])
                    extra_prices = []
                    for extra_price_data in extra_prices_data:
                        extra_price = ExtraPrice(
                            source=extra_price_data.get("source"),
                            source_url=extra_price_data.get("source_url"),
                            price=extra_price_data.get("price")
                        )
                        extra_prices.append(extra_price)
                    
                    # AI note already generated (from parallel batch above)
                    
                    # Create HotelResult with proper sourceUrl mapping
                    hotel_result = HotelResult(
                        id=prop.get("property_token"),
                        name=name,
                        link=link,
                        description=description,
                        rating=rating,
                        reviews=reviews,
                        stars=stars,
                        address=address,
                        phone=phone,
                        features=amenities,
                        price=price,
                        priceLabel=price_label,
                        roomType=room_type,
                        source=source,
                        sourceUrl=source_url or link or "",  # Use source_url first, fallback to link
                        imageUrls=image_urls,
                        aiNote=ai_note,
                        position=HotelPosition(lat=lat, lng=lng) if lat and lng else None,
                        extra_prices=extra_prices if extra_prices else None
                    )
                    
                    logger.info(f"🏨 Agent parsing - Final HotelResult: {name}, Price: {hotel_result.price}, SourceUrl: {hotel_result.sourceUrl}")
                    hotel_results.append(hotel_result)
                    
                except Exception as e:
                    logger.warning(f"Error parsing hotel property: {e}")
                    continue
            
            return HotelSearchResponse(
                resultsTitle=results_title,
                results=hotel_results
            )
            
        except Exception as e:
            logger.error(f"Error parsing SerpAPI results: {e}")
            # Return a fallback response
            return HotelSearchResponse(
                resultsTitle="Hotel Search Results",
                results=[]
            )

    async def parse_serpapi_one_hotel_results(self, serpapi_json_str: str) -> HotelSearchResponse:
        """
        Parse SerpAPI hotel search results JSON string into HotelSearchResponse format
        
        Args:
            serpapi_json_str: JSON string from SerpAPI hotel search
            
        Returns:
            HotelSearchResponse object with parsed hotel data
        """
        try:
            # Parse the JSON string
            import json
            data = json.loads(serpapi_json_str) if isinstance(serpapi_json_str, str) else serpapi_json_str
            
            # Extract search parameters for context
            search_params = data.get("search_parameters", {})
            query = search_params.get("q", "hotel search")
                        
            # Create results title
            results_title = f"Hotels in {query.split(' in ')[-1] if ' in ' in query else 'your search area'}"
            
            # Parse hotel properties
            properties = data.get("properties", [])
            
            # 🚀 OPTIMIZATION: Generate ALL AI notes in parallel
            logger.info(f"🔧 Generating AI notes for {len(properties)} hotels in parallel")
            start_time = asyncio.get_event_loop().time()
            
            ai_note_tasks = [self.generate_ai_note_for_hotel(prop) for prop in properties]
            ai_notes = await asyncio.gather(*ai_note_tasks, return_exceptions=True)
            
            duration = asyncio.get_event_loop().time() - start_time
            logger.info(f"✅ All AI notes generated in {duration:.2f}s (parallel)")
            
            # Build hotel results with pre-generated AI notes
            hotel_results = []
            
            for prop, ai_note in zip(properties, ai_notes):
                try:
                    # Handle errors in AI note generation
                    if isinstance(ai_note, Exception):
                        logger.warning(f"AI note generation failed for {prop.get('name')}: {ai_note}")
                        ai_note = "This looks like a solid choice!"
                    
                    # Extract basic info
                    name = prop.get("name")
                    description = prop.get("description")
                    link = prop.get("link")
                    rating = prop.get("overall_rating") or prop.get("rating")
                    reviews = prop.get("reviews")
                    stars = prop.get("extracted_hotel_class") or prop.get("hotel_class")
                    
                    logger.info(f"🏨 Agent parsing - Hotel: {name}, Stars: {stars}, Overall rating: {rating}, Reviews: {reviews}")
                    
                    # Extract address and phone
                    address = prop.get("address", None)
                    phone = prop.get("phone", None)
                    
                    # Extract pricing - use actual price from data
                    rate_info = prop.get("rate_per_night", {})
                    price = rate_info.get("lowest") if rate_info else None
                    price_label = "Best Price"  # Default label
                    
                    # If main price is null, try to get price from extra_prices
                    if price is None:
                        extra_prices_data = prop.get("extra_prices", [])
                        if extra_prices_data and len(extra_prices_data) > 0:
                            # Get the first available price from extra_prices
                            first_extra_price = extra_prices_data[0].get("price")
                            if first_extra_price is not None:
                                price = first_extra_price
                    
                    # Use actual price from data, no fallbacks
                    if price is not None:
                        # Convert to string if it's a number
                        if isinstance(price, (int, float)):
                            price = f"${int(price)}"
                        else:
                            price = str(price)
                    
                    logger.info(f"🏨 Agent parsing - Hotel: {name}, Price: {price}, Rate info: {rate_info}, Extra prices: {prop.get('extra_prices', [])}")
                    
                    # Extract room type and source
                    room_type = None  # Default
                    source = prop.get("source")
                    source_url = prop.get("source_url")
                    
                    # Extract image URLs properly - handle both formats
                    image_urls = []
                    
                    # First try to get imageUrls directly (from cached data)
                    direct_image_urls = prop.get("imageUrls", [])
                    if direct_image_urls and isinstance(direct_image_urls, list):
                        image_urls.extend(direct_image_urls)
                    
                    # Then try to get images array (from SERP API)
                    images = prop.get("images", [])
                    for image in images:
                        if isinstance(image, dict):
                            # Handle dict format with original_image field
                            image_url = image.get("thumbnail") or image.get("original_image") or image.get("url")
                            if image_url:
                                image_urls.append(image_url)
                        elif isinstance(image, str):
                            # Handle direct string URL
                            image_urls.append(image)
                    
                    logger.info(f"🏨 Agent parsing - Hotel: {name}, Image URLs: {len(image_urls)} images")
                    logger.info(f"🏨 Agent parsing - Direct imageUrls: {len(direct_image_urls)}, Images array: {len(images)}")
                    
                    # Extract amenities
                    amenities = prop.get("amenities", [])
                    
                    # Extract coordinates
                    gps = prop.get("gps_coordinates", {})
                    lat = gps.get("latitude")
                    lng = gps.get("longitude")
                    
                    # Extract extra_prices
                    extra_prices_data = prop.get("extra_prices", [])
                    extra_prices = []
                    for extra_price_data in extra_prices_data:
                        extra_price = ExtraPrice(
                            source=extra_price_data.get("source"),
                            source_url=extra_price_data.get("source_url"),
                            price=extra_price_data.get("price")
                        )
                        extra_prices.append(extra_price_data)
                    
                    # AI note already generated (from parallel batch above)
                    
                    # Create HotelResult with proper sourceUrl mapping
                    hotel_result = HotelResult(
                        id=prop.get("property_token"),
                        name=name,
                        link=link,
                        description=description,
                        rating=rating,
                        reviews=reviews,
                        stars=stars,
                        address=address,
                        phone=phone,
                        features=amenities,
                        price=price,
                        priceLabel=price_label,
                        roomType=room_type,
                        source=source,
                        sourceUrl=source_url or link or "",  # Use source_url first, fallback to link
                        imageUrls=image_urls,
                        aiNote=ai_note,
                        position=HotelPosition(lat=lat, lng=lng) if lat and lng else None,
                        extra_prices=extra_prices if extra_prices else None
                    )
                    
                    logger.info(f"🏨 Agent parsing - Final HotelResult: {name}, Price: {hotel_result.price}, SourceUrl: {hotel_result.sourceUrl}")
                    hotel_results.append(hotel_result)
                    
                except Exception as e:
                    logger.warning(f"Error parsing hotel property: {e}")
                    continue
            
            return HotelSearchResponse(
                resultsTitle=results_title,
                results=hotel_results
            )
            
        except Exception as e:
            logger.error(f"Error parsing SerpAPI results: {e}")
            # Return a fallback response
            return HotelSearchResponse(
                resultsTitle="Hotel Search Results",
                results=[]
            )

    async def parse_tavily_web_search_results(self, tavily_json_str: str) -> WebSearchResponse:
        """
        Parse Tavily web search results JSON string into WebSearchResponse format
        
        Args:
            tavily_json_str: JSON string from Tavily web search
            
        Returns:
            WebSearchResponse object with parsed web search data and images
        """
        try:
            # Parse the JSON string
            import json
            data = json.loads(tavily_json_str) if isinstance(tavily_json_str, str) else tavily_json_str
            
            # Extract search query for context
            query = data.get("query", "web search")
            
            # Create results title
            results_title = f"Images for: {query}"
            
            # Parse images only (skip the full results)
            images_data = data.get("images", [])
            images = []
            
            for img in images_data:
                try:
                    web_search_image = WebSearchImage(
                        url=img.get("url", ""),
                        description=img.get("description")
                    )
                    images.append(web_search_image)
                except Exception as e:
                    logger.warning(f"Error parsing image: {e}")
                    continue
            
            return WebSearchResponse(
                resultsTitle=results_title,
                images=images
            )
            
        except Exception as e:
            logger.error(f"Error parsing Tavily results: {e}")
            # Return a fallback response
            return WebSearchResponse(
                resultsTitle="Images",
                images=[]
            )

    async def generate_suggestions(self, user_message: str, chat_history: List = None) -> List[str]:
        """
        Generate 1 or 2 relevant suggestions for the user's next message based on their current message and chat context
        
        Args:
            user_message: The user's current message
            chat_history: Previous conversation history
            
        Returns:
            List of 3 suggestion strings
        """
        try:
            return [
                "Find nearby attractions",
                "Show me luxury resorts", 
                "Is there any transport to the hotel?"
            ]
            # Create context from chat history
            context = ""
            if chat_history and len(chat_history) > 0:
                # Get last few messages for context
                recent_messages = chat_history[-4:]  # Last 4 messages
                context = "Recent conversation context:\n"
                for msg in recent_messages:
                    if hasattr(msg, 'content'):
                        role = "User" if hasattr(msg, 'type') and msg.type == 'human' else "Assistant"
                        context += f"{role}: {msg.content}\n"
            
            # Create prompt for suggestion generation
            prompt = f"""
            As an Australia hotel agent, generate 2 helpful suggestions for what the user might want to ask next.
            
            User's current message: "{user_message}"
            
            {context}
            
            Generate 1-2 natural, conversational suggestions that would be helpful for a hotel booking assistant.
            Focus on:
            - Hotel search queries (different locations, dates, preferences)
            - Booking-related questions (amenities, policies, pricing)
            - Travel planning questions (attractions, transportation, recommendations)
            - Follow-up questions about specific hotels or areas
            
            Make the suggestions:
            - Natural and conversational (like a real person would ask)
            - Relevant to Australia hotels and travel
            - Varied in type (search, questions, planning)
            - Under 50 characters each
            - Specific and actionable
            - Do not include "you" or "your"
            
            Return only the 3 suggestions, one per line, no numbering or formatting:
            """
            
            # Use the agent's LLM to generate suggestions
            await self._initialize_llm()
            if self.llm:
                response = await self.llm.ainvoke([SystemMessage(content=prompt)])
                suggestions_text = response.content.strip()
                
                # Parse the suggestions
                suggestions = []
                lines = suggestions_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith(('1.', '2.', '3.', '-', '*', '•')):
                        # Clean up the suggestion
                        suggestion = line.strip('"').strip("'").strip()
                        if suggestion and len(suggestion) <= 50:
                            suggestions.append(suggestion)
                
                # Ensure we have exactly 3 suggestions
                if len(suggestions) >= 3:
                    return suggestions[:3]
                elif len(suggestions) > 0:
                    # Pad with default suggestions if needed
                    default_suggestions = [
                        "Find hotels in Sydney CBD",
                        "Show me luxury resorts",
                        "What's the best time to visit?"
                    ]
                    while len(suggestions) < 3:
                        suggestions.append(default_suggestions[len(suggestions)])
                    return suggestions
                else:
                    # Fallback suggestions
                    return [
                        "Find hotels in Sydney CBD",
                        "Show me luxury resorts", 
                        "What's the best time to visit?"
                    ]
            else:
                # Fallback suggestions when LLM is not available
                return [
                    "Find hotels in Sydney CBD",
                    "Show me luxury resorts",
                    "What's the best time to visit?"
                ]
                
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            # Return fallback suggestions
            return [
                "Find hotels in Sydney CBD",
                "Show me luxury resorts",
                "What's the best time to visit?"
            ]

