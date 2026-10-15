from pathlib import Path
from unittest.mock import Mock

import pytest

import audit
import harness.files.changesets as changesets
import model_client
import permissions
import tool_runtime
from approval import task_scope
from config import approval_config


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setattr(permissions, "PROJECT_ROOT", tmp_path)
    monkeypatch.setitem(approval_config, "mode", "manual")
    monkeypatch.setattr(permissions, "confirm_tool", Mock(return_value=True))
    monkeypatch.setattr(audit, "record_tool_event", Mock())
    monkeypatch.setattr(tool_runtime, "record_tool_event", Mock())
    return tmp_path


def edit(path, old_text, new_text):
    return {"path": path, "edits": [{"old_text": old_text, "new_text": new_text}]}


def create(path, content):
    return {"path": path, "content": content}


def apply(changes):
    return tool_runtime.execute_tool("apply_changes", {"path": ".", "changes": changes})


def assert_no_staged_files(root):
    assert not list(root.rglob(".cli-change-*"))


def test_batch_edits_two_files_and_creates_a_file(project):
    (project / "one.txt").write_text("one = old\n", encoding="utf-8")
    (project / "two.txt").write_text("two = old\n", encoding="utf-8")

    result = apply(
        [
            edit("one.txt", "one = old", "one = new"),
            edit("two.txt", "two = old", "two = new"),
            create("nested/three.txt", "three = new\n"),
        ]
    )

    assert result["ok"] is True
    assert (project / "one.txt").read_text(encoding="utf-8") == "one = new\n"
    assert (project / "two.txt").read_text(encoding="utf-8") == "two = new\n"
    assert (project / "nested/three.txt").read_text(encoding="utf-8") == "three = new\n"
    assert [item["action"] for item in result["files"]] == ["edit", "edit", "create"]
    permissions.confirm_tool.assert_called_once()
    tool_runtime.record_tool_event.assert_called_once()
    assert_no_staged_files(project)


@pytest.mark.parametrize(
    ("contents", "old_text"),
    [("key=1\nkey=1\n", "key"), ("key=1\n", "missing")],
)
def test_ambiguous_or_missing_replacement_is_rejected_before_approval(project, contents, old_text):
    target = project / "sample.txt"
    target.write_text(contents, encoding="utf-8")

    result = apply([edit("sample.txt", old_text, "replacement")])

    assert result["ok"] is False
    assert "唯一匹配" in result["error"]
    assert target.read_text(encoding="utf-8") == contents
    permissions.confirm_tool.assert_not_called()


def test_schema_rejects_change_with_both_content_and_edits(project):
    result = apply(
        [{"path": "sample.txt", "content": "new", "edits": [{"old_text": "x", "new_text": "y"}]}]
    )

    assert result["ok"] is False
    assert "参数不符合声明" in result["error"]
    assert not (project / "sample.txt").exists()
    permissions.confirm_tool.assert_not_called()


@pytest.mark.parametrize("blocked_kind", ["private", "outside"])
def test_private_or_outside_member_rejects_the_whole_batch(project, blocked_kind):
    safe = project / "safe.txt"
    safe.write_text("original\n", encoding="utf-8")
    outside = project.parent / (project.name + "-outside.txt")
    blocked_path = ".env/secret.txt" if blocked_kind == "private" else "../" + outside.name

    result = apply([edit("safe.txt", "original", "changed"), create(blocked_path, "blocked")])

    assert result["ok"] is False
    assert safe.read_text(encoding="utf-8") == "original\n"
    assert not (project / ".env").exists()
    assert not outside.exists()
    permissions.confirm_tool.assert_not_called()


def test_symlink_member_rejects_the_whole_batch_before_approval(project):
    safe = project / "safe.txt"
    target = project / "target.txt"
    alias = project / "alias.txt"
    safe.write_text("original\n", encoding="utf-8")
    target.write_text("target\n", encoding="utf-8")
    alias.symlink_to(target)

    result = apply([edit("safe.txt", "original", "changed"), edit("alias.txt", "target", "other")])

    assert result["ok"] is False
    assert safe.read_text(encoding="utf-8") == "original\n"
    assert target.read_text(encoding="utf-8") == "target\n"
    permissions.confirm_tool.assert_not_called()


@pytest.mark.parametrize(
    "changes",
    [
        [create("same.txt", "first"), create("same.txt", "second")],
        [create("node", "file"), create("node/child.txt", "child")],
    ],
)
def test_duplicate_and_parent_child_paths_are_rejected(project, changes):
    result = apply(changes)

    assert result["ok"] is False
    assert "重复或存在父子路径冲突" in result["error"]
    assert not (project / "same.txt").exists()
    assert not (project / "node").exists()
    permissions.confirm_tool.assert_not_called()


def test_refusing_review_leaves_every_file_unchanged(project):
    first = project / "first.txt"
    first.write_text("first old\n", encoding="utf-8")
    permissions.confirm_tool.return_value = False

    result = apply([edit("first.txt", "old", "new"), create("new.txt", "new\n")])

    assert result["ok"] is False
    assert first.read_text(encoding="utf-8") == "first old\n"
    assert not (project / "new.txt").exists()
    permissions.confirm_tool.assert_called_once()


def test_approval_time_change_cancels_the_whole_batch_and_preserves_external_edit(project):
    first = project / "first.txt"
    second = project / "second.txt"
    first.write_text("first old\n", encoding="utf-8")
    second.write_text("second old\n", encoding="utf-8")

    def edit_during_approval(*_args):
        second.write_text("external edit\n", encoding="utf-8")
        return True

    permissions.confirm_tool.side_effect = edit_during_approval
    result = apply([edit("first.txt", "old", "new"), edit("second.txt", "old", "new")])

    assert result["ok"] is False
    assert first.read_text(encoding="utf-8") == "first old\n"
    assert second.read_text(encoding="utf-8") == "external edit\n"
    permissions.confirm_tool.assert_called_once()


def test_creating_an_empty_file_succeeds(project):
    result = apply([create("empty.txt", "")])

    assert result["ok"] is True
    assert (project / "empty.txt").read_bytes() == b""
    permissions.confirm_tool.assert_called_once()


def test_no_change_skips_approval(project):
    target = project / "same.txt"
    target.write_text("same\n", encoding="utf-8")

    result = apply([edit("same.txt", "same", "same")])

    assert result["ok"] is True
    assert result["changed"] is False
    assert target.read_text(encoding="utf-8") == "same\n"
    permissions.confirm_tool.assert_not_called()


def test_second_replace_failure_restores_first_file_and_removes_staging_files(project, monkeypatch):
    first = project / "first.txt"
    second = project / "second.txt"
    first.write_text("first old\n", encoding="utf-8")
    second.write_text("second old\n", encoding="utf-8")
    real_replace = changesets.os.replace
    failed = False

    def fail_second_once(source, destination):
        nonlocal failed
        if Path(destination) == second and not failed:
            failed = True
            raise OSError("injected replace failure")
        return real_replace(source, destination)

    monkeypatch.setattr(changesets.os, "replace", fail_second_once)
    result = apply([edit("first.txt", "old", "new"), edit("second.txt", "old", "new")])

    assert result["ok"] is False
    assert result["rolled_back"] is True
    assert result["rollback_errors"] == []
    assert result["changed"] is False
    assert first.read_text(encoding="utf-8") == "first old\n"
    assert second.read_text(encoding="utf-8") == "second old\n"
    assert_no_staged_files(project)


def test_rollback_preserves_a_later_external_edit_and_reports_partial_change(project, monkeypatch):
    first = project / "first.txt"
    second = project / "second.txt"
    first.write_text("first old\n", encoding="utf-8")
    second.write_text("second old\n", encoding="utf-8")
    real_replace = changesets.os.replace
    failed = False

    def fail_second_after_external_edit(source, destination):
        nonlocal failed
        if Path(destination) == second and not failed:
            failed = True
            first.write_text("external edit after commit\n", encoding="utf-8")
            raise OSError("injected replace failure")
        return real_replace(source, destination)

    monkeypatch.setattr(changesets.os, "replace", fail_second_after_external_edit)
    result = apply([edit("first.txt", "old", "new"), edit("second.txt", "old", "new")])

    assert result["ok"] is False
    assert result["changed"] is True
    assert result["rolled_back"] is False
    assert [item["path"] for item in result["rollback_errors"]] == ["first.txt"]
    assert first.read_text(encoding="utf-8") == "external edit after commit\n"
    assert second.read_text(encoding="utf-8") == "second old\n"
    assert_no_staged_files(project)


def test_auto_review_of_control_file_routes_to_human_without_model_call(project, monkeypatch):
    monkeypatch.setitem(approval_config, "mode", "auto")
    reviewer = Mock(side_effect=AssertionError("model call is not expected"))
    monkeypatch.setattr(model_client, "request_message", reviewer)

    with task_scope("更新项目规则"):
        result = apply([create("AGENTS.md", "project rules\n")])

    assert result["ok"] is True
    assert (project / "AGENTS.md").read_text(encoding="utf-8") == "project rules\n"
    assert [item["method"] for item in result["approval"]] == ["reviewer", "human"]
    assert result["approval"][0]["reason"] == "control_file"
    permissions.confirm_tool.assert_called_once()
    reviewer.assert_not_called()
