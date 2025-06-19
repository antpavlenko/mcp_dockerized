import secrets
import sqlite3
from pathlib import Path

from fastmcp.server import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

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
app = fast_mcp.streamable_http_app()
app.add_middleware(APIKeyMiddleware)


@app.route("/generate-key", methods=["POST"])
async def generate_key(_: Request) -> JSONResponse:
    return JSONResponse({"api_key": create_api_key()})
