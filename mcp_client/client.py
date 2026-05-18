import asyncio
from typing import Any
import yaml
from pydantic import BaseModel
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult

class MCPToolReference(BaseModel):
    server_name: str
    original_tool_name: str
    connection: Any # ClientSession
    model_config = {"arbitrary_types_allowed": True}

class MCPConnection:
    def __init__(self, name: str, params: StdioServerParameters):
        self.name = name
        self.params = params
        self.session: ClientSession | None = None
        self._exit_stack = AsyncExitStack()

    async def connect(self):
        stdio_transport = await self._exit_stack.enter_async_context(stdio_client(self.params))
        self.session = await self._exit_stack.enter_async_context(ClientSession(stdio_transport[0], stdio_transport[1]))
        await self.session.initialize()

    async def list_tools(self):
        if not self.session: raise Exception("Not connected")
        response = await self.session.list_tools()
        return response.tools

    async def call_tool(self, name: str, arguments: dict) -> CallToolResult:
        if not self.session: raise Exception("Not connected")
        return await self.session.call_tool(name, arguments)

    async def close(self):
        await self._exit_stack.aclose()


class MCPClient:
    def __init__(self):
        self.connections: dict[str, MCPConnection] = {}
        self.all_tools: dict[str, MCPToolReference] = {}

    async def connect_all_from_config(self, config_path: str):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        for server_name, server_config in config.get("servers", {}).items():
            if server_config["transport"] == "stdio":
                params = StdioServerParameters(
                    command=server_config["command"],
                    args=server_config["args"],
                    env=server_config.get("env", {})
                )
                conn = MCPConnection(server_name, params)
                await conn.connect()
                self.connections[server_name] = conn

    async def list_all_tools(self) -> list[dict]:
        tools = []
        for server_name, conn in self.connections.items():
            server_tools = await conn.list_tools()
            for tool in server_tools:
                namespaced_name = f"{server_name}__{tool.name}"
                description = f"[{server_name}] {tool.description}"
                
                tool_def = {
                    "name": namespaced_name,
                    "description": description,
                    "inputSchema": tool.inputSchema
                }
                tools.append(tool_def)
                self.all_tools[namespaced_name] = MCPToolReference(
                    server_name=server_name,
                    original_tool_name=tool.name,
                    connection=conn
                )
        return tools

    async def call_tool(self, namespaced_name: str, arguments: dict) -> dict:
        if namespaced_name not in self.all_tools:
            return {"error": f"Unknown tool: {namespaced_name}"}

        ref = self.all_tools[namespaced_name]
        try:
            result = await ref.connection.call_tool(ref.original_tool_name, arguments)
            return {"content": [content.model_dump() for content in result.content]}
        except Exception as e:
            return {"error": str(e)}

    async def disconnect_all(self) -> None:
        for conn in self.connections.values():
            await conn.close()
