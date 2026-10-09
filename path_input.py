"""路径命令解析和受项目边界约束的文件候选。"""
import os
import io
import shlex
from pathlib import Path

import permissions
from config import search_config

PATH_COMMANDS = {'/read', '/attach', '/search', '/grep'}


def parse_path_arguments(text):
    # 只解析第一个路径；关键词中的空格保持原样。
    stream = io.StringIO(text)
    lexer = shlex.shlex(stream, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ''
    try:
        path = lexer.get_token()
    except ValueError as error:
        raise ValueError('路径格式无效；带空格的路径请使用成对引号') from error
    if not path:
        raise ValueError('路径不能为空')
    return path, stream.read().lstrip()


def path_candidates(directory, prefix='', directories_only=False):
    checked = permissions.resolve_project_path(directory)
    if not checked['ok']:
        return [], False
    candidates = []
    truncated = False
    try:
        with os.scandir(checked['path']) as entries:
            for index, entry in enumerate(entries):
                if index >= 1000 or len(candidates) >= 200:
                    truncated = True
                    break
                if not entry.name.startswith(prefix) or entry.is_symlink():
                    continue
                allowed = permissions.resolve_project_path(entry.path)
                if not allowed['ok']:
                    continue
                is_directory = entry.is_dir(follow_symlinks=False)
                if is_directory and entry.name in search_config['ignored_directories']:
                    continue
                if directories_only and not is_directory:
                    continue
                if not is_directory and not entry.is_file(follow_symlinks=False):
                    continue
                relative = str(Path(allowed['path']).relative_to(permissions.PROJECT_ROOT))
                candidates.append((relative, is_directory))
    except OSError:
        return [], False
    return sorted(candidates, key=lambda item: (not item[1], item[0])), truncated
