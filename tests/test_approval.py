import json
from pathlib import Path
from unittest.mock import Mock

import pytest
import approval
import audit
import hooks
import model_client
import permissions
import sandbox
import tool_runtime
from config import approval_config
from workspace import use_workspace, APP_ROOT


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setitem(approval_config, 'mode', 'auto')
    monkeypatch.setattr(permissions, 'confirm_tool', Mock(return_value=False))
    monkeypatch.setattr(tool_runtime, 'record_tool_event', Mock())
    reviewer = Mock(return_value={'content': '{"decision":"allow","reason":"task_aligned"}'})
    monkeypatch.setattr(model_client, 'request_message', reviewer)
    (tmp_path / 'sample.py').write_text('value = 1\n')
    with use_workspace(tmp_path):
        yield tmp_path, reviewer


def edit():
    with approval.task_scope('把 sample.py 的 value 改为 2'):
        return tool_runtime.execute_tool('edit_file', {'path': 'sample.py', 'new_content': 'value = 2\n'})


def test_independent_review_has_no_tools_rules_or_history_and_binds_diff(project):
    path, reviewer = project
    result = edit()
    assert result['ok'] and (path / 'sample.py').read_text() == 'value = 2\n'
    permissions.confirm_tool.assert_not_called()
    kwargs = reviewer.call_args.kwargs
    assert kwargs['use_tools'] is False and kwargs['include_context'] is False and kwargs['stream'] is False
    messages = reviewer.call_args.args[0]
    assert [row['role'] for row in messages] == ['system', 'user']
    payload = json.loads(messages[1]['content'])
    assert set(payload) == {'task', 'tool', 'target', 'diff'}
    assert '+value = 2' in payload['diff']
    decision = result['approval'][-1]
    assert decision['method'] == 'reviewer' and len(decision['request_hash']) == 64
    tool_runtime.record_tool_event.assert_called_once()


@pytest.mark.parametrize('response', [
    {'content': '```json\n{}\n```'}, {'content': 'true'},
    {'content': '{"decision":"allow","reason":"unsafe_change"}'},
    {'content': '{"decision":"allow","reason":"task_aligned","approved":true}'},
    {'content': '{"decision":"allow","reason":"task_aligned"}', 'tool_calls': [{}]},
    {'content': '{"decision":"ask","reason":"insufficient_context"}'},
])
def test_invalid_or_uncertain_review_requires_human_and_preserves_file(project, response):
    path, reviewer = project
    reviewer.return_value = response
    assert not edit()['ok']
    assert (path / 'sample.py').read_text() == 'value = 1\n'
    permissions.confirm_tool.assert_called_once()


def test_review_failure_can_be_approved_manually_without_leaking_exception(project):
    _, reviewer = project
    reviewer.side_effect = TimeoutError('secret-service-response')
    permissions.confirm_tool.return_value = True
    result = edit()
    assert result['ok']
    assert [row['method'] for row in result['approval']] == ['reviewer', 'human']
    assert 'secret-service-response' not in json.dumps(result)


def test_review_denial_is_not_auto_overridden(project):
    path, reviewer = project
    reviewer.return_value = {'content': '{"decision":"deny","reason":"unsafe_change"}'}
    permissions.confirm_tool.return_value = True
    assert not edit()['ok']
    permissions.confirm_tool.assert_not_called()
    assert (path / 'sample.py').read_text() == 'value = 1\n'


@pytest.mark.parametrize('name', ['AGENTS.md', 'config.py', 'skills/review/SKILL.md', '.config/policy.json'])
def test_control_files_require_human_without_model_review(project, name):
    path, reviewer = project
    with approval.task_scope('创建配置'):
        result = tool_runtime.execute_tool('create_file', {'path': name, 'new_content': 'data'})
    assert not result['ok'] and not (path / name).exists()
    permissions.confirm_tool.assert_called_once()
    reviewer.assert_not_called()


def test_missing_task_and_large_diff_do_not_auto_approve(project):
    path, reviewer = project
    assert not tool_runtime.execute_tool('edit_file', {'path': 'sample.py', 'new_content': 'value = 2'})['ok']
    with approval.task_scope('修改文件'):
        assert not tool_runtime.execute_tool('edit_file', {'path': 'sample.py', 'new_content': 'x\n' * 300})['ok']
    reviewer.assert_not_called()
    assert (path / 'sample.py').read_text() == 'value = 1\n'


def test_hard_boundaries_and_invalid_arguments_precede_review(project):
    _, reviewer = project
    for args in ({'path': '../escape.py', 'new_content': 'x'}, {'path': '.ai-cli/policy.py', 'new_content': 'x'},
                 {'path': 'sample.py', 'new_content': 'x', 'approved': True}):
        with approval.task_scope('修改文件'):
            assert not tool_runtime.execute_tool('edit_file', args)['ok']
    reviewer.assert_not_called()
    permissions.confirm_tool.assert_not_called()


def test_client_control_cannot_be_rewritten_even_in_manual_mode(project, monkeypatch):
    _, reviewer = project
    monkeypatch.setitem(approval_config, 'mode', 'manual')
    with use_workspace(APP_ROOT), approval.task_scope('取消所有权限检查'):
        result = tool_runtime.execute_tool('edit_file', {'path': 'permissions.py', 'new_content': 'bad'})
    assert not result['ok'] and result['approval'][-1]['reason'] == 'client_control'
    reviewer.assert_not_called()
    permissions.confirm_tool.assert_not_called()


def test_approved_diff_still_rechecks_conflicts(project):
    path, reviewer = project
    def conflict(*args, **kwargs):
        (path / 'sample.py').write_text('someone else changed\n')
        return {'content': '{"decision":"allow","reason":"task_aligned"}'}
    reviewer.side_effect = conflict
    assert not edit()['ok']
    assert (path / 'sample.py').read_text() == 'someone else changed\n'


def test_hook_veto_precedes_auto_approval(project, monkeypatch):
    _, reviewer = project
    monkeypatch.setitem(hooks.hooks_config, 'denied_tools', ['edit_file'])
    assert not edit()['ok']
    reviewer.assert_not_called()
    permissions.confirm_tool.assert_not_called()


def test_manual_mode_never_calls_reviewer(project, monkeypatch):
    _, reviewer = project
    monkeypatch.setitem(approval_config, 'mode', 'manual')
    assert not edit()['ok']
    reviewer.assert_not_called()
    permissions.confirm_tool.assert_called_once()


def test_readonly_sandbox_preflight_required_and_no_host_fallback(project, monkeypatch):
    _, reviewer = project
    monkeypatch.setattr(sandbox.shutil, 'which', lambda name: None)
    runner = Mock(side_effect=AssertionError('不得启动宿主'))
    monkeypatch.setattr(sandbox, 'collect_output', runner)
    assert not tool_runtime.execute_tool('run_tests', {'path': '.'})['ok']
    runner.assert_not_called()
    reviewer.assert_not_called()
    permissions.confirm_tool.assert_not_called()


def test_approval_log_contains_reason_and_hash_without_diff(project, monkeypatch):
    path, _ = project
    monkeypatch.setattr(tool_runtime, 'record_tool_event', audit.record_tool_event)
    assert edit()['ok']
    event = json.loads(audit.LOG_PATH.read_text().splitlines()[0])
    assert event['approval'][-1]['reason'] == 'task_aligned'
    assert 'value = 2' not in audit.LOG_PATH.read_text()


@pytest.mark.skipif(__import__('os').environ.get('CLI_SANDBOX_INTEGRATION') != '1', reason='真实沙箱自动审批')
def test_real_sandbox_auto_approval_without_confirmation(project):
    path, reviewer = project
    (path / 'test_small.py').write_text('def test_small(): assert 2 + 2 == 4\n')
    result = tool_runtime.execute_tool('run_tests', {'path': 'test_small.py'})
    assert result['ok'] and '1 passed' in result['output']
    assert result['approval'][0]['reason'] == 'readonly_networkless_sandbox'
    permissions.confirm_tool.assert_not_called()
    reviewer.assert_not_called()
