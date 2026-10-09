"""兼容入口。注册位于 tool_registry，执行位于 tool_runtime。"""
from tool_registry import get_tool_definitions
from tool_runtime import execute_tool


# 兼容旧导入；模型请求使用 getter，以便以后动态添加 MCP 工具。
tool_definitions = get_tool_definitions()


def read_file(path):
    return execute_tool("read_file", {"path": path}, source="user")


def search_file(path, keyword):
    return execute_tool("search_file", {"path": path, "keyword": keyword}, source="user")


def list_files(path):
    return execute_tool("list_files", {"path": path}, source="user")


def search_project(path, keyword, glob="*"):
    return execute_tool("search_project", {"path": path, "keyword": keyword, "glob": glob}, source="user")
