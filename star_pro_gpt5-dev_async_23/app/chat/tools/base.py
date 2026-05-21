from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.chat.models import ToolResult


class BaseTool(ABC):
    """Base class for all chat tools"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.enabled = True
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> ToolResult:
        """
        Execute the tool with given input data
        
        Args:
            input_data: Dictionary containing tool-specific parameters
            
        Returns:
            ToolResult with the execution result
        """
        pass
    
    def get_description(self) -> str:
        """Get tool description for the AI agent"""
        return self.description
    
    def is_enabled(self) -> bool:
        """Check if tool is enabled"""
        return self.enabled
    
    def enable(self):
        """Enable the tool"""
        self.enabled = True
    
    def disable(self):
        """Disable the tool"""
        self.enabled = False
