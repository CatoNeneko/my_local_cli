"""有界多文件变更：整批预检、一次审阅、冲突复核和失败补偿。

多个文件不具备文件系统级原子可见性；进程被强杀时也不保证回滚。
"""

import os
from pathlib import Path
import stat
import tempfile

import permissions
from approval import write_boundary
from new_files import check_new_target, prepare_create_file
from patches import build_diff

MAX_FILES = 10
MAX_BYTES = 1048576
MAX_TOTAL_BYTES = 2097152
MAX_DIFF_CHARS = 16000


def _target(path):
    checked = permissions.resolve_project_path(path)
    if not checked["ok"]:
        raise ValueError(checked["error"])
    original = Path(path)
    if not original.is_absolute():
        original = permissions.PROJECT_ROOT / original
    if any(item.is_symlink() for item in (original, *original.parents)):
        raise ValueError("变更路径不能包含符号链接")
    boundary = write_boundary(checked["path"])
    if not boundary["ok"]:
        raise ValueError(boundary["error"])
    return Path(checked["path"])


def _read(target):
    with target.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("单文件超过 1 MiB，请缩小变更范围")
    return raw


def prepare_changes(path, changes):
    """仅准备快照和 diff，不写入文件；path 必须指向项目根目录。"""
    try:
        root = permissions.resolve_project_path(path)
        if not root["ok"]:
            return root
        if Path(root["path"]) != permissions.PROJECT_ROOT:
            raise ValueError("多文件变更的 path 必须为项目根目录 '.'")
        if not isinstance(changes, list) or not 1 <= len(changes) <= MAX_FILES:
            raise ValueError("每批变更需要 1–10 个文件")
        files, seen, total = [], set(), 0
        for change in changes:
            target = _target(change["path"])
            if target in seen or any(p in target.parents or target in p.parents for p in seen):
                raise ValueError("变更路径重复或存在父子路径冲突")
            seen.add(target)
            relative = target.relative_to(permissions.PROJECT_ROOT).as_posix()
            if "content" in change:
                prepared = prepare_create_file(change["path"], change["content"])
                if not prepared["ok"]:
                    return prepared
                original, new, mode = None, prepared["new_bytes"], 0o600
                diff = prepared["diff"] or f"新建空文件: {relative}\n"
            else:
                original = _read(target)
                content = original.decode("utf-8")
                for edit in change["edits"]:
                    old, new_text = edit["old_text"], edit["new_text"]
                    if not old or content.count(old) != 1:
                        raise ValueError(f"{relative}: old_text 必须唯一匹配；请读取准确上下文")
                    content = content.replace(old, new_text, 1)
                new = content.encode("utf-8")
                mode = stat.S_IMODE(target.stat().st_mode)
                diff = build_diff(relative, original.decode("utf-8"), content)
            if len(new) > MAX_BYTES or b"\x00" in new:
                raise ValueError("变更内容超过 1 MiB 或含空字符")
            total += len(new) + len(original or b"")
            if total > MAX_TOTAL_BYTES:
                raise ValueError("整批新旧内容超过 2 MiB，请拆分任务")
            if original == new:
                continue
            files.append(
                {
                    "path": str(target),
                    "original_path": change["path"],
                    "relative": relative,
                    "original_bytes": original,
                    "new_bytes": new,
                    "mode": mode,
                    "diff": diff,
                }
            )
        diff = "".join(item["diff"] for item in files)
        if len(diff) > MAX_DIFF_CHARS:
            raise ValueError("整批 diff 超过 16000 字符，请拆分为较小变更")
        return {
            "ok": True,
            "path": root["path"],
            "files": files,
            "changed": bool(files),
            "diff": diff,
            "details": "整批文件变更；拒绝则整批不写入\n" + diff,
        }
    except (OSError, ValueError, UnicodeError, KeyError, TypeError) as error:
        return {"ok": False, "error": "变更准备失败: " + str(error)}


def _check(files):
    for item in files:
        target = _target(item["original_path"])
        if str(target) != item["path"]:
            raise ValueError("路径目标已变化，请重新审阅")
        if item["original_bytes"] is None:
            checked = check_new_target(item["original_path"])
            if not checked["ok"]:
                raise ValueError(checked["error"])
        elif _read(target) != item["original_bytes"]:
            raise ValueError(f"{item['relative']}: 审批期间文件已变化，整批取消")


def _stage(target, raw, mode):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=target.parent, prefix=".cli-change-", delete=False
        ) as f:
            temporary = Path(f.name)
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
        temporary.chmod(mode)
        return temporary
    except BaseException:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise


def apply_prepared_changes(prepared):
    """调用方须已批准并持工作区写锁；失败时仅补偿仍等于本次写入的文件。"""
    files = prepared["files"]
    staged, committed, directories, rollback_errors = [], [], [], []
    try:
        _check(files)
        for item in files:
            target = Path(item["path"])
            missing = []
            parent = target.parent
            while not parent.exists():
                missing.append(parent)
                parent = parent.parent
            for directory in reversed(missing):
                directory.mkdir()
                directories.append(directory)
            staged.append(_stage(target, item["new_bytes"], item["mode"]))
        _check(files)
        for item, temporary in zip(files, staged):
            # 在整批复核之外，提交每个文件前再次检查，减小外部编辑竞态窗口。
            _check([item])
            if item["original_bytes"] is None:
                os.link(temporary, item["path"])
            else:
                os.replace(temporary, item["path"])
            committed.append(item)
        return {
            "ok": True,
            "changed": bool(files),
            "files": [
                {
                    "path": item["relative"],
                    "action": "create" if item["original_bytes"] is None else "edit",
                }
                for item in files
            ],
            "message": "整批变更已提交",
        }
    except (OSError, ValueError, KeyboardInterrupt) as error:
        for item in reversed(committed):
            restoration = None
            try:
                target = _target(item["original_path"])
                if _read(target) != item["new_bytes"]:
                    raise ValueError("提交后又被外部修改，保留外部内容")
                if item["original_bytes"] is None:
                    target.unlink()
                else:
                    restoration = _stage(target, item["original_bytes"], item["mode"])
                    os.replace(restoration, target)
            except (OSError, ValueError) as rollback_error:
                rollback_errors.append({"path": item["relative"], "error": str(rollback_error)})
            finally:
                if restoration is not None:
                    restoration.unlink(missing_ok=True)
        return {
            "ok": False,
            "changed": bool(rollback_errors),
            "error": "整批提交失败: " + str(error),
            "rolled_back": bool(committed) and not rollback_errors,
            "rollback_errors": rollback_errors,
            "cancelled": isinstance(error, KeyboardInterrupt),
        }
    finally:
        for temporary in staged:
            temporary.unlink(missing_ok=True)
        # 只移除本次创建且仍为空的目录，不删除用户或其他工具的内容。
        for directory in reversed(directories):
            try:
                directory.rmdir()
            except OSError:
                pass
