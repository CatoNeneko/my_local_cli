"""项目递归文字搜索：共享路径策略，跳过符号链接并限制读取和结果规模。"""
import fnmatch
import json
import os
import time
from pathlib import Path

import permissions
from config import search_config


def search_project(path, keyword, glob="*"):
    checked = permissions.resolve_project_path(path)
    if not checked["ok"]:
        return checked
    if not isinstance(keyword, str) or not keyword or not isinstance(glob, str) or not glob:
        return {"ok": False, "error": "关键词和文件匹配模式不能为空"}
    root = Path(checked["path"])
    if not root.is_dir():
        return {"ok": False, "error": "项目搜索目标必须是存在的目录"}
    numeric_keys = ["max_files", "max_file_bytes", "max_total_bytes", "max_matches", "max_output_chars", "timeout_seconds"]
    if any(type(search_config.get(key)) is not int or search_config[key] <= 0 for key in numeric_keys):
        return {"ok": False, "error": "搜索限制必须是正整数"}
    matches = []
    warnings = []
    skipped = {"protected_or_link": 0, "large": 0, "non_text": 0, "unreadable": 0}
    scanned = 0
    total_bytes = 0
    output_chars = 0
    deadline = time.monotonic() + search_config["timeout_seconds"]
    ignored = set(search_config["ignored_directories"])

    def result(reason=""):
        return {"ok": True, "matches": matches, "files_scanned": scanned,
                "bytes_read": total_bytes, "skipped": skipped, "warnings": warnings,
                "truncated": bool(reason), "limit_reason": reason}

    def walk_error(error):
        skipped["unreadable"] += 1
        if len(warnings) < 10:
            warnings.append("部分目录无法遍历: " + type(error).__name__)

    for directory, directories, files in os.walk(root, followlinks=False, onerror=walk_error):
        if time.monotonic() >= deadline:
            return result("搜索时间上限")
        allowed = []
        for name in sorted(directories):
            if time.monotonic() >= deadline:
                return result("搜索时间上限")
            item = Path(directory) / name
            if name in ignored or item.is_symlink() or not permissions.resolve_project_path(str(item))["ok"]:
                skipped["protected_or_link"] += 1
            else:
                allowed.append(name)
        directories[:] = allowed
        for name in sorted(files):
            if time.monotonic() >= deadline:
                return result("搜索时间上限")
            item = Path(directory) / name
            checked = permissions.resolve_project_path(str(item))
            if item.is_symlink() or not checked["ok"]:
                skipped["protected_or_link"] += 1
                continue
            relative = str(item.relative_to(permissions.PROJECT_ROOT))
            if not fnmatch.fnmatchcase(relative, glob) and not fnmatch.fnmatchcase(name, glob):
                continue
            if scanned >= search_config["max_files"]:
                return result("扫描文件数量上限")
            try:
                if not item.is_file():
                    continue
                scanned += 1
                if item.stat().st_size > search_config["max_file_bytes"]:
                    skipped["large"] += 1
                    continue
                remaining = search_config["max_total_bytes"] - total_bytes
                if remaining <= 0:
                    return result("总读取字节上限")
                with open(checked["path"], "rb") as file:
                    raw = file.read(min(search_config["max_file_bytes"], remaining) + 1)
                total_bytes += len(raw)
                if len(raw) > remaining:
                    return result("总读取字节上限")
                if len(raw) > search_config["max_file_bytes"]:
                    skipped["large"] += 1
                    continue
                if b"\x00" in raw:
                    skipped["non_text"] += 1
                    continue
                text = raw.decode("utf-8-sig")
            except UnicodeError:
                skipped["non_text"] += 1
                continue
            except OSError as error:
                skipped["unreadable"] += 1
                if len(warnings) < 10:
                    warnings.append("部分文件无法读取: " + type(error).__name__)
                continue
            for number, line in enumerate(text.splitlines(), start=1):
                if time.monotonic() >= deadline:
                    return result("搜索时间上限")
                position = line.find(keyword)
                if position < 0:
                    continue
                start = max(0, position - 100) if len(line) > 500 else 0
                snippet = line[start:start + 500]
                entry = {"path": relative, "line_number": number, "content": snippet,
                         "content_truncated": start > 0 or start + len(snippet) < len(line)}
                size = len(json.dumps(entry, ensure_ascii=False))
                if output_chars + size > search_config["max_output_chars"]:
                    return result("结果字符数量上限")
                matches.append(entry)
                output_chars += size
                if len(matches) >= search_config["max_matches"]:
                    return result("匹配数量上限")
    return result()
