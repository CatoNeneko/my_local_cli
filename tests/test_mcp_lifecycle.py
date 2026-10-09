import os
import signal
import threading
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

import mcp_client
import mcp_manager
import permissions
import tool_registry
import tool_runtime


pytestmark = pytest.mark.skipif(
    os.environ.get('CLI_MCP_INTEGRATION') != '1', reason='验证真实常驻 MCP 服务'
)


@pytest.fixture
def server(tmp_path, monkeypatch):
    # 每次启动写入一次 PID；工具递增计数用于证明调用之间保留服务状态。
    source = tmp_path / 'server.py'
    pid_log = tmp_path / 'pids.txt'
    source.write_text('''import os
import time
from pathlib import Path
from mcp.server.fastmcp import FastMCP
Path(__file__).with_name('pids.txt').open('a').write(str(os.getpid()) + '\\n')
server = FastMCP('Stateful test')
count = 0
@server.tool()
def increment() -> int:
    global count
    count += 1
    return count
@server.tool()
def slow() -> str:
    time.sleep(30)
    return 'finished'
if __name__ == '__main__':
    server.run(transport='stdio')
''')
    config = {'demo': {'command': sys.executable, 'args': [str(source)], 'timeout_seconds': 1}}
    monkeypatch.setattr(mcp_client, 'mcp_config', config)
    monkeypatch.setattr(mcp_manager, 'mcp_config', config)
    monkeypatch.setattr(mcp_manager, 'record_tool_event', Mock())
    monkeypatch.setattr(tool_runtime, 'record_tool_event', Mock())
    monkeypatch.setattr(permissions, 'confirm_tool', Mock(return_value=True))
    saved = dict(tool_registry.TOOL_REGISTRY)
    yield pid_log
    tool_registry.TOOL_REGISTRY.clear()
    tool_registry.TOOL_REGISTRY.update(saved)


def assert_process_gone(pid_log):
    for pid in pid_log.read_text().splitlines():
        with pytest.raises(ProcessLookupError):
            os.kill(int(pid), 0)


def test_startup_load_reuses_process_refresh_does_not_restart_and_exit_closes(server):
    with mcp_manager.MCPManager() as manager:
        assert manager.load_configured()['demo']['ok']
        assert 'mcp__demo__increment' in manager.tool_names()
        first = tool_runtime.execute_tool('mcp__demo__increment', {})
        second = tool_runtime.execute_tool('mcp__demo__increment', {})
        assert first['content'] == ['1'] and second['content'] == ['2']
        assert manager.refresh('demo')['ok']
        assert len(server.read_text().splitlines()) == 1
        assert permissions.confirm_tool.call_count == 3  # 启动一次，工具调用两次。
    assert 'mcp__demo__increment' not in tool_registry.TOOL_REGISTRY
    assert_process_gone(server)


def test_keyboard_interrupt_closes_service(server):
    with pytest.raises(KeyboardInterrupt):
        with mcp_manager.MCPManager() as manager:
            assert manager.load_configured()['demo']['ok']
            raise KeyboardInterrupt
    assert_process_gone(server)


def test_timeout_disconnects_unregisters_and_refresh_reconnects(server):
    with mcp_manager.MCPManager() as manager:
        assert manager.connect('demo')['ok']
        result = tool_runtime.execute_tool('mcp__demo__slow', {})
        assert not result['ok']
        assert 'mcp__demo__increment' not in tool_registry.TOOL_REGISTRY
        assert_process_gone(server)
        assert manager.refresh('demo')['ok']
        assert len(server.read_text().splitlines()) == 2
    assert_process_gone(server)


def test_sigint_cancels_call_closes_service_and_allows_reconnect(server):
    mcp_client.mcp_config['demo']['timeout_seconds'] = 10
    with mcp_manager.MCPManager() as manager:
        assert manager.connect('demo')['ok']
        timer = threading.Timer(0.3, os.kill, args=(os.getpid(), signal.SIGINT))
        timer.start()
        try:
            result = tool_runtime.execute_tool('mcp__demo__slow', {})
        finally:
            timer.cancel()
            timer.join()
        assert not result['ok'] and result['cancelled']
        assert 'mcp__demo__increment' not in manager.tool_names()
        assert_process_gone(server)
        assert manager.refresh('demo')['ok']
        assert tool_runtime.execute_tool('mcp__demo__increment', {})['content'] == ['1']
    assert_process_gone(server)
