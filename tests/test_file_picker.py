import os

import pytest

import attachments
import file_catalog
import permissions
import tool_runtime
from file_catalog import matching_files, scan_files


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setattr(permissions, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setattr(tool_runtime, 'record_tool_event', lambda *args: None)
    (tmp_path / 'src').mkdir()
    (tmp_path / 'src/alpha.py').write_text('alpha = 1\n')
    (tmp_path / 'src/beta.py').write_text('beta = 2\n')
    (tmp_path / '.ai-cli').mkdir()
    (tmp_path / '.ai-cli/private.txt').write_text('private')
    (tmp_path / 'node_modules').mkdir()
    (tmp_path / 'node_modules/ignored.py').write_text('ignored')
    (tmp_path / 'alias.py').symlink_to(tmp_path / 'src/alpha.py')
    return tmp_path


def test_catalog_ignores_protected_dependencies_and_symlinks(project):
    result = scan_files()
    assert result['files'] == ['src/alpha.py', 'src/beta.py']
    assert not result['truncated']


def test_catalog_reports_limit(project, monkeypatch):
    monkeypatch.setattr(file_catalog, 'MAX_FILES', 1)
    result = scan_files()
    assert len(result['files']) == 1 and result['truncated']
    assert '文件数量' in result['reason']


def test_fuzzy_filename_and_path_ranking():
    paths = ['deep/my_test.py', 'tests/model_client.py', 'model.py', 'other.py']
    assert matching_files(paths, 'mdl') == ['model.py', 'tests/model_client.py']
    assert matching_files(paths, 'tst mdl') == ['tests/model_client.py']
    assert matching_files(paths, 'missing') == []


def test_attachments_read_all_then_make_one_message(project):
    result = attachments.prepare_attachments(['src/alpha.py', 'src/beta.py', 'src/alpha.py'])
    assert result['ok']
    assert result['paths'] == ['src/alpha.py', 'src/beta.py']
    assert 'alpha = 1' in result['message']['content'] and 'beta = 2' in result['message']['content']


def test_failed_batch_has_no_partial_message(project):
    result = attachments.prepare_attachments(['src/alpha.py', '.ai-cli/private.txt'])
    assert not result['ok'] and 'message' not in result
    result = attachments.prepare_attachments(['src/alpha.py', 'missing.py'])
    assert not result['ok'] and 'message' not in result


def test_attachment_batch_size_limit(project, monkeypatch):
    monkeypatch.setattr(attachments, 'MAX_TOTAL_BYTES', 50)
    assert not attachments.prepare_attachments(['src/alpha.py', 'src/beta.py'])['ok']


@pytest.mark.skipif(os.environ.get('CLI_TERMINAL_INTEGRATION') != '1', reason='真实搜索与多选面板')
@pytest.mark.parametrize('keys, expected', [
    ('alpha\r', ['src/alpha.py']),
    ('\t\x1b[B\t\r', ['src/alpha.py', 'src/beta.py']),
    ('alpha\t\x15beta\t\r', ['src/alpha.py', 'src/beta.py']),
    ('unmatched\r', []),
    ('alpha\t\x1b', None),
])
def test_real_fuzzy_multi_select_keys(keys, expected):
    from prompt_toolkit.input import create_pipe_input
    from prompt_toolkit.output import DummyOutput
    from file_picker import pick_files
    with create_pipe_input() as pipe:
        pipe.send_text(keys)
        result = pick_files(['src/alpha.py', 'src/beta.py'], input=pipe, output=DummyOutput())
        assert result == expected
