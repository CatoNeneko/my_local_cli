"""MCP 协议操作：连接参数、握手、发现工具和执行调用。"""
import json
import shlex
from pathlib import Path

from mcp import StdioServerParameters

from config import mcp_config
from workspace import APP_ROOT as PROJECT_ROOT


def prepare_server_connection(server_name):
    specification = mcp_config.get(server_name)
    if not isinstance(specification, dict):
        return {"ok": False, "error": "未知 MCP 服务: " + str(server_name)}
    command = specification.get("command")
    args = specification.get("args")
    timeout = specification.get("timeout_seconds")
    if not isinstance(command, str) or not command or "\x00" in command:
        return {"ok": False, "error": "MCP 启动命令无效"}
    if not isinstance(args, list) or not all(isinstance(arg, str) and "\x00" not in arg for arg in args):
        return {"ok": False, "error": "MCP args 必须是字符串列表"}
    if type(timeout) is not int or not 1 <= timeout <= 60:
        return {"ok": False, "error": "MCP 超时必须是 1～60 秒的整数"}
    executable = Path(command)
    if not executable.is_absolute():
        executable = PROJECT_ROOT / executable
    executable = executable.resolve()
    if not executable.is_file():
        return {"ok": False, "error": "找不到 MCP 服务的启动程序"}
    details = shlex.join([str(executable), *args])
    details += "\n工作目录: " + str(PROJECT_ROOT)
    details += "\n该服务以当前用户权限运行，尚未接入沙箱。"
    environment = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}
    if server_name == 'browser':
        import permissions
        root = permissions.PROJECT_ROOT
        state = root if root == PROJECT_ROOT else root / '.ai-cli'
        environment['PLAYWRIGHT_BROWSERS_PATH'] = str(PROJECT_ROOT / '.browser-runtime')
        environment['AI_CLI_BROWSER_ARTIFACTS'] = str(state / '.browser-artifacts')
        details += '\n浏览器可访问网络；临时 Cookie，不加载用户浏览器档案；截图保存于私有目录。'
    parameters = StdioServerParameters(
        command=str(executable), args=list(args), cwd=str(PROJECT_ROOT),
        env=environment
    )
    return {"ok": True, "parameters": parameters, "timeout": timeout, "details": details}


async def collect_tools(session):
    tools = []
    cursor = None
    seen_cursors = set()
    while True:
        page = await session.list_tools(cursor=cursor)
        tools.extend(tool.model_dump(mode="json") for tool in page.tools)
        if len(tools) > 200:
            raise ValueError("MCP 工具数量超过本阶段的 200 个上限")
        cursor = page.nextCursor
        if not cursor:
            break
        if cursor in seen_cursors:
            raise ValueError("MCP 工具列表分页游标重复")
        seen_cursors.add(cursor)
    return tools


async def call_session_tool(session, tool_name, expected_schema, arguments):
    tools = await collect_tools(session)
    matches = [tool for tool in tools if tool["name"] == tool_name]
    if len(matches) != 1 or matches[0]["inputSchema"] != expected_schema:
        return {"ok": False, "error": "MCP 工具声明已变化，请运行 /mcp refresh"}
    result = await session.call_tool(tool_name, arguments=arguments)
    if any(item.type != "text" for item in result.content):
        return {"ok": False, "error": "本阶段 MCP 只支持文字和结构化 JSON 结果"}
    normalized = {
        "ok": not result.isError,
        "content": [item.text for item in result.content],
        "structured_content": result.structuredContent
    }
    if result.isError:
        normalized["error"] = "MCP 服务报告工具执行失败"
    if len(json.dumps(normalized, ensure_ascii=False)) > 16000:
        return {"ok": False, "error": "MCP 返回内容超过 16000 字符上限"}
    return normalized


def execute_prepared_mcp_tool(connection, tool_name, expected_schema, arguments):
    """内部执行函数：仅在 tool_runtime 完成授权后调用。"""
    return connection["manager"].call_tool(
        connection["server_name"], tool_name, expected_schema, arguments
    )
