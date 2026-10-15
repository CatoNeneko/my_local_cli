import sys
import os
from contextlib import nullcontext
from types import SimpleNamespace
from pathlib import Path

import pytest

import mcp_client
import mcp_manager
import permissions

integration = pytest.mark.skipif(
    os.environ.get("CLI_MCP_INTEGRATION") != "1",
    reason="设置 CLI_MCP_INTEGRATION=1 后在 WSL 宿主环境验证真实服务",
)


@pytest.fixture
def configured(monkeypatch):
    if os.environ.get("CLI_MCP_INTEGRATION") != "1":
        monkeypatch.setattr(
            mcp_manager, "start_blocking_portal", lambda: nullcontext(SimpleNamespace())
        )
    demo = Path(__file__).resolve().parents[1] / "mcp_servers" / "demo_server.py"
    monkeypatch.setattr(
        mcp_client,
        "mcp_config",
        {"demo": {"command": sys.executable, "args": [str(demo)], "timeout_seconds": 10}},
    )
    events = []
    monkeypatch.setattr(
        mcp_manager, "record_tool_event", lambda name, result: events.append((name, result))
    )
    monkeypatch.setattr(permissions, "confirm_tool", lambda *args: True)
    return events


@integration
def test_real_stdio_handshake_and_discovery(configured):
    with mcp_manager.MCPManager() as manager:
        result = manager.connect("demo")
        handle = manager.services.get("demo")
        if handle:
            result = {"ok": result["ok"], "server": handle["server"], "tools": handle["tools"]}
    assert result["ok"], result
    assert result["server"]["name"] == "CLI Demo"
    tool = result["tools"][0]
    assert tool["name"] == "add"
    assert tool["inputSchema"]["properties"]["a"]["type"] == "integer"
    assert tool["inputSchema"]["required"] == ["a", "b"]
    assert len(configured) == 1


def test_denied_start_does_not_connect(configured, monkeypatch):
    monkeypatch.setattr(permissions, "confirm_tool", lambda *args: False)
    monkeypatch.setattr(
        mcp_manager.MCPManager, "_serve", lambda *args: pytest.fail("must not connect")
    )
    with mcp_manager.MCPManager() as manager:
        assert not manager.connect("demo")["ok"]
    assert len(configured) == 1


def test_unknown_server(configured):
    with mcp_manager.MCPManager() as manager:
        assert not manager.connect("missing")["ok"]


def test_invalid_configuration_does_not_prompt(configured, monkeypatch):
    mcp_client.mcp_config["demo"]["args"] = "shell command"
    monkeypatch.setattr(permissions, "confirm_tool", lambda *args: pytest.fail("must not prompt"))
    with mcp_manager.MCPManager() as manager:
        assert not manager.connect("demo")["ok"]


@integration
def test_dead_server_reports_failure(configured):
    mcp_client.mcp_config["demo"]["args"] = ["-c", "pass"]
    with mcp_manager.MCPManager() as manager:
        assert not manager.connect("demo")["ok"]


@integration
def test_unresponsive_server_times_out(configured):
    mcp_client.mcp_config["demo"].update(
        args=["-c", "import time; time.sleep(30)"], timeout_seconds=1
    )
    with mcp_manager.MCPManager() as manager:
        assert not manager.connect("demo")["ok"]
