# MCP Dockerized Server

This repository provides a minimal MCP server based on [fastmcp].
The server exposes the Streamable HTTP transport and protects all
requests using a simple API key.

## Usage

### Build and run with Docker

```bash
docker build -t mcp-server .
docker run -p 8000:8000 -v mcp_data:/data mcp-server
```

The container stores API keys in `/data/api_keys.db`. Mount a volume to
persist keys across restarts.

### Generate API keys

Use the management CLI inside the container to create keys:

```bash
docker run --rm -v mcp_data:/data mcp-server python manage.py generate-key
```

Generated keys are written to `/data/api_keys.db` inside the container or the mounted volume.
You can confirm the file exists by listing it with a one-off container:

```bash
docker run --rm -v mcp_data:/data mcp-server ls -l /data/api_keys.db
```

The printed key can then be supplied via the `X-API-Key` header or
`api_key` query parameter when calling the server.

## Endpoints

The server exposes two simple HTTP endpoints:

| Path | Method | Description |
|------|--------|-------------|
| `/mcp` | `POST` | Streamable HTTP transport for MCP requests. Requires a valid API key. |
| `/generate-key` | `POST` | Generates a new API key. Requires an existing valid API key. |

Interactive API documentation is available at [`/docs`](http://localhost:8000/docs) with the raw schema at [`/openapi.json`](http://localhost:8000/openapi.json).

## Example requests

### Generate a key via HTTP

```bash
curl -X POST http://localhost:8000/generate-key \
     -H "X-API-Key: <your-api-key>"
```

### Call the MCP endpoint

You can issue JSON-RPC requests directly. The example below sends a `ping` request:

```bash
curl -X POST http://localhost:8000/mcp \
     -H "Content-Type: application/json" \
     -H "X-API-Key: <your-api-key>" \
     -d '{"jsonrpc": "2.0", "id": 1, "method": "ping"}'
```

For more advanced interaction you can use the `fastmcp` Python client:

```python
import asyncio
import fastmcp

async def main():
    async with fastmcp.Client(
        "http://localhost:8000/mcp",
        headers={"X-API-Key": "<your-api-key>"},
    ) as client:
        tools = await client.list_tools()
        print(tools)

asyncio.run(main())
```
