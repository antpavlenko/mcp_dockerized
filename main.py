import os
import logging
import secrets
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import importlib
import importlib.util
import inspect
import sys
import threading

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Security, status # type: ignore
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials # type: ignore
from pydantic import BaseModel
from dotenv import load_dotenv

# Optional hot-reload dependencies
try:
    from watchdog.observers import Observer # type: ignore
    from watchdog.events import FileSystemEventHandler # type: ignore
except Exception:
    Observer = None  # type: ignore
    FileSystemEventHandler = object  # type: ignore

from mcp_tools.base import BaseMCPTool
from mcp_tools.console_tool import ConsoleTool
from mcp_tools.system_info_tool import SystemInfoTool

# Load environment variables
load_dotenv()

VERSION = "1.1.0"

class MCPServer:
    def __init__(self):
        self.port = int(os.getenv("MCPD_PORT", 666))
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
        self._tool_meta: Dict[str, Dict[str, Any]] = {}
        self.tools_lock = threading.RLock()
        self.tools_dir = Path("mcp_tools")
        self.tools_dir.mkdir(exist_ok=True)
        self.load_tools()
        
        # Setup FastAPI
        self.app = FastAPI(
            title="MCP Dockerized Server",
            description="A Model Context Protocol server with extensible tools",
            version=VERSION
        )
        self.setup_routes()
        
        # Security
        self.security = HTTPBearer()

        # Start file watcher for hot-loading tools if watchdog is available
        if Observer is not None:
            self._start_tools_watcher()
        else:
            self.logger.warning("watchdog not installed; hot-loading of python tools is disabled. Install 'watchdog' to enable.")

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

    def _load_tool_from_module(self, module, src_path: Path) -> Optional[BaseMCPTool]:
        """Given a loaded module, discover the first BaseMCPTool subclass and instantiate it."""
        tool_cls = None
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BaseMCPTool) and obj is not BaseMCPTool:
                tool_cls = obj
                break
        if not tool_cls:
            return None
        tool: BaseMCPTool = tool_cls()  # type: ignore
        with self.tools_lock:
            # Replace if exists
            self.tools[tool.name] = tool
            self._tool_meta[tool.name] = {"path": str(src_path), "module": module.__name__}
        self.logger.info(f"Loaded tool: {tool.name} from {src_path}")
        return tool

    def _import_module_from_path(self, path: Path) -> Optional[object]:
        """Dynamically import a Python module from a file path with a unique module name."""
        try:
            unique_name = f"mcp_dynamic.{path.stem}_{int(path.stat().st_mtime)}"
            spec = importlib.util.spec_from_file_location(unique_name, str(path))
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[unique_name] = module
                spec.loader.exec_module(module)  # type: ignore
                return module
        except Exception as e:
            self.logger.error(f"Failed to import module from {path}: {e}")
        return None

    def _load_tool_from_file(self, path: Path) -> Optional[BaseMCPTool]:
        module = self._import_module_from_path(path)
        if not module:
            return None
        return self._load_tool_from_module(module, path)

    def _unload_tools_from_path(self, path: Path):
        """Unload any tool previously loaded from the given path."""
        with self.tools_lock:
            to_remove = [name for name, meta in self._tool_meta.items() if meta.get("path") == str(path)]
            for name in to_remove:
                self.tools.pop(name, None)
                mod_name = self._tool_meta[name].get("module")
                if mod_name and mod_name in sys.modules:
                    try:
                        del sys.modules[mod_name]
                    except Exception:
                        pass
                del self._tool_meta[name]
                self.logger.info(f"Unloaded tool: {name} from {path}")

    def load_tools(self):
        """Load all available MCP tools (built-ins + dynamically discovered)."""
        # Built-in tools
        with self.tools_lock:
            console_tool = ConsoleTool()
            self.tools[console_tool.name] = console_tool
            self._tool_meta[console_tool.name] = {"path": str(self.tools_dir / "console_tool.py"), "module": ConsoleTool.__module__}
            self.logger.info(f"Loaded tool: {console_tool.name}")

            system_info_tool = SystemInfoTool()
            self.tools[system_info_tool.name] = system_info_tool
            self._tool_meta[system_info_tool.name] = {"path": str(self.tools_dir / "system_info_tool.py"), "module": SystemInfoTool.__module__}
            self.logger.info(f"Loaded tool: {system_info_tool.name}")

        # Discover other tools in mcp_tools directory
        if self.tools_dir.exists():
            for tool_file in self.tools_dir.glob("*_tool.py"):
                # Skip the built-ins already loaded statically
                if tool_file.name in {"console_tool.py", "system_info_tool.py", "base.py", "__init__.py"}:
                    continue
                try:
                    self._load_tool_from_file(tool_file)
                except Exception as e:
                    self.logger.error(f"Error loading tool {tool_file}: {e}")

    def _start_tools_watcher(self):
        class _Handler(FileSystemEventHandler):
            def __init__(self, outer: "MCPServer"):
                self._outer = outer

            def on_created(self, event):  # type: ignore[override]
                p = Path(event.src_path)
                if p.is_file() and p.name.endswith("_tool.py"):
                    self._outer.logger.info(f"Detected new tool file: {p}")
                    self._outer._load_tool_from_file(p)

            def on_modified(self, event):  # type: ignore[override]
                p = Path(event.src_path)
                if p.is_file() and p.name.endswith("_tool.py"):
                    self._outer.logger.info(f"Detected modified tool file: {p}")
                    self._outer._unload_tools_from_path(p)
                    self._outer._load_tool_from_file(p)

            def on_deleted(self, event):  # type: ignore[override]
                p = Path(event.src_path)
                if p.name.endswith("_tool.py"):
                    self._outer.logger.info(f"Detected deleted tool file: {p}")
                    self._outer._unload_tools_from_path(p)

        self._observer = Observer()
        handler = _Handler(self)
        self._observer.schedule(handler, str(self.tools_dir), recursive=False)
        self._observer.daemon = True
        self._observer.start()
        self.logger.info(f"Started watchdog observer for tools in {self.tools_dir}")

    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            with self.tools_lock:
                tools_count = len(self.tools)
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": VERSION,
                "tools_count": tools_count
            }

        @self.app.post("/api/generate-key")
        async def generate_new_api_key(api_key: str = Depends(self.validate_api_key)):
            """Generate a new API key"""
            new_key = self.generate_api_key()
            return {"api_key": new_key, "message": "New API key generated successfully"}

        @self.app.get("/api/tools")
        async def list_tools(api_key: str = Depends(self.validate_api_key)):
            """Get description of all available tools"""
            with self.tools_lock:
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
            with self.tools_lock:
                tool = self.tools.get(tool_name)
            if not tool:
                raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
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
                "capabilities": {"tools": {"listChanged": True}},
                "serverInfo": {"name": "mcp-dockerized", "version": VERSION}
            }

        @self.app.get("/api/mcp/tools/list")
        async def mcp_list_tools(api_key: str = Depends(self.validate_api_key)):
            """MCP Protocol: List available tools"""
            with self.tools_lock:
                tools_list = [
                    {"name": t.name, "description": t.description, "inputSchema": t.get_parameters_schema()}
                    for t in self.tools.values()
                ]
            return {"tools": tools_list}

        @self.app.post("/api/mcp/tools/call")
        async def mcp_call_tool(
            request: Dict[str, Any],
            api_key: str = Depends(self.validate_api_key)
        ):
            """MCP Protocol: Call a tool"""
            tool_name = request.get("name")
            arguments = request.get("arguments", {})
            with self.tools_lock:
                tool = self.tools.get(tool_name)
            if not tool:
                return {"isError": True, "content": [{"type": "text", "text": f"Tool '{tool_name}' not found"}]}
            try:
                result = await tool.execute(arguments)
                return {"content": [{"type": "text", "text": str(result)}]}
            except Exception as e:
                return {"isError": True, "content": [{"type": "text", "text": f"Tool execution failed: {str(e)}"}]}

        @self.app.post("/api/tools/reload")
        async def reload_tools(api_key: str = Depends(self.validate_api_key)):
            """Manually rescan the tools directory and reload python tools (useful when watchdog is unavailable)."""
            reloaded = []
            errors = []
            if self.tools_dir.exists():
                for tool_file in self.tools_dir.glob("*_tool.py"):
                    if tool_file.name in {"console_tool.py", "system_info_tool.py", "base.py", "__init__.py"}:
                        continue
                    try:
                        self._unload_tools_from_path(tool_file)
                        tool = self._load_tool_from_file(tool_file)
                        if tool:
                            reloaded.append(tool.name)
                    except Exception as e:
                        errors.append({"file": str(tool_file), "error": str(e)})
            return {"reloaded": reloaded, "errors": errors, "timestamp": datetime.utcnow().isoformat()}

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
