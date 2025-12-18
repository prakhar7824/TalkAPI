#!/usr/bin/env python3
"""
PostmanMCP - MCP Server for API Testing
Replaces Postman with conversational API testing via LLM
"""

import asyncio
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from tools import (
    make_request_tool,
    decode_jwt_tool,
    validate_json_schema_tool,
)
from utils import setup_logging

# Initialize server
app = Server("postman-mcp")

# Register tools
@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools"""
    return [
        make_request_tool.get_definition(),
        decode_jwt_tool.get_definition(),
        validate_json_schema_tool.get_definition(),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Route tool calls to appropriate handlers"""
    if name == "make_request":
        result = await make_request_tool.execute(arguments)
    elif name == "decode_jwt":
        result = await decode_jwt_tool.execute(arguments)
    elif name == "validate_json_schema":
        result = await validate_json_schema_tool.execute(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")
    
    return [TextContent(type="text", text=result)]


async def main():
    """Main entry point"""
    setup_logging()
    
    async with stdio_server() as streams:
        await app.run(
            streams[0],
            streams[1],
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())

