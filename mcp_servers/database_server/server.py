import asyncio
import json
import os
from mcp.server.stdio import stdio_server
from mcp.server import Server
from mcp.types import Tool, TextContent

class DatabaseTools:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def query_database(self, sql: str) -> str:
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
            return json.dumps({"error": "Only SELECT queries are allowed"})

        dangerous = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE"]
        for keyword in dangerous:
            if keyword in sql_upper:
                return json.dumps({"error": f"Keyword '{keyword}' is not allowed in read-only queries"})

        if "LIMIT" not in sql_upper:
            sql = sql.rstrip(";") + " LIMIT 100"

        import aiosqlite
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(sql)
                rows = await cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                result = [dict(zip(columns, row)) for row in rows]
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": str(e)})

app = Server("database_server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="query_database",
            description="Run a read-only SQL query against the database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "SQL SELECT query to execute."}
                },
                "required": ["sql"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    db_path = os.environ.get("DATABASE_PATH", "output/platform.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Initialize basic DB if not exists
    if not os.path.exists(db_path):
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, role TEXT)")
        conn.execute("INSERT INTO users (name, role) VALUES ('Admin', 'admin')")
        conn.commit()
        conn.close()

    tools = DatabaseTools(db_path)
    if name == "query_database":
        result = await tools.query_database(arguments["sql"])
        return [TextContent(type="text", text=result)]
    
    return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
