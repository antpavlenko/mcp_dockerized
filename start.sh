#!/bin/bash

echo "🚀 Starting MCP Dockerized Server..."
echo "=================================="

# Build and start the services
docker-compose up --build -d

# Wait a moment for the server to start
sleep 3

# Get the API key from logs
echo ""
echo "🔑 API Key Information:"
echo "======================"
docker-compose logs mcp-server 2>/dev/null | grep -E "(Initial API Key generated|First API key)" | tail -1

echo ""
echo "📊 Server Status:"
echo "=================="
if curl -s http://localhost:${MCPD_PORT:-8000}/health > /dev/null; then
    echo "✅ Server is running and healthy"
    echo "🌐 Health endpoint: http://localhost:${MCPD_PORT:-8000}/health"
    echo "📚 API docs: http://localhost:${MCPD_PORT:-8000}/docs"
else
    echo "❌ Server might not be ready yet. Check logs with: docker-compose logs mcp-server"
fi

echo ""
echo "🔧 Useful Commands:"
echo "==================="
echo "View logs:           docker-compose logs -f mcp-server"
echo "Generate API key:    docker-compose exec mcp-server python generate_api_key.py"
echo "Stop server:         docker-compose down"
echo "Restart server:      docker-compose restart"
