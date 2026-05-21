import os
import json
import re
from typing import Dict, List, Any, Optional

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)

from datetime import datetime

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import BaseTool

from deep_agents_from_scratch.file_tools import ls, read_file, write_file
from deep_agents_from_scratch.prompts import (
    FILE_USAGE_INSTRUCTIONS,
    RESEARCHER_INSTRUCTIONS,
    SUBAGENT_USAGE_INSTRUCTIONS,
    TODO_USAGE_INSTRUCTIONS,
)
from deep_agents_from_scratch.research_tools import think_tool, get_today_str
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

@tool
def simple_search(query: str, max_results: int = 3) -> str:
    """Search the web for current information using Tavily.
    
    Args:
        query: The search query to execute
        max_results: Maximum number of results to return (default: 3)
    
    Returns:
        A formatted string with search results
    """
    try:
        llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-5"))
        prompt = (
            "Return Tavily-compatible JSON for a web search with fields: query, results[{title,url,content}]. "
            f"Max results: {max_results}. Query: {query}"
        )
        ai = llm.invoke([HumanMessage(content=prompt)])
        data = json.loads(ai.content) if ai and isinstance(ai.content, str) else {"results": []}

        results = []
        for result in data.get("results", []):
            title = result.get("title", "No title")
            url = result.get("url", "No URL")
            content = result.get("content", "No content available")
            results.append(f"**{title}**\nURL: {url}\nContent: {content[:300]}...\n")

        if not results:
            return "No search results found."
        return "\n".join(results)
    except Exception as e:
        return f"Search error: {str(e)}"

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


class SimpleAgent:
    """Simple agent implementation without LangGraph that uses model's built-in tool calling."""
    
    def __init__(self, model, tools: List[BaseTool], system_prompt: str, max_iterations: int = 10):
        self.model = model
        self.tools = {tool.name: tool for tool in tools}
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        
        # Bind tools to the model
        self.model_with_tools = model.bind_tools(list(self.tools.values()))
    
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
                            # For tools that work without injected parameters
                            tool = self.tools[tool_name]
                            
                            # For all tools, call normally since they don't need injected parameters
                            result = tool.invoke(tool_args)
                            
                            # Add tool result message
                            tool_message = ToolMessage(
                                content=str(result),
                                tool_call_id=tool_call["id"]
                            )
                            messages.append(tool_message)
                            
                        except Exception as e:
                            error_msg = f"Error executing tool {tool_name}: {str(e)}"
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


# Initialize the model
model = init_chat_model(model="openai:gpt-5", temperature=0.0)

# Limits
max_concurrent_research_units = 3
max_researcher_iterations = 3

# Tools - only use tools that don't require LangGraph injected parameters
# These tools work without LangGraph dependencies
simple_tools = [simple_search, think_tool]  # Only use tools that don't need injected state

# Build prompt
INSTRUCTIONS = (
    "# RESEARCH ASSISTANT\n"
    + "You're Staicey - the organized, funny friend who finds the best deals!"
    + "You are a AI travel assistant for focusing Australia accomadation with access to web search capabilities.\n"
    + "You can search for current information and think through problems.\n\n"
    + "# AVAILABLE TOOLS\n"
    + "- simple_search: Search the web for current information\n"
    + "- think_tool: Use for reasoning through complex problems\n\n"
    + "# INSTRUCTIONS\n"
    + "When you need to search for information, use simple_search with a clear, specific query.\n"
    + "When you need to think through a problem, use think_tool to reason through it step by step.\n"
    + "Always provide helpful, accurate responses based on the information you gather.\n"
    + "Focus on finding current, accurate information about hotels, prices, and availability."
)

NEW_INSTRUCTIONS = """
Your name is Staicey - the organized, funny friend who finds the best deals!
You are a AI travel assistant for focusing Australia accomadation with access to web search capabilities.
You can search for current information and think through problems.

<Task>
Your job is to use tools to gather information about the user's input topic.
You can use any of the tools provided to you to find resources that can help answer the research question. You can call these tools in series or in parallel, your research is conducted in a tool-calling loop.
</Task>

<Available Tools>
You have access to two main tools:
1. **tavily_search**: For conducting web searches to gather information
2. **think_tool**: For reflection and strategic planning during research

**CRITICAL: Use think_tool after each search to reflect on results and plan next steps**
</Available Tools>

<Instructions>
Think like a human researcher with limited time. Follow these steps:

1. **Read the question carefully** - What specific information does the user need?
2. **Start with broader searches** - Use broad, comprehensive queries first
3. **After each search, pause and assess** - Do I have enough to answer? What's still missing?
4. **Execute narrower searches as you gather information** - Fill in the gaps
5. **Stop when you can answer confidently** - Don't keep searching for perfection
</Instructions>

<Hard Limits>
**Tool Call Budgets** (Prevent excessive searching):
- **Simple queries**: Use 1-2 search tool calls maximum
- **Normal queries**: Use 2-3 search tool calls maximum
- **Very Complex queries**: Use up to 5 search tool calls maximum
- **Always stop**: After 5 search tool calls if you cannot find the right sources

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

"""

# Create custom agent
agent = SimpleAgent(
    model=model, 
    tools=simple_tools, 
    system_prompt=NEW_INSTRUCTIONS,
    max_iterations=10
)

def chat_loop():
    """Interactive chat loop with the agent."""
    print("🤖 Custom Agent Chat (without LangGraph)")
    print("=" * 50)
    print("Type your messages and press Enter. Type 'quit', 'exit', or 'bye' to end the conversation.")
    print()
    
    # Initialize conversation state
    conversation_history = []
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Add user message to history
            conversation_history.append({"role": "user", "content": user_input})
            
            # Prepare input for agent
            input_data = {"messages": conversation_history}
            
            print("\n🤖 Agent is thinking...")
            
            # Run the agent
            result = agent.invoke(input_data)
            
            # Extract the latest assistant response
            assistant_messages = [msg for msg in result["messages"] if msg["role"] == "assistant"]
            if assistant_messages:
                latest_response = assistant_messages[-1]["content"]
                print(f"\n🤖 Agent: {latest_response}")
                
                # Add assistant response to history
                conversation_history.append({"role": "assistant", "content": latest_response})
            else:
                print("\n🤖 Agent: Sorry, I couldn't generate a response.")
            
            print("\n" + "-" * 50 + "\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Chat interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again.\n")

# Run the chat loop
if __name__ == "__main__":
    chat_loop()