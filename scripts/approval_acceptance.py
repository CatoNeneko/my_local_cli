import sys
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import approval_config
from workspace import use_workspace
from approval import task_scope
from tool_runtime import execute_tool
from harness.tasks.runtime import close_tasks
import permissions

approval_config["mode"] = "auto"
permissions.confirm_tool = lambda *args: (_ for _ in ()).throw(
    RuntimeError("本次验证不允许人工确认")
)
root = Path(tempfile.mkdtemp(prefix="cli-approval-acceptance-"))
(root / "calc.py").write_text("def add(a, b):\n    return a - b\n")
(root / "test_calc.py").write_text(
    "from calc import add\ndef test_add():\n    assert add(19, 23) == 42\n"
)
report = {"workspace": str(root), "checks": {}}
try:
    with (
        use_workspace(root),
        task_scope("修复 calc.py 中 add 的加法错误；保持 test_calc.py 不变。"),
    ):
        before = execute_tool("run_tests", {"path": "."})
        report["checks"]["baseline_failed"] = not before["ok"] and "1 failed" in before["output"]
        launched = execute_tool(
            "spawn_agent",
            {
                "task": "读取 calc.py 和 test_calc.py，修复 add 的加法错误。你不能写入，必须调用 propose_edit 提出完整 calc.py 修改建议，最后简短说明。"
            },
        )
        report["launch"] = launched
        for _ in range(6):
            done = execute_tool("task_wait", {"task_id": launched["task_id"], "seconds": 30})
            if done["state"] == "finished":
                break
        report["child"] = done.get("agent_result")
        proposals = done.get("agent_result", {}).get("proposals", [])
        if proposals:
            applied = execute_tool(
                "apply_agent_proposal",
                {"task_id": launched["task_id"], "proposal_id": proposals[0]["proposal_id"]},
            )
            report["application"] = applied
            report["checks"]["independent_auto_review"] = applied["ok"] and any(
                item["method"] == "reviewer" and item["decision"] == "allow"
                for item in applied["result"].get("approval", [])
            )
        else:
            report["checks"]["independent_auto_review"] = False
        after = execute_tool("run_tests", {"path": "."})
        report["checks"]["tests_passed"] = after["ok"] and "1 passed" in after["output"]
        report["checks"]["fixed_test_unchanged"] = (
            root / "test_calc.py"
        ).read_text() == "from calc import add\ndef test_add():\n    assert add(19, 23) == 42\n"
        report["checks"]["source_fixed"] = "return a + b" in (root / "calc.py").read_text()
finally:
    close_tasks()
    destination = ROOT / "artifacts/approval/real_acceptance.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report, ensure_ascii=False, indent=2))
if not all(report["checks"].values()):
    raise SystemExit(1)
