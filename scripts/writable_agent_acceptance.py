"""确定性本机夹具：验收可写子代理的审批、冲突与任务生命周期。"""

from __future__ import annotations

from contextlib import ExitStack
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


INITIAL_CONTENT = "def add(a, b):\n    return a - b\n"
APPROVED_CONTENT = "def add(a, b):\n    return a + b\n"
REJECTED_CONTENT = "def add(a, b):\n    return a * b\n"
CONFLICT_CONTENT = "def add(a, b):\n    return a // b\n"
API_KEY_ENV = "CODEX_WRITABLE_AGENT_ACCEPTANCE_KEY"
ARTIFACT = ROOT / "artifacts" / "web" / "writable-agent-acceptance.json"


def _tool_call(identifier: str, name: str, arguments: dict) -> dict:
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
        "id": "writable-agent-acceptance",
        "object": "chat.completion",
        "created": 1,
        "model": "fixture-model",
        "choices": [{"index": 0, "message": message, "finish_reason": finish_reason}],
    }


def _tool_messages(body: dict) -> tuple[list[dict], list[str]]:
    """Parse tool content as JSON; escaped newlines are ordinary JSON string data."""
    names: dict[str, str] = {}
    for message in body.get("messages", []):
        if message.get("role") != "assistant":
            continue
        for call in message.get("tool_calls", []):
            function = call.get("function", {})
            if isinstance(call.get("id"), str) and isinstance(function.get("name"), str):
                names[call["id"]] = function["name"]

    decoded: list[dict] = []
    errors: list[str] = []
    for message in body.get("messages", []):
        if message.get("role") != "tool":
            continue
        content = message.get("content")
        try:
            value = json.loads(content)
        except (TypeError, ValueError):
            errors.append("tool_message_invalid_json")
            continue
        if not isinstance(value, dict):
            errors.append("tool_message_not_object")
            continue
        call_id = message.get("tool_call_id")
        decoded.append({"name": names.get(call_id), "value": value})
    return decoded, errors


def _latest_result(messages: list[dict], tool: str) -> dict | None:
    return next(
        (item["value"] for item in reversed(messages) if item.get("name") == tool),
        None,
    )


class FixtureHandler(BaseHTTPRequestHandler):
    """仅为本机 OpenAI 兼容请求返回固定 JSON，不调用真实模型。"""

    protocol_version = "HTTP/1.0"
    requests: list[dict] = []
    tool_messages: list[list[dict]] = []
    sequence: list[str] = []
    protocol_errors: list[str] = []
    plan: list[dict] = []
    responses: list[dict] = []
    first_request_received = threading.Event()
    release_first_request = threading.Event()

    @classmethod
    def configure(cls, plan: list[dict]) -> None:
        cls.requests = []
        cls.tool_messages = []
        cls.sequence = []
        cls.protocol_errors = []
        cls.responses = []
        cls.plan = plan
        cls.first_request_received = threading.Event()
        cls.release_first_request = threading.Event()

    def log_message(self, *_args):
        pass

    def _reply(self, value: dict, status: int = 200) -> None:
        self.responses.append(value)
        raw = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _step(self, ordinal: int, tool_messages: list[dict]) -> dict | None:
        if ordinal >= len(self.plan):
            return None
        step = self.plan[ordinal]
        if step.get("requires_pty_task"):
            result = _latest_result(tool_messages, "start_pty")
            if not result or not result.get("task_id"):
                return None
        return step

    def _arguments(self, step: dict, tool_messages: list[dict]) -> dict:
        arguments = dict(step.get("arguments", {}))
        task_source = step.get("task_id_from")
        if task_source:
            result = _latest_result(tool_messages, task_source)
            if not result or not isinstance(result.get("task_id"), str):
                self.protocol_errors.append("dynamic_task_id_missing")
                return arguments
            arguments["task_id"] = result["task_id"]
        return arguments

    def do_POST(self):
        try:
            size = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(size))
            ordinal = len(self.requests) - 1
            decoded, decode_errors = _tool_messages(body)
            self.tool_messages.append(decoded)
            self.protocol_errors.extend(decode_errors)

            if self.path != "/v1/chat/completions":
                self.protocol_errors.append("unexpected_path")
            if body.get("model") != "fixture-model" or body.get("stream") is not False:
                self.protocol_errors.append("unexpected_request_mode")
            tool_names = {item.get("function", {}).get("name") for item in body.get("tools", [])}
            conversation = [
                {
                    key: message[key]
                    for key in ("role", "content", "tool_calls", "tool_call_id")
                    if key in message
                }
                for message in body.get("messages", [])
                if message.get("role") == "tool"
                or (message.get("role") == "assistant" and message.get("tool_calls"))
            ]
            self.requests.append(
                {
                    "model": body.get("model"),
                    "stream": body.get("stream"),
                    "messages": conversation,
                    "tool_names": sorted(name for name in tool_names if isinstance(name, str)),
                }
            )
            ordinal = len(self.requests) - 1
            if len(decoded) != ordinal:
                self.protocol_errors.append("tool_result_count_mismatch")
            expected_history = [step["tool"] for step in self.plan[:ordinal]]
            if [item.get("name") for item in decoded] != expected_history:
                self.protocol_errors.append("tool_result_sequence_mismatch")

            if ordinal == 0:
                self.first_request_received.set()
                if not self.release_first_request.wait(timeout=20):
                    self.protocol_errors.append("first_request_gate_timeout")

            step = self._step(ordinal, decoded)
            if step is None:
                self.sequence.append("final")
                self._reply(
                    _completion(
                        {"role": "assistant", "content": "已按工具结果完成本次任务。"},
                        "stop",
                    )
                )
                return

            name = step["tool"]
            if name not in tool_names:
                self.protocol_errors.append("expected_tool_missing")
            self.sequence.append(name)
            message = {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    _tool_call(f"fixture-{ordinal + 1}", name, self._arguments(step, decoded))
                ],
            }
            self._reply(_completion(message, "tool_calls"))
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


def _set_check(case: dict, name: str, passed: object) -> None:
    case.setdefault("checks", {})[name] = bool(passed)


def _snapshot_fixture() -> dict:
    return {
        "requests": list(FixtureHandler.requests),
        "tool_messages": list(FixtureHandler.tool_messages),
        "responses": list(FixtureHandler.responses),
        "sequence": list(FixtureHandler.sequence),
        "protocol_errors": list(FixtureHandler.protocol_errors),
    }


def _pending_until(client, task_id: str, timeout: float = 20) -> tuple[dict, dict | None]:
    deadline = time.monotonic() + timeout
    latest: dict = {}
    while True:
        latest = client.task_status(task_id)
        approvals = latest.get("pending_approvals", [])
        if approvals:
            return latest, approvals[0]
        if latest.get("state") != "running" or time.monotonic() >= deadline:
            return latest, None
        time.sleep(0.1)


def _terminal_status(client, task_id: str, timeout: float = 8) -> dict:
    deadline = time.monotonic() + timeout
    latest: dict = {}
    while time.monotonic() < deadline:
        latest = client.task_status(task_id)
        if latest.get("state") != "running":
            return latest
        time.sleep(0.1)
    return latest


def _wait_for_sequence(expected: str, timeout: float = 10) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if expected in FixtureHandler.sequence:
            return True
        time.sleep(0.05)
    return expected in FixtureHandler.sequence


def _plan(*steps: dict) -> list[dict]:
    return list(steps)


def _start_case(
    case: dict,
    *,
    project: Path,
    store,
    service,
    session_id: str,
    task: str,
    plan: list[dict],
) -> tuple[str | None, object | None]:
    FixtureHandler.configure(plan)
    case["task_prompt"] = task
    parent_run = store.create_run(session_id, f"启动 {case['name']} 验收子任务")
    store.set_run(parent_run["id"], status="running")
    starter = None
    next_client = None
    try:
        from web.task_service import TaskClient

        starter = TaskClient(service.socket_path, session_id, parent_run["id"])
        launched = starter.start_agent(str(project), task)
        case["launch"] = launched
        _set_check(case, "agent_started", launched.get("ok") is True)
        task_id = launched.get("task_id") if launched.get("ok") is True else None
        received = FixtureHandler.first_request_received.wait(timeout=10)
        _set_check(case, "first_request_reached_local_fixture", received)

        store.set_run(parent_run["id"], status="succeeded", answer="父运行结束")
        followup = store.create_run(session_id, f"检查 {case['name']} 子任务状态")
        store.set_run(followup["id"], status="running")
        next_client = TaskClient(service.socket_path, session_id, followup["id"])
        case["parent_run_after_launch"] = store.get_run(parent_run["id"])
        _set_check(
            case,
            "followup_run_can_query_after_parent_run_succeeded",
            store.get_run(parent_run["id"])["status"] == "succeeded"
            and task_id is not None
            and next_client.task_status(task_id).get("ok") is True,
        )
        case["followup_run_id"] = followup["id"]
        return task_id, next_client
    finally:
        FixtureHandler.release_first_request.set()


def _operations(status: dict) -> list[dict]:
    return status.get("agent_result", {}).get("operations", [])


def _operation(operations: list[dict], tool: str) -> dict | None:
    return next((item for item in operations if item.get("tool") == tool), None)


def _record_finish(case: dict, client, task_id: str) -> dict:
    finished = client.wait_task(task_id, seconds=25)
    case["child_status"] = finished
    _set_check(
        case,
        "child_finished_with_valid_result",
        finished.get("state") == "finished"
        and finished.get("exit_code") == 0
        and finished.get("agent_result", {}).get("ok") is True,
    )
    _set_check(case, "fixture_used_at_most_eight_rounds", len(FixtureHandler.requests) <= 8)
    case["fixture"] = _snapshot_fixture()
    _set_check(case, "fixture_protocol_valid", not FixtureHandler.protocol_errors)
    return finished


def _run_edit_case(project: Path, source: Path, store, service, session_id: str) -> dict:

    case = {"name": "approve_edit_tests_and_interactive_pty", "checks": {}}
    source.write_text(INITIAL_CONTENT, encoding="utf-8")
    tests = project / "test_calc.py"
    tests.write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n",
        encoding="utf-8",
    )
    plan = _plan(
        {"tool": "read_file", "arguments": {"path": "calc.py"}},
        {
            "tool": "edit_file",
            "arguments": {"path": "calc.py", "new_content": APPROVED_CONTENT},
        },
        {"tool": "run_tests", "arguments": {"path": "test_calc.py"}},
        {
            "tool": "start_pty",
            "arguments": {
                "path": ".",
                "argv": [
                    "/usr/bin/python3",
                    "-u",
                    "-c",
                    "print('READY', flush=True); value=input(); print('GOT:'+value, flush=True)",
                ],
                "timeout": 30,
            },
        },
        {
            "tool": "task_input",
            "task_id_from": "start_pty",
            "requires_pty_task": True,
            "arguments": {"text": "fixture-input\n"},
        },
        {
            "tool": "task_wait",
            "task_id_from": "start_pty",
            "requires_pty_task": True,
            "arguments": {"seconds": 5},
        },
    )
    task_id, client = _start_case(
        case,
        project=project,
        store=store,
        service=service,
        session_id=session_id,
        task="读取 calc.py，将 add 改成加法；审批后运行 test_calc.py，再启动交互 PTY 并返回输入结果。",
        plan=plan,
    )
    if not task_id or client is None:
        case["fixture"] = _snapshot_fixture()
        return case

    try:
        status, edit_approval = _pending_until(client, task_id)
        case["edit_pending_status"] = status
        case["edit_pending_approval"] = edit_approval
        _set_check(
            case,
            "edit_pending_approval_visible_after_run_rollover",
            status.get("state") == "running"
            and any(
                item.get("action") == "edit_file" for item in status.get("pending_approvals", [])
            )
            and store.get_run(case["parent_run_after_launch"]["id"])["status"] == "succeeded",
        )

        if edit_approval:
            foreign_session = store.create_session("隔离审批会话", str(project))
            foreign_resolve = service.request(
                foreign_session["id"],
                "resolve_task_approval",
                {
                    "task_id": task_id,
                    "approval_id": edit_approval["id"],
                    "allow": True,
                },
            )
            case["foreign_session_resolve"] = foreign_resolve
            _set_check(
                case, "foreign_session_cannot_resolve_approval", foreign_resolve.get("ok") is False
            )
            still_pending = client.task_status(task_id)
            case["status_after_foreign_resolve"] = still_pending
            _set_check(
                case,
                "foreign_resolve_left_approval_pending",
                any(
                    item.get("id") == edit_approval["id"]
                    for item in still_pending.get("pending_approvals", [])
                ),
            )

            approved_edit = service.request(
                session_id,
                "resolve_task_approval",
                {"task_id": task_id, "approval_id": edit_approval["id"], "allow": True},
            )
            case["edit_resolution"] = approved_edit
            _set_check(
                case,
                "edit_approval_resolved_by_service",
                approved_edit.get("ok") is True
                and approved_edit.get("approval", {}).get("status") == "approved",
            )

            next_status, next_approval = _pending_until(client, task_id)
            case["next_pending_status"] = next_status
            case["next_pending_approval"] = next_approval
            if next_approval and next_approval.get("action") == "run_tests":
                _set_check(case, "run_tests_required_manual_approval", True)
                test_resolution = service.request(
                    session_id,
                    "resolve_task_approval",
                    {"task_id": task_id, "approval_id": next_approval["id"], "allow": True},
                )
                case["run_tests_resolution"] = test_resolution
                _set_check(
                    case,
                    "run_tests_approval_resolved",
                    test_resolution.get("ok") is True
                    and test_resolution.get("approval", {}).get("status") == "approved",
                )
                next_status, next_approval = _pending_until(client, task_id)
                case["pty_pending_status"] = next_status
                case["pty_pending_approval"] = next_approval
            else:
                _set_check(case, "run_tests_required_manual_approval", False)
                _set_check(case, "run_tests_approval_resolved", False)
                case["pty_pending_status"] = next_status
                case["pty_pending_approval"] = next_approval

            pty_approval = (
                next_approval
                if next_approval and next_approval.get("action") == "start_pty"
                else None
            )
            _set_check(case, "start_pty_required_manual_approval", bool(pty_approval))
            if pty_approval:
                pty_resolution = service.request(
                    session_id,
                    "resolve_task_approval",
                    {"task_id": task_id, "approval_id": pty_approval["id"], "allow": True},
                )
                case["start_pty_resolution"] = pty_resolution
                _set_check(
                    case,
                    "start_pty_approval_resolved",
                    pty_resolution.get("ok") is True
                    and pty_resolution.get("approval", {}).get("status") == "approved",
                )
            else:
                _set_check(case, "start_pty_approval_resolved", False)

        if _wait_for_sequence("task_input", timeout=8):
            case["task_input_fixture_reached"] = True
        else:
            case["task_input_fixture_reached"] = False

        finished = _record_finish(case, client, task_id)
        operations = _operations(finished)
        case["operations"] = operations
        edit_op = _operation(operations, "edit_file") or {}
        test_op = _operation(operations, "run_tests") or {}
        pty_op = _operation(operations, "start_pty") or {}
        input_op = _operation(operations, "task_input") or {}
        wait_op = _operation(operations, "task_wait") or {}
        _set_check(
            case,
            "edit_file_operation_reports_changed",
            edit_op.get("ok") is True and edit_op.get("changed") is True,
        )
        _set_check(
            case, "calc_file_written", source.read_text(encoding="utf-8") == APPROVED_CONTENT
        )
        _set_check(
            case,
            "run_tests_exit_zero",
            test_op.get("ok") is True and test_op.get("exit_code") == 0,
        )
        _set_check(case, "pty_started", pty_op.get("ok") is True)
        _set_check(case, "pty_input_sent", input_op.get("ok") is True)
        wait_result = next(
            (
                item["value"]
                for item in reversed(
                    FixtureHandler.tool_messages[-1] if FixtureHandler.tool_messages else []
                )
                if item.get("name") == "task_wait"
            ),
            {},
        )
        case["task_wait_result"] = wait_result
        _set_check(
            case,
            "interactive_pty_returned_input_and_exit_zero",
            wait_op.get("ok") is True
            and wait_op.get("exit_code") == 0
            and wait_result.get("state") == "finished"
            and "GOT:fixture-input" in wait_result.get("output", ""),
        )
        _set_check(
            case,
            "read_edit_test_pty_round_sequence",
            FixtureHandler.sequence
            == [
                "read_file",
                "edit_file",
                "run_tests",
                "start_pty",
                "task_input",
                "task_wait",
                "final",
            ],
        )
    except Exception as error:
        case["error"] = f"{type(error).__name__}: {error}"
        _set_check(case, "completed_without_exception", False)
        case["fixture"] = _snapshot_fixture()
        if task_id:
            case["cleanup_status"] = service.request(
                session_id, "task_cancel", {"task_id": task_id}
            )
    return case


def _run_rejection_case(project: Path, source: Path, store, service, session_id: str) -> dict:
    case = {"name": "reject_edit_keeps_original", "checks": {}}
    source.write_text(INITIAL_CONTENT, encoding="utf-8")
    task_id, client = _start_case(
        case,
        project=project,
        store=store,
        service=service,
        session_id=session_id,
        task="读取 calc.py，提出把 add 改成乘法的修改，等待审批并报告结果。",
        plan=_plan(
            {"tool": "read_file", "arguments": {"path": "calc.py"}},
            {
                "tool": "edit_file",
                "arguments": {"path": "calc.py", "new_content": REJECTED_CONTENT},
            },
        ),
    )
    if not task_id or client is None:
        case["fixture"] = _snapshot_fixture()
        return case
    try:
        status, approval = _pending_until(client, task_id)
        case["pending_status"] = status
        case["pending_approval"] = approval
        _set_check(
            case,
            "edit_pending_visible",
            status.get("state") == "running"
            and bool(approval)
            and approval.get("action") == "edit_file",
        )
        if approval:
            resolution = service.request(
                session_id,
                "resolve_task_approval",
                {"task_id": task_id, "approval_id": approval["id"], "allow": False},
            )
            case["resolution"] = resolution
        else:
            resolution = {}
        _set_check(
            case,
            "edit_rejection_persisted",
            resolution.get("ok") is True
            and resolution.get("approval", {}).get("status") == "rejected",
        )
        finished = _record_finish(case, client, task_id)
        operations = _operations(finished)
        case["operations"] = operations
        edit_op = _operation(operations, "edit_file") or {}
        _set_check(
            case,
            "rejected_edit_operation_failed_without_change",
            edit_op.get("ok") is False and edit_op.get("changed") is False,
        )
        _set_check(
            case,
            "original_content_preserved",
            source.read_text(encoding="utf-8") == INITIAL_CONTENT,
        )
        _set_check(
            case,
            "read_edit_final_sequence",
            FixtureHandler.sequence == ["read_file", "edit_file", "final"],
        )
    except Exception as error:
        case["error"] = f"{type(error).__name__}: {error}"
        _set_check(case, "completed_without_exception", False)
        case["fixture"] = _snapshot_fixture()
        case["cleanup_status"] = service.request(session_id, "task_cancel", {"task_id": task_id})
    return case


def _run_conflict_case(project: Path, source: Path, store, service, session_id: str) -> dict:
    case = {"name": "external_change_conflict_is_not_overwritten", "checks": {}}
    source.write_text(INITIAL_CONTENT, encoding="utf-8")
    task_id, client = _start_case(
        case,
        project=project,
        store=store,
        service=service,
        session_id=session_id,
        task="读取 calc.py，提出 add 改为乘法的修改，等待审批并报告结果。",
        plan=_plan(
            {"tool": "read_file", "arguments": {"path": "calc.py"}},
            {
                "tool": "edit_file",
                "arguments": {"path": "calc.py", "new_content": REJECTED_CONTENT},
            },
        ),
    )
    if not task_id or client is None:
        case["fixture"] = _snapshot_fixture()
        return case
    try:
        status, approval = _pending_until(client, task_id)
        case["pending_status"] = status
        case["pending_approval"] = approval
        _set_check(
            case,
            "edit_pending_visible",
            status.get("state") == "running"
            and bool(approval)
            and approval.get("action") == "edit_file",
        )
        source.write_text(CONFLICT_CONTENT, encoding="utf-8")
        case["external_content"] = source.read_text(encoding="utf-8")
        if approval:
            resolution = service.request(
                session_id,
                "resolve_task_approval",
                {"task_id": task_id, "approval_id": approval["id"], "allow": True},
            )
            case["resolution"] = resolution
        else:
            resolution = {}
        _set_check(
            case,
            "edit_approval_resolved",
            resolution.get("ok") is True
            and resolution.get("approval", {}).get("status") == "approved",
        )
        finished = _record_finish(case, client, task_id)
        operations = _operations(finished)
        case["operations"] = operations
        edit_op = _operation(operations, "edit_file") or {}
        _set_check(
            case,
            "runtime_refused_stale_edit",
            edit_op.get("ok") is False
            and edit_op.get("changed") is False
            and "变化"
            in str(
                next(
                    (
                        item["value"].get("error", "")
                        for item in reversed(
                            FixtureHandler.tool_messages[-1] if FixtureHandler.tool_messages else []
                        )
                        if item.get("name") == "edit_file"
                    ),
                    "",
                )
            ),
        )
        _set_check(
            case,
            "external_content_not_overwritten",
            source.read_text(encoding="utf-8") == CONFLICT_CONTENT,
        )
    except Exception as error:
        case["error"] = f"{type(error).__name__}: {error}"
        _set_check(case, "completed_without_exception", False)
        case["fixture"] = _snapshot_fixture()
        case["cleanup_status"] = service.request(session_id, "task_cancel", {"task_id": task_id})
    return case


def _run_cancel_case(project: Path, source: Path, store, service, session_id: str) -> dict:
    case = {"name": "cancel_closes_pending_approval", "checks": {}}
    source.write_text(INITIAL_CONTENT, encoding="utf-8")
    task_id, client = _start_case(
        case,
        project=project,
        store=store,
        service=service,
        session_id=session_id,
        task="读取 calc.py，提出 add 改为乘法的修改，等待审批并报告结果。",
        plan=_plan(
            {"tool": "read_file", "arguments": {"path": "calc.py"}},
            {
                "tool": "edit_file",
                "arguments": {"path": "calc.py", "new_content": REJECTED_CONTENT},
            },
        ),
    )
    if not task_id or client is None:
        case["fixture"] = _snapshot_fixture()
        return case
    try:
        status, approval = _pending_until(client, task_id)
        case["pending_status"] = status
        case["pending_approval"] = approval
        _set_check(
            case,
            "edit_pending_visible",
            status.get("state") == "running"
            and bool(approval)
            and approval.get("action") == "edit_file",
        )
        if approval:
            cancelled = service.request(session_id, "task_cancel", {"task_id": task_id})
            case["cancel_result"] = cancelled
            after_cancel = _terminal_status(client, task_id)
            case["status_after_cancel"] = after_cancel
            _set_check(
                case,
                "task_cancelled_while_approval_pending",
                after_cancel.get("state") == "finished"
                and after_cancel.get("reason") == "cancelled"
                and after_cancel.get("exit_code") is not None,
            )
            resolution = service.request(
                session_id,
                "resolve_task_approval",
                {"task_id": task_id, "approval_id": approval["id"], "allow": True},
            )
            case["resolution_after_cancel"] = resolution
        else:
            resolution = {}
        _set_check(case, "resolve_after_cancel_rejected", resolution.get("ok") is False)
        _set_check(
            case,
            "cancelled_task_did_not_write_file",
            source.read_text(encoding="utf-8") == INITIAL_CONTENT,
        )
        case["fixture"] = _snapshot_fixture()
        _set_check(case, "fixture_protocol_valid", not FixtureHandler.protocol_errors)
        _set_check(case, "fixture_used_at_most_eight_rounds", len(FixtureHandler.requests) <= 8)
    except Exception as error:
        case["error"] = f"{type(error).__name__}: {error}"
        _set_check(case, "completed_without_exception", False)
        case["fixture"] = _snapshot_fixture()
        case["cleanup_status"] = service.request(session_id, "task_cancel", {"task_id": task_id})
    return case


def main() -> int:
    from web.settings import Settings
    from web.store import Store
    from web.task_service import TaskService

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

    fixture = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
    fixture_thread = threading.Thread(target=fixture.serve_forever, daemon=True)
    fixture_thread.start()
    report: dict = {
        "fixture_only": True,
        "real_model_called": False,
        "local_http_stub": "127.0.0.1",
        "settings": {
            "model": "fixture-model",
            "base_url": f"http://127.0.0.1:{fixture.server_port}/v1",
            "api_key_env": API_KEY_ENV,
            "approval_mode": "manual",
        },
        "cases": {},
        "checks": {},
    }
    service = None
    try:
        with tempfile.TemporaryDirectory(prefix="cli-writable-agent-acceptance-") as temporary:
            project = Path(temporary) / "project"
            project.mkdir()
            source = project / "calc.py"
            source.write_text(INITIAL_CONTENT, encoding="utf-8")
            settings = Settings(
                state_dir=project / ".ai-cli" / "web",
                workspace_root=Path(temporary),
                model="fixture-model",
                base_url=f"http://127.0.0.1:{fixture.server_port}/v1",
                api_key_env=API_KEY_ENV,
                approval_mode="manual",
                mcp_enabled=False,
            )
            store = Store(settings.state_dir / "workbench.sqlite")
            session = store.create_session("可写子代理协议验收", str(project))
            service = TaskService(settings, store).start()
            with ExitStack() as cleanup:
                cleanup.callback(service.close)
                cleanup.callback(FixtureHandler.release_first_request.set)
                for runner in (
                    _run_edit_case,
                    _run_rejection_case,
                    _run_conflict_case,
                    _run_cancel_case,
                ):
                    name = {
                        _run_edit_case: "approve_edit_tests_and_interactive_pty",
                        _run_rejection_case: "reject_edit_keeps_original",
                        _run_conflict_case: "external_change_conflict_is_not_overwritten",
                        _run_cancel_case: "cancel_closes_pending_approval",
                    }[runner]
                    try:
                        report["cases"][name] = runner(
                            project, source, store, service, session["id"]
                        )
                    except Exception as error:
                        report["cases"][name] = {
                            "name": name,
                            "checks": {"completed_without_exception": False},
                            "error": f"{type(error).__name__}: {error}",
                            "fixture": _snapshot_fixture(),
                        }
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        FixtureHandler.release_first_request.set()
        fixture.shutdown()
        fixture.server_close()
        fixture_thread.join(timeout=2)
        _restore_environment(saved_environment)

    for case_name, case in report["cases"].items():
        for check_name, passed in case.get("checks", {}).items():
            report["checks"][f"{case_name}.{check_name}"] = bool(passed)
    report["passed"] = (
        bool(report["checks"]) and all(report["checks"].values()) and "error" not in report
    )
    report["failed_checks"] = [name for name, passed in report["checks"].items() if not passed]
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "passed": report["passed"],
                "failed_checks": report["failed_checks"],
                "artifact": str(ARTIFACT),
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
