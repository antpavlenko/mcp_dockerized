# MCP Dockerized Server

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68.0+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-blue.svg)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This repository provides a minimal MCP server based on [fastmcp].
The server exposes the Streamable HTTP transport and protects all
requests using a simple API key authentication system.

## Use Cases

- **Local AI Model Serving**: Run an MCP server locally to interact with AI models through a standardized interface
- **Development Environment**: Set up a consistent development environment for applications that consume MCP services
- **Prototyping**: Quickly test MCP-based applications without complex cloud setup
- **Self-hosted AI Solutions**: Deploy in environments where cloud-based solutions aren't feasible
- **Integration Testing**: Use as a stable test backend for applications that depend on MCP services

## Installation and Setup

### Prerequisites

- Docker and Docker Compose installed on your system
- Basic familiarity with command-line operations
- At least 500MB of free disk space

### Build and run with Docker

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp_dockerized.git
cd mcp_dockerized

# Build and run the container
docker build -t mcp-server .
docker run -p 8000:8000 -v mcp_data:/data mcp-server
```

The container stores API keys in `/data/api_keys.db`. Mount a volume to
persist keys across restarts.

### Run with Docker Compose

Create the included `docker-compose.yml` file and start the service:

```bash
# Start the service
docker compose up --build -d

# View logs
docker compose logs -f
```

This builds the image if necessary and launches the server on port 8000.
The API key database is persisted in the `mcp_data` volume.

### Generate API keys

Use the management CLI inside the container to create keys:

```bash
docker run --rm -v mcp_data:/data mcp-server python manage.py generate-key
```

If you're using Docker Compose:

```bash
docker compose run --rm mcp python manage.py generate-key
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

Interactive API documentation is available at [`/docs`](http://localhost:8000/docs) (also accessible via `/doc`) with the raw schema at [`/openapi.json`](http://localhost:8000/openapi.json).

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

### Call a tool via HTTP

Tools are invoked using the `tools/call` method. Provide the tool name and any
arguments in the JSON-RPC payload. The example below runs the built-in
`terminal` tool:

```bash
curl -X POST http://localhost:8000/mcp \
     -H "Content-Type: application/json" \
     -H "X-API-Key: <your-api-key>" \
     -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "terminal", "arguments": {"cmd": "echo hello"}}}'
```

### Using the Python Client

For more advanced interaction you can use the `fastmcp` Python client:

```python
import asyncio
from fastmcp.client import Client, StreamableHttpTransport

async def main():
    transport = StreamableHttpTransport(
        "http://localhost:8000/mcp",
        headers={"X-API-Key": "<your-api-key>"},
    )
    async with Client(transport) as client:
        tools = await client.list_tools()
        print(tools)
        result = await client.call_tool("terminal", {"cmd": "echo hello"})
        print(result[0].text)

asyncio.run(main())
```

## Plugins

Additional tools and resources can be added by placing modules in the
`plugins` package. Each module should expose a `setup(server)` function
which receives the `FastMCP` instance and registers tools or resources.
All modules in this package are automatically imported on startup.

This repository ships with a `terminal` plugin providing a simple tool
for running commands on the host system.

### Creating a Custom Plugin

1. Create a new Python module in the `plugins` directory
2. Implement the `setup(server)` function
3. Register your tools or resources

Example plugin structure:

```python
# plugins/my_plugin.py
from fastmcp import Tool, FastMCP

def setup(server: FastMCP):
    @server.tool("my_tool")
    async def my_tool(params: dict):
        # Tool implementation
        return {"result": "Success!"}
```

## Configuration

The server can be configured using the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_DB_PATH` | Path to the SQLite database file for API keys | `/data/api_keys.db` |
| `MCP_PORT` | Port on which the server listens | `8000` |

Example usage with custom values:

```bash
docker run -p 9000:9000 -v mcp_data:/custom_data -e MCP_PORT=9000 -e MCP_DB_PATH=/custom_data/keys.db mcp-server
```

## Troubleshooting

### API Key Issues

**Problem**: "Invalid API key" errors when making requests
**Solution**: Ensure you're using a valid API key generated with the `generate-key` command. Keys are stored in the database file at the path specified by `MCP_DB_PATH`.

**Problem**: API keys not persisting across container restarts
**Solution**: Make sure you're mounting a volume correctly to store the database file:
```bash
docker run -p 8000:8000 -v mcp_data:/data mcp-server
```

### Connection Issues

**Problem**: Cannot connect to the server
**Solution**: Verify that:
1. The server is running (`docker ps` should show the container)
2. You're connecting to the correct port (default is 8000)
3. There are no firewall rules blocking the connection

**Problem**: Connection refused errors
**Solution**: Check if the port is already in use by another service:
```bash
lsof -i :8000
```

### Plugin Issues

**Problem**: Custom plugins aren't being loaded
**Solution**: Ensure your plugin:
1. Is placed in the `plugins` directory
2. Contains a `setup(server)` function
3. Has no syntax errors

**Problem**: Errors when calling tools
**Solution**: Check the server logs for detailed error messages:
```bash
docker logs <container_id>
```

## Performance Tuning

For production use, consider adjusting these settings:

- Increase container resources (CPU/memory) for heavy workloads
- Use a dedicated volume with high I/O performance for the database
- Set appropriate timeout values for your specific use case
