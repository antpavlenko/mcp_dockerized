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

#### Method 1: Using the API
```bash
curl -X POST http://localhost:8000/api/generate-key \
  -H "Authorization: Bearer <existing-api-key>"
```

#### Method 2: Using the Python Script
```bash
# Generate locally (when server is stopped)
docker-compose exec mcp-server python generate_api_key.py

# Generate via API (when server is running)
docker-compose exec mcp-server python generate_api_key.py --api
```

#### Method 3: Direct Container Execution
```bash
docker run --rm -v $(pwd)/data:/app/data mcp-dockerized python generate_api_key.py
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
  - Use the provided `test_api.http` file
  - Replace `YOUR_API_KEY_HERE` with your actual API key
  - Click "Send Request" above each request block

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

2. **Open `test_api.http`** and replace `YOUR_API_KEY_HERE` with your actual key

3. **Click "Send Request"** above any test block to execute it

4. **Use VS Code tasks** (Ctrl+Shift+P → "Tasks: Run Task"):
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
1. Generate new API key:
   ```bash
   docker-compose exec mcp-server python generate_api_key.py
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
