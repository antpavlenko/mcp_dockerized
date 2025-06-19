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
