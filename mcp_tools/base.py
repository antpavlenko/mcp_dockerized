from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

class BaseMCPTool(ABC):
    """Abstract base class for MCP tools"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"mcp-tool.{self.name}")
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name identifier"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for users"""
        pass
    
    @abstractmethod
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool parameters"""
        pass
    
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """Execute the tool with given parameters"""
        pass
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> None:
        """Validate parameters against schema (override if needed)"""
        pass
