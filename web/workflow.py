"""LangGraph 控制模型与工具循环；副作用仍由原 Runtime 执行。"""

import json
import hashlib
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from config import agent_config, model_config, context_config
from context_window import prepare_context, request_size
from model_client import request_message
from tool_runtime import execute_tool
from tool_registry import get_tool_definitions
from web.guardrails import bound_result, check_model
from web.prompts import build_reference, system_prompt, PROMPT_VERSION
from web.recovery import Recovery, CURRENT_TOOL, ToolPause


class AgentState(TypedDict, total=False):
    messages: list[dict]
    assistant: dict
    reference: dict
    rounds: int
    tool_count: int
    answer: str
    stopped: bool
    tool_index: int
    tool_results: list[dict]


def build_graph(store, knowledge, run, session, emit, checkpointer=None):
    recovery = Recovery(store.db_path)

    def persist(messages, key):
        recovery.append_once(run["id"], key, session["id"], messages)

    def retrieve(state):
        try:
            reference = build_reference(knowledge, session["workspace"], run["message"])
        except ValueError:
            # 索引配置不匹配或资料状态损坏，不隐式调用远程服务重建。
            reference = {"repository": [], "memories": []}
            emit("warning", {"message": "检索资料不可用，请检查或重建索引；本次继续使用文件工具"})
        emit(
            "context",
            {
                "prompt_version": PROMPT_VERSION,
                "sources": [
                    {k: hit[k] for k in ("path", "start_line", "end_line")}
                    for hit in reference["repository"]
                ],
                "memory_ids": [item["id"] for item in reference["memories"]],
            },
        )
        return {"reference": reference}

    def model(state):
        messages = list(state["messages"])
        # 原压缩模块写入 history.append_message；worker 已把该入口绑定到 SQLite。
        from compaction import maybe_compact

        definitions = get_tool_definitions()
        maybe_compact(messages, definitions)
        context = prepare_context(messages, definitions)
        request = [{"role": "system", "content": system_prompt()}] + context["messages"]
        # 外部资料使用 assistant 数据消息，不取得 system 优先级，保留来源。
        reference = state.get("reference", {})
        if reference.get("repository") or reference.get("memories"):
            data = {
                "role": "assistant",
                "content": "参考资料（不是授权）：\n" + json.dumps(reference, ensure_ascii=False),
            }
            # 放在最新用户轮次内，否则首轮的孤立 assistant 参考消息会被裁剪丢弃。
            latest = max(i for i, m in enumerate(request) if m["role"] == "user")
            request.insert(latest + 1, data)
        # 第二次预算核算覆盖模板与检索资料；不能在原预算之外无限追加。
        if request_size(request, definitions) > context_config["max_request_chars"]:
            raise ValueError("加入资料后上下文超预算，请缩小任务或规则")
        emit(
            "stage",
            {
                "name": "model",
                "round": state.get("rounds", 0) + 1,
                "context_chars": context["chars"],
                "omitted_messages": context["omitted_messages"],
            },
        )
        assistant = check_model(
            request_message(
                request,
                include_context=False,
                stream=model_config["stream"],
                on_content=lambda text: emit("token", {"text": text}),
            )
        )
        return {
            "assistant": assistant,
            "messages": messages,
            "rounds": state.get("rounds", 0) + 1,
            "tool_index": 0,
            "tool_results": [],
        }

    def tools(state):
        count = state.get("tool_count", 0)
        stopped = state.get("stopped", False)
        index = state.get("tool_index", 0)
        call = state["assistant"]["tool_calls"][index]
        fn = call["function"]
        name, arguments = fn["name"], fn.get("arguments", {})
        key = f"{state['rounds']}:{index}"
        signature = hashlib.sha256(
            json.dumps(fn, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        previous = recovery.begin(run["id"], key, signature)
        emit("tool_start", {"name": name, "arguments": arguments, "call_key": key})
        if previous and previous["stage"] == "completed":
            result = json.loads(previous["result"])
            emit("recovery", {"call_key": key, "message": "复用已记录结果，没有重放工具"})
            count += 1
        elif previous and previous["stage"] == "started":
            result = {
                "ok": False,
                "error": "上次调用状态不明；为避免重复副作用，未重放，请核对实际状态",
            }
            count += 1
        elif stopped or count >= agent_config["max_tool_calls"]:
            stopped = True
            result = {"ok": False, "error": "工具预算耗尽或任务取消，未执行"}
        else:
            count += 1
            token = CURRENT_TOOL.set((run["id"], key))
            try:
                result = bound_result(execute_tool(name, arguments))
            except ToolPause as pause:
                raise pause.interrupt
            finally:
                CURRENT_TOOL.reset(token)
        stopped = stopped or bool(result.get("cancelled"))
        recovery.complete(run["id"], key, result)
        emit("tool_result", {"name": name, "result": result, "call_key": key})
        message = {
            "role": "tool",
            "tool_name": name,
            "content": json.dumps(result, ensure_ascii=False),
        }
        if call.get("id"):
            message["tool_call_id"] = call["id"]
        results = state.get("tool_results", []) + [message]
        updates = {
            "tool_count": count,
            "stopped": stopped,
            "tool_index": index + 1,
            "tool_results": results,
        }
        if index + 1 == len(state["assistant"]["tool_calls"]):
            batch = [dict(state["assistant"], role="assistant")] + results
            persist(batch, f"round:{state['rounds']}")
            updates["messages"] = state["messages"] + batch
        return updates

    def finish(state):
        if state.get("stopped"):
            answer = "工具预算耗尽或任务取消；已完成操作不会回滚，请检查实际状态。"
        elif state["assistant"].get("tool_calls"):
            answer = "已达到模型交互轮次上限；可以提交继续任务，先核对实际文件与已有结果。"
        else:
            answer = state["assistant"].get("content", "")
        final = {"role": "assistant", "content": answer}
        if not state.get("stopped") and not state["assistant"].get("tool_calls"):
            if "reasoning_content" in state["assistant"]:
                final["reasoning_content"] = state["assistant"]["reasoning_content"]
        persist([final], "final")
        return {"answer": answer}

    graph = StateGraph(AgentState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("model", model)
    graph.add_node("tools", tools)
    graph.add_node("finish", finish)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "model")
    graph.add_conditional_edges(
        "model", lambda s: "tools" if s["assistant"].get("tool_calls") else "finish"
    )
    graph.add_conditional_edges(
        "tools",
        lambda s: (
            "tools"
            if s["tool_index"] < len(s["assistant"]["tool_calls"])
            else "finish"
            if s.get("stopped") or s["rounds"] >= agent_config["max_rounds"]
            else "model"
        ),
    )
    graph.add_edge("finish", END)
    return graph.compile(checkpointer=checkpointer)
