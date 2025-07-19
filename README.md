# MCP Dockerized

A Model Context Protocol (MCP) server that can be easily deployed via Docker Compose with extensible tools and secure API key authentication.

## Features

- ✅ **Containerized Deployment**: Easy deployment via Docker Compose
- ✅ **Configurable Port**: Listen on any port via environment variables
- ✅ **Health Check Endpoint**: Built-in health monitoring
- ✅ **API Key Authentication**: Secure access with unlimited API keys
- ✅ **Timestamped Logging**: Configurable log levels with timestamps
- ✅ **Extensible Tools**: Abstract tool system for easy extension
- ✅ **Console Tool**: Execute host machine commands
- ✅ **MCP Protocol Compliance**: Follows Model Context Protocol specification
- ✅ **Tool Discovery**: Automatic endpoint to describe all available tools

## Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd mcp_dockerized
   ```

2. **Configure environment** (optional):
   ```bash
   cp .env.example .env
   # Edit .env file as needed
   ```

3. **Start the server**:
   ```bash
   docker-compose up -d
   ```

4. **Get your API key**:
   ```bash
   docker-compose logs mcp-server | grep "First API key"
   ```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCPD_PORT` | `8000` | Port for the MCP server |
| `MCPD_LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `MCPD_API_KEY_LENGTH` | `32` | Length of generated API keys |

### Example `.env` file:
```env
MCPD_PORT=8000
MCPD_LOG_LEVEL=INFO
MCPD_API_KEY_LENGTH=32
```

## API Endpoints

### Health Check
```bash
GET /health
```

### Authentication
All API endpoints require a Bearer token in the Authorization header:
```bash
Authorization: Bearer <your-api-key>
```

### Core Endpoints

#### List Tools
```bash
GET /api/tools
```
Returns descriptions of all available tools.

#### Execute Tool
```bash
POST /api/tools/{tool_name}
Content-Type: application/json

{
  "command": "ls -la",
  "timeout": 30
}
```

#### Generate New API Key
```bash
POST /api/generate-key
```

### MCP Protocol Endpoints

#### Initialize MCP Connection
```bash
GET /api/mcp/initialize
```

#### List MCP Tools
```bash
GET /api/mcp/tools/list
```

#### Call MCP Tool
```bash
POST /api/mcp/tools/call
Content-Type: application/json

{
  "name": "console",
  "arguments": {
    "command": "echo 'Hello World'"
  }
}
```

## Available Tools

### Console Tool
Execute commands on the host machine.

**Parameters:**
- `command` (required): The command to execute
- `timeout` (optional): Timeout in seconds (default: 30)
- `working_directory` (optional): Working directory for execution

**Example:**
```json
{
  "command": "ls -la /tmp",
  "timeout": 15,
  "working_directory": "/home/user"
}
```

## API Key Management

### Initial API Key
The server generates an initial API key on first startup. Check the logs:
```bash
docker-compose logs mcp-server | grep "API Key generated"
```

### Generate Additional API Keys

#### Using the API
```bash
curl -X POST http://localhost:8000/api/generate-key \
  -H "Authorization: Bearer <existing-api-key>"
```

## Creating Custom Tools

### 1. Create a New Tool File

Create a new file in the `mcp_tools/` directory following the naming pattern `*_tool.py`:

```python
# mcp_tools/my_custom_tool.py
from typing import Dict, Any
from .base import BaseMCPTool

class MyCustomTool(BaseMCPTool):
    @property
    def name(self) -> str:
        return "my_custom_tool"
    
    @property
    def description(self) -> str:
        return "Description of what my custom tool does"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_param": {
                    "type": "string",
                    "description": "Description of the parameter"
                }
            },
            "required": ["input_param"]
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        input_param = parameters.get("input_param")
        # Your tool logic here
        return {"result": f"Processed: {input_param}"}
```

### 2. Register the Tool

Add your tool to the `load_tools()` method in `main.py`:

```python
def load_tools(self):
    # Existing tools...
    
    # Add your custom tool
    from mcp_tools.my_custom_tool import MyCustomTool
    custom_tool = MyCustomTool()
    self.tools[custom_tool.name] = custom_tool
    self.logger.info(f"Loaded tool: {custom_tool.name}")
```

### 3. Rebuild and Deploy
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

## Development

### VS Code Extensions for Testing

For the best development experience, install these VS Code extensions:

#### **Primary Testing Extension**
- **REST Client** (`humao.rest-client`) - Test API endpoints directly in VS Code

#### **Development Extensions**
- **Python** (`ms-python.python`) - Python language support
- **Python Debugger** (`ms-python.debugpy`) - Advanced Python debugging
- **Docker** (`ms-azuretools.vscode-docker`) - Docker container management
- **YAML** (`redhat.vscode-yaml`) - YAML file validation

#### **Alternative HTTP Clients**
- **Thunder Client** (`rangav.vscode-thunder-client`) - Postman-like interface
- **Postman** (`postman.postman-for-vscode`) - Official Postman extension

### Testing with REST Client

1. **Get your API key**:
   ```bash
   docker-compose logs mcp-server | grep "First API key"
   ```

2. **Use your preferred HTTP client** to test the API endpoints

3. **Use VS Code tasks** (Ctrl+Shift+P → "Tasks: Run Task"):
   - Start MCP Server
   - Stop MCP Server  
   - Test MCP Server
   - Generate API Key
   - View Server Logs

### Local Development Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run locally**:
   ```bash
   python main.py
   ```

### Testing

Test the health endpoint:
```bash
curl http://localhost:8000/health
```

Test tool listing:
```bash
curl -H "Authorization: Bearer <your-api-key>" \
     http://localhost:8000/api/tools
```

Test console tool:
```bash
curl -X POST \
  -H "Authorization: Bearer <your-api-key>" \
  -H "Content-Type: application/json" \
  -d '{"command": "echo Hello World"}' \
  http://localhost:8000/api/tools/console
```

## Security Considerations

- **API Keys**: Store API keys securely and rotate them regularly
- **Console Tool**: The console tool can execute any command - use with caution
- **Network**: Consider running behind a reverse proxy in production
- **Container Security**: Run as non-root user (already configured)

## Monitoring and Logs

### View Logs
```bash
# All logs
docker-compose logs -f mcp-server

# Only errors
docker-compose logs mcp-server | grep ERROR

# Follow logs
docker-compose logs -f --tail=50 mcp-server
```

### Health Monitoring
The server includes a health check endpoint that's automatically used by Docker Compose:
```bash
curl http://localhost:8000/health
```

## Troubleshooting

### Server Won't Start
1. Check port availability:
   ```bash
   lsof -i :8000
   ```

2. Check logs:
   ```bash
   docker-compose logs mcp-server
   ```

### API Key Issues
1. Generate new API key using the API:
   ```bash
   curl -X POST http://localhost:8000/api/generate-key \
     -H "Authorization: Bearer <existing-api-key>"
   ```

2. Check existing keys:
   ```bash
   cat data/api_keys.json
   ```

### Tool Execution Fails
1. Check tool parameters schema
2. Verify authentication
3. Check server logs for detailed error messages

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions, please open an issue on the GitHub repository.

## Docker Hub Deployment

### Pre-built Images
MCP Dockerized is available on Docker Hub with support for multiple Linux platforms:

- **Linux AMD64/ARM64/ARM v7**: `antpavlenkohmcorp/mcp-dockerized:latest`

### Quick Start with Docker Hub

#### Linux/macOS:
```bash
# Run with default settings
docker run -d -p 8000:8000 antpavlenkohmcorp/mcp-dockerized:latest

# Run with custom environment variables
docker run -d -p 8000:8000 \
  -e MCPD_PORT=8000 \
  -e MCPD_LOG_LEVEL=INFO \
  -v $(pwd)/data:/app/data \
  antpavlenkohmcorp/mcp-dockerized:latest
```

#### Windows:
```powershell
# Run Linux container on Windows (recommended)
docker run -d -p 8000:8000 antpavlenkohmcorp/mcp-dockerized:latest

# Run with persistent data
docker run -d -p 8000:8000 `
  -e MCPD_PORT=8000 `
  -e MCPD_LOG_LEVEL=INFO `
  -v ${PWD}/data:/app/data `
  antpavlenkohmcorp/mcp-dockerized:latest
```

#### Using Docker Compose with Docker Hub:
```bash
# Update your docker-compose.yml to use the Docker Hub image:
# image: antpavlenkohmcorp/mcp-dockerized:latest
```

### Platform-Specific Pulls
```bash
# Force specific architecture (Linux)
docker run --platform linux/amd64 -d -p 8000:8000 antpavlenkohmcorp/mcp-dockerized:latest
docker run --platform linux/arm64 -d -p 8000:8000 antpavlenkohmcorp/mcp-dockerized:latest

# ARM v7 (Raspberry Pi)
docker run --platform linux/arm/v7 -d -p 8000:8000 antpavlenkohmcorp/mcp-dockerized:latest
```

### Building and Publishing Your Own Images

#### Prerequisites:
1. **Docker Desktop** with buildx support
2. **Docker Hub account**

#### Manual Build Process:
```bash
# 1. Enable Docker buildx
docker buildx create --name mcp-builder --use

# 2. Build and push multi-platform
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  --tag YOUR_DOCKERHUB_USERNAME/mcp-dockerized:latest \
  --push .

# 3. Build Windows (on Windows machine)
docker build -f Dockerfile.windows \
  -t YOUR_DOCKERHUB_USERNAME/mcp-dockerized:latest-windows .
docker push YOUR_DOCKERHUB_USERNAME/mcp-dockerized:latest-windows
```

#### Automated Builds with GitHub Actions:
The repository includes GitHub Actions workflows for automated building and testing. 

**For Pull Requests**: The workflow will build and test Docker images without requiring any setup.

**For Publishing to Docker Hub**: If you want to automatically publish images to Docker Hub, set these secrets in your GitHub repository settings (Settings → Secrets and variables → Actions):
- `DOCKER_USERNAME`: Your Docker Hub username
- `DOCKER_PASSWORD`: Your Docker Hub password or access token

**Note**: Without these secrets, the workflow will still build and test the images for pull requests, but won't publish them to Docker Hub.
# Updated Fri Jul 18 23:39:42 EDT 2025
