import os
from typing import Any

import pytest
import requests


MCP_BASE_URL = os.environ.get("MCP_BASE_URL")
MCP_SYSTEM_KEY = os.environ.get("MCP_SYSTEM_KEY")


@pytest.mark.skipif(
    not MCP_BASE_URL or not MCP_SYSTEM_KEY,
    reason="MCP_BASE_URL and MCP_SYSTEM_KEY must be set for live MCP tests",
)
def test_hello_mcp_endpoint_round_trip() -> None:
    """Calls the deployed MCP webhook and asserts the hello tool responds."""

    url = f"{MCP_BASE_URL.rstrip('/')}/runtime/webhooks/mcp_extension"
    url = f"{url}?code={MCP_SYSTEM_KEY}"

    payload = {
        "messageType": "call_tool",
        "toolName": "hello_mcp",
        "arguments": {},
    }

    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()

    data: Any
    try:
        data = response.json()
    except ValueError:
        data = response.text

    assert "Hello I am MCPTool" in str(data)
