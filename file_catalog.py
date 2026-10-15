"""有限扫描的项目文件索引与文件名模糊匹配，不读取文件正文。"""

import os
import time
from pathlib import Path

import permissions
from config import search_config

MAX_FILES = 5000
MAX_ENTRIES = 20000
SCAN_SECONDS = 2


def scan_files():
    files = []
    stack = [permissions.PROJECT_ROOT]
    visited = 0
    deadline = time.monotonic() + SCAN_SECONDS
    reason = ""
    warnings = []
    while stack and not reason:
        if time.monotonic() >= deadline:
            reason = "扫描时间上限"
            break
        directory = stack.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    visited += 1
                    if visited > MAX_ENTRIES:
                        reason = "目录项数量上限"
                        break
                    if time.monotonic() >= deadline:
                        reason = "扫描时间上限"
                        break
                    if entry.is_symlink():
                        continue
                    checked = permissions.resolve_project_path(entry.path)
                    if not checked["ok"]:
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        if entry.name not in search_config["ignored_directories"]:
                            stack.append(Path(entry.path))
                    elif entry.is_file(follow_symlinks=False):
                        files.append(
                            str(Path(checked["path"]).relative_to(permissions.PROJECT_ROOT))
                        )
                        if len(files) >= MAX_FILES:
                            reason = "文件数量上限"
                            break
        except OSError as error:
            if len(warnings) < 5:
                warnings.append("跳过无法读取的目录: " + str(error))
    return {
        "files": sorted(files),
        "truncated": bool(reason),
        "reason": reason,
        "warnings": warnings,
    }


def fuzzy_score(query, path):
    text = path.casefold()
    tokens = query.casefold().split()
    gap = 0
    for token in tokens:
        cursor = 0
        positions = []
        for char in token:
            position = text.find(char, cursor)
            if position < 0:
                return None
            positions.append(position)
            cursor = position + 1
        gap += positions[-1] - positions[0] + 1 - len(token)
    basename = Path(path).name.casefold()
    return (0 if query.casefold() in basename else 1, gap, len(path), path)


def matching_files(paths, query):
    ranked = []
    for path in paths:
        score = fuzzy_score(query, path)
        if score is not None:
            ranked.append((score, path))
    return [path for _, path in sorted(ranked)]
