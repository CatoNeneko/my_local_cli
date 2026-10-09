from unittest.mock import Mock

import permissions
import tool_runtime
from tool_display import show_diff, tool_finished, tool_started


def test_summary_does_not_dump_replacement_or_mcp_arguments(capsys):
    tool_started('edit_file', {'path': 'sample.py', 'new_content': 'PRIVATE_CONTENT'})
    tool_started('mcp__demo__add', {'token': 'PRIVATE_TOKEN'})
    tool_finished('read_file', {'ok': True, 'content': 'PRIVATE_CONTENT'})
    shown = capsys.readouterr().out
    assert 'sample.py' in shown and '返回文字: 15 字符' in shown
    assert 'PRIVATE_CONTENT' not in shown and 'PRIVATE_TOKEN' not in shown


def test_diff_preserves_review_lines_and_escapes_terminal_controls(capsys):
    show_diff('--- before/sample.py\n+++ after/sample.py\n@@ -1 +1 @@\n-old\n+new\x1b[2J\u202e\n')
    shown = capsys.readouterr().out
    assert '+1 / -1 行' in shown
    assert '-old' in shown and '+new\\u001b[2J\\u202e' in shown
    assert '\x1b' not in shown and '\u202e' not in shown
    assert shown.index('[待审查修改]') < shown.index('[审查结束]')


def test_output_summary_is_bounded_without_changing_result(capsys):
    result = {'ok': False, 'error': 'failed', 'exit_code': 1,
              'output': 'x' * 5000, 'output_truncated': True, 'hook_warning': 'warning'}
    tool_finished('run_tests', result)
    shown = capsys.readouterr().out
    assert len(shown) < 1200 and '退出码: 1' in shown
    assert '摘要截断' in shown and 'Hook 警告' in shown
    assert len(result['output']) == 5000


def test_runtime_refusal_shows_diff_before_prompt_and_preserves_file(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(permissions, 'PROJECT_ROOT', tmp_path)
    audit = Mock()
    monkeypatch.setattr(tool_runtime, 'record_tool_event', audit)
    target = tmp_path / 'sample.py'
    target.write_text('value = 1\n')
    def refuse(*args):
        shown = capsys.readouterr().out
        assert '[执行中] edit_file' in shown
        assert '-value = 1' in shown and '+value = 2' in shown
        assert '[审查结束]' in shown
        return False
    monkeypatch.setattr(permissions, 'confirm_tool', refuse)
    result = tool_runtime.execute_tool('edit_file', {'path': 'sample.py', 'new_content': 'value = 2\n'})
    assert not result['ok'] and target.read_text() == 'value = 1\n'
    assert '[失败/未执行] edit_file' in capsys.readouterr().out
    audit.assert_called_once()
