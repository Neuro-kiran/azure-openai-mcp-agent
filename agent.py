"""Azure OpenAI tool-calling agent that discovers its tools from an MCP server.

Auth: Microsoft Entra ID via DefaultAzureCredential (no API keys in code or env).
Usage: python agent.py "What VMs are running in resource group rg-demo?"
"""
import asyncio
import json
import os
import sys
from pathlib import Path

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AzureOpenAI

SERVER = str(Path(__file__).with_name("azure_ops_mcp_server.py"))
MAX_STEPS = 6
SYSTEM = ("You are an Azure operations assistant. Use the tools to answer. "
          "You only have read-only tools. Summarise results clearly.")


def mcp_tools_to_openai(tools) -> list[dict]:
    """Convert MCP tool definitions into OpenAI function-calling schema."""
    return [
        {"type": "function",
         "function": {"name": t.name, "description": t.description or "", "parameters": t.inputSchema}}
        for t in tools
    ]


def make_client() -> AzureOpenAI:
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
    return AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        azure_ad_token_provider=token_provider,
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )


async def run(question: str) -> str:
    client, model = make_client(), os.environ["AZURE_OPENAI_DEPLOYMENT"]
    params = StdioServerParameters(command=sys.executable, args=[SERVER])
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        tools = mcp_tools_to_openai((await session.list_tools()).tools)
        messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]
        for _ in range(MAX_STEPS):
            reply = client.chat.completions.create(model=model, messages=messages, tools=tools).choices[0].message
            if not reply.tool_calls:
                return reply.content or ""
            messages.append(reply)
            for call in reply.tool_calls:
                result = await session.call_tool(call.function.name, json.loads(call.function.arguments))
                text = "\n".join(c.text for c in result.content if hasattr(c, "text"))
                messages.append({"role": "tool", "tool_call_id": call.id, "content": text})
        return "Stopped: too many tool-calling steps."


if __name__ == "__main__":
    print(asyncio.run(run(" ".join(sys.argv[1:]) or "List my resource groups.")))
