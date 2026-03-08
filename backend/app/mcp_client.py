import asyncio
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

class MCPClient:
    def __init__(self):
        # Path to the server script we just created
        self.server_script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "hotel_ops_server.py")
        self.session = None
        self.exit_stack = AsyncExitStack()

    async def connect(self):
        """Connect to the local MCP server."""
        print(f"[MCPClient] Connecting to server at {self.server_script_path}...")
        
        server_params = StdioServerParameters(
            command=sys.executable, # Use the same python interpreter
            args=[self.server_script_path],
            env=None
        )

        try:
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            self.read, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.read, self.write)
            )
            await self.session.initialize()
            print("[MCPClient] Connected and initialized.")
            
        except Exception as e:
            print(f"[MCPClient] Connection failed: {e}")
            raise e

    async def list_tools(self):
        """List available tools from the server."""
        if not self.session:
            try:
                await asyncio.wait_for(self.connect(), timeout=3.0)
            except asyncio.TimeoutError:
                raise Exception("MCP connection timeout")
            except Exception as e:
                raise Exception(f"MCP connection failed: {str(e)}")
        
        try:
            response = await asyncio.wait_for(
                self.session.list_tools(),
                timeout=2.0
            )
            return response.tools
        except asyncio.TimeoutError:
            raise Exception("MCP list_tools timeout")

    async def call_tool(self, name: str, arguments: dict):
        """Execute a tool."""
        if not self.session:
            try:
                await asyncio.wait_for(self.connect(), timeout=3.0)
            except asyncio.TimeoutError:
                raise Exception("MCP connection timeout")
            except Exception as e:
                raise Exception(f"MCP connection failed: {str(e)}")
        
        try:
            result = await asyncio.wait_for(
                self.session.call_tool(name, arguments),
                timeout=5.0
            )
            return result.content
        except asyncio.TimeoutError:
            raise Exception(f"Tool {name} execution timeout")

    async def close(self):
        await self.exit_stack.aclose()
