import json
from copy import deepcopy
from unittest.mock import Mock

import pytest

import agent
import context_window as context
import history
import model_client
import project_instructions
import skills


@pytest.fixture
def budget(monkeypatch):
    monkeypatch.setattr(context, 'context_config', {'max_request_chars': 64000, 'max_history_turns': 2})
    monkeypatch.setitem(project_instructions.instruction_state, 'content', 'PROJECT_RULE')
    saved = dict(skills.active_skills)
    skills.clear_skills()
    yield context.context_config
    skills.clear_skills()
    skills.active_skills.update(saved)


def turn(number):
    return [{'role': 'user', 'content': str(number)}, {'role': 'assistant', 'content': 'answer'}]


def tool_turn():
    return [
        {'role': 'user', 'content': 'read files'},
        {'role': 'assistant', 'content': '', 'tool_calls': [
            {'function': {'name': 'read_file', 'arguments': {'path': 'a.py'}}},
            {'function': {'name': 'list_files', 'arguments': {'path': '.'}}}
        ]},
        {'role': 'tool', 'tool_name': 'read_file', 'content': '{"ok":true}'},
        {'role': 'tool', 'tool_name': 'list_files', 'content': '{"ok":true}'},
        {'role': 'assistant', 'content': 'done'}
    ]


def test_recent_turns_kept_with_rules_and_skills_history_unchanged(budget):
    skills.active_skills['review'] = 'SKILL_RULE'
    messages = turn(1) + turn(2) + turn(3)
    original = deepcopy(messages)
    result = context.prepare_context(messages, [])
    assert result['sent_turns'] == 2 and result['omitted_messages'] == 2
    assert result['messages'][-4:] == turn(2) + turn(3)
    assert 'PROJECT_RULE' in str(result['messages']) and 'SKILL_RULE' in str(result['messages'])
    assert messages == original


def test_tool_calls_and_results_are_kept_as_complete_user_turn(budget):
    messages = turn(1) + tool_turn() + turn(3)
    result = context.prepare_context(messages, [])
    assert result['messages'][-7:] == tool_turn() + turn(3)


def test_char_budget_drops_entire_old_turn(budget):
    latest = [{'role': 'user', 'content': 'latest'}]
    prefix = project_instructions.build_model_messages([])
    budget['max_request_chars'] = context.request_size(prefix + latest, [])
    result = context.prepare_context(turn(1) + latest, [])
    assert result['messages'] == prefix + latest
    assert result['chars'] <= result['budget']


def test_oversized_latest_turn_is_rejected_before_network(budget, monkeypatch):
    budget['max_request_chars'] = context.request_size(
        project_instructions.build_model_messages([]), model_client.get_tool_definitions()
    ) + 100
    request = Mock()
    monkeypatch.setattr(model_client.urllib.request, 'urlopen', request)
    with pytest.raises(context.ContextBudgetError, match='最新一轮消息超预算'):
        model_client.request_message([{'role': 'user', 'content': 'x' * 2000}])
    request.assert_not_called()


def test_system_and_tool_definitions_are_counted(budget):
    budget['max_request_chars'] = 1000
    with pytest.raises(context.ContextBudgetError, match='工具声明已超预算'):
        context.prepare_context([{'role': 'user', 'content': 'hi'}], [{'description': 'x' * 2000}])


def test_incomplete_latest_tool_turn_is_rejected(budget):
    with pytest.raises(context.ContextBudgetError, match='不完整'):
        context.prepare_context(tool_turn()[:3], [])


def test_damaged_old_turn_and_orphan_results_are_not_sent(budget):
    damaged = tool_turn()[:3]
    orphan = {'role': 'tool', 'tool_name': 'read_file', 'content': 'orphan'}
    result = context.prepare_context([orphan] + damaged + turn(2), [])
    assert result['messages'][-2:] == turn(2)
    assert not any(message['role'] == 'tool' for message in result['messages'])


def test_generation_system_prompt_is_preserved_without_project_context(budget):
    messages = [{'role': 'system', 'content': 'GENERATION_RULE'}, {'role': 'user', 'content': 'purpose'}]
    assert context.prepare_context(messages, [], include_context=False)['messages'] == messages


def test_actual_request_matches_budgeted_payload_and_disk_is_not_trimmed(budget, tmp_path, monkeypatch):
    messages = turn(1) + turn(2) + turn(3)
    monkeypatch.setattr(history, 'HISTORY_PATH', tmp_path / 'history.jsonl')
    history.append_messages(messages)
    response = Mock()
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    response.read.return_value = b'{"message":{"content":"ok"}}'
    captured = []
    def request(request, timeout):
        captured.append(json.loads(request.data))
        return response
    monkeypatch.setattr(model_client.urllib.request, 'urlopen', request)
    model_client.request_message(messages)
    expected = context.prepare_context(messages, captured[0]['tools'])
    assert captured[0]['messages'] == expected['messages']
    assert len(json.dumps(captured[0], ensure_ascii=False)) == expected['chars']
    assert history.load_history() == messages


def test_agent_returns_readable_budget_error_without_tools(budget, monkeypatch):
    monkeypatch.setattr(agent, 'request_message', Mock(side_effect=context.ContextBudgetError('too large')))
    execute = Mock()
    monkeypatch.setattr(agent, 'execute_tool', execute)
    assert 'too large' in agent.run_agent([{'role': 'user', 'content': 'hi'}])
    execute.assert_not_called()


@pytest.mark.parametrize('value', [0, -1, True])
def test_invalid_budget_fails_explicitly(budget, value):
    budget['max_request_chars'] = value
    with pytest.raises(context.ContextBudgetError):
        context.prepare_context([], [])
