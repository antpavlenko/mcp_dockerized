import os
import logging
import secrets
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Security, status # type: ignore
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials # type: ignore
from pydantic import BaseModel
from dotenv import load_dotenv

from mcp_tools.base import BaseMCPTool
from mcp_tools.console_tool import ConsoleTool
from mcp_tools.system_info_tool import SystemInfoTool

# Load environment variables
load_dotenv()

class MCPServer:
    def __init__(self):
        self.port = int(os.getenv("MCPD_PORT", 8000))
        self.log_level = os.getenv("MCPD_LOG_LEVEL", "INFO").upper()
        self.api_key_length = int(os.getenv("MCPD_API_KEY_LENGTH", 32))
        
        # Setup logging
        self.setup_logging()
        
        # Initialize data directory and API keys
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.api_keys_file = self.data_dir / "api_keys.json"
        
        # Load or generate initial API key
        self.api_keys = self.load_api_keys()
        if not self.api_keys:
            initial_key = self.generate_api_key()
            self.logger.info(f"🔑 Initial API Key generated: {initial_key}")
        
        # Initialize MCP tools
        self.tools: Dict[str, BaseMCPTool] = {}
        self.load_tools()
        
        # Setup FastAPI
        self.app = FastAPI(
            title="MCP Dockerized Server",
            description="A Model Context Protocol server with extensible tools",
            version="1.0.0"
        )
        self.setup_routes()
        
        # Security
        self.security = HTTPBearer()

    def setup_logging(self):
        """Setup logging with timestamp and configurable level"""
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger("mcp-server")

    def load_api_keys(self) -> List[str]:
        """Load API keys from file"""
        if self.api_keys_file.exists():
            try:
                with open(self.api_keys_file, 'r') as f:
                    data = json.load(f)
                    return data.get('keys', [])
            except Exception as e:
                self.logger.error(f"Error loading API keys: {e}")
                return []
        return []

    def save_api_keys(self):
        """Save API keys to file"""
        try:
            with open(self.api_keys_file, 'w') as f:
                json.dump({'keys': self.api_keys}, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving API keys: {e}")

    def generate_api_key(self) -> str:
        """Generate a new API key"""
        api_key = secrets.token_urlsafe(self.api_key_length)
        self.api_keys.append(api_key)
        self.save_api_keys()
        self.logger.info(f"New API key generated and saved")
        return api_key

    def validate_api_key(self, credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())):
        """Validate API key"""
        if credentials.credentials not in self.api_keys:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        return credentials.credentials

    def load_tools(self):
        """Load all available MCP tools"""
        # Add console tool
        console_tool = ConsoleTool()
        self.tools[console_tool.name] = console_tool
        self.logger.info(f"Loaded tool: {console_tool.name}")

        # Add system info tool
        system_info_tool = SystemInfoTool()
        self.tools[system_info_tool.name] = system_info_tool
        self.logger.info(f"Loaded tool: {system_info_tool.name}")

        # Auto-discover additional tools from mcp_tools directory
        tools_dir = Path("mcp_tools")
        if tools_dir.exists():
            for tool_file in tools_dir.glob("*_tool.py"):
                if tool_file.name not in ["console_tool.py", "system_info_tool.py"]:  # Skip already loaded
                    try:
                        # Dynamic import would go here for additional tools
                        pass
                    except Exception as e:
                        self.logger.error(f"Error loading tool {tool_file}: {e}")

    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0",
                "tools_count": len(self.tools)
            }

        @self.app.post("/api/generate-key")
        async def generate_new_api_key(api_key: str = Depends(self.validate_api_key)):
            """Generate a new API key"""
            new_key = self.generate_api_key()
            return {"api_key": new_key, "message": "New API key generated successfully"}

        @self.app.get("/api/tools")
        async def list_tools(api_key: str = Depends(self.validate_api_key)):
            """Get description of all available tools"""
            tools_info = []
            for tool_name, tool in self.tools.items():
                tools_info.append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.get_parameters_schema()
                })
            return {"tools": tools_info}

        @self.app.post("/api/tools/{tool_name}")
        async def execute_tool(
            tool_name: str,
            request: Dict[str, Any],
            api_key: str = Depends(self.validate_api_key)
        ):
            """Execute a specific tool"""
            if tool_name not in self.tools:
                raise HTTPException(
                    status_code=404,
                    detail=f"Tool '{tool_name}' not found"
                )
            
            tool = self.tools[tool_name]
            try:
                result = await tool.execute(request)
                return {
                    "tool": tool_name,
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                }
            except Exception as e:
                self.logger.error(f"Error executing tool {tool_name}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Tool execution failed: {str(e)}"
                )

        @self.app.get("/api/mcp/initialize")
        async def mcp_initialize(api_key: str = Depends(self.validate_api_key)):
            """MCP Protocol: Initialize connection"""
            return {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {
                        "listChanged": True
                    }
                },
                "serverInfo": {
                    "name": "mcp-dockerized",
                    "version": "1.0.0"
                }
            }

        @self.app.get("/api/mcp/tools/list")
        async def mcp_list_tools(api_key: str = Depends(self.validate_api_key)):
            """MCP Protocol: List available tools"""
            tools_list = []
            for tool_name, tool in self.tools.items():
                tools_list.append({
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.get_parameters_schema()
                })
            return {"tools": tools_list}

        @self.app.post("/api/mcp/tools/call")
        async def mcp_call_tool(
            request: Dict[str, Any],
            api_key: str = Depends(self.validate_api_key)
        ):
            """MCP Protocol: Call a tool"""
            tool_name = request.get("name")
            arguments = request.get("arguments", {})
            
            if tool_name not in self.tools:
                return {
                    "isError": True,
                    "content": [{"type": "text", "text": f"Tool '{tool_name}' not found"}]
                }
            
            tool = self.tools[tool_name]
            try:
                result = await tool.execute(arguments)
                return {
                    "content": [{"type": "text", "text": str(result)}]
                }
            except Exception as e:
                return {
                    "isError": True,
                    "content": [{"type": "text", "text": f"Tool execution failed: {str(e)}"}]
                }

    def run(self):
        """Start the MCP server"""
        self.logger.info(f"🚀 Starting MCP Dockerized Server on port {self.port}")
        self.logger.info(f"📊 Log level: {self.log_level}")
        self.logger.info(f"🔧 Loaded {len(self.tools)} tools: {list(self.tools.keys())}")
        
        if self.api_keys:
            self.logger.info(f"🔑 Active API keys: {len(self.api_keys)}")
            self.logger.info(f"🔑 First API key: {self.api_keys[0]}")
        
        uvicorn.run(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level=self.log_level.lower()
        )

if __name__ == "__main__":
    server = MCPServer()
    server.run()
