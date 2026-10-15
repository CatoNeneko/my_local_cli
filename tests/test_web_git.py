from pathlib import Path
import subprocess

import pytest

from web.git_changes import GitManager


def _git(repository: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


@pytest.fixture
def repository(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "Test User")
    _git(root, "config", "user.email", "test@example.invalid")
    (root / "tracked.py").write_text("base = 1\n", encoding="utf-8")
    _git(root, "add", "tracked.py")
    _git(root, "commit", "-qm", "initial")
    return root


@pytest.fixture
def manager(tmp_path):
    return GitManager(tmp_path / "state")


def test_snapshot_preserves_dirty_task_start_content_and_restores_atomically(manager, repository):
    target = repository / "tracked.py"
    target.write_text("already dirty = 2\n", encoding="utf-8")

    snapshot = manager.snapshot(repository, "run-before-edit")
    assert manager.list_snapshots(repository)[0]["id"] == snapshot["id"]
    target.write_text("agent result = 3\n", encoding="utf-8")
    preview = manager.preview_restore(repository, snapshot["id"], "tracked.py")

    assert snapshot["file_count"] == 1
    assert "already dirty = 2" in preview["diff"]
    assert preview["current_hash"]
    result = manager.restore(repository, snapshot["id"], "tracked.py", preview["current_hash"])

    assert result["restored"] is True
    assert result["changed"] is True
    assert target.read_text(encoding="utf-8") == "already dirty = 2\n"


def test_restore_reports_conflict_when_file_changed_after_preview(manager, repository):
    target = repository / "tracked.py"
    snapshot = manager.snapshot(repository, "run-conflict")
    target.write_text("first task result\n", encoding="utf-8")
    preview = manager.preview_restore(repository, snapshot["id"], "tracked.py")
    target.write_text("newer user edit\n", encoding="utf-8")

    result = manager.restore(repository, snapshot["id"], "tracked.py", preview["current_hash"])

    assert result["restored"] is False
    assert result["conflict"] is True
    assert target.read_text(encoding="utf-8") == "newer user edit\n"


def test_snapshot_excludes_private_ignored_and_symlink_files(manager, repository, tmp_path):
    (repository / ".gitignore").write_text("ignored.py\n", encoding="utf-8")
    (repository / ".env").write_text("TOKEN=private\n", encoding="utf-8")
    (repository / "ignored.py").write_text("ignored secret\n", encoding="utf-8")
    hidden = repository / ".private"
    hidden.mkdir()
    (hidden / "inside.py").write_text("hidden secret\n", encoding="utf-8")
    outside = tmp_path / "outside.py"
    outside.write_text("outside secret\n", encoding="utf-8")
    link = repository / "linked.py"
    try:
        link.symlink_to(outside)
    except (NotImplementedError, OSError):
        pytest.skip("当前环境不支持创建符号链接")
    (repository / "new.py").write_text("public new file\n", encoding="utf-8")

    snapshot = manager.snapshot(repository, "run-private")
    assert snapshot["file_count"] == 2
    assert manager.preview_restore(repository, snapshot["id"], "tracked.py")["can_restore"] is True
    assert manager.preview_restore(repository, snapshot["id"], "new.py")["can_restore"] is True
    assert snapshot["skipped"]["private"] >= 2
    assert snapshot["skipped"]["symlink"] == 1
    with pytest.raises(ValueError):
        manager.preview_restore(repository, snapshot["id"], ".env")
    with pytest.raises(ValueError):
        manager.preview_restore(repository, snapshot["id"], "linked.py")
    with pytest.raises(ValueError):
        manager.preview_restore(repository, snapshot["id"], "ignored.py")


def test_status_and_diff_report_only_safe_project_changes(manager, repository):
    (repository / "tracked.py").write_text("changed = True\n", encoding="utf-8")
    (repository / "new.md").write_text("new public note\n", encoding="utf-8")
    (repository / ".env").write_text("SECRET=do-not-show\n", encoding="utf-8")

    status = manager.status(repository)
    diff = manager.diff(repository)

    assert status["clean"] is False
    assert status["suppressed_changes"] is True
    assert {item["path"] for item in status["files"]} == {"tracked.py", "new.md"}
    assert "changed = True" in diff["diff"]
    assert "new public note" in diff["diff"]
    assert "do-not-show" not in diff["diff"]


def test_workspace_must_be_repository_root_and_git_must_exist(
    manager, repository, tmp_path, monkeypatch
):
    nested = repository / "nested"
    nested.mkdir()
    with pytest.raises(ValueError, match="根目录"):
        manager.status(nested)
    with pytest.raises(ValueError, match="不是 Git 仓库"):
        manager.status(tmp_path)

    import web.git_changes as git_changes

    monkeypatch.setattr(git_changes.shutil, "which", lambda _name: None)
    with pytest.raises(RuntimeError, match="找不到 Git"):
        manager.status(repository)
