import secrets
import sqlite3
from pathlib import Path

from fastmcp.server import FastMCP
from fastapi.openapi.docs import get_swagger_ui_html
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse

DB_PATH = Path("/data/api_keys.db")


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS api_keys (key TEXT PRIMARY KEY)"
        )


def create_api_key() -> str:
    key = secrets.token_hex(32)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO api_keys (key) VALUES (?)", (key,))
    return key


def validate_key(key: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT 1 FROM api_keys WHERE key=?", (key,)).fetchone()
    return row is not None


class APIKeyMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            request = Request(scope, receive)
            # allow unauthenticated access to documentation endpoints
            if request.url.path not in {"/docs", "/openapi.json"}:
                key = request.headers.get("x-api-key") or request.query_params.get(
                    "api_key"
                )
                if not key or not validate_key(key):
                    response = JSONResponse({"detail": "Invalid API key"}, status_code=401)
                    await response(scope, receive, send)
                    return
        await self.app(scope, receive, send)


init_db()
fast_mcp = FastMCP()
app = fast_mcp.http_app()
app.add_middleware(APIKeyMiddleware)


async def generate_key(_: Request) -> JSONResponse:
    return JSONResponse({"api_key": create_api_key()})


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
    return get_swagger_ui_html(openapi_url="/openapi.json", title="MCP Server API")


app.add_route("/openapi.json", openapi, methods=["GET"])
app.add_route("/docs", swagger, methods=["GET"])
