import json
import os
import time

import pytest
from web.settings import Settings
from web.store import Store
from web.task_service import TaskService, TaskClient, _rpc


def test_service_rpc_identity_and_session_scope(tmp_path):
    settings = Settings(tmp_path / ".ai-cli/web", tmp_path)
    store = Store(settings.state_dir / "workbench.sqlite")
    first = store.create_session("first", str(tmp_path))
    second = store.create_session("second", str(tmp_path))
    with store._connection(write=True) as db:
        db.execute("""CREATE TABLE background_tasks (
            id TEXT PRIMARY KEY,session_id TEXT,snapshot TEXT,private TEXT,updated_at REAL)""")
        db.execute(
            "INSERT INTO background_tasks VALUES (?,?,?,?,?)",
            (
                "stored-task",
                first["id"],
                json.dumps(
                    {
                        "ok": True,
                        "task_id": "stored-task",
                        "kind": "pty",
                        "state": "running",
                        "output": "hello",
                        "output_bytes": 5,
                    }
                ),
                "{}",
                time.time(),
            ),
        )
    service = TaskService(settings, store).start()
    try:
        assert service.request(None, "ping")["ok"]
        assert not _rpc(service.socket_path, "wrong-token", None, "ping")["ok"]
        assert (
            service.request(second["id"], "task_status", {"task_id": "stored-task"})["ok"] is False
        )
        own = service.request(first["id"], "task_status", {"task_id": "stored-task"})
        assert own["state"] == "interrupted" and own["reason"] == "supervisor_restart"
        assert own["output"] == "hello"
        assert service.request(first["id"], "list_tasks")["tasks"][0]["task_id"] == "stored-task"
        client = TaskClient(service.socket_path, first["id"], "nonexistent-run")
        assert client.owns_task("stored-task")
        assert client.start_agent(str(tmp_path), "analyze")["ok"] is False
        with pytest.raises(ValueError):
            client._request("close")
        assert os.stat(service.token_path).st_mode & 0o077 == 0
    finally:
        service.close()
    assert not service.socket_path.exists() and not service.token_path.exists()


def test_completed_subagent_proposal_survives_supervisor_rebuild(tmp_path):
    tmp_path = tmp_path / "cli-task-agent-acceptance-abcdefghijklmnopqrst"
    tmp_path.mkdir()
    settings = Settings(tmp_path / ".ai-cli/web", tmp_path)
    store = Store(settings.state_dir / "workbench.sqlite")
    session = store.create_session("agent", str(tmp_path))
    service = TaskService(settings, store).start()
    try:
        original_content = "value='sk-abcdefghijklmnopqrstuv'"
        proposal = {
            "proposal_id": "1",
            "tool": "edit_file",
            "path": "calc.py",
            "new_content": original_content,
            "original_hash": "hash",
        }
        public = {
            "ok": True,
            "task_id": "agent-task",
            "kind": "agent",
            "state": "finished",
            "output": "",
            "agent_result": {
                "reply": "ready",
                "proposals": [{"proposal_id": "1", "path": "calc.py"}],
            },
        }
        private = {
            "workspace": str(tmp_path),
            "task": "fix",
            "applied_proposals": [],
            "agent_raw": {"ok": True, "proposals": [proposal]},
        }
        with store._connection(write=True) as db:
            db.execute(
                "INSERT INTO background_tasks VALUES (?,?,?,?,?)",
                ("agent-task", session["id"], json.dumps(public), json.dumps(private), time.time()),
            )
    finally:
        service.close()
    service = TaskService(settings, store).start()
    try:
        result = service.request(
            session["id"], "proposal", {"task_id": "agent-task", "proposal_id": "1"}
        )
        assert result["proposal"]["new_content"] == original_content
        assert result["job"]["workspace"] == str(tmp_path)
        status = service.request(session["id"], "task_status", {"task_id": "agent-task"})
        assert "new_content" not in json.dumps(status)
        assert service.request(
            session["id"], "mark_applied", {"task_id": "agent-task", "proposal_id": "1"}
        )["ok"]
        assert not service.request(
            session["id"], "proposal", {"task_id": "agent-task", "proposal_id": "1"}
        )["ok"]
    finally:
        service.close()


def test_cli_backend_delegation_does_not_cleanup_service_tasks(monkeypatch):
    from harness.tasks.runtime import TASK_BACKEND, owns_task, task_kind, close_tasks, inspect_task

    class Backend:
        def owns_task(self, identifier):
            return identifier == "owned"

        def job_kind(self, identifier):
            return "pty"

        def inspect_task(self, identifier, offset=0):
            return {"ok": True, "output": "persisted"}

    token = TASK_BACKEND.set(Backend())
    try:
        assert owns_task("owned") and not owns_task("other")
        assert task_kind("owned") == "pty"
        assert inspect_task("owned")["output"] == "persisted"
        close_tasks()  # 不存在隐式 global close RPC。
    finally:
        TASK_BACKEND.reset(token)
