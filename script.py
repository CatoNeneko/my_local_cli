import json
import shlex
import urllib.error
from tools import search_file, search_project
from tool_registry import get_tool_definitions
from tools import read_file
from config import model_config
from agent import run_agent
from history import clear_history, load_history, append_message
from mcp_manager import MCPManager
from config import mcp_config
from project_instructions import load_project_instructions, instruction_state
from skills import activate_skill, clear_skills, list_skills
from skill_generation import generate_skill
from sessions import SessionManager
from context_window import ContextBudgetError, prepare_context
from console_output import ConsoleOutput
from streaming import ModelResponseError
from command_help import show_help
from terminal_input import TerminalInput
from path_input import parse_path_arguments
from contextlib import nullcontext
from attachments import prepare_attachments
from tool_display import safe_text


def show_history(messages):
    if not messages:
        print("there's no messages")
    else:
        for message in messages:
            print(message["role"] + ": " + message["content"])


def attach_files(paths, messages):
    result = prepare_attachments(paths)
    if not result["ok"]:
        print(safe_text(result["error"]))
        return
    append_message(result["message"])
    messages.append(result["message"])
    print("已添加附件:", safe_text(", ".join(result["paths"])))


def main(*, initial_session=None, plain=False, no_mcp=False, workspace=None):
    from workspace import use_workspace

    context = use_workspace(workspace) if workspace is not None else nullcontext()
    with context:
        from harness.tasks.runtime import close_tasks

        try:
            return _main(initial_session=initial_session, plain=plain, no_mcp=no_mcp)
        finally:
            close_tasks()


def _main(*, initial_session=None, plain=False, no_mcp=False):
    clear_skills()
    session_manager = SessionManager()
    initial_messages = None
    if initial_session:
        result = session_manager.switch(initial_session)
        if not result["ok"]:
            raise ValueError(result["error"])
        initial_messages = result["messages"]
    terminal = TerminalInput(plain=plain)
    print("Local AI CLI | 直接描述任务，/help 查看命令")
    from permissions import PROJECT_ROOT

    print("工作目录:", PROJECT_ROOT)
    from config import approval_config

    print("审批模式:", approval_config["mode"])
    if terminal.session is not None:
        print("Enter 发送 | Alt+Enter 换行 | Tab 补全")
    instruction_result = load_project_instructions()
    print(instruction_result["message"])
    with terminal.confirmations(), MCPManager() as mcp_manager:
        for name, result in ({} if no_mcp else mcp_manager.load_configured()).items():
            if result["ok"]:
                print("MCP 已加载:", name)
            else:
                print("MCP 加载失败:", name, result["error"])
        messages = load_history() if initial_messages is None else initial_messages

        while True:
            user_text = terminal.read(session_manager.current_name).strip()

            if user_text in ("/files", "/browse"):
                if user_text == "/files":
                    selected = terminal.pick_files()
                else:
                    path = terminal.pick_file()
                    selected = [path] if path is not None else None
                if selected:
                    attach_files(selected, messages)
                continue

            path_arguments = None
            command, separator, argument = user_text.partition(" ")
            if command in ("/read", "/attach", "/search", "/grep"):
                try:
                    path_arguments = parse_path_arguments(argument)
                    if command in ("/read", "/attach") and path_arguments[1]:
                        raise ValueError("路径含空格时请使用引号；此命令只接受一个路径")
                except ValueError as error:
                    print(error)
                    continue

            if user_text == "/exit":
                break

            if user_text == "":
                continue

            if user_text == "/help":
                show_help()
                continue

            if user_text == "/history":
                show_history(messages)
                continue

            if user_text == "/clear":
                clear_history()
                messages.clear()
                print("assistant: messages cleared")
                continue

            if user_text == "/save":
                result = session_manager.export(messages)
                print("已导出: " + result["path"] if result["ok"] else result["error"])
                continue

            if user_text == "/sessions":
                result = session_manager.list_sessions()
                if not result["ok"]:
                    print(result["error"])
                else:
                    for name in result["names"]:
                        marker = " (当前)" if name == session_manager.current_name else ""
                        print(name + marker)
                continue

            if user_text == "/session":
                print("当前会话:", session_manager.current_name)
                print("用法: /session <名称>，不存在时创建")
                continue

            if user_text == "/session rename" or user_text.startswith("/session rename "):
                parts = user_text.split(maxsplit=2)
                if len(parts) != 3:
                    print("用法: /session rename <新名称>")
                    continue
                result = session_manager.rename(parts[2])
                print(result["message"] if result["ok"] else result["error"])
                continue

            if user_text.startswith("/session "):
                name = user_text.split(maxsplit=1)[1]
                result = session_manager.switch(name)
                if result["ok"]:
                    messages = result["messages"]
                    print("已切换会话:", name, "消息数:", len(messages))
                else:
                    print(result["error"])
                continue

            if command == "/approval":
                mode = argument.strip()
                if not mode:
                    print("当前审批模式:", approval_config["mode"])
                elif mode in ("auto", "manual"):
                    approval_config["mode"] = mode
                    print("审批模式已切换:", mode)
                else:
                    print("用法: /approval [auto|manual]")
                continue

            if command == "/compact":
                from config import context_config
                from compaction import compact_messages, context_view

                option = argument.strip()
                if option in ("auto on", "auto off"):
                    context_config["auto_compact"] = option == "auto on"
                    print("自动压缩:", "on" if context_config["auto_compact"] else "off")
                elif option == "status":
                    view = context_view(messages)
                    print(
                        "自动压缩:",
                        context_config["auto_compact"],
                        "摘要字符:",
                        len(view["summary"]),
                        "已摘要消息:",
                        view["covered"],
                    )
                elif not option:
                    result = compact_messages(messages)
                    print(result["message"] if result["ok"] else result["error"])
                else:
                    print("用法: /compact，/compact status，/compact auto on|off")
                continue

            if user_text == "/context":
                try:
                    context = prepare_context(messages, get_tool_definitions())
                    print("请求字符预算:", context["chars"], "/", context["budget"])
                    print("发送用户轮次:", context["sent_turns"], "/", context["total_turns"])
                    print("省略历史消息:", context["omitted_messages"])
                    print(
                        "已摘要消息:",
                        context["summarized_messages"],
                        "摘要字符:",
                        context["summary_chars"],
                    )
                except ContextBudgetError as error:
                    print("上下文超限或无效:", error)
                continue

            if user_text == "":
                continue

            if user_text == "/model":
                print("current model:" + model_config["model"])
                continue

            if user_text.startswith("/read "):
                path = path_arguments[0]
                result = read_file(path)

                if not result["ok"]:
                    print(result["error"])
                    continue

                content = result["content"]
                line_number = 1
                for line in content.splitlines():
                    print(line_number, ":", line)
                    line_number += 1
                continue

            if user_text.startswith("/attach "):
                path = path_arguments[0]
                attach_files([path], messages)
                continue

            if user_text == "/grep" or user_text.startswith("/grep "):
                path, keyword = path_arguments
                if not keyword:
                    print("用法: /grep <目录> <关键词>，例如 /grep . run_agent")
                    continue
                result = search_project(path, keyword)
                if not result["ok"]:
                    print(result["error"])
                    continue
                for match in result["matches"]:
                    print(match["path"] + ":" + str(match["line_number"]) + ": " + match["content"])
                print("扫描文件:", result["files_scanned"], "匹配行:", len(result["matches"]))
                if result["truncated"]:
                    print("搜索结果不完整:", result["limit_reason"])
                for warning in result["warnings"]:
                    print("搜索警告:", warning)
                print("跳过统计:", result["skipped"])
                continue

            if user_text.startswith("/search "):
                path, keyword = path_arguments
                if not keyword:
                    print("/search + path + keyword")
                    continue
                result = search_file(path, keyword)
                if not result["ok"]:
                    print(result["error"])
                    continue
                if result["matches"] == []:
                    print("no matches")
                    continue
                print("found matches")
                for match in result["matches"]:
                    print(match["line_number"], ":", match["content"])
                continue

            if user_text.startswith("/model "):
                parts = user_text.split(maxsplit=1)
                model_config["model"] = parts[1]
                print("model has switched to " + model_config["model"])
                continue

            if user_text == "/stream":
                if model_config["stream"]:
                    stream_type = "on"
                else:
                    stream_type = "off"
                print("current stream type:" + stream_type)
                continue

            if user_text.startswith("/stream "):
                parts = user_text.split(maxsplit=1)
                mode = parts[1]
                if mode == "on":
                    model_config["stream"] = True
                    print("流式输出已开启")
                elif mode == "off":
                    model_config["stream"] = False
                    print("流式输出已关闭")
                else:
                    print("unknown mode")

                continue

            if user_text == "/skills":
                result = list_skills()
                if not result["ok"]:
                    print(result["error"])
                elif not result["skills"]:
                    print("没有可用 Skill，请放入 skills/<名称>/SKILL.md")
                else:
                    for skill in result["skills"]:
                        status = "已启用" if skill["active"] else "未启用"
                        print(skill["name"] + " (" + status + ")")
                continue

            if user_text == "/skill clear":
                clear_skills()
                print("已停用所有 Skills")
                continue

            if user_text == "/skill generate" or user_text.startswith("/skill generate "):
                parts = user_text.split(maxsplit=3)
                if len(parts) != 4:
                    print("用法: /skill generate <名称> <用途>")
                    continue
                print("正在生成 Skill 草稿...")
                result = generate_skill(parts[2], parts[3])
                print(result["message"] if result["ok"] else result["error"])
                continue

            if user_text.startswith("/skill "):
                name = user_text.split(maxsplit=1)[1]
                result = activate_skill(name)
                if result["ok"]:
                    print("已启用 Skill:", name)
                else:
                    print(result["error"])
                continue

            if user_text == "/instructions":
                print(instruction_state["message"])
                if instruction_state["content"]:
                    print(instruction_state["content"])
                continue

            if command == "/browser":
                if no_mcp:
                    print("本次运行已通过 --no-mcp 禁用浏览器 MCP")
                    continue
                action, _, rest = argument.partition(" ")
                actions = {
                    "open": "open_page",
                    "read": "read_page",
                    "click": "click",
                    "fill": "fill",
                    "wait": "wait_text",
                    "screenshot": "screenshot",
                    "close": "close_browser",
                }
                try:
                    if action not in actions:
                        raise ValueError()
                    if action == "open":
                        args = {"url": rest.strip()}
                    elif action == "click":
                        args = {"ref": rest.strip()}
                    elif action == "fill":
                        ref, value = rest.split(" ", 1)
                        args = {"ref": ref, "value": value}
                    elif action == "wait":
                        args = {"text": rest}
                    else:
                        if rest.strip():
                            raise ValueError()
                        args = {}
                    connected = mcp_manager.connect("browser")
                    if not connected["ok"]:
                        print(connected["error"])
                        continue
                    from tool_runtime import execute_tool

                    result = execute_tool("mcp__browser__" + actions[action], args, source="user")
                    print(
                        safe_text(
                            json.dumps(
                                result.get("structured_content") or result,
                                ensure_ascii=False,
                                indent=2,
                            )
                        )
                    )
                except ValueError:
                    print(
                        "用法: /browser open <URL> | read | click <ref> | fill <ref> <文字> | wait <文字> | screenshot | close"
                    )
                continue

            if user_text == "/mcp tools":
                names = mcp_manager.tool_names()
                print("可用 MCP 工具:", ", ".join(names) if names else "无")
                continue

            if user_text == "/mcp refresh":
                if no_mcp:
                    print("本次运行已通过 --no-mcp 禁用 MCP")
                    continue
                for name in mcp_config:
                    result = mcp_manager.refresh(name)
                    if result["ok"]:
                        print("MCP 已刷新:", name)
                    else:
                        print("MCP 刷新失败:", name, result["error"])
                continue

            if user_text == "/tasks":
                from harness.tasks.runtime import list_tasks

                print(safe_text(json.dumps(list_tasks(), ensure_ascii=False, indent=2)))
                continue

            if command in ("/approve_task", "/reject_task"):
                from harness.tasks.runtime import inspect_task, resolve_task_approval
                from permissions import confirm_tool

                try:
                    task_id, approval_id = argument.split()
                    status = inspect_task(task_id)
                    request = next(
                        item
                        for item in status.get("pending_approvals", [])
                        if item["id"] == approval_id
                    )
                    allow = command == "/approve_task" and confirm_tool(
                        request["action"], request["target"], request["details"]
                    )
                    result = resolve_task_approval(task_id, approval_id, allow)
                    print(safe_text(json.dumps(result, ensure_ascii=False, indent=2)))
                except (ValueError, StopIteration):
                    print("任务或审批不存在，请先用 /task 查看待审批请求")
                continue

            if command in ("/pty", "/agent", "/task", "/send", "/cancel", "/apply"):
                from tool_runtime import execute_tool

                try:
                    if command == "/pty":
                        arguments = {"argv": shlex.split(argument)}
                        name = "start_pty"
                    elif command == "/agent":
                        name, arguments = "spawn_agent", {"task": argument}
                    elif command == "/apply":
                        identifier, proposal = argument.split()
                        name, arguments = (
                            "apply_agent_proposal",
                            {"task_id": identifier, "proposal_id": proposal},
                        )
                    elif command == "/task":
                        name, arguments = "task_status", {"task_id": argument.strip()}
                    elif command == "/cancel":
                        name, arguments = "task_cancel", {"task_id": argument.strip()}
                    else:
                        identifier, text = argument.split(" ", 1)
                        name, arguments = "task_input", {"task_id": identifier, "text": text + "\n"}
                    result = execute_tool(name, arguments, source="user")
                    print(safe_text(json.dumps(result, ensure_ascii=False, indent=2)))
                except ValueError:
                    print("命令参数错误，请查看 /help")
                continue

            if user_text.startswith("/"):
                print("unknown command: " + user_text)
                continue

            message = {"role": "user", "content": user_text}

            messages.append(message)
            append_message(message)

            try:
                output = ConsoleOutput()
                final_messages = []
                reply = run_agent(messages, output=output, on_final=final_messages.append)
            except ModelResponseError as error:
                print("模型响应错误:", error)
                continue
            except urllib.error.HTTPError as error:
                print("service request failed:", error.code)
                continue
            except urllib.error.URLError as error:
                print("model request failed", error.reason)
                continue
            except TimeoutError:
                print("model timeout 5/5, plz try again later")
                continue

            message = (
                final_messages[-1] if final_messages else {"role": "assistant", "content": reply}
            )
            messages.append(message)
            append_message(message)
            output.final(reply)


if __name__ == "__main__":
    # 保留老入口名称，同时使用同一套启动参数与可信配置。
    from cli import main as launch
    import sys

    sys.exit(launch())
