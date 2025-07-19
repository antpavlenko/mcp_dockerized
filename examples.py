#!/usr/bin/env python3
"""
Example usage script for MCP Dockerized Server
Demonstrates how to interact with the server programmatically
"""

import requests
import json
import sys
from pathlib import Path

class MCPClient:
    def __init__(self, base_url="http://localhost:8000", api_key=None):
        self.base_url = base_url
        self.api_key = api_key or self._get_api_key()
        
        if not self.api_key:
            raise ValueError("No API key available. Make sure the server is running.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _get_api_key(self):
        """Get API key from data file"""
        data_file = Path("data/api_keys.json")
        if data_file.exists():
            try:
                with open(data_file, 'r') as f:
                    data = json.load(f)
                    keys = data.get('keys', [])
                    return keys[0] if keys else None
            except:
                pass
        return None
    
    def health_check(self):
        """Check server health"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def list_tools(self):
        """List all available tools"""
        response = requests.get(f"{self.base_url}/api/tools", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def execute_tool(self, tool_name, parameters):
        """Execute a specific tool"""
        response = requests.post(
            f"{self.base_url}/api/tools/{tool_name}",
            headers=self.headers,
            json=parameters
        )
        response.raise_for_status()
        return response.json()
    
    def run_command(self, command, timeout=30, working_directory=None):
        """Run a console command"""
        params = {"command": command, "timeout": timeout}
        if working_directory:
            params["working_directory"] = working_directory
        
        return self.execute_tool("console", params)
    
    def get_system_info(self, info_type="all", filter_env=None):
        """Get system information"""
        params = {"info_type": info_type}
        if filter_env:
            params["filter_env"] = filter_env
        
        return self.execute_tool("system_info", params)
    
    def generate_api_key(self):
        """Generate a new API key"""
        response = requests.post(f"{self.base_url}/api/generate-key", headers=self.headers)
        response.raise_for_status()
        return response.json()

def example_basic_usage():
    """Basic usage examples"""
    print("🚀 MCP Client - Basic Usage Examples")
    print("=" * 50)
    
    try:
        # Initialize client
        client = MCPClient()
        print(f"✅ Connected to MCP server")
        
        # Health check
        health = client.health_check()
        print(f"🏥 Server health: {health['status']}")
        
        # List tools
        tools = client.list_tools()
        print(f"\n🔧 Available tools ({len(tools['tools'])}):")
        for tool in tools['tools']:
            print(f"   - {tool['name']}: {tool['description']}")
        
        # Run a simple command
        print(f"\n💻 Running console command...")
        result = client.run_command("echo 'Hello from MCP Client!'")
        if result['result']['success']:
            print(f"   Output: {result['result']['stdout'].strip()}")
        else:
            print(f"   Error: {result['result']['stderr']}")
        
        # Get system info
        print(f"\n📊 Getting system time...")
        sys_info = client.get_system_info("time")
        time_info = sys_info['result']['time']
        print(f"   UTC Time: {time_info['utc']}")
        
        print(f"\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def example_advanced_usage():
    """Advanced usage examples"""
    print("🚀 MCP Client - Advanced Usage Examples")
    print("=" * 50)
    
    try:
        client = MCPClient()
        
        # Multiple commands in sequence
        commands = [
            "pwd",
            "ls -la",
            "uname -a",
            "df -h"
        ]
        
        print("💻 Running multiple commands:")
        for cmd in commands:
            print(f"\n   Command: {cmd}")
            result = client.run_command(cmd)
            if result['result']['success']:
                output = result['result']['stdout'].strip()
                # Truncate long output
                if len(output) > 200:
                    output = output[:200] + "..."
                print(f"   Output: {output}")
            else:
                print(f"   Error: {result['result']['stderr']}")
        
        # Get filtered environment variables
        print(f"\n🌍 Environment variables (MCPD_* only):")
        env_info = client.get_system_info("environment", "MCPD_")
        env_vars = env_info['result']['environment']
        if env_vars:
            for key, value in env_vars.items():
                print(f"   {key}={value}")
        else:
            print("   No MCPD_* environment variables found")
        
        # Generate new API key
        print(f"\n🗝️  Generating new API key...")
        new_key_result = client.generate_api_key()
        new_key = new_key_result['api_key']
        print(f"   New API key: {new_key[:10]}...{new_key[-10:]}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def example_error_handling():
    """Error handling examples"""
    print("🚀 MCP Client - Error Handling Examples")
    print("=" * 50)
    
    try:
        client = MCPClient()
        
        # Test invalid tool
        print("🔧 Testing invalid tool name:")
        try:
            client.execute_tool("nonexistent_tool", {})
        except requests.exceptions.HTTPError as e:
            print(f"   ✅ Correctly caught error: {e.response.status_code}")
        
        # Test invalid command
        print("\n💻 Testing invalid console command:")
        result = client.run_command("nonexistent_command_12345")
        if not result['result']['success']:
            print(f"   ✅ Command failed as expected")
            print(f"   Error: {result['result']['stderr'].strip()}")
        
        # Test command timeout
        print("\n⏰ Testing command timeout:")
        result = client.run_command("sleep 2", timeout=1)
        if not result['result']['success']:
            print(f"   ✅ Command timed out as expected")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        example_type = sys.argv[1]
        
        if example_type == "basic":
            example_basic_usage()
        elif example_type == "advanced":
            example_advanced_usage()
        elif example_type == "errors":
            example_error_handling()
        else:
            print("Usage: python examples.py [basic|advanced|errors]")
            sys.exit(1)
    else:
        print("Available examples:")
        print("  python examples.py basic     - Basic usage examples")
        print("  python examples.py advanced  - Advanced usage examples")
        print("  python examples.py errors    - Error handling examples")

if __name__ == "__main__":
    main()
