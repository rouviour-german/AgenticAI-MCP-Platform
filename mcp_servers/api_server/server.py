import asyncio
import json
import httpx
from mcp.server.stdio import stdio_server
from mcp.server import Server
from mcp.types import Tool, TextContent

class APITools:
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=10.0)

    async def get_weather(self, city: str) -> str:
        # Mock weather API since we don't have a real key configured
        # In a real app, you'd call an actual weather API
        try:
            return json.dumps({
                "city": city,
                "temperature": "20°C",
                "condition": "Sunny",
                "humidity": "45%"
            }, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

app = Server("api_server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_weather",
            description="Get current weather for a city.",
            inputSchema={
                "type": "object",
                "properties": {"city": {"type": "string", "description": "Name of the city"}},
                "required": ["city"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    tools = APITools()
    if name == "get_weather":
        result = await tools.get_weather(arguments["city"])
        return [TextContent(type="text", text=result)]
    
    return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
