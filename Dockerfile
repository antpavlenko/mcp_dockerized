FROM python:3.12-slim

# Add Docker Hub metadata
LABEL org.opencontainers.image.title="MCP Dockerized powered by FastMCP"
LABEL org.opencontainers.image.description="A dockerized Model Control Protocol (MCP) server with API key authentication and plugin support"
LABEL org.opencontainers.image.version="0.1.1"
LABEL org.opencontainers.image.authors="Anton Pavlenko <anton@pavlenko.expert>"
LABEL org.opencontainers.image.url="https://github.com/antpavlenko/mcp_dockerized"
LABEL org.opencontainers.image.documentation="https://github.com/antpavlenko/mcp_dockerized/README.md"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.vendor="HMCorp Fund"
LABEL org.opencontainers.image.base.name="python:3.12-slim"

# Application-specific labels
LABEL com.mcp.api-version="1.0"
LABEL com.mcp.components="fastmcp,sqlite,python3"
LABEL com.mcp.port="8000"

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Default environment variables
ENV MCP_DB_PATH=/data/api_keys.db
ENV MCP_PORT=8000

# Use exec form with environment variable expansion
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port $MCP_PORT"]
