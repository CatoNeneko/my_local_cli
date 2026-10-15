"""有界调度器。任务状态持久化，运行进程不共享 CLI 全局状态。"""

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading

from web.guardrails import check_input
from web.recovery import Recovery
from web.git_changes import GitManager

ACTIVE = {"queued", "running", "waiting_approval"}


class Runner:
    def __init__(self, settings, store):
        self.settings, self.store = settings, store
        self.pool = ThreadPoolExecutor(
            max_workers=settings.max_workers, thread_name_prefix="agent-job"
        )
        self.lock = threading.RLock()
        self.jobs = {}
        self.closed = False
        self.recovery = Recovery(store.db_path)
        self.git = GitManager(settings.state_dir)
        self.task_service = None

    def _diagnose(self, run_id, error, stage="dispatcher"):
        from web.diagnostics import safe_diagnostic

        diagnostic = safe_diagnostic(error, stage, run_id)
        self._log_diagnostic(run_id, diagnostic)
        self.store.add_event(run_id, "diagnostic", diagnostic)
        return diagnostic

    def _log_diagnostic(self, run_id, diagnostic):
        from web.diagnostics import DiagnosticLog

        try:
            directory = self.settings.state_dir / "diagnostics" / run_id
            directory.mkdir(parents=True, exist_ok=True, mode=0o700)
            DiagnosticLog(directory / "events.jsonl").append(diagnostic)
        except OSError:
            # 独立日志不可写时仍通过数据库事件完成任务状态更新。
            pass

    def submit(self, session_id, message):
        guard = check_input(message)
        if not self.settings.model_ready:
            raise RuntimeError("请在服务器环境配置 AI_CLI_MODEL 与 API 密钥；本地模型保持停用")
        with self.lock:
            if self.closed:
                raise RuntimeError("服务正在关闭")
            active = [r for r in self.store.list_runs() if r["status"] in ACTIVE]
            if any(r["session_id"] == session_id for r in active):
                raise ValueError("同一会话已有活动任务，请等待或取消")
            if len(active) >= 32:
                raise ValueError("任务队列已满")
            run = self.store.create_run(session_id, message)
            self.store.append_messages(session_id, [{"role": "user", "content": message}])
            self.store.add_event(run["id"], "guardrail", guard)
            job = {
                "process": None,
                "cancelled": False,
                "done": False,
                "write_lock": threading.Lock(),
            }
            self.jobs[run["id"]] = job
            job["future"] = self.pool.submit(self._run, run["id"], job)
            return run

    def _finish(self, run_id, status, answer="", error=""):
        with self.lock:
            run = self.store.get_run(run_id)
            if run["status"] not in ACTIVE:
                return
            for approval in self.store.pending_approvals(run_id):
                self.store.resolve_approval(approval["id"], False)
            self.store.set_run(run_id, status=status, answer=answer, error=error)
            self.store.add_event(
                run_id, "done", {"status": status, "answer": answer, "error": error}
            )

    def _run(self, run_id, job, resume=None):
        timer = None
        process = None
        root = Path(__file__).resolve().parents[1]
        try:
            with self.lock:
                if job["cancelled"]:
                    return
                run = self.store.get_run(run_id)
                session = self.store.get_session(run["session_id"])
                state = self.settings.state_dir / "sessions" / session["id"]
                state.mkdir(parents=True, exist_ok=True)
                if resume is None:
                    try:
                        from harness.infrastructure.workspace_locks import workspace_write_lock

                        with workspace_write_lock(session["workspace"]):
                            snapshot = self.git.snapshot(session["workspace"], run_id)
                        self.store.add_event(run_id, "snapshot", snapshot)
                    except (ValueError, RuntimeError):
                        self.store.add_event(
                            run_id,
                            "warning",
                            {
                                "message": "任务前快照不可用；工作目录不是有效 Git 根目录或超出快照限制"
                            },
                        )
                # LangSmith tracing 明确关闭；凭据留在 worker 环境，不出现在 payload。
                environment = dict(
                    os.environ,
                    LANGSMITH_TRACING="false",
                    LANGCHAIN_TRACING_V2="false",
                    PYTHONDONTWRITEBYTECODE="1",
                )
                process = subprocess.Popen(
                    [sys.executable, "-m", "web.worker"],
                    cwd=root,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    encoding="utf-8",
                    start_new_session=True,
                    env=environment,
                )
                job["process"] = process
                self.store.set_run(run_id, status="running", pid=process.pid)
                payload = {
                    "run_id": run_id,
                    "db_path": self.store.db_path,
                    "knowledge_path": str(self.settings.state_dir / "knowledge.sqlite"),
                    "checkpoint_path": str(state / "checkpoints.sqlite"),
                    "session_state": str(state),
                    "approval_mode": self.settings.approval_mode,
                    "mcp_enabled": self.settings.mcp_enabled,
                    "model_config": {
                        **self.settings.model_settings(),
                        "max_response_bytes": 1048576,
                    },
                }
                if resume is not None:
                    payload["resume"] = resume
                if self.task_service is not None:
                    payload["tasks_socket"] = str(self.task_service.socket_path)
                process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
                process.stdin.flush()
            timer = threading.Timer(
                self.settings.run_timeout, lambda: self.cancel(run_id, "任务总运行时间超限")
            )
            timer.daemon = True
            timer.start()
            done = None
            paused = False
            for line in iter(lambda: process.stdout.readline(262145), ""):
                if len(line) > 262144:
                    raise ValueError("worker 事件超限")
                event = json.loads(line)
                kind, data = event["kind"], event["payload"]
                if kind == "done":
                    done = data
                else:
                    self.store.add_event(run_id, kind, data)
                    if kind == "diagnostic":
                        self._log_diagnostic(run_id, data)
                    if kind == "paused":
                        paused = True
                        self.recovery.paused(run_id)
            code = process.wait(timeout=5)
            if done:
                self._finish(run_id, done["status"], done.get("answer", ""), done.get("error", ""))
            elif not paused:
                self._diagnose(run_id, RuntimeError("worker exit"), "worker_exit")
                self._finish(
                    run_id, "failed", error=f"worker 异常退出（{code}）；请核对已发生的操作"
                )
        except Exception as error:
            diagnostic = self._diagnose(run_id, error)
            self._finish(run_id, "failed", error=diagnostic["title"] + "：" + diagnostic["message"])
        finally:
            if timer:
                timer.cancel()
            if process:
                if process.poll() is None:
                    self._terminate(process)
                process.wait(timeout=5)
                process.stdin.close()
                process.stdout.close()
            with self.lock:
                job["done"] = True
                self.jobs.pop(run_id, None)

    @staticmethod
    def _terminate(process):
        try:
            os.kill(process.pid, signal.SIGTERM)
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    def cancel(self, run_id, reason="用户取消任务；已完成操作不会回滚"):
        with self.lock:
            job = self.jobs.get(run_id)
            run = self.store.get_run(run_id)
            if not run or run["status"] not in ACTIVE:
                return False
            if job:
                job["cancelled"] = True
            for approval in self.store.pending_approvals(run_id):
                self.store.resolve_approval(approval["id"], False)
            self._finish(run_id, "cancelled", error=reason)
            process = job["process"] if job else None
        if process:
            self._terminate(process)
        return True

    def approve(self, identifier, allow):
        with self.lock:
            approval = self.store.get_approval(identifier)
            job = self.jobs.get(approval["run_id"]) if approval else None
            if not approval:
                return None
            run = self.store.get_run(approval["run_id"])
            # live worker 尚未报告 paused 时，先等待退出，避免同时恢复同一图。
            if job:
                with self.recovery.connection() as db:
                    durable = db.execute(
                        "SELECT 1 FROM tool_receipts WHERE run_id=? AND stage IN ('awaiting','paused')",
                        (run["id"],),
                    ).fetchone()
                if durable:
                    result = self.store.resolve_approval(identifier, allow)
                    if result:
                        job["future"].add_done_callback(
                            lambda _: self._resume_approved(run["id"], identifier, allow)
                        )
                    return result
            result = self.store.resolve_approval(identifier, allow)
            if result:
                if job and job["process"] and job["process"].poll() is None:
                    job["process"].stdin.write(
                        json.dumps({"approval_id": identifier, "allow": allow}) + "\n"
                    )
                    job["process"].stdin.flush()
                else:
                    self._resume_approved(run["id"], identifier, allow)
            return result

    def recover(self):
        self.recovery.recover_runs(self.store)
        # 批准已持久化但服务在调度前退出的情况，不丢失用户决定。
        for run in self.store.list_runs():
            if run["status"] != "waiting_approval":
                continue
            with self.recovery.connection() as db:
                receipt = db.execute(
                    "SELECT approval_id FROM tool_receipts WHERE run_id=? AND stage='paused'",
                    (run["id"],),
                ).fetchone()
            approval = self.store.get_approval(receipt["approval_id"]) if receipt else None
            if approval and approval["status"] != "pending":
                if self.settings.model_ready:
                    self._resume_approved(
                        run["id"], approval["id"], approval["status"] == "approved"
                    )
                else:
                    self.store.set_run(
                        run["id"],
                        status="interrupted",
                        error="批准已保存，但模型配置不可用；请配置后继续任务",
                    )

    def _resume_approved(self, run_id, approval_id, allow):
        with self.lock:
            run = self.store.get_run(run_id)
            if self.closed or run["status"] != "waiting_approval" or run_id in self.jobs:
                return
            job = {
                "process": None,
                "cancelled": False,
                "done": False,
                "write_lock": threading.Lock(),
            }
            self.jobs[run_id] = job
            job["future"] = self.pool.submit(
                self._run, run_id, job, {"approval_id": approval_id, "allow": allow}
            )

    def continue_run(self, run_id):
        run = self.store.get_run(run_id)
        if not run or run["status"] not in ("interrupted", "failed", "cancelled"):
            raise ValueError("只能继续已中断、失败或取消的任务")
        return self.submit(
            run["session_id"],
            "继续之前任务："
            + run["message"][:8000]
            + "\n上次运行已停止，部分副作用可能已经发生。先重新检查文件和工具证据，不盲目重复操作。",
        )

    def close(self):
        with self.lock:
            self.closed = True
            identifiers = list(self.jobs)
        for identifier in identifiers:
            self.cancel(identifier, "服务关闭；任务停止，已完成操作不会回滚")
        self.pool.shutdown(wait=True, cancel_futures=True)
