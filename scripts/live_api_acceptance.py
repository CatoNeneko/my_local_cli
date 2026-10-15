"""显式授权的 DeepSeek 官方联测：凭据仅从环境或隐藏输入读取。

使用真实模型响应及 Runtime，只对临时项目进行操作，不保存请求或回复正文。
"""

import argparse
import contextlib
from datetime import datetime, timezone
import getpass
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import urllib.error
import urllib.request
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
BASE = "https://api.deepseek.com/v1"
MAX_REQUESTS = 24
REPORT_PATH = ROOT / "artifacts/live/deepseek.json"
REQUIRED_CHECKS = (
    "json_tools",
    "stream_tools",
    "real_model_multifile_tests",
    "independent_automatic_review",
    "model_interactive_pty",
    "real_writable_subagent",
    "real_web_worker_session",
)


def summarize_report(report):
    """按最后一次尝试验收，保留原始 checks，不把缺失用量当作零。"""
    latest = {case["name"]: case for case in report["checks"]}
    checks = {name: latest.get(name, {}).get("passed") is True for name in REQUIRED_CHECKS}
    requests = report["requests"]
    usage = {}
    for field in ("prompt_tokens", "completion_tokens", "total_tokens"):
        values = [row.get(field) for row in requests]
        usage[field] = (
            sum(values) if values and all(type(value) is int for value in values) else None
        )
    return {
        "required_checks": len(REQUIRED_CHECKS),
        "completed_checks": sum(name in latest for name in REQUIRED_CHECKS),
        "passed_checks": sum(checks.values()),
        "passed": all(checks.values()),
        "latest_checks": checks,
        "attempt_count": len(report["checks"]),
        "failed_attempt_count": sum(case.get("passed") is not True for case in report["checks"]),
        "usage": {
            "scope": "instrumented_parent_process_requests_only",
            "request_count": len(requests),
            **usage,
            "subprocess_usage": None,
            "excludes": ["preliminary_probes", "subagent_worker", "web_worker"],
        },
    }


def error_details(error):
    details = {"type": type(error).__name__}
    if isinstance(error, urllib.error.HTTPError):
        details["http_status"] = error.code
    return details


class Transport:
    def __init__(self, report, key_env):
        from model_client import NoAuthRedirect

        self.report, self.key_env = report, key_env
        self.opener = urllib.request.build_opener(NoAuthRedirect())

    @contextlib.contextmanager
    def open(self, request, timeout=45):
        if request.full_url != BASE + "/chat/completions":
            raise ValueError("联测只允许 DeepSeek 官方 Chat Completions 端点")
        if len(self.report["requests"]) >= MAX_REQUESTS:
            raise ValueError("联测达到总请求预算")
        body = json.loads(request.data)
        if body["model"] != self.report["model"]:
            raise ValueError("联测模型已变化")
        body.update(max_tokens=4096, thinking={"type": "enabled"})
        if body.get("stream"):
            body["stream_options"] = {"include_usage": True}
        request.data = json.dumps(body, ensure_ascii=False).encode()
        record = {
            "stream": body.get("stream", False),
            "http_status": None,
            "tool_schema_count": len(body.get("tools", [])),
            "replayed_reasoning_messages": sum(
                "reasoning_content" in row for row in body["messages"]
            ),
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
        }
        self.report["requests"].append(record)
        self.report["real_model_called"] = True
        captured = bytearray()
        started = time.monotonic()
        try:
            with self.opener.open(request, timeout=min(timeout, 45)) as response:
                record["http_status"] = response.status

                class Capture:
                    def read(self, size=-1):
                        raw = response.read(size)
                        captured.extend(raw)
                        return raw

                    def readline(self, size=-1):
                        raw = response.readline(size)
                        captured.extend(raw)
                        return raw

                yield Capture()
        except urllib.error.HTTPError as error:
            record["http_status"] = error.code
            # 只保留错误类别和是否指出 reasoning 字段，不保存服务正文。
            try:
                raw = error.read(16000).decode("utf-8", errors="replace")
                record["reasoning_replay_error"] = "reasoning_content" in raw
            finally:
                error.close()
            raise
        finally:
            record["elapsed_seconds"] = round(time.monotonic() - started, 3)
            try:
                payloads = (
                    [
                        json.loads(line[5:])
                        for line in captured.decode().splitlines()
                        if line.startswith("data:") and "[DONE]" not in line
                    ]
                    if body.get("stream")
                    else [json.loads(captured)]
                )
                for payload in payloads:
                    usage = payload.get("usage") or {}
                    for field in ("prompt_tokens", "completion_tokens", "total_tokens"):
                        if type(usage.get(field)) is int:
                            record[field] = usage[field]
                    for choice in payload.get("choices", []):
                        message = choice.get("delta", choice.get("message", {}))
                        if message.get("reasoning_content"):
                            record["received_reasoning"] = True
            except (ValueError, UnicodeError, TypeError, AttributeError):
                pass


@contextlib.contextmanager
def client_scope(report, key_env):
    import api_adapter
    import model_client
    from config import model_config

    importlib.reload(api_adapter)
    importlib.reload(model_client)
    transport = Transport(report, key_env)
    values = dict(provider="openai", model=report["model"], base_url=BASE, api_key_env=key_env)
    with (
        patch.dict(model_config, values),
        patch.object(model_client.urllib.request, "build_opener", return_value=transport),
    ):
        yield model_client


def protocol(report, key_env):
    from tool_registry import get_tool_definitions
    from tool_runtime import execute_tool
    from workspace import use_workspace

    definitions = [
        item for item in get_tool_definitions() if item["function"]["name"] == "read_file"
    ]
    for stream in (False, True):
        case = {"name": "stream_tools" if stream else "json_tools", "passed": False}
        report["checks"].append(case)
        try:
            with tempfile.TemporaryDirectory(prefix="deepseek-protocol-") as directory:
                root = Path(directory)
                marker = "deepseek-live-marker: maple-7931"
                (root / "marker.txt").write_text(marker + "\n")
                messages = [
                    {
                        "role": "user",
                        "content": "请先实际调用 read_file 读取 marker.txt，然后原样返回文件内容。",
                    }
                ]
                chunks = []
                with (
                    client_scope(report, key_env) as client,
                    use_workspace(root),
                    patch.object(client, "get_tool_definitions", return_value=definitions),
                ):
                    first = client.request_message(
                        messages, include_context=False, stream=stream, timeout=45
                    )
                    calls = first.get("tool_calls", [])
                    assert len(calls) == 1 and calls[0]["function"]["name"] == "read_file"
                    call = calls[0]
                    assert call["function"]["arguments"] == {"path": "marker.txt"}
                    result = execute_tool("read_file", call["function"]["arguments"])
                    assert result["ok"]
                    messages.extend(
                        [
                            first,
                            {
                                "role": "tool",
                                "tool_name": "read_file",
                                "tool_call_id": call["id"],
                                "content": json.dumps(result),
                            },
                        ]
                    )
                    final = client.request_message(
                        messages,
                        include_context=False,
                        stream=stream,
                        on_content=chunks.append,
                        timeout=45,
                    )
                    assert marker in final["content"] and not final.get("tool_calls")
                    case.update(passed=True, actual_read=True, content_chunks=len(chunks))
        except Exception as error:
            case["error"] = error_details(error)
        print(json.dumps(case, ensure_ascii=False), flush=True)


def coding_workflow(report, key_env):
    import agent
    from config import approval_config, agent_config, context_config
    import permissions
    from tool_registry import TOOL_REGISTRY
    from workspace import use_workspace

    case = {"name": "real_model_multifile_tests", "passed": False}
    report["checks"].append(case)
    try:
        with tempfile.TemporaryDirectory(prefix="deepseek-workflow-") as directory:
            root = Path(directory)
            (root / "calc.py").write_text("def add(a, b):\n    return a - b\n")
            tests = "from calc import add\ndef test_add():\n    assert add(19, 23) == 42\n"
            (root / "test_calc.py").write_text(tests)
            approved = []

            def confirm(name, target, details=""):
                accepted = name in {"apply_changes", "edit_file", "create_file", "run_tests"}
                approved.append({"tool": name, "accepted": accepted})
                return accepted

            allowed = {
                "read_file",
                "list_files",
                "search_file",
                "search_project",
                "apply_changes",
                "edit_file",
                "create_file",
                "run_tests",
            }
            with (
                client_scope(report, key_env),
                use_workspace(root),
                contextlib.ExitStack() as stack,
            ):
                importlib.reload(agent)
                stack.enter_context(
                    patch.dict(
                        TOOL_REGISTRY,
                        {k: v for k, v in TOOL_REGISTRY.items() if k in allowed},
                        clear=True,
                    )
                )
                stack.enter_context(patch.dict(approval_config, mode="manual"))
                stack.enter_context(patch.dict(agent_config, max_rounds=8, max_tool_calls=12))
                stack.enter_context(patch.dict(context_config, auto_compact=False))
                stack.enter_context(patch.object(permissions, "confirm_tool", confirm))
                from tool_runtime import execute_tool

                before = execute_tool("run_tests", {"path": "test_calc.py"})
                assert before["ok"] is False and before.get("exit_code") == 1
                task = (
                    "请读取 calc.py 和 test_calc.py，修复 add 的加法错误。"
                    "使用 apply_changes 一次修复 calc.py 并新建 notes/change.md 说明改动。"
                    "禁止修改 test_calc.py。然后调用 run_tests 测试 test_calc.py。"
                    "只根据实际工具结果汇报，测试成功后结束。"
                )
                messages = [{"role": "user", "content": task}]
                agent.run_agent(messages)
                tool_results = [
                    {"name": m["tool_name"], "result": json.loads(m["content"])}
                    for m in messages
                    if m["role"] == "tool"
                ]
                assert (root / "test_calc.py").read_text() == tests
                assert any(r["name"] == "apply_changes" and r["result"]["ok"] for r in tool_results)
                assert (root / "notes/change.md").is_file()
                assert any(
                    r["name"] == "run_tests" and r["result"].get("exit_code") == 0
                    for r in tool_results
                )
                case.update(
                    passed=True,
                    baseline_exit_code=1,
                    fixed_test_exit_code=0,
                    original_tests_unchanged=True,
                    tool_names=[r["name"] for r in tool_results],
                    trusted_fixture_approvals=approved,
                )
    except Exception as error:
        case["error"] = error_details(error)
    print(json.dumps(case, ensure_ascii=False), flush=True)


def automatic_review(report, key_env):
    import permissions
    from approval import task_scope
    from config import approval_config
    from tool_runtime import execute_tool
    from workspace import use_workspace

    case = {"name": "independent_automatic_review", "passed": False}
    report["checks"].append(case)
    try:
        with tempfile.TemporaryDirectory(prefix="deepseek-review-") as directory:
            root = Path(directory)
            (root / "calc.py").write_text("def add(a, b):\n    return a - b\n")
            with (
                client_scope(report, key_env),
                use_workspace(root),
                task_scope("修复 calc.py 的 add 函数，使它返回两个参数的和。"),
                patch.dict(approval_config, mode="auto"),
                patch.object(permissions, "confirm_tool", return_value=False) as manual,
            ):
                result = execute_tool(
                    "edit_file",
                    {"path": "calc.py", "new_content": "def add(a, b):\n    return a + b\n"},
                )
                decisions = result.get("approval", [])
                assert result["ok"] and any(
                    d.get("method") == "reviewer" and d.get("decision") == "allow"
                    for d in decisions
                )
                assert not manual.called
                case.update(passed=True, reviewer_decision="allow", manual_fallback_used=False)
    except Exception as error:
        case["error"] = error_details(error)
    print(json.dumps(case, ensure_ascii=False), flush=True)


def interactive_pty(report, key_env):
    import agent
    import permissions
    from config import approval_config, context_config
    from harness.tasks.runtime import close_tasks
    from tool_registry import TOOL_REGISTRY
    from workspace import use_workspace

    case = {"name": "model_interactive_pty", "passed": False}
    report["checks"].append(case)
    try:
        with tempfile.TemporaryDirectory(prefix="deepseek-pty-") as directory:
            allowed = {
                "start_pty",
                "task_status",
                "task_wait",
                "task_input",
                "task_cancel",
                "list_tasks",
            }
            with (
                client_scope(report, key_env),
                use_workspace(directory),
                patch.dict(
                    TOOL_REGISTRY,
                    {k: v for k, v in TOOL_REGISTRY.items() if k in allowed},
                    clear=True,
                ),
                patch.dict(approval_config, mode="manual"),
                patch.dict(context_config, auto_compact=False),
                patch.object(permissions, "confirm_tool", return_value=True) as approvals,
            ):
                importlib.reload(agent)
                messages = [
                    {
                        "role": "user",
                        "content": "请亲自使用 start_pty 启动 python -u -c \"print('READY',flush=True); print('ECHO:'+input(),flush=True)\"。"
                        "然后用 task_input 输入 DEEPSEEK_PTY_OK 加换行，调用 task_wait 等待退出。"
                        "必须实际使用终端工具，最后依据输出与退出码汇报。",
                    }
                ]
                try:
                    agent.run_agent(messages)
                    results = [
                        {"name": m["tool_name"], "value": json.loads(m["content"])}
                        for m in messages
                        if m["role"] == "tool"
                    ]
                    assert any(r["name"] == "task_input" and r["value"]["ok"] for r in results)
                    assert any(
                        r["value"].get("exit_code") == 0
                        and "ECHO:DEEPSEEK_PTY_OK" in r["value"].get("output", "")
                        for r in results
                    )
                    case.update(
                        passed=True,
                        tool_names=[r["name"] for r in results],
                        startup_approval_count=approvals.call_count,
                        exit_code=0,
                    )
                finally:
                    close_tasks()
    except Exception as error:
        case["error"] = error_details(error)
    print(json.dumps(case, ensure_ascii=False), flush=True)


def writable_child(report, key_env):
    import permissions
    from approval import task_scope
    from config import model_config, approval_config, agent_config
    from harness.tasks.runtime import inspect_task, resolve_task_approval, close_tasks
    from tool_runtime import execute_tool
    from workspace import use_workspace

    case = {"name": "real_writable_subagent", "passed": False, "usage": None}
    report["checks"].append(case)
    try:
        with tempfile.TemporaryDirectory(prefix="deepseek-child-") as directory:
            root = Path(directory)
            (root / "child_note.txt").write_text("before\n")
            with (
                use_workspace(root),
                task_scope("让子代理修正 child_note.txt"),
                patch.dict(
                    model_config,
                    provider="openai",
                    model=report["model"],
                    base_url=BASE,
                    api_key_env=key_env,
                ),
                patch.dict(approval_config, mode="manual"),
                patch.dict(agent_config, max_rounds=4, max_tool_calls=4),
                patch.object(permissions, "confirm_tool", return_value=True),
            ):
                try:
                    started = execute_tool(
                        "spawn_agent",
                        {
                            "task": "先读取 child_note.txt，再使用 edit_file 把完整内容改为 DEEPSEEK_CHILD_OK 加换行，然后结束。"
                            "不要修改其他文件，不运行测试或终端。"
                        },
                    )
                    assert started["ok"]
                    task_id = started["task_id"]
                    deadline, decisions = time.monotonic() + 90, 0
                    while time.monotonic() < deadline:
                        state = inspect_task(task_id)
                        for approval in state.get("pending_approvals", []):
                            allow = (
                                approval["action"] == "edit_file"
                                and Path(approval["target"]) == root / "child_note.txt"
                            )
                            result = resolve_task_approval(task_id, approval["id"], allow)
                            assert result["ok"]
                            decisions += 1
                        if state.get("state") == "finished":
                            break
                        time.sleep(0.2)
                    assert (
                        state.get("state") == "finished"
                        and (root / "child_note.txt").read_text() == "DEEPSEEK_CHILD_OK\n"
                    )
                    case.update(
                        passed=True, independent_task_approvals=decisions, actual_file_changed=True
                    )
                finally:
                    close_tasks()
    except Exception as error:
        case["error"] = error_details(error)
    print(json.dumps(case, ensure_ascii=False), flush=True)


def web_roundtrip(report, key_env):
    from fastapi.testclient import TestClient
    from web.app import create_app
    from web.settings import Settings

    case = {"name": "real_web_worker_session", "passed": False, "usage": None}
    report["checks"].append(case)
    try:
        with tempfile.TemporaryDirectory(prefix="deepseek-web-") as directory:
            root = Path(directory)
            marker = "WEB_DEEPSEEK_LIVE_4297"
            (root / "marker.txt").write_text(marker + "\n")
            settings = Settings(
                root / ".ai-cli/web",
                root,
                model=report["model"],
                base_url=BASE,
                api_key_env=key_env,
                stream=True,
            )
            app = create_app(settings)
            with TestClient(app) as client:
                session = client.post(
                    "/api/sessions", json={"title": "live", "workspace": str(root)}
                ).json()
                response = client.post(
                    f"/api/sessions/{session['id']}/runs",
                    json={
                        "message": "请使用 read_file 读取 marker.txt，并只原样返回文件内容；不要调用其他工具。"
                    },
                )
                assert response.status_code == 202
                identifier = response.json()["id"]
                deadline = time.monotonic() + 90
                while time.monotonic() < deadline:
                    state = app.state.store.get_run(identifier)
                    if state["status"] in {"succeeded", "failed", "cancelled", "interrupted"}:
                        break
                    time.sleep(0.2)
                assert state["status"] == "succeeded" and marker in state["answer"]
                messages = app.state.store.messages(session["id"])
                assert any(m["role"] == "tool" and m["tool_name"] == "read_file" for m in messages)
                assert any(m["role"] == "assistant" and "reasoning_content" in m for m in messages)
                case.update(
                    passed=True,
                    persisted_tool_result=True,
                    protocol_metadata_persisted=True,
                    final_answer_contains_file_marker=True,
                )
    except Exception as error:
        case["error"] = error_details(error)
    print(json.dumps(case, ensure_ascii=False), flush=True)


def workflow(report, key_env):
    cases = [
        ("real_model_multifile_tests", coding_workflow),
        ("independent_automatic_review", automatic_review),
        ("model_interactive_pty", interactive_pty),
        ("real_writable_subagent", writable_child),
        ("real_web_worker_session", web_roundtrip),
    ]
    for name, run in cases:
        latest = next((c for c in reversed(report["checks"]) if c["name"] == name), None)
        if latest and latest["passed"]:
            continue
        run(report, key_env)
        save(report)


def save(report):
    report["summary"] = summarize_report(report)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="明确允许 DeepSeek 官方请求")
    parser.add_argument("--interactive", action="store_true", help="逐阶段执行，凭据只读一次")
    parser.add_argument("--model", default="deepseek-flash")
    args = parser.parse_args(argv)
    if not args.live:
        parser.error("需要 --live 显式开启真实 API 联测")
    if args.model not in {"deepseek-flash", "deepseek-v4-pro"}:
        parser.error("此联测入口仅接受当前 DeepSeek 官方模型")
    key_env = "DEEPSEEK_API_KEY"
    provided = key_env in os.environ
    if not provided:
        if not sys.stdin.isatty():
            parser.error("非交互环境需要预先设置 DEEPSEEK_API_KEY，不能回退到明文输入")
        os.environ[key_env] = getpass.getpass("DeepSeek credential (hidden): ")
    if not os.environ[key_env].strip():
        if not provided:
            os.environ.pop(key_env, None)
        parser.error("DEEPSEEK_API_KEY 不能为空")
    report = {
        "provider": "deepseek-official",
        "model": args.model,
        "base_url": BASE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "real_model_called": False,
        "requests": [],
        "checks": [],
    }
    try:
        if args.interactive:
            import live_api_acceptance as suite

            while True:
                print("COMMAND protocol/workflow/quit:", flush=True)
                command = input().strip()
                if command == "quit":
                    break
                if command not in {"protocol", "workflow"}:
                    continue
                importlib.reload(suite)
                getattr(suite, command)(report, key_env)
                save(report)
        else:
            protocol(report, key_env)
            if all(c["passed"] for c in report["checks"]):
                workflow(report, key_env)
    finally:
        if not provided:
            os.environ.pop(key_env, None)
        save(report)
    return 0 if report["summary"]["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
