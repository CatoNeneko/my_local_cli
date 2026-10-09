import json

from config import agent_config, model_config
from history import append_messages
from model_client import request_message
from tools import execute_tool
from context_window import ContextBudgetError


def run_agent(messages, output=None):
    from approval import task_scope
    task = next((message.get('content', '') for message in reversed(messages) if message.get('role') == 'user'), '')
    with task_scope(task):
        return _run_agent(messages, output)


def _run_agent(messages, output=None):
    tool_count = 0
    max_tool_calls = agent_config["max_tool_calls"]
    for round_number in range(agent_config["max_rounds"]):
        try:
            if output is None:
                assistant_message = request_message(messages)
            else:
                output.begin()
                try:
                    assistant_message = request_message(
                        messages, stream=model_config['stream'], on_content=output.write
                    )
                finally:
                    output.end()
        except ContextBudgetError as error:
            return "上下文请求已停止：" + str(error)
        except KeyboardInterrupt:
            return "已取消当前模型生成；此前完成的工具操作不会回滚。"
        if not isinstance(assistant_message, dict):
            return "模型返回格式错误：消息必须是字典。"

        content = assistant_message.get("content", "")
        if not isinstance(content, str):
            return "模型返回格式错误：content 必须是字符串。"
        tool_calls = assistant_message.get("tool_calls", [])
        if not isinstance(tool_calls, list):
            return "模型返回格式错误：tool_calls 必须是列表。"
        if not tool_calls:
            # 最终文字回复仍由主循环保存，避免重复记录。
            return content

        # 先验证整批结构，防止执行到一半才发现无法识别的调用。
        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                return "模型返回格式错误：单条工具调用必须是字典。"
            function = tool_call.get("function")
            if not isinstance(function, dict):
                return "模型返回格式错误：缺少有效的 function。"
            name = function.get("name")
            if not isinstance(name, str) or not name:
                return "模型返回格式错误：工具名称必须是非空字符串。"

        assistant_message = dict(assistant_message)
        assistant_message["role"] = "assistant"
        assistant_message["content"] = content
        round_messages = [assistant_message]
        budget_exhausted = False
        cancelled = False

        for tool_call in tool_calls:
            function = tool_call["function"]
            name = function["name"]
            arguments = function.get("arguments", {})
            if cancelled:
                result = {'ok': False, 'cancelled': True, 'error': '任务已取消，工具未执行'}
            elif tool_count >= max_tool_calls:
                # 不执行超预算调用，但补齐结果，使保存的消息链完整。
                budget_exhausted = True
                result = {"ok": False, "error": "调用预算耗尽，工具未执行"}
            else:
                tool_count += 1
                try:
                    result = execute_tool(name, arguments)
                except KeyboardInterrupt:
                    result = {'ok': False, 'cancelled': True, 'error': '工具已取消；已完成操作不会回滚'}
                cancelled = bool(result.get('cancelled'))

            tool_message = {
                "role": "tool",
                "tool_name": name,
                "content": json.dumps(result, ensure_ascii=False)
            }
            if tool_call.get("id"):
                tool_message["tool_call_id"] = tool_call["id"]
            round_messages.append(tool_message)

        append_messages(round_messages)
        messages.extend(round_messages)
        if cancelled:
            return '已取消当前任务并返回输入；已完成的操作不会回滚，请检查写入或外部操作的实际状态。'
        if budget_exhausted:
            return "已达到工具调用总次数上限，请缩小任务范围。"

    return "已达到工具调用轮次上限，请缩小任务范围。"
