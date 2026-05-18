import asyncio
import json
from typing import Callable, Any
from pydantic import BaseModel, ValidationError

class ToolDefinition(BaseModel):
    name: str
    description: str
    inputSchema: dict

class ContentBlock(BaseModel):
    type: str
    text: str | None = None
    data: str | None = None
    mimeType: str | None = None

class ToolResult(BaseModel):
    content: list[ContentBlock]
    isError: bool = False

class ToolHandler(BaseModel):
    definition: ToolDefinition
    handler: Callable
    model_config = {"arbitrary_types_allowed": True}

class BaseMCPServer:
    def __init__(self, name: str, description: str, version: str = "1.0.0", tool_timeout=5.0):
        self.name = name
        self.description = description
        self.version = version
        self.tool_timeout = tool_timeout
        self._tools: dict[str, ToolHandler] = {}

    def register_tool(self, name: str, description: str, input_schema: dict, handler: Callable) -> None:
        self._tools[name] = ToolHandler(
            definition=ToolDefinition(name=name, description=description, inputSchema=input_schema),
            handler=handler,
        )

    async def handle_list_tools(self) -> list[ToolDefinition]:
        return [th.definition for th in self._tools.values()]

    def _validate_arguments(self, arguments: dict, schema: dict):
        pass # In a real implementation use jsonschema validation

    async def handle_call_tool(self, name: str, arguments: dict) -> ToolResult:
        if name not in self._tools:
            return ToolResult(content=[ContentBlock(type="text", text=f"Unknown tool: {name}")], isError=True)

        handler = self._tools[name]
        try:
            self._validate_arguments(arguments, handler.definition.inputSchema)
            if asyncio.iscoroutinefunction(handler.handler):
                result = await asyncio.wait_for(handler.handler(**arguments), timeout=self.tool_timeout)
            else:
                result = handler.handler(**arguments)

            if isinstance(result, str):
                return ToolResult(content=[ContentBlock(type="text", text=result)])
            elif isinstance(result, dict) or isinstance(result, list):
                return ToolResult(content=[ContentBlock(type="text", text=json.dumps(result, indent=2))])
            else:
                return ToolResult(content=[ContentBlock(type="text", text=str(result))])

        except ValidationError as e:
            return ToolResult(content=[ContentBlock(type="text", text=f"Invalid arguments: {e}")], isError=True)
        except asyncio.TimeoutError:
            return ToolResult(content=[ContentBlock(type="text", text=f"Tool '{name}' timed out after {self.tool_timeout}s")], isError=True)
        except Exception as e:
            return ToolResult(content=[ContentBlock(type="text", text=f"Tool error: {type(e).__name__}: {e}")], isError=True)
