import logging
import secrets
import sqlite3
import os
from pathlib import Path

from fastmcp.server import FastMCP
import importlib
import pkgutil
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
from urllib.parse import parse_qs

DB_PATH = Path(os.environ.get("MCP_DB_PATH", "/data/api_keys.db"))
PLUGINS_PACKAGE = "plugins"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS api_keys (key TEXT PRIMARY KEY)"
        )
    logger.info("Database initialized at %s", DB_PATH)


def create_api_key() -> str:
    key = secrets.token_hex(32)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO api_keys (key) VALUES (?)", (key,))
    logger.info("Created a new API key")
    return key


def validate_key(key: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT 1 FROM api_keys WHERE key=?", (key,)).fetchone()
    if row is None:
        logger.warning("Invalid API key attempted: %s", key[:8])
    return row is not None


def load_plugins(server: FastMCP, package: str = PLUGINS_PACKAGE) -> None:
    """Load tool and resource plugins from the given package."""
    try:
        pkg = importlib.import_module(package)
    except ModuleNotFoundError:
        logger.warning("Plugins package %s not found", package)
        return

    for _, module_name, _ in pkgutil.iter_modules(pkg.__path__):
        module = importlib.import_module(f"{package}.{module_name}")
        setup = getattr(module, "setup", None)
        if callable(setup):
            setup(server)


class APIKeyMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            path = scope.get("path", "")
            logger.info("Handling request for %s", path)
            
            headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
            key = headers.get("x-api-key")
            if not key:
                query = parse_qs(scope.get("query_string", b"").decode())
                values = query.get("api_key")
                key = values[0] if values else None
                if not key:
                    logger.warning("Missing API key for request to %s", path)
                    response = JSONResponse({"detail": "Invalid API key"}, status_code=401)
                    await response(scope, receive, send)
                    return

            if not validate_key(key):
                logger.warning("Invalid API key for request to %s", path)
                response = JSONResponse({"detail": "Invalid API key"}, status_code=401)
                await response(scope, receive, send)
                return
            
        await self.app(scope, receive, send)




async def generate_key(_: Request) -> JSONResponse:
    key = create_api_key()
    logger.info("API key generated via endpoint")
    return JSONResponse({"api_key": key})


init_db()
fast_mcp = FastMCP()
load_plugins(fast_mcp)
app = fast_mcp.http_app()
logger.info("FastMCP application initialized")
app.add_middleware(APIKeyMiddleware)

app.add_route("/generate-key", generate_key, methods=["POST"])
logger.info("Routes registered. Server ready.")
