"""用户文件工具的便利接口，所有操作复用统一 Runtime。"""

from tool_runtime import execute_tool


def read_file(path):
    return execute_tool("read_file", {"path": path}, source="user")


def search_file(path, keyword):
    return execute_tool("search_file", {"path": path, "keyword": keyword}, source="user")


def list_files(path):
    return execute_tool("list_files", {"path": path}, source="user")


def search_project(path, keyword, glob="*"):
    return execute_tool(
        "search_project", {"path": path, "keyword": keyword, "glob": glob}, source="user"
    )
