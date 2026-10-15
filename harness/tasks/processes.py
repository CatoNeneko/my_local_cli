"""有界的真实进程任务驱动。"""

import atexit
import json
import os
import pty
import select
import signal
import subprocess
import threading
import time
import uuid

JOBS = {}
LOCK = threading.RLock()
MAX_OUTPUT = 65536


def launch(
    command, *, terminal=False, payload=None, timeout=120, kind="pty", metadata=None, on_finish=None
):
    if kind == "agent" and (
        not isinstance(payload, dict)
        or not all(isinstance(payload.get(key), str) for key in ("workspace", "task"))
    ):
        raise ValueError("子代理启动数据无效")
    with LOCK:
        if sum(job["process"].poll() is None for job in JOBS.values()) >= 4:
            return {"ok": False, "error": "同时运行任务达到上限（4 个）"}
        # CLI 保留有限的近期结果，避免累计次数永久阻止新的任务。
        for identifier in list(JOBS):
            if len(JOBS) < 64:
                break
            if JOBS[identifier]["done"]:
                JOBS.pop(identifier)
        if len(JOBS) >= 64:
            return {"ok": False, "error": "任务池已满，不能启动新任务"}
        master = slave = None
        if terminal:
            master, slave = pty.openpty()
        try:
            process = subprocess.Popen(
                command,
                stdin=slave if terminal else subprocess.PIPE,
                stdout=slave if terminal else subprocess.PIPE,
                stderr=slave if terminal else subprocess.DEVNULL,
                start_new_session=True,
                env=dict(os.environ)
                if kind == "agent"
                else {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
            )
        except BaseException:
            if master is not None:
                os.close(master)
            raise
        finally:
            if slave is not None:
                os.close(slave)
        identifier = (
            payload["task_id"]
            if kind == "agent" and payload.get("task_id")
            else uuid.uuid4().hex[:12]
        )
        job = dict(metadata or {})
        job.update(
            {
                "task_id": identifier,
                "process": process,
                "fd": master if terminal else process.stdout.fileno(),
                "output": bytearray(),
                "reason": "",
                "kind": kind,
                "terminal": terminal,
                "done": False,
                "lock": threading.RLock(),
                "on_finish": on_finish,
            }
        )
        JOBS[identifier] = job
    try:
        if payload is not None:
            process.stdin.write(json.dumps(payload, ensure_ascii=False).encode())
            process.stdin.close()
        thread = threading.Thread(target=_collect, args=(job, timeout), daemon=True)
        job["thread"] = thread
        thread.start()
    except BaseException:
        _kill(job)
        if process.stdin is not None and not terminal:
            try:
                process.stdin.close()
            except OSError:
                pass
        process.wait()
        _close(job)
        with LOCK:
            JOBS.pop(identifier, None)
        raise
    return {"ok": True, "task_id": identifier, "kind": kind, "state": "running"}


def _kill(job):
    try:
        os.killpg(job["process"].pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _close(job):
    if job["terminal"]:
        os.close(job["fd"])
    else:
        job["process"].stdout.close()


def _collect(job, timeout):
    deadline = time.monotonic() + timeout
    try:
        while True:
            if time.monotonic() >= deadline:
                job["reason"] = "timeout"
                _kill(job)
                break
            ready, _, _ = select.select([job["fd"]], [], [], 0.1)
            if ready:
                try:
                    chunk = os.read(job["fd"], 8192)
                except OSError:
                    break
                if not chunk:
                    break
                with job["lock"]:
                    remaining = MAX_OUTPUT - len(job["output"])
                    job["output"].extend(chunk[:remaining])
                    if len(chunk) > remaining:
                        job["reason"] = "output_limit"
                        _kill(job)
                        break
            elif job["process"].poll() is not None:
                break
    finally:
        try:
            # 给正常退出留出时间，然后清理仍占用终端的后代。
            try:
                job["process"].wait(timeout=0.2)
            except subprocess.TimeoutExpired:
                pass
            _kill(job)
            job["process"].wait()
            with job["lock"]:
                _close(job)
        finally:
            callback = job.get("on_finish")
            if callable(callback):
                try:
                    callback()
                except Exception as exc:
                    with job["lock"]:
                        job["cleanup_error"] = type(exc).__name__
            with job["lock"]:
                job["done"] = True


def inspect_task(task_id, offset=0):
    job = JOBS.get(task_id)
    if job is None:
        return {"ok": False, "error": "未知任务 ID；任务仅在当前 CLI 进程有效"}
    with job["lock"]:
        raw = bytes(job["output"])
        result = {
            "ok": True,
            "task_id": task_id,
            "kind": job["kind"],
            "state": "finished" if job["done"] else "running",
            "exit_code": job["process"].poll(),
            "reason": job["reason"],
            "output": raw[offset : offset + 16000].decode("utf-8", errors="replace"),
            "next_offset": min(len(raw), offset + 16000),
            "output_bytes": len(raw),
            "more_output": len(raw) > offset + 16000,
        }
        if job.get("cleanup_error"):
            result["cleanup_error"] = job["cleanup_error"]
        if offset > len(raw):
            return {"ok": False, "error": "输出偏移超过已收集长度"}
        if job["kind"] == "agent" and job["done"]:
            try:
                result["agent_result"] = json.loads(raw)
                proposals = result["agent_result"].get("proposals", [])
                result["agent_result"]["proposals"] = [
                    {key: item.get(key) for key in ("proposal_id", "tool", "path")}
                    for item in proposals
                ]
                # 原始输出含建议源码；模型查询仅收到摘要，实际应用取内部完整数据。
                result["output"] = ""
                result["more_output"] = False
                reply = result["agent_result"].get("reply", "")
                if len(reply) > 16000:
                    result["agent_result"]["reply"] = reply[:16000]
                    result["agent_result"]["reply_truncated"] = True
            except (ValueError, UnicodeError):
                result["ok"] = False
                result["error"] = "子代理异常结束，未返回有效结果"
        return result


def send_input(task_id, text):
    job = JOBS.get(task_id)
    if job is None or not job["terminal"]:
        return {"ok": False, "error": "未知 PTY 任务"}
    with job["lock"]:
        if job["done"] or job["process"].poll() is not None:
            return {"ok": False, "error": "任务已结束"}
        data = text.encode("utf-8")
        written = os.write(job["fd"], data)
        return {"ok": written == len(data), "bytes_written": written}


def cancel_task(task_id):
    job = JOBS.get(task_id)
    if job is None:
        return {"ok": False, "error": "未知任务"}
    if job["done"]:
        return inspect_task(task_id)
    job["reason"] = "cancelled"
    _kill(job)
    job["thread"].join(timeout=2)
    return inspect_task(task_id)


def wait_task(task_id, seconds=10):
    job = JOBS.get(task_id)
    if job is None:
        return {"ok": False, "error": "未知任务"}
    job["thread"].join(timeout=seconds)
    return inspect_task(task_id)


def list_tasks():
    return {
        "ok": True,
        "tasks": [
            {
                key: value
                for key, value in inspect_task(identifier).items()
                if key in ("task_id", "kind", "state", "exit_code", "reason")
            }
            for identifier in JOBS
        ],
    }


def close_tasks():
    for identifier in list(JOBS):
        cancel_task(identifier)
    JOBS.clear()


atexit.register(close_tasks)
