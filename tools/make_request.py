"""make_request tool - HTTP request handler (TalkAPI by RAJ)"""

import json
import sys
import time
from typing import Any, Dict, Optional
from mcp.types import Tool, TextContent
import httpx
from urllib.parse import urlencode, urlparse

from utils import resolve_localhost, is_destructive_method, format_response


class MakeRequestTool:
    """Tool for making HTTP requests with comprehensive error handling"""
    
    def get_definition(self) -> Tool:
        """Return tool definition for MCP"""
        return Tool(
            name="make_request",
            description=(
                "Make an HTTP request to any API endpoint. "
                "Handles GET, POST, PUT, PATCH, DELETE methods with proper body, "
                "query parameters, headers, and timeout. Returns status code, "
                "headers, response time, and body for LLM analysis."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "enum": ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
                        "description": "HTTP method",
                    },
                    "url": {
                        "type": "string",
                        "description": "Full URL or path (if relative, assumes localhost:8000)",
                    },
                    "body": {
                        "type": ["object", "string", "null"],
                        "description": "Request body as structured object (preferred) or JSON string",
                    },
                    "headers": {
                        "type": "object",
                        "description": "HTTP headers as key-value pairs",
                        "additionalProperties": {"type": "string"},
                    },
                    "params": {
                        "type": "object",
                        "description": "Query parameters as key-value pairs (auto-encoded)",
                        "additionalProperties": {"type": ["string", "number", "boolean"]},
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Request timeout in seconds (default: 30)",
                        "default": 30,
                    },
                },
                "required": ["method", "url"],
            },
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute the HTTP request"""
        method = arguments.get("method", "GET").upper()
        url = arguments.get("url", "")
        body = arguments.get("body")
        headers = arguments.get("headers", {})
        params = arguments.get("params")
        timeout = arguments.get("timeout", 30)
        
        # Safety check for destructive methods
        if is_destructive_method(method):
            # Log warning but proceed (local dev assumption)
            print(f"⚠️  Warning: {method} request to {url}", file=sys.stderr)
        
        # Resolve localhost correctly
        url = resolve_localhost(url)
        
        # Handle query parameters
        if params:
            parsed_url = urlparse(url)
            query_string = urlencode(params, doseq=True)
            if parsed_url.query:
                # Merge with existing query parameters
                url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{parsed_url.query}&{query_string}"
            else:
                url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{query_string}"
            # Preserve fragment if present
            if parsed_url.fragment:
                url += f"#{parsed_url.fragment}"
        
        # Prepare body
        json_body = None
        content_type = headers.get("Content-Type", headers.get("content-type"))
        
        if body is not None:
            if isinstance(body, str):
                # Try to parse JSON string
                try:
                    json_body = json.loads(body)
                except json.JSONDecodeError:
                    # If not JSON, treat as raw string
                    json_body = body
                    if not content_type:
                        content_type = "text/plain"
            else:
                # Structured object - convert to JSON
                json_body = body
                if not content_type:
                    content_type = "application/json"
            
            if content_type:
                headers["Content-Type"] = content_type
        
        # Make request
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=json_body if isinstance(json_body, (dict, list)) else None,
                    content=json_body if isinstance(json_body, str) else None,
                    headers=headers,
                )
                
                response_time = time.time() - start_time
                
                # Try to parse response body
                try:
                    response_body = response.json()
                except Exception:
                    response_body = response.text
                
                return format_response(
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    body=response_body,
                    response_time=response_time,
                    method=method,
                    url=url,
                )
        
        except httpx.TimeoutException:
            response_time = time.time() - start_time
            return format_response(
                status_code=0,
                headers={},
                body={"error": f"Request timeout after {timeout}s"},
                response_time=response_time,
                method=method,
                url=url,
                error="TIMEOUT",
            )
        
        except httpx.RequestError as e:
            response_time = time.time() - start_time
            return format_response(
                status_code=0,
                headers={},
                body={"error": str(e)},
                response_time=response_time,
                method=method,
                url=url,
                error="REQUEST_ERROR",
            )

