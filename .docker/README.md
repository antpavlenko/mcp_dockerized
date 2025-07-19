# 🐳 MCP Dockerized

**Containerized Model Context Protocol (MCP) server with extensible tools and secure API key authentication.**

[![Docker Hub](https://img.shields.io/docker/v/antpavlenkohmcorp/mcp-dockerized?label=Docker%20Hub&logo=docker)](https://hub.docker.com/r/antpavlenkohmcorp/mcp-dockerized)
[![Multi-Platform](https://img.shields.io/badge/platform-linux%2Famd64%20%7C%20arm64%20%7C%20armv7-blue?logo=docker)](https://hub.docker.com/r/antpavlenkohmcorp/mcp-dockerized)
[![License](https://img.shields.io/github/license/antpavlenko/mcp_dockerized)](https://github.com/antpavlenko/mcp_dockerized/blob/main/LICENSE)

## 🚀 Quick Start

### Basic Usage
```bash
# Run with default settings
docker run -d -p 8000:8000 antpavlenkohmcorp/mcp-dockerized:latest

# Check health
curl http://localhost:8000/health
```

### Production Setup
```bash
# Run with persistent data and custom config
docker run -d \
  --name mcp-server \
  -p 8000:8000 \
  -e MCPD_LOG_LEVEL=INFO \
  -e MCPD_API_KEY_LENGTH=32 \
  -v mcp_data:/app/data \
  --restart unless-stopped \
  antpavlenkohmcorp/mcp-dockerized:latest
```

### Docker Compose
```yaml
version: '3.8'
services:
  mcp-server:
    image: antpavlenkohmcorp/mcp-dockerized:latest
    ports:
      - "8000:8000"
    environment:
      - MCPD_PORT=8000
      - MCPD_LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 🔑 Getting Your API Key

After starting the container, get your API key from the logs:
```bash
docker logs <container-name> | grep "First API key"
```

## 🛠️ Features

- ✅ **Multi-Platform Support**: AMD64, ARM64, ARM v7
- ✅ **API Key Authentication**: Secure access control
- ✅ **Health Monitoring**: Built-in health check endpoint
- ✅ **Extensible Tools**: Easy to add custom MCP tools
- ✅ **Console Tool**: Execute host machine commands
- ✅ **Configurable Logging**: Timestamped logs with levels
- ✅ **Non-Root User**: Runs securely as non-privileged user
- ✅ **Production Ready**: Health checks and restart policies

## 📋 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCPD_PORT` | `8000` | Port for the MCP server |
| `MCPD_LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `MCPD_API_KEY_LENGTH` | `32` | Length of generated API keys |

## 🔗 API Endpoints

- `GET /health` - Health check
- `GET /api/tools` - List available tools
- `POST /api/tools/{tool_name}` - Execute tool
- `POST /api/generate-key` - Generate new API key
- `GET /api/mcp/initialize` - Initialize MCP connection
- `POST /api/mcp/tools/call` - Call MCP tool

## 🔒 Security

- Non-root container execution
- API key authentication required
- Configurable key lengths
- Health check monitoring
- Minimal attack surface

## 📚 Documentation

**Full documentation**: [GitHub Repository](https://github.com/antpavlenko/mcp_dockerized)

**Issues & Support**: [GitHub Issues](https://github.com/antpavlenko/mcp_dockerized/issues)

**Maintainer**: Anton Pavlenko <apavlenko@hmcorp.fund>

## 📄 License

MIT License - see [LICENSE](https://github.com/antpavlenko/mcp_dockerized/blob/main/LICENSE) for details.
