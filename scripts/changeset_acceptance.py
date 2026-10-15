"""固定协议夹具驱动真实 Web worker，验证批量 diff 审批和沙箱测试。"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from web.app import create_app
from web.settings import Settings


class ModelFixture(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        results = [
            json.loads(item["content"]) for item in body["messages"] if item["role"] == "tool"
        ]
        calls = [
            ("read_file", {"path": "calc.py"}),
            (
                "apply_changes",
                {
                    "changes": [
                        {
                            "path": "calc.py",
                            "edits": [{"old_text": "return a - b", "new_text": "return a + b"}],
                        },
                        {"path": "notes/change.md", "content": "修复加法；原测试不变。\n"},
                    ]
                },
            ),
            ("run_tests", {"path": "test_calc.py"}),
        ]
        message = {"content": "按真实工具结果验收。"}
        reason = "stop"
        if len(results) < len(calls):
            name, arguments = calls[len(results)]
            message = {
                "content": "",
                "tool_calls": [
                    {
                        "id": f"batch-{len(results)}",
                        "type": "function",
                        "function": {
                            "name": name,
                            "arguments": json.dumps(arguments, ensure_ascii=False),
                        },
                    }
                ],
            }
            reason = "tool_calls"
        raw = json.dumps({"choices": [{"message": message, "finish_reason": reason}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *_args):
        pass


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), ModelFixture)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    key_name = "CHANGESET_FIXTURE_KEY"
    previous = os.environ.get(key_name)
    os.environ[key_name] = "offline-fixture-only"
    try:
        with tempfile.TemporaryDirectory(prefix="cli-batch-") as temporary:
            root = Path(temporary)
            (root / "calc.py").write_text("def add(a, b):\n    return a - b\n")
            tests = "from calc import add\ndef test_add():\n    assert add(19, 23) == 42\n"
            (root / "test_calc.py").write_text(tests)
            settings = Settings(
                root / ".ai-cli/web",
                root,
                model="fixture",
                base_url=f"http://127.0.0.1:{server.server_port}/v1",
                api_key_env=key_name,
                stream=False,
            )
            app = create_app(settings)
            approvals = []
            with TestClient(app) as client:
                session = client.post(
                    "/api/sessions", json={"title": "batch", "workspace": str(root)}
                ).json()
                response = client.post(
                    f"/api/sessions/{session['id']}/runs",
                    json={"message": "修复加法，新增变更说明，保持测试不变并验证。"},
                )
                assert response.status_code == 202, response.text
                identifier = response.json()["id"]
                deadline = time.monotonic() + 60
                while time.monotonic() < deadline:
                    state = app.state.store.get_run(identifier)
                    for approval in app.state.store.pending_approvals(identifier):
                        if approval["id"] in approvals:
                            continue
                        if "apply_changes" in approval["action"]:
                            assert (
                                "calc.py" in approval["diff"]
                                and "notes/change.md" in approval["diff"]
                            )
                            assert "return a - b" in (root / "calc.py").read_text()
                            assert not (root / "notes/change.md").exists()
                        approvals.append(approval["id"])
                        decision = client.post(
                            f"/api/approvals/{approval['id']}", json={"allow": True}
                        )
                        assert decision.status_code == 200, decision.text
                    if state["status"] in ("succeeded", "failed", "cancelled", "interrupted"):
                        break
                    time.sleep(0.1)
                assert state["status"] == "succeeded", state
                messages = app.state.store.messages(session["id"])
                outcomes = [
                    json.loads(item["content"]) for item in messages if item["role"] == "tool"
                ]
                assert len(approvals) == 2 and all(item["ok"] for item in outcomes), outcomes
                assert outcomes[-1]["exit_code"] == 0
                assert (root / "test_calc.py").read_text() == tests
                assert "return a + b" in (root / "calc.py").read_text()
                assert (root / "notes/change.md").is_file()
                report = {
                    "fixture_only": True,
                    "real_model_called": False,
                    "batch_approval_before_both_writes": True,
                    "related_files_changed": 2,
                    "original_tests_unchanged": True,
                    "test_exit_code": outcomes[-1]["exit_code"],
                    "approved_tool_calls": len(approvals),
                    "status": state["status"],
                }
                output = ROOT / "artifacts/upgrade/changeset.json"
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
                print(json.dumps(report, ensure_ascii=False))
    finally:
        if previous is None:
            os.environ.pop(key_name, None)
        else:
            os.environ[key_name] = previous
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == "__main__":
    main()
