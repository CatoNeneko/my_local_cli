import json
from unittest.mock import Mock

import pytest

import history
import model_client
import permissions
import project_instructions
import skills


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setattr(permissions, "PROJECT_ROOT", tmp_path)
    saved = dict(skills.active_skills)
    skills.clear_skills()
    yield tmp_path
    skills.clear_skills()
    skills.active_skills.update(saved)


def write_skill(project, name, content="先读取文件，再给审查意见。"):
    path = project / "skills" / name / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_discovery_does_not_activate_or_load_content(project):
    write_skill(project, "review")
    (project / "skills" / "no-instructions").mkdir()
    assert skills.list_skills()["skills"] == [{"name": "review", "active": False}]
    assert skills.get_skill_messages() == []


def test_only_selected_skill_enters_actual_request(project, monkeypatch):
    monkeypatch.setitem(model_client.model_config, "provider", "ollama")
    write_skill(project, "review", "REVIEW_RULE")
    write_skill(project, "other", "UNSELECTED_RULE")
    assert skills.activate_skill("review")["ok"]
    captured = []
    response = Mock()
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    response.read.return_value = b'{"message":{"content":"ok"}}'

    def request(request, timeout):
        captured.append(json.loads(request.data))
        return response

    monkeypatch.setattr(model_client.urllib.request, "urlopen", request)
    messages = [{"role": "user", "content": "检查代码"}]
    model_client.request_message(messages)
    text = json.dumps(captured[0]["messages"], ensure_ascii=False)
    assert "REVIEW_RULE" in text and "UNSELECTED_RULE" not in text
    assert messages == [{"role": "user", "content": "检查代码"}]


def test_clear_history_retains_skill_and_explicit_deactivation_removes_it(project, monkeypatch):
    write_skill(project, "review", "REVIEW_RULE")
    skills.activate_skill("review")
    monkeypatch.setattr(history, "HISTORY_PATH", project / "history.jsonl")
    history.clear_history()
    assert history.load_history() == []
    assert "REVIEW_RULE" in str(project_instructions.build_model_messages([]))
    skills.clear_skills()
    assert "REVIEW_RULE" not in str(project_instructions.build_model_messages([]))


@pytest.mark.parametrize(
    "name", ["../outside", "/absolute", "name/other", "name\\other", "", "clear"]
)
def test_invalid_skill_names_are_rejected(project, name):
    assert not skills.activate_skill(name)["ok"]
    assert not skills.active_skills


def test_external_and_outside_skills_symlinks_are_rejected(project):
    path = write_skill(project, "review")
    path.unlink()
    path.symlink_to(project.parent / "outside.md")
    assert not skills.activate_skill("review")["ok"]
    path.unlink()
    (project / "other.md").write_text("internal but outside skills")
    path.symlink_to(project / "other.md")
    assert not skills.activate_skill("review")["ok"]
    assert skills.list_skills()["skills"] == []


@pytest.mark.parametrize("raw", [b"", b"\xff", b"a" * 32769])
def test_invalid_content_is_not_activated(project, raw):
    write_skill(project, "review").write_bytes(raw)
    assert not skills.activate_skill("review")["ok"]
    assert not skills.active_skills


def test_missing_directory_and_file_are_handled(project):
    assert skills.list_skills() == {"ok": True, "skills": []}
    assert not skills.activate_skill("missing")["ok"]


def test_activation_limit_reloading_and_total_bytes(project):
    for name in ["one", "two", "three", "four"]:
        write_skill(project, name, "a" * 30000)
    assert skills.activate_skill("one")["ok"]
    assert skills.activate_skill("two")["ok"]
    assert not skills.activate_skill("three")["ok"]
    write_skill(project, "three", "small")
    assert skills.activate_skill("three")["ok"]
    assert not skills.activate_skill("four")["ok"]
    write_skill(project, "one", "changed")
    assert skills.activate_skill("one")["ok"]
    assert skills.active_skills["one"] == "changed"
