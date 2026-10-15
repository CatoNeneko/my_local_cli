"""固定示例历史的真实模型摘要、恢复与自动触发验证；不会调用文件修改工具。"""

import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from compaction import compact_messages, context_view
from config import context_config
import history
from model_client import request_message
from sessions import SessionManager
from workspace import use_workspace

MARKER = "COMPACT_CEDAR_739"


def seed():
    result = []
    for number in range(5):
        text = (
            "项目记忆暗号是 " + MARKER + "。用户要求始终不能修改 test_calc.py。"
            if number == 0
            else f"继续讨论项目第 {number} 阶段；暂不执行操作。"
        )
        result.extend(
            [{"role": "user", "content": text}, {"role": "assistant", "content": "已记录讨论。"}]
        )
    return result


def ask(messages):
    question = {
        "role": "user",
        "content": "只用一句话回答：最早的项目记忆暗号是什么，用户要求不能修改哪个文件？不要调用工具。",
    }
    history.append_message(question)
    messages.append(question)
    reply = request_message(messages)
    if reply.get("tool_calls"):
        raise ValueError("验证要求仅返回回答，不能调用工具")
    history.append_message({"role": "assistant", "content": reply["content"]})
    messages.append({"role": "assistant", "content": reply["content"]})
    return reply["content"]


def main():
    workspace = Path(tempfile.mkdtemp(prefix="cli-compaction-acceptance-"))
    checks, replies = {}, {}
    with use_workspace(workspace):
        manager = SessionManager()
        manager.switch("manual")
        messages = seed()
        history.append_messages(messages)
        original_bytes = history.HISTORY_PATH.read_bytes()
        result = compact_messages(messages)
        checks["manual_saved"] = result["ok"] and result["changed"]
        checks["raw_history_preserved"] = history.HISTORY_PATH.read_bytes().startswith(
            original_bytes
        )
        replies["manual"] = ask(messages)
        checks["manual_recalls_old_fact"] = (
            MARKER in replies["manual"] and "test_calc.py" in replies["manual"]
        )
        assert manager.rename("renamed")["ok"]
    with use_workspace(workspace):
        restarted = SessionManager()
        restored = restarted.switch("renamed")["messages"]
        checks["restart_summary_restored"] = bool(context_view(restored)["summary"])
        replies["restart"] = ask(restored)
        checks["restart_recalls_old_fact"] = (
            MARKER in replies["restart"] and "test_calc.py" in replies["restart"]
        )
        assert restarted.switch("automatic")["ok"]
        messages = seed()
        history.append_messages(messages)
        context_config["auto_compact"] = True
        context_config["max_history_turns"] = 3
        replies["automatic"] = ask(messages)
        checks["automatic_saved"] = bool(context_view(messages)["summary"])
        checks["automatic_recalls_old_fact"] = (
            MARKER in replies["automatic"] and "test_calc.py" in replies["automatic"]
        )
    report = {
        "workspace": str(workspace),
        "checks": checks,
        "replies": replies,
        "note": "原历史由固定示例构造；摘要及后续回答由真实模型生成。",
    }
    path = ROOT / "artifacts/compaction/real_acceptance.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
