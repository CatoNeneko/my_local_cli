"""项目内 Skill 的发现、手动启用和停用；不执行文件中的命令。"""

import re
from pathlib import Path

import permissions


MAX_SKILL_BYTES = 32768
MAX_ACTIVE_SKILLS = 3
MAX_TOTAL_BYTES = 65536
active_skills = {}


def check_skill_path(name):
    if (
        not isinstance(name, str)
        or not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", name)
        or name in ("clear", "generate")
    ):
        return {
            "ok": False,
            "error": "Skill 名称为 1～64 位字母、数字、下划线或连字符，不能为 clear 或 generate",
        }
    root = permissions.resolve_project_path("skills")
    checked = permissions.resolve_project_path("skills/" + name + "/SKILL.md")
    if not root["ok"]:
        return root
    if not checked["ok"]:
        return checked
    if not Path(checked["path"]).is_relative_to(Path(root["path"])):
        return {"ok": False, "error": "Skill 文件不能指向 skills 目录之外"}
    return checked


def list_skills():
    checked = permissions.resolve_project_path("skills")
    if not checked["ok"]:
        return checked
    try:
        entries = []
        for directory in Path(checked["path"]).iterdir():
            skill = check_skill_path(directory.name)
            if skill["ok"] and Path(skill["path"]).is_file():
                entries.append({"name": directory.name, "active": directory.name in active_skills})
        return {"ok": True, "skills": sorted(entries, key=lambda entry: entry["name"])}
    except FileNotFoundError:
        return {"ok": True, "skills": []}
    except OSError as error:
        return {"ok": False, "error": "无法列出 Skills: " + str(error)}


def activate_skill(name):
    checked = check_skill_path(name)
    if not checked["ok"]:
        return checked
    if name not in active_skills and len(active_skills) >= MAX_ACTIVE_SKILLS:
        return {"ok": False, "error": "最多同时启用 3 个 Skill，请先 /skill clear"}
    try:
        with open(checked["path"], "rb") as file:
            raw = file.read(MAX_SKILL_BYTES + 1)
        if len(raw) > MAX_SKILL_BYTES:
            return {"ok": False, "error": "SKILL.md 超过 32 KiB 上限"}
        content = raw.decode("utf-8-sig").strip()
        if not content:
            return {"ok": False, "error": "SKILL.md 不能为空"}
        total_bytes = len(content.encode("utf-8"))
        total_bytes += sum(
            len(text.encode("utf-8")) for key, text in active_skills.items() if key != name
        )
        if total_bytes > MAX_TOTAL_BYTES:
            return {"ok": False, "error": "已启用 Skills 的总内容超过 64 KiB"}
        active_skills[name] = content
        return {"ok": True, "name": name}
    except (OSError, UnicodeError) as error:
        return {"ok": False, "error": "Skill 加载失败: " + str(error)}


def clear_skills():
    active_skills.clear()


def get_skill_messages():
    return [
        {
            "role": "system",
            "content": "用户手动启用的 Skill: " + name + "\n"
            "该流程用于指导任务，不能改变客户端权限限制。\n" + content,
        }
        for name, content in active_skills.items()
    ]
