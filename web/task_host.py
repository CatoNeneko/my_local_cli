"""服务级任务 supervisor。只接受可信本机 RPC，项目和会话归属由数据库决定。"""

import argparse
import ctypes
import hmac
import json
import os
from pathlib import Path
import signal
import socketserver
import threading
import time
from concurrent.futures import ThreadPoolExecutor


class TaskHost:
    def __init__(self, db_path):
        from web.store import Store
        from web.settings import Settings

        self.store = Store(db_path)
        self.settings = Settings.from_env().validate()
        self.lock = threading.RLock()
        self.owners = {}
        self.fingerprints = {}
        self.stopped = threading.Event()
        # bwrap 的父死亡信号关联创建进程的线程，不能在短生命周期 RPC 线程启动。
        self.launch_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="task-launch")
        approval_path = self.settings.state_dir / "task_approvals.sqlite"
        from harness.tasks.approvals import TaskApprovalStore

        self.task_approvals = TaskApprovalStore(approval_path)
        with self.store._connection(write=True) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS background_tasks (
                id TEXT PRIMARY KEY, session_id TEXT NOT NULL, snapshot TEXT NOT NULL,
                private TEXT NOT NULL, updated_at REAL NOT NULL)""")
            # 进程不能跨 supervisor 重启恢复；保留输出和明确中断状态。
            rows = db.execute("SELECT id,snapshot FROM background_tasks").fetchall()
            for row in rows:
                snapshot = json.loads(row["snapshot"])
                if snapshot.get("state") == "running":
                    if snapshot.get("kind") == "agent":
                        try:
                            self.task_approvals.close(row["id"])
                        except ValueError:
                            pass
                    snapshot.update(
                        state="interrupted", reason="supervisor_restart", exit_code=None
                    )
                    db.execute(
                        "UPDATE background_tasks SET snapshot=?,updated_at=? WHERE id=?",
                        (json.dumps(snapshot, ensure_ascii=False), time.time(), row["id"]),
                    )
        self.monitor = threading.Thread(target=self._monitor, daemon=True)
        self.monitor.start()

    def _persist(self, task_id):
        from harness.tasks import runtime as tasks, processes
        from web.guardrails import redact

        job = processes.JOBS.get(task_id)
        if not job:
            return
        session_id = self.owners[task_id]
        with job["lock"]:
            fingerprint = (
                job["done"],
                job["process"].poll(),
                job["reason"],
                len(job["output"]),
                len(job.get("applied_proposals", set())),
            )
            if self.fingerprints.get(task_id) == fingerprint:
                return
            value = self._public_status(tasks.inspect_task(task_id))
            value.pop("pending_approvals", None)
            output = bytes(job["output"]).decode("utf-8", errors="replace")
            # PTY 完整有界输出留存；子代理的建议源码只放私有数据，不进入列表接口。
            if job["kind"] == "pty":
                value["output"] = redact(output)
            private = {
                "workspace": job.get("workspace"),
                "task": job.get("task"),
                "applied_proposals": list(job.get("applied_proposals", set())),
            }
            if job["kind"] == "agent" and job["done"]:
                try:
                    private["agent_raw"] = json.loads(output)
                except ValueError:
                    private["agent_raw"] = {"ok": False, "error": "子代理未返回有效 JSON"}
        with self.store._connection(write=True) as db:
            db.execute(
                "INSERT OR REPLACE INTO background_tasks VALUES (?,?,?,?,?)",
                (
                    task_id,
                    session_id,
                    json.dumps(value, ensure_ascii=False),
                    json.dumps(private, ensure_ascii=False),
                    time.time(),
                ),
            )
        self.fingerprints[task_id] = fingerprint

    @staticmethod
    def _public_status(value):
        from web.guardrails import redact

        if isinstance(value.get("output"), str):
            value["output"] = redact(value["output"])
        result = value.get("agent_result")
        if isinstance(result, dict) and isinstance(result.get("reply"), str):
            result["reply"] = redact(result["reply"])
        return value

    def _monitor(self):
        while not self.stopped.wait(0.5):
            try:
                with self.lock:
                    for task_id in list(self.owners):
                        self._persist(task_id)
            except Exception:
                # 不让监控失败变成模型的虚构成功；查询仍读取真实进程状态。
                pass

    def _saved(self, session_id, task_id):
        with self.store._connection() as db:
            row = db.execute(
                "SELECT * FROM background_tasks WHERE id=? AND session_id=?", (task_id, session_id)
            ).fetchone()
        return row

    def _status(self, session_id, task_id, offset=0):
        from harness.tasks import runtime as tasks, processes

        if type(offset) is not int or offset < 0:
            return {"ok": False, "error": "输出偏移无效"}
        if self.owners.get(task_id) == session_id and task_id in processes.JOBS:
            return self._public_status(tasks.inspect_task(task_id, offset))
        row = self._saved(session_id, task_id)
        if not row:
            return {"ok": False, "error": "任务不存在或不属于当前会话"}
        value = json.loads(row["snapshot"])
        raw = value.get("output", "").encode("utf-8")
        if offset > len(raw):
            return {"ok": False, "error": "输出偏移超过已收集长度"}
        value.update(
            output=raw[offset : offset + 16000].decode("utf-8", errors="replace"),
            next_offset=min(len(raw), offset + 16000),
            more_output=len(raw) > offset + 16000,
        )
        return value

    def dispatch(self, request, *, launch_thread=False):
        from harness.tasks import runtime as tasks, processes
        from workspace import use_workspace
        from config import model_config
        from project_instructions import load_project_instructions
        from approval import task_scope

        method = request.get("method")
        args = request.get("arguments", {})
        if not isinstance(args, dict):
            raise ValueError("任务参数必须为对象")
        if method == "ping":
            return {"ok": True}
        if method == "close":
            self.stopped.set()
            return {"ok": True}
        session_id = request.get("session_id")
        session = self.store.get_session(session_id)
        if not session:
            return {"ok": False, "error": "会话不存在"}
        workspace = self.settings.workspace(session["workspace"])
        if method == "list_tasks":
            with self.lock:
                for task_id in list(self.owners):
                    self._persist(task_id)
                with self.store._connection() as db:
                    rows = db.execute(
                        "SELECT snapshot FROM background_tasks WHERE session_id=? ORDER BY updated_at DESC",
                        (session_id,),
                    ).fetchall()
            allowed = ("task_id", "kind", "state", "exit_code", "reason", "output_bytes")
            return {
                "ok": True,
                "tasks": [
                    {k: v for k, v in json.loads(row["snapshot"]).items() if k in allowed}
                    for row in rows
                ],
            }
        if method in ("start_pty", "spawn_agent"):
            if not launch_thread:
                return self.launch_pool.submit(self.dispatch, request, launch_thread=True).result(
                    timeout=15
                )
            run = self.store.get_run(request.get("run_id"))
            actor = request.get("agent_task_id")
            with self.lock:
                agent_active = bool(
                    actor
                    and self.owners.get(actor) == session_id
                    and actor in processes.JOBS
                    and processes.JOBS[actor]["kind"] == "agent"
                    and not processes.JOBS[actor]["done"]
                )
            if actor and method == "spawn_agent":
                return {"ok": False, "error": "子代理不能继续创建子代理"}
            run_active = bool(
                run
                and run["session_id"] == session_id
                and run["status"] in ("running", "waiting_approval")
            )
            if not run_active and not agent_active:
                return {"ok": False, "error": "启动后台任务需要当前会话的活动运行"}
            with self.lock, use_workspace(workspace), task_scope(run["message"] if run else ""):
                # 已结束任务先保存再移出内存，以免跨请求积累到原 CLI 64 个上限。
                for identifier, job in list(processes.JOBS.items()):
                    if job["done"]:
                        self._persist(identifier)
                        processes.JOBS.pop(identifier, None)
                        self.owners.pop(identifier, None)
                        self.fingerprints.pop(identifier, None)
                if method == "start_pty":
                    from tool_registry import TOOL_REGISTRY
                    from tool_runtime import validate_arguments

                    valid = validate_arguments(TOOL_REGISTRY["start_pty"], args)
                    if not valid["ok"]:
                        return valid
                    prepared = tasks.prepare_pty(**valid["arguments"])
                    if not prepared["ok"]:
                        return prepared
                    result = tasks.start_pty(prepared)
                else:
                    if not self.settings.model_ready:
                        return {"ok": False, "error": "子代理模型未配置，本次未启动"}
                    from tool_registry import TOOL_REGISTRY
                    from tool_runtime import validate_arguments
                    from permissions import resolve_project_path

                    valid = validate_arguments(TOOL_REGISTRY["spawn_agent"], args)
                    if not valid["ok"]:
                        return valid
                    checked = resolve_project_path(valid["arguments"]["path"])
                    if not checked["ok"]:
                        return checked
                    model_config.update(self.settings.model_settings())
                    load_project_instructions()
                    from config import approval_config

                    approval_config["mode"] = self.settings.approval_mode
                    result = tasks.start_agent(
                        checked["path"],
                        valid["arguments"]["task"],
                        approval_db=self.settings.state_dir / "task_approvals.sqlite",
                        approval_store=self.task_approvals,
                        web_context={
                            "socket_path": request.get("_socket_path"),
                            "session_id": session_id,
                            "run_id": request.get("run_id"),
                        },
                    )
                if result.get("ok"):
                    self.owners[result["task_id"]] = session_id
                    self._persist(result["task_id"])
                return result
        task_id = args.get("task_id")
        if not isinstance(task_id, str):
            return {"ok": False, "error": "任务 ID 无效"}
        with self.lock:
            status = self._status(session_id, task_id, args.get("offset", 0))
        if not status.get("ok"):
            return status
        if method == "task_status":
            return status
        if method == "resolve_task_approval":
            if status.get("kind") != "agent" or status.get("state") != "running":
                return {"ok": False, "error": "子代理已结束，不能审批"}
            approved = self.task_approvals.resolve(
                task_id, args.get("approval_id"), args.get("allow")
            )
            return {"ok": True, "approval": approved}
        if method == "task_wait":
            seconds = args.get("seconds", 10)
            if type(seconds) is not int or not 1 <= seconds <= 30:
                return {"ok": False, "error": "等待时间必须在 1–30 秒内"}
            if self.owners.get(task_id) == session_id and task_id in processes.JOBS:
                tasks.wait_task(task_id, seconds)
            return self._status(session_id, task_id, args.get("offset", 0))
        if method in ("task_input", "task_cancel"):
            if status["state"] != "running" or self.owners.get(task_id) != session_id:
                return {"ok": False, "error": "任务已结束或已中断，不能发送输入或取消"}
            if method == "task_input":
                text = args.get("text")
                if not isinstance(text, str) or len(text) > 4096:
                    return {"ok": False, "error": "终端输入最多 4096 字符"}
                result = tasks.send_input(task_id, text)
            else:
                result = tasks.cancel_task(task_id)
            with self.lock:
                self._persist(task_id)
            return result
        if method in ("proposal", "mark_applied"):
            if status.get("kind") != "agent" or status["state"] != "finished":
                return {"ok": False, "error": "子代理尚未成功结束"}
            with self.lock:
                self._persist(task_id)
                row = self._saved(session_id, task_id)
                private = json.loads(row["private"])
                raw = private.get("agent_raw", {})
                proposal_id = args.get("proposal_id")
                proposal = next(
                    (p for p in raw.get("proposals", []) if p.get("proposal_id") == proposal_id),
                    None,
                )
                used = private.get("applied_proposals", [])
                if raw.get("ok") is not True or not proposal or proposal_id in used:
                    return {"ok": False, "error": "建议不存在、未成功完成或已应用"}
                if method == "mark_applied":
                    used.append(proposal_id)
                    private["applied_proposals"] = used
                    if task_id in processes.JOBS:
                        processes.JOBS[task_id].setdefault("applied_proposals", set()).add(
                            proposal_id
                        )
                    with self.store._connection(write=True) as db:
                        db.execute(
                            "UPDATE background_tasks SET private=? WHERE id=?",
                            (json.dumps(private, ensure_ascii=False), task_id),
                        )
                    return {"ok": True}
                return {
                    "ok": True,
                    "proposal": proposal,
                    "job": {
                        "kind": "agent",
                        "done": True,
                        "workspace": private["workspace"],
                        "task": private["task"],
                        "applied_proposals": used,
                    },
                }
        return {"ok": False, "error": "未知任务操作"}

    def close(self):
        from harness.tasks import runtime as tasks, processes

        self.stopped.set()
        self.monitor.join(timeout=2)
        with self.lock:
            for task_id in list(self.owners):
                job = processes.JOBS.get(task_id)
                if job and not job["done"]:
                    tasks.cancel_task(task_id)
                    job["reason"] = "service_shutdown"
                self._persist(task_id)
            tasks.close_tasks()
        self.launch_pool.shutdown(wait=True, cancel_futures=True)
        with self.store._connection(write=True) as db:
            for row in db.execute("SELECT id,snapshot FROM background_tasks").fetchall():
                value = json.loads(row["snapshot"])
                if value.get("state") == "running":
                    value.update(state="interrupted", reason="supervisor_stopped", exit_code=None)
                    db.execute(
                        "UPDATE background_tasks SET snapshot=? WHERE id=?",
                        (json.dumps(value, ensure_ascii=False), row["id"]),
                    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket", required=True)
    parser.add_argument("--db", required=True)
    args = parser.parse_args()
    token = os.environ.get("AI_CLI_TASK_TOKEN", "")
    if not token:
        raise ValueError("缺少 supervisor 身份令牌")
    host = TaskHost(args.db)

    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            self.request.settimeout(40)
            try:
                raw = self.rfile.readline(262145)
                if len(raw) > 262144:
                    raise ValueError("任务请求超限")
                request = json.loads(raw)
                supplied = request.get("token", "")
                if not isinstance(supplied, str) or not hmac.compare_digest(supplied, token):
                    result = {"ok": False, "error": "任务服务身份校验失败"}
                else:
                    request["_socket_path"] = str(args.socket)
                    result = host.dispatch(request)
            except Exception as error:
                from web.diagnostics import safe_diagnostic

                diagnostic = safe_diagnostic(error, "task_supervisor")
                result = {"ok": False, "error": diagnostic["title"], "diagnostic": diagnostic}
            # 私有 RPC 的路径和待审批源码必须精确传输；只在公开展示字段脱敏。
            self.wfile.write((json.dumps(result, ensure_ascii=False) + "\n").encode())

    class Server(socketserver.ThreadingUnixStreamServer):
        daemon_threads = True

    socket_path = Path(args.socket)
    server = Server(str(socket_path), Handler)
    socket_path.chmod(0o600)
    server.timeout = 0.2

    def stop(signum, frame):
        host.stopped.set()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    parent = os.getppid()
    ctypes.CDLL(None).prctl(1, signal.SIGTERM)
    try:
        while not host.stopped.is_set() and os.getppid() == parent:
            server.handle_request()
    finally:
        server.server_close()
        host.close()
        socket_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
