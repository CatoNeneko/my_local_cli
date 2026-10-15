import subprocess
import sys
import threading
from pathlib import Path
from unittest.mock import Mock

import pytest

from harness.tasks import processes, runtime
from harness.tasks.approvals import TaskApprovalStore


def test_tool_interaction_reuses_access_check(monkeypatch):
    import tool_runtime
    from config import approval_config

    class Backend:
        checks = 0
        inputs = 0

        def inspect_task(self, identifier):
            self.checks += 1
            return {"ok": True, "task_id": identifier, "kind": "pty"}

        def send_input(self, identifier, text):
            self.inputs += 1
            return {"ok": True}

    backend = Backend()
    token = runtime.TASK_BACKEND.set(backend)
    monkeypatch.setitem(approval_config, "mode", "manual")
    monkeypatch.setattr(tool_runtime, "record_tool_event", lambda *args: None)
    try:
        assert tool_runtime.execute_tool("task_input", {"task_id": "owned", "text": "hello\n"})[
            "ok"
        ]
        assert backend.checks == 1 and backend.inputs == 1
    finally:
        runtime.TASK_BACKEND.reset(token)


def test_status_queries_do_not_reinitialize_approval_database(tmp_path, monkeypatch):
    store = TaskApprovalStore(tmp_path / "state/tasks.sqlite")
    store.register("owned", "private-token", str(tmp_path))
    process = Mock()
    process.poll.return_value = None
    processes.JOBS["owned"] = {
        "kind": "agent",
        "done": False,
        "lock": threading.RLock(),
        "process": process,
        "reason": "",
        "output": bytearray(),
        "approval_store": store,
    }
    monkeypatch.setattr(
        TaskApprovalStore, "__init__", Mock(side_effect=AssertionError("reinitialized"))
    )
    try:
        for _ in range(5):
            assert runtime.inspect_task("owned")["pending_approvals"] == []
    finally:
        processes.JOBS.pop("owned")
        store.close("owned")


def test_payload_preparation_failure_revokes_registered_task(tmp_path, monkeypatch):
    import project_instructions
    from workspace import use_workspace

    monkeypatch.setattr(
        project_instructions, "build_model_messages", Mock(side_effect=RuntimeError("fixture"))
    )
    with use_workspace(tmp_path), pytest.raises(RuntimeError):
        runtime.start_agent(str(tmp_path), "fixture")
    store = TaskApprovalStore(tmp_path / ".ai-cli/task_approvals.sqlite")
    with store._connection() as connection:
        rows = connection.execute("SELECT state FROM task_owners").fetchall()
    assert len(rows) == 1 and rows[0]["state"] == "closed"


def test_process_driver_and_lock_do_not_load_agent_workflow():
    project = Path(__file__).resolve().parents[1]
    code = f"""import sys
sys.path.insert(0,{str(project)!r})
import harness.tasks.processes
import harness.infrastructure.workspace_locks
assert 'langgraph' not in sys.modules
assert 'web.workflow' not in sys.modules
assert 'model_client' not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code], capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0, result.stderr


def test_completed_pool_does_not_permanently_block_new_tasks(monkeypatch):
    process = Mock()
    process.poll.return_value = 0
    monkeypatch.setattr(
        processes,
        "JOBS",
        {f"old-{index}": {"done": True, "process": process} for index in range(64)},
    )
    launched = processes.launch([sys.executable, "-c", 'print("fresh")'])
    try:
        assert launched["ok"]
        assert len(processes.JOBS) == 64 and "old-0" not in processes.JOBS
        result = processes.wait_task(launched["task_id"], 3)
        assert result["exit_code"] == 0 and "fresh" in result["output"]
    finally:
        processes.cancel_task(launched["task_id"])


def test_write_confirmation_does_not_hold_workspace_lock(tmp_path, monkeypatch):
    import permissions
    import tool_runtime
    from config import approval_config
    from workspace import use_workspace

    project = Path(__file__).resolve().parents[1]
    target = tmp_path / "example.txt"
    target.write_text("before")
    code = f"import sys;sys.path.insert(0,{str(project)!r});from harness.infrastructure.workspace_locks import workspace_write_lock\nwith workspace_write_lock({str(tmp_path)!r}): print('unlocked')"

    def confirm(*args):
        result = subprocess.run(
            [sys.executable, "-I", "-c", code], capture_output=True, text=True, timeout=3
        )
        assert result.returncode == 0 and "unlocked" in result.stdout, result.stderr
        return True

    monkeypatch.setattr(permissions, "confirm_tool", confirm)
    monkeypatch.setitem(approval_config, "mode", "manual")
    monkeypatch.setattr(tool_runtime, "record_tool_event", lambda *args: None)
    with use_workspace(tmp_path):
        assert tool_runtime.execute_tool(
            "edit_file", {"path": "example.txt", "new_content": "after"}
        )["ok"]
    assert target.read_text() == "after"
