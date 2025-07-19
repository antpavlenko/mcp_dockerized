import subprocess
import asyncio
import shlex
from typing import Dict, Any
from .base import BaseMCPTool

class ConsoleTool(BaseMCPTool):
    """Tool for executing console commands on the host machine"""
    
    @property
    def name(self) -> str:
        return "console"
    
    @property
    def description(self) -> str:
        return "Execute console commands on the host machine. Use with caution."
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The console command to execute"
                },
                "timeout": {
                    "type": "number",
                    "description": "Timeout in seconds (default: 30)",
                    "default": 30
                },
                "working_directory": {
                    "type": "string",
                    "description": "Working directory for command execution (optional)"
                }
            },
            "required": ["command"]
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a console command"""
        command = parameters.get("command")
        timeout = parameters.get("timeout", 30)
        working_dir = parameters.get("working_directory")
        
        if not command:
            raise ValueError("Command is required")
        
        self.logger.info(f"Executing command: {command}")
        
        try:
            # Use shell=True for complex commands but be aware of security implications
            # In production, consider more restrictive command parsing
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise TimeoutError(f"Command timed out after {timeout} seconds")
            
            return {
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr.decode('utf-8', errors='replace'),
                "return_code": process.returncode,
                "success": process.returncode == 0
            }
            
        except Exception as e:
            self.logger.error(f"Error executing command '{command}': {e}")
            raise RuntimeError(f"Command execution failed: {str(e)}")
