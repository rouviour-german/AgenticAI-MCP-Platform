class SchemaTranslator:
    """
    Translates MCP tool definitions into the LLM's native tool format.
    Specifically for OpenAI format, as DeepSeek uses the same API interface.
    """

    def to_openai_tools(self, mcp_tools: list[dict]) -> list[dict]:
        """
        Convert MCP tools to OpenAI's function calling format.

        OpenAI format:
        {
            "type": "function",
            "function": {
                "name": "database__query_database",
                "description": "...",
                "parameters": { ... JSON Schema ... }
            }
        }
        """
        openai_tools = []
        for tool in mcp_tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["inputSchema"]
                }
            })
        return openai_tools
