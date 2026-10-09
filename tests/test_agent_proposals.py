import hashlib
import json
from unittest.mock import Mock

import pytest
import agent_proposals
import approval
import model_client
import permissions
import process_tasks
import tool_runtime
from config import approval_config
from workspace import use_workspace


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setitem(approval_config, 'mode', 'auto')
    monkeypatch.setattr(permissions, 'confirm_tool', Mock(return_value=False))
    monkeypatch.setattr(tool_runtime, 'record_tool_event', Mock())
    monkeypatch.setattr(process_tasks, 'JOBS', {})
    monkeypatch.setattr(agent_proposals, 'PROPOSALS', [])
    reviewer = Mock(return_value={'content': '{"decision":"allow","reason":"task_aligned"}'})
    monkeypatch.setattr(model_client, 'request_message', reviewer)
    (tmp_path / 'sample.py').write_text('value = 1\n')
    with use_workspace(tmp_path):
        yield tmp_path, reviewer


def job(path, proposal):
    process_tasks.JOBS['worker'] = {'kind': 'agent', 'done': True, 'workspace': str(path),
        'task': '用户原始任务：把 value 改为 2',
        'output': json.dumps({'ok': True, 'reply': '建议', 'task': '伪造授权', 'proposals': [proposal]}).encode()}


def test_child_proposal_does_not_write_then_parent_reviews_original_task(project):
    path, reviewer = project
    result = agent_proposals.propose_edit(str(path / 'sample.py'), 'value = 2\n')
    assert result['ok'] and (path / 'sample.py').read_text() == 'value = 1\n'
    job(path, agent_proposals.PROPOSALS[0])
    with approval.task_scope('当前聊天中的无关任务'):
        applied = tool_runtime.execute_tool('apply_agent_proposal', {'task_id': 'worker', 'proposal_id': '1'})
    assert applied['ok'] and (path / 'sample.py').read_text() == 'value = 2\n'
    reviewed = json.loads(reviewer.call_args.args[0][1]['content'])
    assert reviewed['task'] == '用户原始任务：把 value 改为 2'
    assert not tool_runtime.execute_tool('apply_agent_proposal', {'task_id': 'worker', 'proposal_id': '1'})['ok']
    permissions.confirm_tool.assert_not_called()


def test_file_changed_since_child_proposal_is_preserved_before_review(project):
    path, reviewer = project
    agent_proposals.propose_edit(str(path / 'sample.py'), 'value = 2\n')
    job(path, agent_proposals.PROPOSALS[0])
    (path / 'sample.py').write_text('user edited\n')
    assert not tool_runtime.execute_tool('apply_agent_proposal', {'task_id': 'worker', 'proposal_id': '1'})['ok']
    assert (path / 'sample.py').read_text() == 'user edited\n'
    reviewer.assert_not_called()


def test_child_cannot_escape_or_choose_execution_tool(project):
    path, reviewer = project
    for proposal in (
        {'proposal_id': '1', 'tool': 'create_file', 'path': '../outside.py', 'new_content': 'bad'},
        {'proposal_id': '1', 'tool': 'run_tests', 'path': '.', 'new_content': 'bad'},
        {'proposal_id': '1', 'tool': 'create_file', 'path': '.ai-cli/policy.py', 'new_content': 'bad'},
    ):
        job(path, proposal)
        assert not tool_runtime.execute_tool('apply_agent_proposal', {'task_id': 'worker', 'proposal_id': '1'})['ok']
    reviewer.assert_not_called()
    permissions.confirm_tool.assert_not_called()


def test_review_denies_child_change_without_writing(project):
    path, reviewer = project
    agent_proposals.propose_edit(str(path / 'sample.py'), 'value = 2\n')
    job(path, agent_proposals.PROPOSALS[0])
    reviewer.return_value = {'content': '{"decision":"deny","reason":"out_of_scope"}'}
    result = tool_runtime.execute_tool('apply_agent_proposal', {'task_id': 'worker', 'proposal_id': '1'})
    assert not result['ok'] and (path / 'sample.py').read_text() == 'value = 1\n'


def test_failed_or_foreign_child_result_cannot_apply(project):
    path, reviewer = project
    agent_proposals.propose_file(str(path / 'new.py'), 'value = 2\n')
    job(path, agent_proposals.PROPOSALS[0])
    process_tasks.JOBS['worker']['workspace'] = str(path.parent)
    assert not tool_runtime.execute_tool('apply_agent_proposal', {'task_id': 'worker', 'proposal_id': '1'})['ok']
    process_tasks.JOBS['worker']['workspace'] = str(path)
    process_tasks.JOBS['worker']['output'] = b'{"ok": false}'
    assert not tool_runtime.execute_tool('apply_agent_proposal', {'task_id': 'worker', 'proposal_id': '1'})['ok']
    reviewer.assert_not_called()
    assert not (path / 'new.py').exists()


def test_proposal_limits(project):
    path, _ = project
    for number in range(3):
        assert agent_proposals.propose_file(str(path / f'new{number}.py'), 'value = 2')['ok']
    assert not agent_proposals.propose_file(str(path / 'more.py'), 'value = 2')['ok']
