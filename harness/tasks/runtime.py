"""任务应用入口：选择本地驱动或会话 RPC，准备工具并绑定审批生命周期。"""

from contextvars import ContextVar
import json
import os
import sys
from pathlib import Path
import uuid

from harness.tasks import processes
from harness.tasks.approvals import TaskApprovalStore

TASK_BACKEND = ContextVar("task_backend", default=None)


def owns_task(task_id):
    backend = TASK_BACKEND.get()
    return backend.owns_task(task_id) if backend else task_id in processes.JOBS


def task_access(task_id):
    backend = TASK_BACKEND.get()
    if backend:
        return backend.inspect_task(task_id)
    job = processes.JOBS.get(task_id)
    return (
        {"ok": True, "task_id": task_id, "kind": job.get("kind")}
        if job
        else {"ok": False, "error": "未知当前进程任务 ID"}
    )


def task_kind(task_id):
    backend = TASK_BACKEND.get()
    return backend.job_kind(task_id) if backend else processes.JOBS.get(task_id, {}).get("kind")


def inspect_task(task_id, offset=0):
    backend = TASK_BACKEND.get()
    if backend:
        return backend.inspect_task(task_id, offset)
    result = processes.inspect_task(task_id, offset)
    job = processes.JOBS.get(task_id)
    if result.get("ok") and job and job.get("approval_store"):
        result["pending_approvals"] = job["approval_store"].pending(task_id)
    return result


def send_input(task_id, text):
    backend = TASK_BACKEND.get()
    return backend.send_input(task_id, text) if backend else processes.send_input(task_id, text)


def cancel_task(task_id):
    backend = TASK_BACKEND.get()
    return backend.cancel_task(task_id) if backend else processes.cancel_task(task_id)


def wait_task(task_id, seconds=10):
    backend = TASK_BACKEND.get()
    if backend:
        return backend.wait_task(task_id, seconds)
    processes.wait_task(task_id, seconds)
    return inspect_task(task_id)


def list_tasks():
    backend = TASK_BACKEND.get()
    return backend.list_tasks() if backend else processes.list_tasks()


def close_tasks():
    if TASK_BACKEND.get() is None:
        processes.close_tasks()


def prepare_pty(path, argv, timeout=120):
    from sandbox import prepare_tests, build_test_command, limited_program
    from permissions import PROJECT_ROOT

    checked = prepare_tests(path)
    if not checked["ok"]:
        return checked
    target = Path(checked["path"])
    if not target.is_dir():
        return {"ok": False, "error": "PTY 工作路径必须是目录"}
    command = build_test_command(
        target, checked["bwrap"], checked["resource_limits"], checked["runtime_env"]
    )
    split = command.index("--")
    helper = "import os,sys,fcntl,termios;\ntry: os.setsid()\nexcept PermissionError: pass\nfcntl.ioctl(0,termios.TIOCSCTTY,0); os.execvpe(sys.argv[1],sys.argv[1:],os.environ)"
    command = command[: split + 1] + limited_program(
        ["/usr/bin/python3", "-c", helper] + argv, checked["resource_limits"]
    )
    command[command.index("--chdir") + 1] = str(
        Path("/workspace") / target.relative_to(PROJECT_ROOT)
    )
    return {
        "ok": True,
        "command": command,
        "timeout": timeout,
        "workspace_path": checked["path"],
        "argv": list(argv),
        "resource_limits": checked["resource_limits"],
        "details": "只读、禁网 PTY 命令: "
        + json.dumps(argv, ensure_ascii=False)
        + "; 超时 "
        + str(timeout)
        + "; 资源上限 "
        + json.dumps(checked["resource_limits"]),
    }


def start_pty(prepared):
    backend = TASK_BACKEND.get()
    if backend:
        return backend.start_pty(prepared)
    return processes.launch(prepared["command"], terminal=True, timeout=prepared["timeout"])


def start_agent(path, task, *, approval_db=None, web_context=None, approval_store=None):
    backend = TASK_BACKEND.get()
    if backend:
        return backend.start_agent(path, task)
    from config import model_config, agent_config, approval_config
    from project_instructions import build_model_messages
    from permissions import PROJECT_ROOT
    from workspace import APP_ROOT
    from approval import current_task

    identifier = uuid.uuid4().hex[:12]
    token = uuid.uuid4().hex + uuid.uuid4().hex
    approval_db = (
        Path(approval_db) if approval_db else PROJECT_ROOT / ".ai-cli/task_approvals.sqlite"
    )
    store = approval_store or TaskApprovalStore(approval_db)
    store.register(identifier, token, str(PROJECT_ROOT))
    try:
        payload = {
            "workspace": str(PROJECT_ROOT),
            "path": path,
            "task": task,
            "model_config": dict(model_config),
            "agent_config": dict(agent_config),
            "approval_config": dict(approval_config),
            "approval_db": str(approval_db),
            "owner_pid": os.getpid(),
            "task_id": identifier,
            "approval_token": token,
            "web_context": web_context,
            "instructions": build_model_messages([]),
        }
        result = processes.launch(
            [sys.executable, str(APP_ROOT / "subagent_worker.py")],
            payload=payload,
            kind="agent",
            timeout=300,
            metadata={
                "workspace": str(PROJECT_ROOT),
                "task": current_task() or task,
                "approval_store": store,
            },
            on_finish=lambda: store.close(identifier),
        )
    except BaseException:
        store.close(identifier)
        raise
    if not result.get("ok"):
        store.close(identifier)
    return result


def resolve_task_approval(task_id, approval_id, allow):
    backend = TASK_BACKEND.get()
    if backend:
        return backend.resolve_approval(task_id, approval_id, allow)
    from permissions import PROJECT_ROOT

    job = processes.JOBS.get(task_id)
    if (
        not job
        or job["kind"] != "agent"
        or job["done"]
        or job.get("workspace") != str(PROJECT_ROOT)
    ):
        return {"ok": False, "error": "子代理任务不存在、已结束或不属于当前项目"}
    return {"ok": True, "approval": job["approval_store"].resolve(task_id, approval_id, allow)}
