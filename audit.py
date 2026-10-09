import json
from pathlib import Path
from datetime import datetime, timezone


LOG_PATH = Path(__file__).resolve().parent / "tool_events.jsonl"


def record_tool_event(name, result):
    event = {
        "time": datetime.now(timezone.utc).isoformat(),
        "tool": name,
        "ok": result["ok"],
        "error": result.get("error", "")
    }
    if "approval" in result:
        event["approval"] = result["approval"]
    if "hook_warning" in result:
        event["hook_warning"] = result["hook_warning"]
    if result.get('cancelled'):
        event['cancelled'] = True

    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as file:
            file.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError as error:
        print("工具日志写入失败:", error)
