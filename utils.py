"""Utility functions for TalkAPI - Built by RAJ"""

import json
import os
import sys
from typing import Dict, Any, Optional
from urllib.parse import urlparse


def setup_logging():
    """Setup basic logging configuration"""
    # Can be extended with proper logging if needed
    pass


def resolve_localhost(url: str) -> str:
    """
    Resolve localhost correctly for different environments.
    
    Handles:
    - Relative paths (assumes localhost:8000)
    - localhost in Docker (maps to host.docker.internal)
    - Native localhost
    """
    if not url:
        return url
    
    # If it's a relative path, assume localhost:8000
    if not url.startswith(("http://", "https://")):
        url = f"http://localhost:8000{url}" if not url.startswith("/") else f"http://localhost:8000{url}"
    
    parsed = urlparse(url)
    
    # Check if we're in Docker
    in_docker = os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER") == "true"
    
    # Replace localhost with host.docker.internal if in Docker
    if in_docker and parsed.hostname in ("localhost", "127.0.0.1"):
        new_netloc = parsed.netloc.replace("localhost", "host.docker.internal")
        new_netloc = new_netloc.replace("127.0.0.1", "host.docker.internal")
        url = f"{parsed.scheme}://{new_netloc}{parsed.path}"
        if parsed.query:
            url += f"?{parsed.query}"
        if parsed.fragment:
            url += f"#{parsed.fragment}"
    
    return url


def is_destructive_method(method: str) -> bool:
    """Check if HTTP method is destructive (DELETE, PUT)"""
    return method.upper() in ("DELETE", "PUT")


def format_response(
    status_code: int,
    headers: Dict[str, str],
    body: Any,
    response_time: float,
    method: str,
    url: str,
    error: Optional[str] = None,
) -> str:
    """
    Format HTTP response for LLM consumption.
    
    Returns a structured JSON string with all relevant information
    for the LLM to analyze the API response.
    """
    result = {
        "status_code": status_code,
        "method": method,
        "url": url,
        "response_time_ms": round(response_time * 1000, 2),
        "headers": headers,
        "body": body,
    }
    
    if error:
        result["error_type"] = error
    
    # Add helpful analysis hints
    if status_code >= 500:
        result["analysis_hint"] = "Server error - check server logs, database connection, or environment variables"
    elif status_code == 401:
        result["analysis_hint"] = "Unauthorized - check authentication token or credentials"
    elif status_code == 403:
        result["analysis_hint"] = "Forbidden - check user permissions"
    elif status_code == 404:
        result["analysis_hint"] = "Not found - check URL path and route configuration"
    elif status_code == 422:
        result["analysis_hint"] = "Validation error - check request body format and required fields"
    
    # Format as readable JSON
    return json.dumps(result, indent=2, default=str)

