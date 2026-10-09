import os
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import history
import permissions
import script
import terminal_input
from path_input import parse_path_arguments, path_candidates


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setattr(permissions, 'PROJECT_ROOT', tmp_path)
    (tmp_path / 'src').mkdir()
    (tmp_path / 'src/a file.py').write_text('value = 1\n')
    (tmp_path / '.env').write_text('private')
    (tmp_path / 'alias').symlink_to(tmp_path / 'src', target_is_directory=True)
    return tmp_path


def completions(text):
    from prompt_toolkit.completion import CompleteEvent
    from prompt_toolkit.document import Document
    return list(terminal_input.create_completer().get_completions(Document(text), CompleteEvent()))


def test_path_completion_hides_private_and_quotes_spaces(project):
    (project / '__pycache__').mkdir()
    entries = completions('/attach ')
    assert [entry.text for entry in entries] == ['src/']
    entries = completions('/attach src/a')
    assert entries[0].text == '"src/a file.py"'
    assert entries[0].start_position == -len('src/a')
    assert completions('/read ../') == []
    assert completions('/read .env') == []
    assert completions('/grep src/a') == []
    assert completions('/search "src/a file.py" keyword') == []


def test_path_parser_preserves_keywords_and_supports_quotes():
    assert parse_path_arguments('"src/a file.py" hello  world') == ('src/a file.py', 'hello  world')
    assert parse_path_arguments("'a file.py'") == ('a file.py', '')
    assert parse_path_arguments('sample.py hello world') == ('sample.py', 'hello world')
    with pytest.raises(ValueError):
        parse_path_arguments('"unclosed')


def test_picker_navigates_and_cancels_without_reading(project, monkeypatch):
    import terminal_dialog
    terminal = terminal_input.TerminalInput(plain=True)
    terminal.session = object()
    selections = iter([('src', True), ('src/a file.py', False)])
    seen = []
    def choose(title, options):
        seen.append(options)
        return next(selections)
    monkeypatch.setattr(terminal_dialog, 'choose', choose)
    assert terminal.pick_file() == 'src/a file.py'
    assert [label for _, label in seen[0]] == ['📁 src']
    assert seen[1][0][0] == ('.', True)
    monkeypatch.setattr(terminal_dialog, 'choose', lambda *args: None)
    assert terminal.pick_file() is None


def test_confirmation_default_denial_and_plain_mode(monkeypatch):
    import terminal_dialog
    choose = Mock(return_value=None)
    monkeypatch.setattr(terminal_dialog, 'choose', choose)
    terminal = terminal_input.TerminalInput(plain=True)
    terminal.session = object()
    with terminal.confirmations():
        assert not permissions.confirm_tool('edit_file', 'example.py')
        assert choose.call_args.args[1][0][0] is False
        choose.return_value = True
        assert permissions.confirm_tool('edit_file', 'example.py')
    monkeypatch.setattr('builtins.input', lambda prompt: 'n')
    assert not permissions.confirm_tool('edit_file', 'example.py')
    assert choose.call_count == 2


def test_files_command_attaches_through_real_permission_entry(project, monkeypatch):
    monkeypatch.setattr(history, 'HISTORY_PATH', project / 'history.jsonl')
    monkeypatch.setattr('tool_runtime.record_tool_event', Mock())
    class NoServices:
        def __enter__(self): return self
        def __exit__(self, *args): pass
    monkeypatch.setattr(script, 'MCPManager', NoServices)
    monkeypatch.setattr(terminal_input.TerminalInput, 'pick_files', lambda self: ['src/a file.py'])
    lines = iter(['/files', '/search "src/a file.py" value', '/exit'])
    monkeypatch.setattr('builtins.input', lambda prompt: next(lines))
    script.main(plain=True, no_mcp=True)
    messages = history.load_history()
    assert len(messages) == 1 and 'value = 1' in messages[0]['content']
    assert 'src/a file.py' in messages[0]['content']


@pytest.mark.skipif(os.environ.get('CLI_TERMINAL_INTEGRATION') != '1', reason='宿主环境验证方向键选择面板')
@pytest.mark.parametrize('keys, expected', [('\r', False), ('\x1b[B\r', True), ('\x1b', None)])
def test_real_selection_keys(keys, expected):
    from prompt_toolkit.input import create_pipe_input
    from prompt_toolkit.output import DummyOutput
    from terminal_dialog import choose
    with create_pipe_input() as pipe:
        pipe.send_text(keys)
        assert choose('允许吗？', [(False, '拒绝'), (True, '允许')],
                      input=pipe, output=DummyOutput()) is expected
