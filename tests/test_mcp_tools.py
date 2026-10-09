import asyncio
import json
import os
import sys
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import agent
import history
import mcp_client
from mcp_manager import MCPManager
import mcp_tools
import permissions
import tool_registry
import tool_runtime


integration = pytest.mark.skipif(
    os.environ.get('CLI_MCP_INTEGRATION') != '1', reason='需要真实 MCP 子进程'
)


@pytest.fixture
def registry(monkeypatch):
    saved = dict(tool_registry.TOOL_REGISTRY)
    monkeypatch.setattr(permissions, 'confirm_tool', Mock(return_value=True))
    monkeypatch.setattr(tool_runtime, 'record_tool_event', Mock())
    monkeypatch.setattr('mcp_manager.record_tool_event', Mock())
    yield
    tool_registry.TOOL_REGISTRY.clear()
    tool_registry.TOOL_REGISTRY.update(saved)


def discovered():
    return {
        'connection': {'details': 'test command; current user rights'},
        'tools': [{'name': 'add', 'description': 'add integers', 'inputSchema': {
            'type': 'object', 'properties': {'a': {'type': 'integer'}, 'b': {'type': 'integer'}},
            'required': ['a', 'b'], 'additionalProperties': False
        }}]
    }


def test_registration_exposes_model_definition_and_binds_remote_name(registry, monkeypatch):
    handler = Mock(return_value={'ok': True, 'content': ['42']})
    monkeypatch.setattr(mcp_tools, 'execute_prepared_mcp_tool', handler)
    data = discovered()
    assert mcp_tools.register_server_tools('demo', data)['names'] == ['mcp__demo__add']
    data['tools'][0]['inputSchema']['properties'].clear()
    definitions = tool_registry.get_tool_definitions()
    definition = next(d['function'] for d in definitions if d['function']['name'] == 'mcp__demo__add')
    assert definition['parameters']['properties']['a']['type'] == 'integer'
    assert tool_runtime.execute_tool('mcp__demo__add', {'a': 19, 'b': 23})['ok']
    assert handler.call_args.args[1] == 'add'
    assert handler.call_args.args[3] == {'a': 19, 'b': 23}
    permissions.confirm_tool.assert_called_once()
    tool_runtime.record_tool_event.assert_called_once()


@pytest.mark.parametrize('args', [
    {'a': '19', 'b': 23}, {'a': True, 'b': 23}, {'a': 19},
    {'a': 19, 'b': 23, 'approved': True}, []
])
def test_invalid_mcp_arguments_never_prompt_or_call(registry, monkeypatch, args):
    handler = Mock()
    monkeypatch.setattr(mcp_tools, 'execute_prepared_mcp_tool', handler)
    assert mcp_tools.register_server_tools('demo', discovered())['ok']
    assert not tool_runtime.execute_tool('mcp__demo__add', args)['ok']
    permissions.confirm_tool.assert_not_called()
    handler.assert_not_called()


def test_mcp_denial_and_unknown_source_never_launch(registry, monkeypatch):
    handler = Mock()
    monkeypatch.setattr(mcp_tools, 'execute_prepared_mcp_tool', handler)
    mcp_tools.register_server_tools('demo', discovered())
    permissions.confirm_tool.return_value = False
    args = {'a': 19, 'b': 23}
    assert not tool_runtime.execute_tool('mcp__demo__add', args)['ok']
    assert not tool_runtime.execute_tool('mcp__demo__add', args, source='unknown')['ok']
    handler.assert_not_called()
    assert tool_runtime.record_tool_event.call_count == 2


@pytest.mark.parametrize('bad', [
    {'type': 'object', 'properties': {'a': {'$ref': 'https://example.com/schema'}}},
    {'type': 'object', 'properties': {'a': {'$ref': 'file:///etc/passwd'}}},
    {'type': 'object', 'properties': {'a': {'type': 'wrong'}}}
])
def test_invalid_schema_keeps_previous_registration(registry, bad):
    mcp_tools.register_server_tools('demo', discovered())
    previous = tool_registry.TOOL_REGISTRY['mcp__demo__add']
    data = discovered()
    data['tools'].append({'name': 'broken', 'inputSchema': bad})
    assert not mcp_tools.register_server_tools('demo', data)['ok']
    assert tool_registry.TOOL_REGISTRY['mcp__demo__add'] is previous
    assert 'mcp__demo__broken' not in tool_registry.TOOL_REGISTRY


def test_refresh_removes_disappeared_tools(registry):
    mcp_tools.register_server_tools('demo', discovered())
    data = discovered()
    data['tools'] = []
    assert mcp_tools.register_server_tools('demo', data)['ok']
    assert 'mcp__demo__add' not in tool_registry.TOOL_REGISTRY
    assert 'read_file' in tool_registry.TOOL_REGISTRY


def test_duplicate_remote_names_fail_without_partial_registration(registry):
    data = discovered()
    data['tools'].append(deepcopy(data['tools'][0]))
    assert not mcp_tools.register_server_tools('demo', data)['ok']
    assert 'mcp__demo__add' not in tool_registry.TOOL_REGISTRY


def test_pagination_is_collected_and_repeating_cursor_rejected():
    async def run():
        pages = iter([
            SimpleNamespace(tools=[], nextCursor='next'),
            SimpleNamespace(tools=[], nextCursor='next')
        ])
        async def list_tools(cursor=None):
            return next(pages)
        with pytest.raises(ValueError, match='分页游标重复'):
            await mcp_client.collect_tools(SimpleNamespace(list_tools=list_tools))
    asyncio.run(run())


def real_discovery(monkeypatch, manager):
    script = Path(__file__).resolve().parents[1] / 'mcp_servers' / 'demo_server.py'
    monkeypatch.setattr(mcp_client, 'mcp_config', {'demo': {
        'command': sys.executable, 'args': [str(script)], 'timeout_seconds': 10
    }})
    result = manager.connect('demo')
    assert result['ok'], result
    handle = manager.services['demo']
    return {'connection': handle['connection'], 'tools': handle['tools']}



@integration
def test_agent_loop_with_real_mcp_and_history(registry, monkeypatch, tmp_path, request):
    manager = MCPManager()
    manager.__enter__()
    request.addfinalizer(lambda: manager.__exit__(None, None, None))
    real_discovery(monkeypatch, manager)
    monkeypatch.setattr(history, 'HISTORY_PATH', tmp_path / 'history.jsonl')
    messages = [{'role': 'user', 'content': '使用 MCP 计算 19 + 23'}]
    history.append_messages(messages)
    snapshots = []
    def model_response(current):
        snapshots.append(deepcopy(current))
        if len(snapshots) == 1:
            return {'content': '', 'tool_calls': [{'function': {
                'name': 'mcp__demo__add', 'arguments': {'a': 19, 'b': 23}
            }}]}
        result = json.loads(current[-1]['content'])
        assert result['ok'] and result['content'] == ['42']
        return {'content': '结果是 42'}
    monkeypatch.setattr(agent, 'request_message', model_response)
    assert agent.run_agent(messages) == '结果是 42'
    assert history.load_history() == messages
    assert permissions.confirm_tool.call_count == 2  # 发现服务一次，调用一次。
    tool_runtime.record_tool_event.assert_called_once()


@integration
def test_changed_schema_is_rejected_before_remote_call(registry, monkeypatch, request):
    manager = MCPManager()
    manager.__enter__()
    request.addfinalizer(lambda: manager.__exit__(None, None, None))
    result = real_discovery(monkeypatch, manager)
    tool = result['tools'][0]
    changed = deepcopy(tool['inputSchema'])
    changed['description'] = 'changed'
    response = mcp_client.execute_prepared_mcp_tool(result['connection'], 'add', changed, {'a': 1, 'b': 2})
    assert not response['ok'] and '声明已变化' in response['error']
