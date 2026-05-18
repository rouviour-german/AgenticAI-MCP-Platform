import asyncio
import os
from dotenv import load_dotenv
from agent.core import MCPAgent
from rich.console import Console
from rich.markdown import Markdown

async def main():
    load_dotenv()
    console = Console()
    
    console.print("[bold blue]🔌 MCP Agent Platform v1.1 (DeepSeek Edition)[/bold blue]")
    console.print("=" * 50)
    
    agent = MCPAgent()
    
    console.print("Connecting to MCP servers...")
    await agent.initialize()
    
    console.print("\n[bold green]Ready.[/bold green] Type 'quit' or 'exit' to stop.")
    
    while True:
        try:
            user_input = console.input("\n[bold cyan]You:[/bold cyan] ")
            if user_input.strip().lower() in ["quit", "exit"]:
                break
                
            console.print("\n[dim]Thinking...[/dim]")
            response = await agent.chat(user_input)
            
            console.print(f"\n[bold magenta]Agent:[/bold magenta]")
            console.print(Markdown(response))
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

    await agent.mcp_client.disconnect_all()
    console.print("Shutdown complete.")

if __name__ == "__main__":
    asyncio.run(main())
