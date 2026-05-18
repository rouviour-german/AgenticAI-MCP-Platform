import asyncio
import json
import os
from pathlib import Path
from mcp.server.stdio import stdio_server
from mcp.server import Server
from mcp.types import Tool, TextContent

class FilesystemTools:
    def __init__(self, sandbox_root: str):
        self.sandbox_root = Path(sandbox_root).resolve()
        self.sandbox_root.mkdir(parents=True, exist_ok=True)

    def _validate_path(self, path: str) -> Path:
        resolved = (self.sandbox_root / path).resolve()
        if not str(resolved).startswith(str(self.sandbox_root)):
            raise Exception(f"SecurityError: Path '{path}' escapes sandbox boundary")
        return resolved

    async def read_file(self, path: str, encoding: str = "utf-8") -> str:
        try:
            safe_path = self._validate_path(path)
            if not safe_path.exists():
                return json.dumps({"error": f"File not found: {path}"})
            if safe_path.stat().st_size > 1_000_000:
                return json.dumps({"error": "File too large (>1MB)."})
            return safe_path.read_text(encoding=encoding)
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def write_file(self, path: str, content: str) -> str:
        try:
            safe_path = self._validate_path(path)
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            safe_path.write_text(content)
            return json.dumps({"status": "success", "path": path, "bytes_written": len(content)})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def list_directory(self, path: str = ".", recursive: bool = False) -> str:
        try:
            safe_path = self._validate_path(path)
            if not safe_path.is_dir():
                return json.dumps({"error": f"Not a directory: {path}"})
            entries = []
            pattern = "**/*" if recursive else "*"
            for item in safe_path.glob(pattern):
                relative = item.relative_to(self.sandbox_root)
                entries.append({
                    "name": str(relative),
                    "type": "directory" if item.is_dir() else "file",
                    "size_bytes": item.stat().st_size if item.is_file() else None,
                })
            return json.dumps(entries[:500], indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

app = Server("filesystem_server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="read_file",
            description="Read file contents in the sandbox directory.",
            inputSchema={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"]
            }
        ),
        Tool(
            name="write_file",
            description="Write text to a file in the sandbox.",
            inputSchema={
                "type": "object",
                "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                "required": ["path", "content"]
            }
        ),
        Tool(
            name="list_directory",
            description="List directory contents.",
            inputSchema={
                "type": "object",
                "properties": {"path": {"type": "string", "default": "."}, "recursive": {"type": "boolean", "default": False}},
                "required": ["path"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    fs_root = os.environ.get("FILESYSTEM_ROOT", "./sandbox_files")
    tools = FilesystemTools(fs_root)
    
    if name == "read_file":
        result = await tools.read_file(arguments["path"])
        return [TextContent(type="text", text=result)]
    elif name == "write_file":
        result = await tools.write_file(arguments["path"], arguments["content"])
        return [TextContent(type="text", text=result)]
    elif name == "list_directory":
        result = await tools.list_directory(arguments.get("path", "."), arguments.get("recursive", False))
        return [TextContent(type="text", text=result)]
    
    return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
