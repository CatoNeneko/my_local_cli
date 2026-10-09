from unittest.mock import Mock
import os
import sys
from pathlib import Path

import pytest

import new_files
import permissions
import tool_runtime


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setattr(permissions, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setattr(tool_runtime, 'record_tool_event', Mock())
    monkeypatch.setattr(permissions, 'confirm_tool', Mock(return_value=True))
    return tmp_path


def create(path, content='value = 1\n'):
    return tool_runtime.execute_tool('create_file', {'path': path, 'new_content': content})


def test_create_nested_file_after_review(project, capsys):
    def approve(*args):
        assert not (project / 'src').exists()
        assert '+value = 1' in capsys.readouterr().out
        return True
    permissions.confirm_tool.side_effect = approve
    assert create('src/example.py')['ok']
    assert (project / 'src/example.py').read_text() == 'value = 1\n'
    assert not list((project / 'src').glob('.cli-new-*'))
    tool_runtime.record_tool_event.assert_called_once()


def test_refusal_creates_no_directory(project):
    permissions.confirm_tool.return_value = False
    assert not create('src/example.py')['ok']
    assert not (project / 'src').exists()


def test_existing_and_concurrently_created_file_never_overwritten(project):
    target = project / 'example.py'
    target.write_text('original')
    assert not create('example.py')['ok']
    assert target.read_text() == 'original'
    permissions.confirm_tool.assert_not_called()
    target.unlink()
    def race(*args):
        target.write_text('created during review')
        return True
    permissions.confirm_tool.side_effect = race
    assert not create('example.py')['ok']
    assert target.read_text() == 'created during review'


@pytest.mark.parametrize('path', ['../outside.py', '.env', '.git/new.py', 'sessions/new.py'])
def test_protected_paths_fail_before_approval(project, path):
    assert not create(path)['ok']
    permissions.confirm_tool.assert_not_called()


def test_symlink_parent_rejected_and_retarget_during_review_blocked(project):
    (project / 'real').mkdir()
    (project / 'alias').symlink_to(project / 'real', target_is_directory=True)
    assert not create('alias/new.py')['ok']
    permissions.confirm_tool.assert_not_called()
    def retarget(*args):
        (project / 'src').symlink_to(project / 'real', target_is_directory=True)
        return True
    permissions.confirm_tool.side_effect = retarget
    assert not create('src/new.py')['ok']
    assert not (project / 'real/new.py').exists()


def test_empty_unicode_and_limit(project, monkeypatch):
    assert create('empty.txt', '')['ok']
    assert (project / 'empty.txt').read_bytes() == b''
    assert create('中文.txt', '你好')['ok']
    monkeypatch.setattr(new_files, 'MAX_NEW_FILE_BYTES', 3)
    assert not create('oversize.txt', '你好')['ok']
    assert not (project / 'oversize.txt').exists()
    assert not create('nul.txt', '\x00')['ok']


@pytest.mark.skipif(os.environ.get('CLI_SANDBOX_INTEGRATION') != '1', reason='真实新建文件到沙箱测试流程')
def test_created_code_and_test_run_in_real_sandbox(project, monkeypatch):
    import sandbox
    monkeypatch.setattr(sandbox, 'PROJECT_ROOT', project)
    monkeypatch.setattr(sandbox, 'RUNTIME_ENV', Path(sys.prefix))
    assert create('add.py', 'def add(a, b):\n    return a + b\n')['ok']
    assert create('test_add.py', 'from add import add\n\ndef test_add():\n    assert add(19, 23) == 42\n')['ok']
    result = tool_runtime.execute_tool('run_tests', {'path': 'test_add.py'})
    assert result['ok'], result
    assert '1 passed' in result['output']
    assert (project / 'add.py').read_text() == 'def add(a, b):\n    return a + b\n'
