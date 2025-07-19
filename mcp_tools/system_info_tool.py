import json
import os
from datetime import datetime
from typing import Dict, Any
from .base import BaseMCPTool

class SystemInfoTool(BaseMCPTool):
    """Tool for getting system information"""
    
    @property
    def name(self) -> str:
        return "system_info"
    
    @property
    def description(self) -> str:
        return "Get system information including environment variables, current time, and process info"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "info_type": {
                    "type": "string",
                    "enum": ["environment", "time", "process", "all"],
                    "description": "Type of system information to retrieve",
                    "default": "all"
                },
                "filter_env": {
                    "type": "string",
                    "description": "Filter environment variables by prefix (optional)"
                }
            },
            "required": []
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get system information"""
        info_type = parameters.get("info_type", "all")
        filter_env = parameters.get("filter_env")
        
        result = {}
        
        if info_type in ["environment", "all"]:
            env_vars = dict(os.environ)
            if filter_env:
                env_vars = {k: v for k, v in env_vars.items() if k.startswith(filter_env)}
            result["environment"] = env_vars
        
        if info_type in ["time", "all"]:
            result["time"] = {
                "utc": datetime.utcnow().isoformat(),
                "timestamp": datetime.utcnow().timestamp()
            }
        
        if info_type in ["process", "all"]:
            result["process"] = {
                "pid": os.getpid(),
                "cwd": os.getcwd(),
                "user": os.getenv("USER", "unknown")
            }
        
        return result
