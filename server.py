import logging
import secrets
import sqlite3
from pathlib import Path

from fastmcp.server import FastMCP
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from swagger_ui_bundle import swagger_ui_path
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
from urllib.parse import parse_qs

DB_PATH = Path("/data/api_keys.db")

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


class APIKeyMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            path = scope.get("path", "")
            logger.info("Handling request for %s", path)
            if path not in {"/docs", "/doc", "/openapi.json"}:
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


init_db()
fast_mcp = FastMCP()
app = fast_mcp.http_app()
logger.info("FastMCP application initialized")
app.add_middleware(APIKeyMiddleware)
app.mount("/static", StaticFiles(directory=swagger_ui_path), name="static")


async def generate_key(_: Request) -> JSONResponse:
    key = create_api_key()
    logger.info("API key generated via endpoint")
    return JSONResponse({"api_key": key})


app.add_route("/generate-key", generate_key, methods=["POST"])


OPENAPI_SCHEMA = {
    "openapi": "3.0.0",
    "info": {"title": "MCP Server", "version": "1.0.0"},
    "paths": {
        "/mcp": {
            "post": {
                "summary": "Streamable HTTP endpoint for MCP requests",
                "description": "Accepts MCP JSON-RPC requests via Streamable HTTP. Requires a valid API key.",
                "responses": {"200": {"description": "Success"}, "401": {"description": "Invalid API key"}},
            }
        },
        "/generate-key": {
            "post": {
                "summary": "Generate a new API key",
                "description": "Creates and returns a new API key. Requires an existing valid API key.",
                "responses": {"200": {"description": "New API key"}, "401": {"description": "Invalid API key"}},
            }
        },
    },
}


async def openapi(_: Request) -> JSONResponse:
    return JSONResponse(OPENAPI_SCHEMA)


async def swagger(_: Request) -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="MCP Server API",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
        swagger_favicon_url="/static/favicon-32x32.png",
    )


app.add_route("/openapi.json", openapi, methods=["GET"])
app.add_route("/docs", swagger, methods=["GET"])
app.add_route("/doc", swagger, methods=["GET"])
logger.info("Routes registered. Server ready.")
