import difflib
import os
import tempfile
from pathlib import Path

from permissions import resolve_project_path


def build_diff(path, old_content, new_content):
    diff_lines = difflib.unified_diff(
        old_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile="before/" + path,
        tofile="after/" + path,
    )
    rendered = []
    for line in diff_lines:
        if line.endswith("\n"):
            rendered.append(line)
        else:
            rendered.append(line + "\n\\ No newline at end of file\n")
    return "".join(rendered)


def prepare_edit(path, new_content):
    if not isinstance(path, str) or not isinstance(new_content, str):
        return {"ok": False, "error": "路径和新内容必须是字符串"}

    path_result = resolve_project_path(path)
    if not path_result["ok"]:
        return path_result

    target = Path(path_result["path"])
    try:
        original_bytes = target.read_bytes()
        old_content = original_bytes.decode("utf-8")
        new_bytes = new_content.encode("utf-8")
    except UnicodeError:
        return {"ok": False, "error": "文件或新内容不是有效的 UTF-8 文本"}
    except OSError as error:
        return {"ok": False, "error": "读取失败: " + str(error)}

    return {
        "ok": True,
        "path": str(target),
        "original_bytes": original_bytes,
        "new_bytes": new_bytes,
        "changed": original_bytes != new_bytes,
        "diff": build_diff(path, old_content, new_content),
    }


def preview_edit(path, new_content):
    prepared = prepare_edit(path, new_content)
    if not prepared["ok"]:
        return prepared
    return {"ok": True, "changed": prepared["changed"], "diff": prepared["diff"]}


def apply_prepared_edit(prepared):
    """内部写入实现，只由已授权的执行入口调用。"""
    if not prepared["changed"]:
        return {"ok": True, "changed": False, "message": "文件内容没有变化"}
    target = Path(prepared["path"])
    temporary_path = None
    try:
        checked = resolve_project_path(prepared["path"])
        if not checked["ok"]:
            return checked
        if checked["path"] != str(target):
            return {"ok": False, "error": "路径目标已变化，请重新审查"}
        if target.read_bytes() != prepared["original_bytes"]:
            return {"ok": False, "error": "文件在审查期间已变化，请重新生成修改"}

        original_mode = target.stat().st_mode
        with tempfile.NamedTemporaryFile(
            dir=target.parent, prefix=".cli-edit-", delete=False
        ) as file:
            temporary_path = Path(file.name)
            file.write(prepared["new_bytes"])
            file.flush()
            os.fsync(file.fileno())
        os.chmod(temporary_path, original_mode)

        checked = resolve_project_path(prepared["path"])
        if not checked["ok"] or checked["path"] != str(target):
            return {"ok": False, "error": "路径目标已变化，请重新审查"}
        if target.read_bytes() != prepared["original_bytes"]:
            return {"ok": False, "error": "文件在写入前已变化，修改已取消"}

        os.replace(temporary_path, target)
        temporary_path = None
        return {"ok": True, "changed": True, "path": str(target), "message": "修改已写入"}
    except OSError as error:
        return {"ok": False, "error": "写入失败: " + str(error)}
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except OSError as error:
                print("清理临时文件失败:", error)


def edit_file(path, new_content):
    # 保留旧接口，但也必须经过统一执行入口。
    from tool_runtime import execute_tool

    return execute_tool("edit_file", {"path": path, "new_content": new_content})
