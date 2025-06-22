import httpx
from fastmcp.server import FastMCP
from typing import Optional, Dict, Any, Union


def setup(server: FastMCP) -> None:
    @server.tool(name="jsonapi", description="Make HTTP requests to external APIs")
    async def jsonapi(
        endpoint: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP requests to external APIs and return JSON responses.
        
        Args:
            endpoint: URL to send the request to
            method: HTTP method (GET, POST, PUT, etc.)
            headers: Optional HTTP headers
            params: Optional URL parameters
            json: Optional JSON body for the request
        """
        headers = headers or {}
        method = method.upper()
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=endpoint,
                    headers=headers,
                    params=params,
                    json=json,
                    timeout=30.0,
                    follow_redirects=True
                )
                
                # Try to parse response as JSON
                try:
                    data = response.json()
                except ValueError:
                    # Return text if not JSON
                    data = response.text
                
                return {
                    "status_code": response.status_code,
                    "success": 200 <= response.status_code < 300,
                    "headers": dict(response.headers),
                    "data": data
                }
                
            except httpx.RequestError as e:
                return {
                    "status_code": None,
                    "success": False,
                    "error": f"Request error: {str(e)}",
                    "data": None
                }