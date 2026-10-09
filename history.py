import json
from pathlib import Path


HISTORY_PATH = Path(__file__).resolve().parent / "history.jsonl"


def clear_history():
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as file:
        pass


def append_messages(messages):
    # 先序列化完整的一轮，成功后再追加；不在模型请求阶段写半条调用。
    text = "".join(json.dumps(message, ensure_ascii=False) + "\n" for message in messages)
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_PATH, "a", encoding="utf-8") as file:
        file.write(text)


def append_message(message):
    append_messages([message])


def load_history(path=None):
    messages = []
    try:
        with open(HISTORY_PATH if path is None else path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    print("跳过一条损坏的记录")
                    continue
                if not isinstance(message, dict):
                    print("跳过一条不是字典的记录")
                    continue
                if "role" not in message or "content" not in message:
                    print("跳过一条缺少字段的记录")
                    continue
                if not isinstance(message["content"], str):
                    print("跳过一条非文字记录")
                    continue
                if message["role"] not in ("user", "assistant", "tool"):
                    print("跳过一条身份非法记录")
                    continue
                if message["role"] == "tool":
                    if not isinstance(message.get("tool_name"), str) or not message["tool_name"]:
                        print("跳过一条缺少工具名称的记录")
                        continue
                if "tool_calls" in message:
                    if message["role"] != "assistant" or not isinstance(message["tool_calls"], list):
                        print("跳过一条工具调用格式错误的记录")
                        continue
                messages.append(message)
    except FileNotFoundError:
        pass
    return messages
