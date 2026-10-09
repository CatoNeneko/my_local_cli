from copy import deepcopy
from unittest.mock import Mock

import pytest

import hooks
import permissions
import skill_generation
import skills
import tool_runtime


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setattr(permissions, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setattr(permissions, 'confirm_tool', Mock(return_value=True))
    monkeypatch.setattr(tool_runtime, 'record_tool_event', Mock())
    monkeypatch.setattr(hooks, 'hooks_config', {
        'before_tool': [], 'after_tool': [], 'denied_tools': []
    })
    monkeypatch.setattr(skill_generation, 'request_message', Mock(return_value={
        'content': '# 审查测试\n\n用途：检查测试是否覆盖边界。\n\n先读取测试，再报告问题。'
    }))
    saved = dict(skills.active_skills)
    skills.clear_skills()
    yield tmp_path
    skills.active_skills.update(saved)


def test_generated_skill_uses_diff_confirmation_and_no_auto_activation(project, capsys):
    def approve(*args):
        output = capsys.readouterr().out
        assert '+# 审查测试' in output
        return True
    permissions.confirm_tool.side_effect = approve
    result = skill_generation.generate_skill('test-review', '检查测试覆盖')
    assert result['ok'], result
    assert (project / 'skills/test-review/SKILL.md').read_text().startswith('# 审查测试')
    assert not skills.active_skills
    skill_generation.request_message.assert_called_once()
    assert skill_generation.request_message.call_args.kwargs == {'use_tools': False, 'include_context': False}
    permissions.confirm_tool.assert_called_once()
    tool_runtime.record_tool_event.assert_called_once()


def test_refusal_makes_no_directory_or_file(project):
    permissions.confirm_tool.return_value = False
    assert not skill_generation.generate_skill('review', '审查代码')['ok']
    assert not (project / 'skills').exists()


def test_existing_skill_is_not_overwritten_or_sent_to_model(project):
    path = project / 'skills/review/SKILL.md'
    path.parent.mkdir(parents=True)
    path.write_text('original')
    assert not skill_generation.generate_skill('review', 'new')['ok']
    assert path.read_text() == 'original'
    skill_generation.request_message.assert_not_called()


def test_conflicting_create_during_confirmation_preserves_other_file(project):
    def conflict(*args):
        path = project / 'skills/review/SKILL.md'
        path.parent.mkdir(parents=True)
        path.write_text('someone else created it')
        return True
    permissions.confirm_tool.side_effect = conflict
    assert not skill_generation.generate_skill('review', '审查')['ok']
    assert (project / 'skills/review/SKILL.md').read_text() == 'someone else created it'
    assert not list(project.rglob('.skill-draft-*'))


@pytest.mark.parametrize('reply', [
    {'content': ''}, {'content': 123}, {'content': '```markdown\n# test\n```'},
    {'content': 'a' * 32769}, {'content': 'hello', 'tool_calls': [{}]}, []
])
def test_bad_generated_output_is_not_saved_or_confirmed(project, reply):
    skill_generation.request_message.return_value = reply
    assert not skill_generation.generate_skill('review', '审查')['ok']
    permissions.confirm_tool.assert_not_called()
    assert not (project / 'skills').exists()


def test_network_failure_reports_error(project):
    skill_generation.request_message.side_effect = TimeoutError
    assert 'TimeoutError' in skill_generation.generate_skill('review', '审查')['error']
    assert not (project / 'skills').exists()


@pytest.mark.parametrize('name', ['../outside', 'review/../other', 'clear', 'generate', 'a' * 65, ''])
def test_invalid_names_do_not_request_model(project, name):
    assert not skill_generation.generate_skill(name, '审查')['ok']
    skill_generation.request_message.assert_not_called()


def test_before_hook_blocks_creation_before_confirmation(project):
    hooks.hooks_config.update(before_tool=['deny_configured_tools'], denied_tools=['create_skill'])
    result = skill_generation.generate_skill('review', '审查')
    assert not result['ok'] and 'Hook' in result['error']
    permissions.confirm_tool.assert_not_called()
    assert not (project / 'skills').exists()


@pytest.mark.parametrize('handler', [Mock(side_effect=RuntimeError), lambda context: None])
def test_broken_before_hook_fails_closed(project, monkeypatch, handler):
    hooks.hooks_config['before_tool'] = ['custom']
    monkeypatch.setitem(hooks.HOOK_HANDLERS, 'custom', handler)
    assert not skill_generation.generate_skill('review', '审查')['ok']
    assert not (project / 'skills').exists()


def test_after_hook_failure_keeps_success_and_records_warning(project, monkeypatch):
    hooks.hooks_config['after_tool'] = ['custom']
    monkeypatch.setitem(hooks.HOOK_HANDLERS, 'custom', Mock(side_effect=RuntimeError))
    result = skill_generation.generate_skill('review', '审查')
    assert result['ok'] and 'hook_warning' in result
    assert (project / 'skills/review/SKILL.md').exists()
    assert tool_runtime.record_tool_event.call_args.args[1]['hook_warning'] == result['hook_warning']


def test_hook_cannot_mutate_arguments_and_result_snapshots(project, monkeypatch):
    def mutate(context):
        context['arguments']['path'] = '../outside'
        if 'result' in context:
            context['result']['ok'] = False
        return {'ok': True}
    monkeypatch.setitem(hooks.HOOK_HANDLERS, 'custom', mutate)
    hooks.hooks_config.update(before_tool=['custom'], after_tool=['custom'])
    result = skill_generation.generate_skill('review', '审查')
    assert result['ok']
    assert (project / 'skills/review/SKILL.md').exists()


def test_hook_lifecycle_order_and_after_receives_denial(project, monkeypatch):
    calls = []
    def before(context):
        calls.append(('before', deepcopy(context)))
        return {'ok': True}
    def after(context):
        calls.append(('after', deepcopy(context)))
        return {'ok': True}
    monkeypatch.setitem(hooks.HOOK_HANDLERS, 'before', before)
    monkeypatch.setitem(hooks.HOOK_HANDLERS, 'after', after)
    hooks.hooks_config.update(before_tool=['before'], after_tool=['after'])
    permissions.confirm_tool.return_value = False
    result = skill_generation.generate_skill('review', '审查')
    assert not result['ok']
    assert [name for name, context in calls] == ['before', 'after']
    assert calls[1][1]['result']['ok'] is False
