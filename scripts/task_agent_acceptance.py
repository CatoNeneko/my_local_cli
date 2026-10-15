"""本机确定性协议夹具：验收 web 常驻子代理与建议应用流程。"""

from __future__ import annotations

from contextlib import ExitStack
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
import tempfile
import threading


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


INITIAL_CONTENT = "def add(a, b):\n    return a - b\n"
PROPOSED_CONTENT = "def add(a, b):\n    return a + b\n"
ORIGINAL_TASK = "修复 calc.py 中 add 的加法实现，并保留函数签名。"
PROPOSAL_ID = "1"
API_KEY_ENV = "CODEX_TASK_AGENT_ACCEPTANCE_KEY"
ARTIFACT = ROOT / "artifacts" / "web" / "task-agent-acceptance.json"


def _tool_call(identifier: str, name: str, arguments: dict[str, str]) -> dict:
    return {
        "id": identifier,
        "type": "function",
        "function": {
            "name": name,
            "arguments": json.dumps(arguments, ensure_ascii=False),
        },
    }


def _completion(message: dict, finish_reason: str) -> dict:
    return {
        "id": "task-agent-acceptance",
        "object": "chat.completion",
        "created": 1,
        "model": "fixture-model",
        "choices": [{"index": 0, "message": message, "finish_reason": finish_reason}],
    }


def _tool_results(body: dict) -> list[dict]:
    results = []
    for message in body.get("messages", []):
        if message.get("role") != "tool":
            continue
        try:
            value = json.loads(message.get("content", ""))
        except (TypeError, ValueError):
            continue
        if isinstance(value, dict):
            results.append(value)
    return results


class FixtureHandler(BaseHTTPRequestHandler):
    """只对本机请求返回固定的 OpenAI 兼容 JSON 响应。"""

    protocol_version = "HTTP/1.0"
    requests: list[dict] = []
    sequence: list[str] = []
    protocol_errors: list[str] = []
    first_request_received = threading.Event()
    release_first_request = threading.Event()

    def log_message(self, *_args):
        pass

    def _reply(self, value: dict, status: int = 200) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            self.requests.append(body)
            ordinal = len(self.requests)
            if self.path != "/v1/chat/completions":
                self.protocol_errors.append("unexpected_path")
            if body.get("model") != "fixture-model" or body.get("stream") is not False:
                self.protocol_errors.append("unexpected_request_mode")

            tool_names = {item.get("function", {}).get("name") for item in body.get("tools", [])}
            if not {"read_file", "propose_edit"}.issubset(tool_names):
                self.protocol_errors.append("expected_tools_missing")

            if ordinal == 1:
                self.sequence.append("read_file")
                self.first_request_received.set()
                if not self.release_first_request.wait(timeout=15):
                    self.protocol_errors.append("first_request_gate_timeout")
                message = {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [_tool_call("fixture-read", "read_file", {"path": "calc.py"})],
                }
                self._reply(_completion(message, "tool_calls"))
                return

            if ordinal == 2:
                if not any(item.get("content") == INITIAL_CONTENT for item in _tool_results(body)):
                    self.protocol_errors.append("read_file_result_missing")
                self.sequence.append("propose_edit")
                message = {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        _tool_call(
                            "fixture-propose",
                            "propose_edit",
                            {"path": "calc.py", "new_content": PROPOSED_CONTENT},
                        )
                    ],
                }
                self._reply(_completion(message, "tool_calls"))
                return

            if ordinal == 3:
                if not any(item.get("proposal_id") == PROPOSAL_ID for item in _tool_results(body)):
                    self.protocol_errors.append("proposal_result_missing")
                self.sequence.append("final")
                self._reply(
                    _completion(
                        {"role": "assistant", "content": "已提出加法修复建议。"},
                        "stop",
                    )
                )
                return

            self.protocol_errors.append("unexpected_extra_request")
            self._reply(_completion({"role": "assistant", "content": "结束。"}, "stop"))
        except Exception as error:
            self.protocol_errors.append(type(error).__name__)
            try:
                self._reply({"error": {"message": "local fixture protocol error"}}, status=500)
            except OSError:
                pass


def _restore_environment(saved: dict[str, str | None]) -> None:
    for name, value in saved.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value


def main() -> int:
    from web.settings import Settings
    from web.store import Store
    from web.task_service import TaskClient, TaskService

    FixtureHandler.requests = []
    FixtureHandler.sequence = []
    FixtureHandler.protocol_errors = []
    FixtureHandler.first_request_received = threading.Event()
    FixtureHandler.release_first_request = threading.Event()
    fixture = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
    fixture_thread = threading.Thread(target=fixture.serve_forever, daemon=True)
    fixture_thread.start()

    proxy_names = (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
        "NO_PROXY",
        "no_proxy",
        API_KEY_ENV,
    )
    saved_environment = {name: os.environ.get(name) for name in proxy_names}
    os.environ[API_KEY_ENV] = "fixture-only-no-network-credential"
    for name in proxy_names:
        if name != API_KEY_ENV:
            os.environ.pop(name, None)
    os.environ["NO_PROXY"] = "127.0.0.1,localhost"
    os.environ["no_proxy"] = "127.0.0.1,localhost"

    report: dict = {
        "fixture_only": True,
        "real_model_called": False,
        "local_http_stub": True,
        "checks": {},
    }
    service = None
    try:
        with (
            tempfile.TemporaryDirectory(prefix="cli-task-agent-acceptance-") as temporary,
            ExitStack() as cleanup,
        ):
            project = Path(temporary) / "project"
            project.mkdir()
            source = project / "calc.py"
            source.write_text(INITIAL_CONTENT, encoding="utf-8")

            settings = Settings(
                state_dir=project / ".ai-cli" / "web",
                workspace_root=project,
                model="fixture-model",
                base_url=f"http://127.0.0.1:{fixture.server_port}/v1",
                api_key_env=API_KEY_ENV,
                approval_mode="manual",
                mcp_enabled=False,
            )
            store = Store(settings.state_dir / "workbench.sqlite")
            session = store.create_session("子代理协议验收", str(project))
            first_run = store.create_run(session["id"], ORIGINAL_TASK)
            store.set_run(first_run["id"], status="running")

            service = TaskService(settings, store).start()
            cleanup.callback(service.close)
            cleanup.callback(FixtureHandler.release_first_request.set)
            first_client = TaskClient(service.socket_path, session["id"], first_run["id"])
            launched = first_client.start_agent(str(project), ORIGINAL_TASK)
            report["launch"] = launched
            report["checks"]["valid_run_started_agent"] = launched.get("ok") is True
            if not launched.get("ok"):
                raise AssertionError("活动 session/run 未能启动子代理")

            task_id = launched["task_id"]
            request_reached_gate = FixtureHandler.first_request_received.wait(timeout=10)
            report["checks"]["agent_reached_local_stub"] = request_reached_gate
            if not request_reached_gate:
                raise AssertionError("子代理未能连接本机 JSON stub")

            # 子代理此时正等待首次模型响应；结束原 run 后再创建后续 run。
            store.set_run(first_run["id"], status="succeeded", answer="父运行已结束")
            next_run = store.create_run(session["id"], "在后续运行中查看已完成的建议")
            store.set_run(next_run["id"], status="running")
            next_client = TaskClient(service.socket_path, session["id"], next_run["id"])
            waiting_status = first_client.task_status(task_id)
            report["checks"]["agent_survived_original_run_end"] = (
                store.get_run(first_run["id"])["status"] == "succeeded"
                and waiting_status.get("state") == "running"
            )
            FixtureHandler.release_first_request.set()

            finished = next_client.wait_task(task_id, seconds=30)
            report["child_status"] = finished
            child_result = finished.get("agent_result", {})
            report["checks"]["agent_completed_successfully"] = (
                finished.get("state") == "finished"
                and finished.get("exit_code") == 0
                and child_result.get("ok") is True
            )
            report["checks"]["protocol_sequence_read_propose_final"] = (
                FixtureHandler.sequence == ["read_file", "propose_edit", "final"]
                and len(FixtureHandler.requests) == 3
                and not FixtureHandler.protocol_errors
            )
            if not report["checks"]["agent_completed_successfully"]:
                raise AssertionError("子代理没有返回成功的最终结果")
            if not report["checks"]["protocol_sequence_read_propose_final"]:
                raise AssertionError("本机 JSON 协议请求顺序或内容不符合预期")

            summaries = child_result.get("proposals", [])
            proposal_summary = next(
                (item for item in summaries if item.get("proposal_id") == PROPOSAL_ID),
                None,
            )
            report["checks"]["edit_proposal_created"] = bool(
                proposal_summary
                and proposal_summary.get("tool") == "edit_file"
                and proposal_summary.get("path") == "calc.py"
            )
            if not report["checks"]["edit_proposal_created"]:
                raise AssertionError("子代理没有暂存 calc.py 的 edit_file 建议")

            # 强制把完成结果写入 supervisor 持久层，供后续 RPC 读取。
            service.request(session["id"], "list_tasks")
            proposal_response = next_client.proposal(task_id, PROPOSAL_ID)
            report["checks"]["proposal_workspace_matches_project"] = proposal_response.get(
                "job", {}
            ).get("workspace") == str(project)
            report["checks"]["next_run_retrieved_persisted_proposal"] = (
                proposal_response.get("ok") is True
                and proposal_response.get("proposal", {}).get("new_content") == PROPOSED_CONTENT
                and store.get_run(first_run["id"])["status"] == "succeeded"
            )
            report["checks"]["source_unchanged_before_apply"] = (
                source.read_text(encoding="utf-8") == INITIAL_CONTENT
            )

            foreign_session = store.create_session("隔离会话", str(project))
            foreign_run = store.create_run(foreign_session["id"], "隔离查询")
            store.set_run(foreign_run["id"], status="running")
            foreign_client = TaskClient(
                service.socket_path, foreign_session["id"], foreign_run["id"]
            )
            foreign_query = foreign_client.proposal(task_id, PROPOSAL_ID)
            report["checks"]["foreign_session_query_rejected"] = foreign_query.get("ok") is False

            # 捕获共享 Runtime 实际展示的 diff，并用可信测试 stub 接受人工确认。
            import permissions
            import tool_runtime
            from config import approval_config
            from harness.tasks.runtime import TASK_BACKEND
            from workspace import use_workspace
            from unittest.mock import patch

            shown_diffs: list[str] = []
            confirmations: list[dict] = []

            def confirm_tool(name: str, target: str, details: str = "") -> bool:
                confirmations.append(
                    {
                        "name": name,
                        "target": target,
                        "details": details,
                        "diff": shown_diffs[-1] if shown_diffs else "",
                    }
                )
                return True

            backend_token = TASK_BACKEND.set(next_client)
            try:
                with (
                    patch.dict(approval_config, {"mode": "manual"}),
                    patch.object(tool_runtime, "show_diff", side_effect=shown_diffs.append),
                    patch.object(permissions, "confirm_tool", side_effect=confirm_tool),
                    use_workspace(project),
                ):
                    report["checks"]["runtime_workspace_matches_project"] = (
                        permissions.PROJECT_ROOT == project.resolve()
                    )
                    application = tool_runtime.execute_tool(
                        "apply_agent_proposal",
                        {"task_id": task_id, "proposal_id": PROPOSAL_ID},
                    )
                    repeated_application = tool_runtime.execute_tool(
                        "apply_agent_proposal",
                        {"task_id": task_id, "proposal_id": PROPOSAL_ID},
                    )
            finally:
                TASK_BACKEND.reset(backend_token)

            report["application"] = application
            report["repeated_application"] = repeated_application
            report["confirmation"] = confirmations[0] if confirmations else None
            expected_diff = bool(
                shown_diffs
                and "-    return a - b" in shown_diffs[0]
                and "+    return a + b" in shown_diffs[0]
            )
            inner_approvals = application.get("result", {}).get("approval", [])
            report["checks"].update(
                {
                    "runtime_application_succeeded": (
                        application.get("ok") is True
                        and application.get("result", {}).get("changed") is True
                    ),
                    "source_changed_only_after_application": source.read_text(encoding="utf-8")
                    == PROPOSED_CONTENT,
                    "diff_was_shown_before_confirmation": expected_diff
                    and bool(confirmations)
                    and confirmations[0]["diff"] == shown_diffs[0],
                    "human_confirmation_covered_edit_file": (
                        len(confirmations) == 1
                        and confirmations[0]["name"] == "edit_file"
                        and confirmations[0]["target"] == str(source)
                    ),
                    "runtime_recorded_human_approval": any(
                        item.get("tool") == "edit_file"
                        and item.get("method") == "human"
                        and item.get("decision") == "allow"
                        for item in inner_approvals
                    ),
                    "second_application_rejected": repeated_application.get("ok") is False,
                }
            )

            report["task_id"] = task_id
            report["stub_request_count"] = len(FixtureHandler.requests)
            report["subagent_protocol_sequence"] = list(FixtureHandler.sequence)
            report["stub_protocol_errors"] = list(FixtureHandler.protocol_errors)
            report["diff"] = shown_diffs[0] if shown_diffs else ""
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {error}"
        report["checks"].setdefault("completed_without_exception", False)
    else:
        report["checks"]["completed_without_exception"] = True
    finally:
        FixtureHandler.release_first_request.set()
        fixture.shutdown()
        fixture.server_close()
        fixture_thread.join(timeout=2)
        _restore_environment(saved_environment)

    report.setdefault("stub_request_count", len(FixtureHandler.requests))
    report.setdefault("subagent_protocol_sequence", list(FixtureHandler.sequence))
    report.setdefault("stub_protocol_errors", list(FixtureHandler.protocol_errors))
    report["passed"] = bool(report["checks"]) and all(report["checks"].values())
    report["failed_checks"] = [name for name, passed in report["checks"].items() if not passed]
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
