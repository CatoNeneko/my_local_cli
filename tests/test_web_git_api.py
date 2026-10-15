import subprocess

from fastapi.testclient import TestClient
from web.app import create_app
from web.settings import Settings


def repo(root):
    root.mkdir()
    target = root / "calc.py"
    target.write_text("value = 1\n")
    for args in (
        ["init", "-q"],
        ["add", "calc.py"],
        ["-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "seed"],
    ):
        subprocess.run(["git", *args], cwd=root, capture_output=True, check=True)
    return target


def test_git_restore_api_requires_approval_and_detects_conflict(tmp_path):
    target = repo(tmp_path / "project")
    target.write_text("value = 2 # user dirty\n")
    app = create_app(Settings(tmp_path / ".ai-cli/web", tmp_path))
    with TestClient(app) as client:
        session = client.post(
            "/api/sessions", json={"title": "git", "workspace": str(target.parent)}
        ).json()
        prefix = f"/api/sessions/{session['id']}/git"
        assert client.get(prefix + "/status").json()["files"][0]["path"] == "calc.py"
        snapshot = client.post(prefix + "/snapshots", json={}).json()
        target.write_text("value = 3\n")
        body = {"snapshot_id": snapshot["id"], "path": "calc.py"}
        preview = client.post(prefix + "/restore-preview", json=body).json()
        assert "user dirty" in preview["diff"]
        denied = client.post(
            prefix + "/restore",
            json={**body, "expected_hash": preview["current_hash"], "allow": False},
        )
        assert not denied.json()["restored"] and target.read_text() == "value = 3\n"
        target.write_text("value = 4 # concurrent\n")
        conflict = client.post(
            prefix + "/restore",
            json={**body, "expected_hash": preview["current_hash"], "allow": True},
        )
        assert conflict.json()["conflict"] and target.read_text() == "value = 4 # concurrent\n"
        fresh = client.post(prefix + "/restore-preview", json=body).json()
        restored = client.post(
            prefix + "/restore",
            json={**body, "expected_hash": fresh["current_hash"], "allow": True},
        )
        assert restored.json()["restored"] and target.read_text() == "value = 2 # user dirty\n"
        assert client.post(prefix + "/restore", json={**body, "allow": "true"}).status_code == 422
        assert (
            client.post(
                prefix + "/restore-preview",
                json={"snapshot_id": snapshot["id"], "path": "../escape.py"},
            ).status_code
            == 400
        )


def test_resume_endpoint_creates_new_task_with_state_verification(tmp_path, monkeypatch):
    app = create_app(Settings(tmp_path / ".ai-cli/web", tmp_path))
    with TestClient(app) as client:
        store = app.state.store
        session = store.create_session("resume", str(tmp_path))
        old = store.create_run(session["id"], "修复加法")
        store.set_run(old["id"], status="interrupted")
        seen = []

        def submit(session_id, message):
            seen.append(message)
            return store.create_run(session_id, message)

        monkeypatch.setattr(app.state.runner, "submit", submit)
        resumed = client.post(f"/api/runs/{old['id']}/resume", json={})
        assert resumed.status_code == 202 and resumed.json()["id"] != old["id"]
        assert "不盲目重复操作" in seen[0] and "修复加法" in seen[0]
        assert store.get_run(old["id"])["status"] == "interrupted"
