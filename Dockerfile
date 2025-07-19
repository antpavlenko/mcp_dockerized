FROM python:3.11-slim

# Set build arguments for multi-platform builds
ARG TARGETPLATFORM
ARG BUILDPLATFORM

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Labels for metadata (Docker Hub & OCI)
LABEL org.opencontainers.image.title="MCP Dockerized" \
      org.opencontainers.image.description="🐳 Containerized Model Context Protocol (MCP) server with extensible tools, API key authentication, and multi-platform support. Easy deployment via Docker Compose with built-in health checks and logging." \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="Anton Pavlenko" \
      org.opencontainers.image.authors="Anton Pavlenko <apavlenko@hmcorp.fund>" \
      org.opencontainers.image.url="https://hub.docker.com/r/antpavlenkohmcorp/mcp-dockerized" \
      org.opencontainers.image.documentation="https://github.com/antpavlenko/mcp_dockerized/blob/main/README.md" \
      org.opencontainers.image.source="https://github.com/antpavlenko/mcp_dockerized" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.created="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
      maintainer="Anton Pavlenko <apavlenko@hmcorp.fund>" \
      io.artifacthub.package.readme-url="https://raw.githubusercontent.com/antpavlenko/mcp_dockerized/main/README.md" \
      io.artifacthub.package.logo-url="https://raw.githubusercontent.com/antpavlenko/mcp_dockerized/main/.docker/icon.png" \
      io.artifacthub.package.keywords="mcp,model-context-protocol,docker,api,tools,containerized,python" \
      io.artifacthub.package.category="integration-delivery" \
      io.artifacthub.package.alternative-locations="docker.io/antpavlenkohmcorp/mcp-dockerized"

# Start the application
CMD ["python", "main.py"]
