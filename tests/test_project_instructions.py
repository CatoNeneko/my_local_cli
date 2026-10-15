import json
from unittest.mock import Mock

import pytest

import history
import model_client
import permissions
import project_instructions as instructions
from config import model_config


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setattr(permissions, "PROJECT_ROOT", tmp_path)
    saved = dict(instructions.instruction_state)
    yield tmp_path
    instructions.instruction_state.clear()
    instructions.instruction_state.update(saved)


def test_loaded_rules_survive_clear_and_are_not_persisted(project, monkeypatch):
    (project / "AGENTS.md").write_text("用中文解释变量。", encoding="utf-8")
    monkeypatch.setattr(history, "HISTORY_PATH", project / "history.jsonl")
    assert instructions.load_project_instructions()["status"] == "loaded"
    messages = [{"role": "user", "content": "你好"}]
    history.append_messages(messages)
    sent = instructions.build_model_messages(messages)
    assert [m["role"] for m in sent] == ["system", "system", "user"]
    assert "用中文解释变量。" in sent[1]["content"]
    assert history.load_history() == messages
    messages.clear()
    history.clear_history()
    assert history.load_history() == []
    assert "用中文解释变量。" in instructions.build_model_messages(messages)[1]["content"]


def test_request_body_contains_rules_without_mutating_history(project, monkeypatch):
    monkeypatch.setitem(model_config, "provider", "ollama")
    (project / "AGENTS.md").write_text("代码修改要说明原因。")
    instructions.load_project_instructions()
    messages = [{"role": "user", "content": "检查代码"}]
    response = Mock()
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    response.read.return_value = b'{"message":{"content":"ok"}}'
    requests = []

    def capture(request, timeout):
        requests.append(json.loads(request.data))
        return response

    monkeypatch.setattr(model_client.urllib.request, "urlopen", capture)
    model_client.request_message(messages)
    assert "代码修改要说明原因。" in requests[0]["messages"][1]["content"]
    assert messages == [{"role": "user", "content": "检查代码"}]


@pytest.mark.parametrize(
    "raw, status",
    [
        (b"", "empty"),
        (b"  \n", "empty"),
        (b"\xff", "error"),
        (b"a" * 65537, "error"),
        (b"\xef\xbb\xbfhello", "loaded"),
    ],
)
def test_empty_invalid_large_and_bom_files(project, raw, status):
    (project / "AGENTS.md").write_bytes(raw)
    result = instructions.load_project_instructions()
    assert result["status"] == status
    assert bool(result["content"]) == (status == "loaded")


def test_missing_file_clears_previous_rules(project):
    path = project / "AGENTS.md"
    path.write_text("old rules")
    instructions.load_project_instructions()
    path.unlink()
    assert instructions.load_project_instructions()["status"] == "missing"
    assert len(instructions.build_model_messages([])) == 1


def test_external_symlink_is_rejected(project):
    (project / "AGENTS.md").symlink_to(project.parent / "external_rules.md")
    result = instructions.load_project_instructions()
    assert result["status"] == "error" and "项目目录之外" in result["message"]


def test_directory_is_reported_as_error(project):
    (project / "AGENTS.md").mkdir()
    assert instructions.load_project_instructions()["status"] == "error"
