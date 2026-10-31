import asyncio
import sys

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import azure_ops_mcp_server as srv
from agent import SERVER, mcp_tools_to_openai


def test_validate_name_blocks_injection():
    assert srv.validate_name("rg-demo_1") == "rg-demo_1"
    for bad in ["rg; rm -rf /", "--query", "a b", "", "x" * 200]:
        with pytest.raises(ValueError):
            srv.validate_name(bad)


def test_mcp_tools_convert_to_openai_schema_over_real_stdio():
    async def go():
        params = StdioServerParameters(command=sys.executable, args=[SERVER])
        async with stdio_client(params) as (r, w), ClientSession(r, w) as s:
            await s.initialize()
            return mcp_tools_to_openai((await s.list_tools()).tools)

    tools = asyncio.run(go())
    assert {t["function"]["name"] for t in tools} == {
        "list_resource_groups", "list_resources_in_group", "list_vms"}
    vm = next(t for t in tools if t["function"]["name"] == "list_vms")
    assert vm["function"]["parameters"]["required"] == ["resource_group"]
