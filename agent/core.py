import asyncio
import os
import time
from uuid import uuid4
from tenacity import retry, wait_exponential, stop_after_attempt
import structlog
from pydantic import BaseModel

from agent.llm import LLMClient
from mcp_client.client import MCPClient
from mcp_client.schema_translator import SchemaTranslator

class RateLimiterRegistry:
    def __init__(self):
        self.limits = {} # simple mock
    async def check(self, server_name: str):
        pass # mock rate checker

class CircuitBreakerRegistry:
    def __init__(self):
        pass
    def check(self, server_name: str):
        pass
    def record_success(self, server_name: str):
        pass
    def record_failure(self, server_name: str):
        pass

class MetricsCollector:
    def record_tool_call(self, server: str, tool: str, success: bool):
        pass

class TraceSpan:
    def __init__(self, name):
        pass
    def __enter__(self): return self
    def __exit__(self, exc_type, exc_val, exc_tb): pass

class TracerContext:
    def span(self, name, type_):
        return TraceSpan(name)

class Tracer:
    def start_trace(self, name, meta) -> TracerContext:
        return TracerContext()
    def end_trace(self, id):
        pass

SYSTEM_PROMPT = """You are a helpful AI agent with access to multiple tools via MCP (Model Context Protocol).
Analyze the user request, plan, and execute tool calls as needed.
Return your final thoughts and the text response.
"""

class MCPAgent:
    def __init__(self):
        self.llm = LLMClient(api_key=os.getenv("DEEPSEEK_API_KEY", ""))
        self.mcp_client = MCPClient()
        self.rate_limiters = RateLimiterRegistry()
        self.circuit_breakers = CircuitBreakerRegistry()
        self.tracer = Tracer()
        self.logger = structlog.get_logger("mcp-agent")
        self.metrics = MetricsCollector()

    async def initialize(self, server_config: str = "config/servers.yaml") -> None:
        await self.mcp_client.connect_all_from_config(server_config)
        mcp_tools = await self.mcp_client.list_all_tools()
        self.openai_tools = SchemaTranslator().to_openai_tools(mcp_tools)
        self.logger.info(f"Connected to {len(self.mcp_client.connections)} servers, {len(self.openai_tools)} tools available")

    async def chat(self, user_message: str) -> str:
        trace_ctx = self.tracer.start_trace("agent_chat", {"user_message": user_message[:100]})
        messages = [{"role": "user", "content": user_message}]

        for iteration in range(10):
            with trace_ctx.span("llm_call", "llm"):
                response = await self.llm.chat(
                    system=SYSTEM_PROMPT,
                    messages=messages,
                    tools=self.openai_tools,
                )

            if response.tool_calls:
                tool_results = []
                messages.append(response) # Add the assistant response with tool calls
                
                for tool_call in response.tool_calls:
                    import json
                    arguments = json.loads(tool_call.function.arguments)
                    result = await self._execute_tool_with_resilience(
                        tool_call.function.name, arguments, trace_ctx
                    )
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": json.dumps(result)
                    })
                continue
            
            trace = self.tracer.end_trace("agent_chat")
            self.logger.info("Agent responded", response=response.content)
            return response.content

    async def _execute_tool_with_resilience(self, tool_name: str, arguments: dict, trace_ctx) -> dict:
        server_name = tool_name.split("__")[0]
        with trace_ctx.span(f"tool:{tool_name}", "mcp_tool"):
            try:
                await self.rate_limiters.check(server_name)
                self.circuit_breakers.check(server_name)
                
                # Setup retries wrapper
                @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
                async def do_call():
                    return await self.mcp_client.call_tool(tool_name, arguments)
                
                result = await do_call()
                self.circuit_breakers.record_success(server_name)
                self.metrics.record_tool_call(server_name, tool_name, success=True)
                return result
            except Exception as e:
                self.circuit_breakers.record_failure(server_name)
                self.metrics.record_tool_call(server_name, tool_name, success=False)
                return {"error": str(e)}
