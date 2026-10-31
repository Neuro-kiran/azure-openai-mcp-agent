# Azure OpenAI + MCP Tool-Calling Agent

An AI agent on **Azure OpenAI (Azure AI Foundry)** that discovers its tools at runtime from a **Model Context Protocol (MCP)** server and calls them in a bounded tool-calling loop. Authentication uses **Microsoft Entra ID** (`DefaultAzureCredential`) - no API keys.

```
user -> Azure OpenAI (chat + tools) <-> agent loop <--MCP/stdio--> azure_ops_mcp_server.py -> az CLI (read-only)
```

## Highlights
- MCP tool definitions are converted to OpenAI function-calling schema automatically
- Keyless auth with Entra ID / managed identity
- Read-only tools with input validation (blocks argument injection); loop capped at 6 steps

## Run
```bash
pip install -r requirements.txt
cp .env.example .env && export $(grep -v '^#' .env | xargs)   # endpoint + your deployment name
az login
python agent.py "What VMs are running in resource group rg-demo?"
```
The identity needs the *Cognitive Services OpenAI User* role on the resource and Reader on the subscription.

## Test
```bash
pytest   # includes a real stdio MCP client <-> server test
```

## Stack
Python, Azure OpenAI / AI Foundry, MCP, azure-identity, Azure CLI.
