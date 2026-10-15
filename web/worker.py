"""可信 worker：独立进程绑定 workspace，用 stdout JSONL 传递事件，stdin 接收审批。"""

from contextlib import redirect_stdout
import ctypes
import json
import os
from pathlib import Path
import signal
import sys
import threading


def main():
    payload = json.loads(sys.stdin.readline())
    pipe = sys.stdout
    lock = threading.Lock()

    def emit(kind, data):
        from web.guardrails import redact

        line = redact(json.dumps({"kind": kind, "payload": data}, ensure_ascii=False, default=str))
        with lock:
            pipe.write(line + "\n")
            pipe.flush()

    # 父服务退出时 worker 不继续无人审批执行；仅 Linux/WSL 支持。
    if sys.platform == "linux":
        parent = os.getppid()
        ctypes.CDLL(None).prctl(1, signal.SIGTERM)
        if os.getppid() != parent:
            return

    def interrupted(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupted)
    from config import approval_config, model_config

    model_config.update(payload["model_config"])
    approval_config["mode"] = payload["approval_mode"]
    # 输出日志与协议分离，禁止自然语言冒充事件。
    with redirect_stdout(sys.stderr):
        from workspace import use_workspace
        from web.store import Store
        from web.knowledge import KnowledgeStore
        from mcp_manager import MCPManager
        from harness.tasks.runtime import close_tasks, TASK_BACKEND
        from approval import task_scope
        import history
        import permissions
        import tool_runtime
        from project_instructions import load_project_instructions
        from langgraph.checkpoint.sqlite import SqliteSaver
        from web.workflow import build_graph
        from web.recovery import Recovery, CURRENT_TOOL, ToolPause
        from langgraph.types import interrupt, Command
        from langgraph.errors import GraphInterrupt

        store = Store(payload["db_path"])
        run = store.get_run(payload["run_id"])
        session = store.get_session(run["session_id"])
        knowledge = KnowledgeStore(payload["knowledge_path"])
        recovery = Recovery(store.db_path)
        if payload.get("tasks_socket"):
            from web.task_service import TaskClient

            TASK_BACKEND.set(TaskClient(payload["tasks_socket"], session["id"], run["id"]))
        last_diff = {"value": ""}

        def show_diff(diff):
            last_diff["value"] = diff
            emit("diff", {"diff": diff})

        def confirm(name, target, details=""):
            action = name + "\n目标: " + str(target) + "\n" + details
            diff = last_diff["value"]
            last_diff["value"] = ""
            current = CURRENT_TOOL.get()
            receipt = recovery.get(*current) if current else None
            approval = (
                store.get_approval(receipt["approval_id"])
                if receipt and receipt["approval_id"]
                else None
            )
            if approval is None:
                approval = store.create_approval(run["id"], action, diff)
                if current:
                    recovery.awaiting(*current, approval["id"])
                store.set_run(run["id"], status="waiting_approval")
                emit("approval", approval)
            try:
                if current:
                    try:
                        value = interrupt(
                            {"approval_id": approval["id"], "action": approval["action"]}
                        )
                    except GraphInterrupt as interruption:
                        raise ToolPause(interruption)
                else:
                    # MCP 启动在图外；保留短生命周期人工确认，不伪称可图恢复。
                    value = json.loads(sys.stdin.readline(4096))
                # 可信服务必须先持久化该审批决定；stdin 消息只负责唤醒。
                resolved = store.get_approval(approval["id"])
                accepted = (
                    value.get("approval_id") == approval["id"]
                    and value.get("allow") is True
                    and resolved["status"] == "approved"
                    and action == approval["action"]
                    and diff == approval["diff"]
                )
                if value.get("allow") and not accepted:
                    emit(
                        "warning", {"message": "恢复时操作或 diff 已变化，旧批准不适用；本次未执行"}
                    )
            except (ValueError, AttributeError):
                accepted = False
            if current:
                # 批准之后、产生副作用之前标为执行中；崩溃窗口不能再当作安全暂停。
                recovery.executing(*current)
            store.set_run(run["id"], status="running")
            return accepted

        tool_runtime.show_diff = show_diff
        permissions.confirm_tool = confirm
        try:
            with use_workspace(session["workspace"]):
                # Web 历史不混用 CLI 默认会话；保护目录位于服务私有状态目录。
                history.HISTORY_PATH = Path(payload["session_state"]) / "history.jsonl"
                history.append_messages = lambda batch: store.append_messages(session["id"], batch)
                history.append_message = lambda message: store.append_messages(
                    session["id"], [message]
                )
                load_project_instructions()
                with task_scope(run["message"]), MCPManager() as manager:
                    if payload["mcp_enabled"]:
                        emit("mcp", manager.load_configured())
                    with SqliteSaver.from_conn_string(payload["checkpoint_path"]) as saver:
                        graph = build_graph(store, knowledge, run, session, emit, saver)
                        initial = (
                            Command(resume=payload["resume"])
                            if payload.get("resume")
                            else {
                                "messages": store.messages(session["id"]),
                                "rounds": 0,
                                "tool_count": 0,
                                "stopped": False,
                            }
                        )
                        result = graph.invoke(
                            initial,
                            {"configurable": {"thread_id": run["id"]}, "recursion_limit": 30},
                        )
                        if result.get("__interrupt__"):
                            recovery.paused(run["id"])
                            emit(
                                "paused",
                                {
                                    "status": "waiting_approval",
                                    "message": "图已持久暂停，运行槽位已释放",
                                },
                            )
                            return
                emit("done", {"status": "succeeded", "answer": result["answer"], "error": ""})
        except KeyboardInterrupt:
            emit(
                "done",
                {
                    "status": "cancelled",
                    "answer": "",
                    "error": "任务已取消；已完成写入或外部操作不会回滚，请核对实际状态",
                },
            )
        except Exception as error:
            from web.diagnostics import safe_diagnostic

            diagnostic = safe_diagnostic(error, "agent", run["id"])
            emit("diagnostic", diagnostic)
            emit(
                "done",
                {
                    "status": "failed",
                    "answer": "",
                    "error": diagnostic["title"] + "：" + diagnostic["message"],
                    "diagnostic": diagnostic,
                },
            )
        finally:
            close_tasks()


if __name__ == "__main__":
    main()
