"""构造有界请求上下文；磁盘历史不裁剪，工具链按用户轮次保留。"""
import json

from config import context_config, model_config
from project_instructions import build_model_messages


class ContextBudgetError(ValueError):
    pass


def valid_turn(turn):
    pending = []
    for message in turn:
        role = message.get("role")
        if role == "assistant":
            if pending:
                return False
            calls = message.get("tool_calls", [])
            if not isinstance(calls, list):
                return False
            for call in calls:
                if not isinstance(call, dict) or not isinstance(call.get("function"), dict):
                    return False
                name = call["function"].get("name")
                if not isinstance(name, str) or not name:
                    return False
                pending.append(name)
        elif role == "tool":
            if not pending or message.get("tool_name") != pending.pop(0):
                return False
        elif role != "user":
            return False
    return not pending


def split_turns(messages):
    turns = []
    for message in messages:
        if not isinstance(message, dict):
            raise ContextBudgetError("聊天消息格式无效")
        if message.get("role") == "user":
            turns.append([message])
        elif turns:
            turns[-1].append(message)
        # 没有对应用户轮次的开头残留消息不发送，避免孤立工具结果。
    return turns


def request_size(messages, tools):
    if model_config.get("provider") == "openai":
        from api_adapter import wire_messages
        messages = wire_messages(messages)
    return len(json.dumps({
        "model": model_config["model"], "messages": messages,
        "stream": False, "tools": tools
    }, ensure_ascii=False))


def prepare_context(messages, tools, include_context=True):
    budget = context_config.get("max_request_chars")
    turn_limit = context_config.get("max_history_turns")
    if type(budget) is not int or budget <= 0 or type(turn_limit) is not int or turn_limit <= 0:
        raise ContextBudgetError("上下文预算必须是正整数")
    from compaction import context_view, summary_message
    view = context_view(messages) if include_context else {'messages': messages, 'summary': '', 'covered': 0}
    messages = view['messages']
    prefix = build_model_messages([]) if include_context else []
    if view['summary']:
        prefix.append(summary_message(view['summary']))
    start = 0
    # Skill 生成请求带有自己的 system 提示，也始终保留。
    while start < len(messages) and isinstance(messages[start], dict) and messages[start].get("role") == "system":
        prefix.append(messages[start])
        start += 1
    turns = split_turns(messages[start:])
    if request_size(prefix, tools) > budget:
        raise ContextBudgetError("系统规则、Skills 和工具声明已超预算，请减少规则或工具")
    selected = []
    kept = 0
    for index in range(len(turns) - 1, -1, -1):
        turn = turns[index]
        if not valid_turn(turn):
            if index == len(turns) - 1:
                raise ContextBudgetError("最新一轮工具调用与结果不完整，请检查或清空当前会话")
            continue
        candidate = turn + selected
        if request_size(prefix + candidate, tools) > budget:
            if not selected:
                raise ContextBudgetError("最新一轮消息超预算，请缩小附件、工具结果或输入，或调整上下文预算")
            break
        selected = candidate
        kept += 1
        if kept >= turn_limit:
            break
    final = prefix + selected
    return {
        "messages": final, "chars": request_size(final, tools), "budget": budget,
        "total_turns": len(turns), "sent_turns": kept,
        "summarized_messages": view["covered"], "summary_chars": len(view["summary"]),
        "omitted_messages": len(messages) - start - len(selected)
    }
