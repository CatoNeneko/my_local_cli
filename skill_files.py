"""新建 Skill 文件：审查后独占创建，不覆盖已有文件。"""

import os
import tempfile
from pathlib import Path

import permissions
from patches import build_diff
from skills import MAX_SKILL_BYTES, check_skill_path


def check_new_skill_target(path):
    checked = permissions.resolve_project_path(path)
    if not checked["ok"]:
        return checked
    target = Path(checked["path"])
    relative = target.relative_to(permissions.PROJECT_ROOT)
    if len(relative.parts) != 3 or relative.parts[0] != "skills" or relative.parts[2] != "SKILL.md":
        return {"ok": False, "error": "只能创建 skills/<名称>/SKILL.md"}
    skill = check_skill_path(relative.parts[1])
    if not skill["ok"]:
        return skill
    for item in [permissions.PROJECT_ROOT / "skills", target.parent, target]:
        if item.is_symlink():
            return {"ok": False, "error": "生成 Skill 的目标不能是符号链接"}
    if target.exists():
        return {"ok": False, "error": "Skill 文件已存在，生成操作不会覆盖它"}
    return {"ok": True, "path": str(target)}


def prepare_create_skill(path, new_content):
    checked = check_new_skill_target(path)
    if not checked["ok"]:
        return checked
    if not isinstance(new_content, str) or not new_content.strip() or "\x00" in new_content:
        return {"ok": False, "error": "Skill 内容必须是非空文字，不能包含空字符"}
    raw = new_content.encode("utf-8")
    if len(raw) > MAX_SKILL_BYTES:
        return {"ok": False, "error": "Skill 内容超过 32 KiB 上限"}
    return {
        "ok": True,
        "path": checked["path"],
        "new_bytes": raw,
        "diff": build_diff(checked["path"], "", new_content),
        "details": "新建 Skill 文件，不覆盖已有文件，也不自动启用",
    }


def apply_prepared_skill(prepared):
    temporary_path = None
    try:
        checked = check_new_skill_target(prepared["path"])
        if not checked["ok"] or checked["path"] != prepared["path"]:
            return {"ok": False, "error": "目标已变化或已存在，创建已取消"}
        target = Path(checked["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=target.parent, prefix=".skill-draft-", delete=False
        ) as file:
            temporary_path = Path(file.name)
            file.write(prepared["new_bytes"])
            file.flush()
            os.fsync(file.fileno())
        checked = check_new_skill_target(prepared["path"])
        if not checked["ok"] or checked["path"] != str(target):
            return {"ok": False, "error": "目标在写入前已变化，创建已取消"}
        # link 只创建不存在的目标；并发创建时失败，而不是覆盖别人的文件。
        os.link(temporary_path, target)
        return {"ok": True, "path": str(target), "message": "Skill 已保存，尚未启用"}
    except OSError as error:
        return {"ok": False, "error": "Skill 保存失败: " + str(error)}
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except OSError as error:
                print("Skill 临时文件清理失败:", error)
