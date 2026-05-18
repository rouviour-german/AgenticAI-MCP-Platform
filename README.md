# AgenticAI MCP Platform

> A production-ready Agentic AI platform leveraging the Model Context Protocol (MCP) with DeepSeek integration.

## Overview

This project is a production-grade Agentic AI platform demonstrating how to use the Model Context Protocol (MCP) to standardize tool interactions, specifically tailored to use the **DeepSeek API** in place of Anthropic or OpenAI models.

**Version: 1.1** 

This platform acts as the bridge between impressive AI demos and reliable shipped products, emphasizing production engineering: auth, rate limiting, circuit breakers, retries, tracing, and logging.

## Core Architecture

- **MCP Client**: Discovers servers, reads capabilities, translates schemas, and routes tool calls to the correct server.
- **MCP Servers**: 3 built-in servers extending the LLM's capabilities.
  - `database_server`: SQLite database read/write wrapper with read-only query protections.
  - `filesystem_server`: Sandboxed filesystem reader/writer.
  - `api_server`: Generic mock weather REST API wrapper.
- **DeepSeek LLM**: Leverages DeepSeek Chat via their OpenAI-compatible endpoint.
- **Resilience Layer**: Intercepts MCP Tool calls with robust failure mitigation patterns (token bucket rate limits, automated circuit breakers for broken integrations).
- **Observability Layer**: Detailed console logging, trace contexts, and metrics recording.

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd AgenticAI-MCP-Platform
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   Copy `.env.example` to `.env` and add your valid `DEEPSEEK_API_KEY`:
   ```bash
   cp .env.example .env
   # Edit .env with your DeepSeek API key
   ```

5. **Run the platform:**
   ```bash
   python main.py
   ```

## Features

- 🚀 **Production-Ready**: Built-in resilience patterns including circuit breakers and rate limiting
- 🔒 **Secure**: JWT authentication and sandboxed file system access
- 📊 **Observable**: Comprehensive logging and metrics collection
- 🔌 **Extensible**: Easy-to-add MCP servers for new tools
- 🎯 **DeepSeek Optimized**: First-class support for DeepSeek API integration

## Why MCP?

Before MCP, agents needed custom integration code for every tool (Agent A ──custom code──→ Slack API). With MCP, we write one MCP server per tool. Every agent connects to it universally (Agent A ──MCP──→ Slack MCP Server). 

MCP provides primitives for:
1. **Tools:** Executable functions
2. **Resources:** Readable data entities
3. **Prompts:** Reusable user prompts
4. **Transport:** JSON-RPC over stdio or SSE

## Extending

To add a new tool simply implement a new MCP Server using the official Python SDK, and add it to `config/servers.yaml`. The schema translation ensures the DeepSeek API immediately recognizes the tool.

---

## Author & Contact

- **GitHub:** [@rouviour-german](https://github.com/rouviour-german)
- **Email:** [rouviourgermanmeetings@gmail.com](mailto:rouviourgermanmeetings@gmail.com)
- **Profile:** https://github.com/rouviour-german

