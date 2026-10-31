"""Small MCP server exposing read-only Azure helper tools via the Azure CLI (stdio).

Tools: list_resource_groups, list_resources_in_group, list_vms.
Run standalone: python azure_ops_mcp_server.py
"""
import json
import re
import subprocess

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("azure-ops")
_SAFE = re.compile(r"^[A-Za-z0-9_(][A-Za-z0-9._()\-]{0,89}$")  # RG-name charset; must not start with "-"


def _az(*args: str) -> str:
    result = subprocess.run(["az", *args, "-o", "json"], capture_output=True, text=True, timeout=60)
    return result.stdout if result.returncode == 0 else f"ERROR: {result.stderr.strip()}"


def validate_name(name: str) -> str:
    """Reject anything that is not a plain resource-group name (prevents arg injection)."""
    if not _SAFE.match(name):
        raise ValueError(f"invalid resource group name: {name!r}")
    return name


@mcp.tool()
def list_resource_groups() -> str:
    """List resource groups in the current subscription."""
    return _az("group", "list", "--query", "[].{name:name,location:location}")


@mcp.tool()
def list_resources_in_group(resource_group: str) -> str:
    """List resources (name, type, location) inside a resource group."""
    rg = validate_name(resource_group)
    return _az("resource", "list", "-g", rg, "--query", "[].{name:name,type:type,location:location}")


@mcp.tool()
def list_vms(resource_group: str) -> str:
    """List virtual machines (name, size, power state) in a resource group."""
    rg = validate_name(resource_group)
    return _az("vm", "list", "-g", rg, "-d", "--query",
               "[].{name:name,size:hardwareProfile.vmSize,power:powerState}")


if __name__ == "__main__":
    mcp.run()
