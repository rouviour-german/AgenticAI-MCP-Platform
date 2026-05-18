from openai import AsyncOpenAI

class LLMClient:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

    async def chat(self, system: str, messages: list, tools: list | None = None):
        api_messages = [{"role": "system", "content": system}] + messages
        
        kwargs = {
            "model": "deepseek-chat",
            "messages": api_messages,
            "temperature": 0.0,
        }
        
        if tools:
            kwargs["tools"] = tools

        response = await self.client.chat.completions.create(**kwargs)
        
        return response.choices[0].message
