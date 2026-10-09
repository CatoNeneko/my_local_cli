"""普通 UTF-8 文件的新建：审查后创建，已有目标一律拒绝覆盖。"""
import os
import tempfile
from pathlib import Path

import permissions
from patches import build_diff

MAX_NEW_FILE_BYTES = 1048576


def check_new_target(path):
    checked = permissions.resolve_project_path(path)
    if not checked['ok']:
        return checked
    target = Path(checked['path'])
    # 检查原始路径的每一层，拒绝通过符号链接新建文件。
    original = Path(path)
    if not original.is_absolute():
        original = permissions.PROJECT_ROOT / original
    for item in [original, *original.parents]:
        if item.is_symlink():
            return {'ok': False, 'error': '新建文件的路径不能包含符号链接'}
        if item.exists() and item != original and not item.is_dir():
            return {'ok': False, 'error': '父路径不是目录'}
    if target.exists():
        return {'ok': False, 'error': '目标已存在；请先读取并使用 edit_file，不能覆盖'}
    return checked


def prepare_create_file(path, new_content):
    checked = check_new_target(path)
    if not checked['ok']:
        return checked
    if not isinstance(new_content, str) or '\x00' in new_content:
        return {'ok': False, 'error': '新文件内容必须是文字，不能包含空字符'}
    try:
        raw = new_content.encode('utf-8')
    except UnicodeError:
        return {'ok': False, 'error': '新文件内容不是有效 UTF-8'}
    if len(raw) > MAX_NEW_FILE_BYTES:
        return {'ok': False, 'error': '新文件内容超过 1 MiB 上限'}
    relative = str(Path(checked['path']).relative_to(permissions.PROJECT_ROOT))
    return {'ok': True, 'path': checked['path'], 'original_path': path,
            'new_bytes': raw, 'diff': build_diff(relative, '', new_content),
            'details': '新建 UTF-8 文件；必要时创建父目录；拒绝覆盖已有文件'}


def apply_prepared_file(prepared):
    temporary = None
    try:
        checked = check_new_target(prepared['original_path'])
        if not checked['ok']:
            return checked
        if checked['path'] != prepared['path']:
            return {'ok': False, 'error': '目标已变化，请重新审查'}
        target = Path(checked['path'])
        target.parent.mkdir(parents=True, exist_ok=True)
        # 临时文件写完之后，link 独占发布；并发创建也不会覆盖。
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.cli-new-', delete=False) as file:
            temporary = Path(file.name)
            file.write(prepared['new_bytes'])
            file.flush()
            os.fsync(file.fileno())
        checked = check_new_target(prepared['original_path'])
        if not checked['ok'] or checked['path'] != str(target):
            return {'ok': False, 'error': '目标在写入前已变化或已存在，创建取消'}
        os.link(temporary, target)
        return {'ok': True, 'changed': True, 'path': str(target), 'message': '新文件已创建'}
    except OSError as error:
        return {'ok': False, 'error': '新建失败: ' + str(error)}
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError as error:
                from tool_display import emit, short_text
                emit('新文件临时文件清理失败: ' + short_text(error), 'ansiyellow')
