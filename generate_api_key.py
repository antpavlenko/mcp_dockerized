#!/usr/bin/env python3
"""
Script to generate new API keys for the MCP server
Can be run inside the Docker container to generate additional API keys
"""

import os
import sys
import json
import secrets
import requests
from pathlib import Path

def generate_api_key_locally():
    """Generate API key locally by modifying the keys file"""
    data_dir = Path("data")
    api_keys_file = data_dir / "api_keys.json"
    
    # Load existing keys
    keys = []
    if api_keys_file.exists():
        try:
            with open(api_keys_file, 'r') as f:
                data = json.load(f)
                keys = data.get('keys', [])
        except Exception as e:
            print(f"Error loading existing keys: {e}")
            return None
    
    # Generate new key
    new_key = secrets.token_urlsafe(32)
    keys.append(new_key)
    
    # Save updated keys
    data_dir.mkdir(exist_ok=True)
    try:
        with open(api_keys_file, 'w') as f:
            json.dump({'keys': keys}, f, indent=2)
        print(f"✅ New API key generated: {new_key}")
        return new_key
    except Exception as e:
        print(f"❌ Error saving new key: {e}")
        return None

def generate_api_key_via_api():
    """Generate API key via the API endpoint"""
    port = os.getenv("MCPD_PORT", "8000")
    base_url = f"http://localhost:{port}"
    
    # Try to get an existing API key from the file
    data_dir = Path("data")
    api_keys_file = data_dir / "api_keys.json"
    
    if not api_keys_file.exists():
        print("❌ No existing API keys found. Cannot authenticate with API.")
        return None
    
    try:
        with open(api_keys_file, 'r') as f:
            data = json.load(f)
            existing_keys = data.get('keys', [])
            
        if not existing_keys:
            print("❌ No existing API keys found in file.")
            return None
        
        # Use the first key to authenticate
        auth_key = existing_keys[0]
        headers = {"Authorization": f"Bearer {auth_key}"}
        
        response = requests.post(f"{base_url}/api/generate-key", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            new_key = result.get("api_key")
            print(f"✅ New API key generated via API: {new_key}")
            return new_key
        else:
            print(f"❌ API request failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error generating key via API: {e}")
        return None

def main():
    """Main function"""
    print("🔑 MCP Dockerized - API Key Generator")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--api":
        print("Generating API key via API endpoint...")
        generate_api_key_via_api()
    else:
        print("Generating API key locally...")
        generate_api_key_locally()

if __name__ == "__main__":
    main()
