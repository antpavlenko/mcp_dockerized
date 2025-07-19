#!/usr/bin/env python3
"""
Test script for MCP Dockerized Server
Validates all core functionality
"""

import requests
import json
import time
import sys
import os
from pathlib import Path

class MCPTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_key = None
        
    def get_api_key(self):
        """Get API key from the data file"""
        data_file = Path("data/api_keys.json")
        if not data_file.exists():
            print("❌ No API keys file found. Make sure the server has been started.")
            return None
            
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
                keys = data.get('keys', [])
                if keys:
                    return keys[0]
        except Exception as e:
            print(f"❌ Error reading API keys: {e}")
        return None
    
    def test_health(self):
        """Test health endpoint"""
        print("🏥 Testing health endpoint...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed - Status: {data.get('status')}")
                return True
            else:
                print(f"❌ Health check failed - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_authentication(self):
        """Test API key authentication"""
        print("🔐 Testing authentication...")
        
        # Test without API key
        try:
            response = requests.get(f"{self.base_url}/api/tools")
            if response.status_code == 401:
                print("✅ Unauthorized access properly rejected")
            else:
                print(f"⚠️  Expected 401, got {response.status_code}")
        except Exception as e:
            print(f"❌ Auth test error: {e}")
            return False
        
        # Get API key
        self.api_key = self.get_api_key()
        if not self.api_key:
            print("❌ Could not get API key")
            return False
        
        # Test with API key
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            response = requests.get(f"{self.base_url}/api/tools", headers=headers)
            if response.status_code == 200:
                print("✅ Authentication with API key successful")
                return True
            else:
                print(f"❌ Authentication failed - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Auth test error: {e}")
            return False
    
    def test_tools_listing(self):
        """Test tools listing endpoint"""
        print("🔧 Testing tools listing...")
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            response = requests.get(f"{self.base_url}/api/tools", headers=headers)
            if response.status_code == 200:
                data = response.json()
                tools = data.get('tools', [])
                print(f"✅ Found {len(tools)} tools:")
                for tool in tools:
                    print(f"   - {tool.get('name')}: {tool.get('description')}")
                return True
            else:
                print(f"❌ Tools listing failed - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Tools listing error: {e}")
            return False
    
    def test_console_tool(self):
        """Test console tool execution"""
        print("💻 Testing console tool...")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Test simple command
        payload = {"command": "echo 'Hello from MCP!'"}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/tools/console", 
                headers=headers, 
                json=payload
            )
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {})
                stdout = result.get('stdout', '').strip()
                if 'Hello from MCP!' in stdout:
                    print("✅ Console tool executed successfully")
                    print(f"   Output: {stdout}")
                    return True
                else:
                    print(f"❌ Unexpected output: {stdout}")
                    return False
            else:
                print(f"❌ Console tool failed - Status: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Console tool error: {e}")
            return False
    
    def test_system_info_tool(self):
        """Test system info tool"""
        print("📊 Testing system info tool...")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {"info_type": "time"}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/tools/system_info", 
                headers=headers, 
                json=payload
            )
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {})
                if 'time' in result:
                    print("✅ System info tool executed successfully")
                    print(f"   Time info: {result['time']}")
                    return True
                else:
                    print(f"❌ Unexpected result: {result}")
                    return False
            else:
                print(f"❌ System info tool failed - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ System info tool error: {e}")
            return False
    
    def test_mcp_protocol(self):
        """Test MCP protocol endpoints"""
        print("🔌 Testing MCP protocol endpoints...")
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # Test initialize
        try:
            response = requests.get(f"{self.base_url}/api/mcp/initialize", headers=headers)
            if response.status_code == 200:
                data = response.json()
                if 'protocolVersion' in data:
                    print("✅ MCP initialize endpoint working")
                else:
                    print("❌ MCP initialize missing protocol version")
                    return False
            else:
                print(f"❌ MCP initialize failed - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ MCP initialize error: {e}")
            return False
        
        # Test tools list
        try:
            response = requests.get(f"{self.base_url}/api/mcp/tools/list", headers=headers)
            if response.status_code == 200:
                data = response.json()
                tools = data.get('tools', [])
                print(f"✅ MCP tools list working - {len(tools)} tools found")
                return True
            else:
                print(f"❌ MCP tools list failed - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ MCP tools list error: {e}")
            return False
    
    def test_api_key_generation(self):
        """Test new API key generation"""
        print("🗝️  Testing API key generation...")
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            response = requests.post(f"{self.base_url}/api/generate-key", headers=headers)
            if response.status_code == 200:
                data = response.json()
                new_key = data.get('api_key')
                if new_key and len(new_key) > 20:
                    print("✅ New API key generated successfully")
                    print(f"   New key: {new_key[:10]}...")
                    return True
                else:
                    print("❌ Invalid API key received")
                    return False
            else:
                print(f"❌ API key generation failed - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API key generation error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 MCP Dockerized Server Test Suite")
        print("=" * 50)
        
        tests = [
            self.test_health,
            self.test_authentication,
            self.test_tools_listing,
            self.test_console_tool,
            self.test_system_info_tool,
            self.test_mcp_protocol,
            self.test_api_key_generation
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
                print()  # Empty line between tests
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {e}")
                print()
        
        print("=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! MCP server is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
            return False

def main():
    """Main function"""
    port = os.getenv("MCPD_PORT", "8000")
    base_url = f"http://localhost:{port}"
    
    tester = MCPTester(base_url)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--wait":
        print("Waiting for server to start...")
        time.sleep(5)
    
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
