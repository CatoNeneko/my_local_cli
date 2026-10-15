import json

import pytest

import history
import permissions
import skills
from sessions import SessionManager


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "HISTORY_PATH", tmp_path / "history.jsonl")
    monkeypatch.setattr(permissions, "PROJECT_ROOT", tmp_path)
    saved = dict(skills.active_skills)
    skills.clear_skills()
    yield tmp_path
    skills.clear_skills()
    skills.active_skills.update(saved)


def test_switch_persists_independent_histories_and_default_is_preserved(project):
    manager = SessionManager()
    original = {"role": "user", "content": "默认会话"}
    history.append_message(original)
    assert manager.switch("work")["messages"] == []
    work = {"role": "user", "content": "工作会话"}
    history.append_message(work)
    assert manager.switch("default")["messages"] == [original]
    assert manager.switch("work")["messages"] == [work]
    assert manager.list_sessions()["names"] == ["default", "work"]


def test_new_process_manager_can_reload_named_history(project, monkeypatch):
    manager = SessionManager()
    manager.switch("work")
    history.append_message({"role": "assistant", "content": "stored"})
    monkeypatch.setattr(history, "HISTORY_PATH", project / "history.jsonl")
    restarted = SessionManager()
    assert restarted.current_name == "default"
    assert restarted.switch("work")["messages"][0]["content"] == "stored"


def test_clear_only_clears_current_session(project):
    manager = SessionManager()
    history.append_message({"role": "user", "content": "keep"})
    manager.switch("work")
    history.append_message({"role": "user", "content": "clear me"})
    history.clear_history()
    assert manager.switch("default")["messages"][0]["content"] == "keep"
    assert manager.switch("work")["messages"] == []


def test_tool_request_and_results_survive_session_switch(project):
    manager = SessionManager()
    manager.switch("work")
    messages = [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [{"function": {"name": "read_file", "arguments": {"path": "a.py"}}}],
        },
        {"role": "tool", "tool_name": "read_file", "content": '{"ok":true,"content":"42"}'},
    ]
    history.append_messages(messages)
    manager.switch("default")
    assert manager.switch("work")["messages"] == messages


def test_skills_are_isolated_and_restored_within_current_process(project):
    manager = SessionManager()
    skills.active_skills["review"] = "review rules"
    assert manager.switch("work")["ok"]
    assert not skills.active_skills
    skills.active_skills["testing"] = "testing rules"
    manager.switch("default")
    assert skills.active_skills == {"review": "review rules"}
    manager.switch("work")
    assert skills.active_skills == {"testing": "testing rules"}
    manager.switch("work")
    assert skills.active_skills == {"testing": "testing rules"}


@pytest.mark.parametrize("name", ["../outside", "/absolute", "a/b", "a\\b", "", "a" * 65])
def test_invalid_name_preserves_current_path_and_skills(project, name):
    manager = SessionManager()
    old_path = history.HISTORY_PATH
    skills.active_skills["review"] = "rules"
    assert not manager.switch(name)["ok"]
    assert history.HISTORY_PATH == old_path and manager.current_name == "default"
    assert skills.active_skills == {"review": "rules"}


def test_symlink_directory_and_session_file_are_rejected(project):
    manager = SessionManager()
    directory = project / "sessions"
    directory.symlink_to(project.parent, target_is_directory=True)
    assert not manager.switch("work")["ok"]
    directory.unlink()
    directory.mkdir()
    (directory / "work.jsonl").symlink_to(project.parent / "outside.jsonl")
    assert not manager.switch("work")["ok"]
    assert manager.list_sessions()["names"] == ["default"]


def test_unreadable_target_keeps_old_session(project):
    manager = SessionManager()
    (project / "sessions").mkdir()
    (project / "sessions/work.jsonl").write_bytes(b"\xff")
    assert not manager.switch("work")["ok"]
    assert manager.current_name == "default"
    assert history.HISTORY_PATH == project / "history.jsonl"


def test_exports_are_per_session_and_private_from_tools(project):
    manager = SessionManager()
    original = [{"role": "user", "content": "default export"}]
    first = manager.export(original)
    manager.switch("work")
    second = manager.export([{"role": "user", "content": "work export"}])
    assert first["path"] != second["path"]
    assert json.loads((project / "history.json").read_text()) == original
    assert not permissions.resolve_project_path("sessions/work.jsonl")["ok"]
    assert not permissions.resolve_project_path("sessions/work.export.json")["ok"]


def test_rename_default_preserves_history_and_updates_future_writes(project):
    manager = SessionManager()
    first = {"role": "user", "content": "before rename"}
    history.append_message(first)
    skills.active_skills["review"] = "rules"
    assert manager.rename("renamed")["ok"]
    assert manager.current_name == "renamed"
    assert not (project / "history.jsonl").exists()
    history.append_message({"role": "assistant", "content": "after rename"})
    assert history.load_history()[0] == first
    assert len(history.load_history()) == 2
    manager.switch("other")
    manager.switch("renamed")
    assert skills.active_skills == {"review": "rules"}
    assert manager.switch("default")["messages"] == []


def test_rename_rejects_existing_target_without_changing_state(project):
    manager = SessionManager()
    manager.switch("occupied")
    history.append_message({"role": "user", "content": "target"})
    manager.switch("default")
    history.append_message({"role": "user", "content": "source"})
    assert not manager.rename("occupied")["ok"]
    assert manager.current_name == "default"
    assert history.load_history()[0]["content"] == "source"
    assert manager.switch("occupied")["messages"][0]["content"] == "target"


def test_rename_empty_session_and_same_name(project):
    manager = SessionManager()
    assert manager.rename("empty")["ok"]
    assert history.load_history() == []
    assert manager.rename("empty")["ok"]


@pytest.mark.parametrize("name", ["../outside", "rename", "a" * 65])
def test_invalid_rename_preserves_state(project, name):
    manager = SessionManager()
    assert not manager.rename(name)["ok"]
    assert manager.current_name == "default"


def test_rename_source_unlink_failure_rolls_back_new_link(project, monkeypatch):
    from pathlib import Path

    manager = SessionManager()
    history.append_message({"role": "user", "content": "keep"})
    original_unlink = Path.unlink

    def fail_source(path, *args, **kwargs):
        if path == project / "history.jsonl":
            raise PermissionError("test failure")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_source)
    assert not manager.rename("renamed")["ok"]
    assert manager.current_name == "default"
    assert (project / "history.jsonl").exists()
    assert not (project / "sessions/renamed.jsonl").exists()
