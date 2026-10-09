"""会话管理；文件路径由名称生成，独立于模型文件工具的访问入口。"""
import json
import os
import re
from pathlib import Path

import history
from skills import active_skills


class SessionManager:
    def __init__(self):
        self.default_path = Path(history.HISTORY_PATH)
        self.directory = self.default_path.parent / "sessions"
        self.current_name = "default"
        self.skill_snapshots = {}

    def path_for(self, name):
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", name) or name == "rename":
            raise ValueError("会话名为 1～64 位字母、数字、下划线或连字符，不能为 rename")
        if self.directory.is_symlink():
            raise ValueError("会话目录不能是符号链接")
        path = self.default_path if name == "default" else self.directory / (name + ".jsonl")
        if path.is_symlink():
            raise ValueError("会话文件不能是符号链接")
        if path.exists() and not path.is_file():
            raise ValueError("会话历史路径不是普通文件")
        return path

    def switch(self, name):
        try:
            path = self.path_for(name)
            # 先成功读取目标，再提交路径、名称和 Skill 状态，避免失败后串会话。
            messages = history.load_history(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                with open(path, "x", encoding="utf-8"):
                    pass
            self.skill_snapshots[self.current_name] = dict(active_skills)
            if name != self.current_name:
                active_skills.clear()
                active_skills.update(self.skill_snapshots.get(name, {}))
            history.HISTORY_PATH = path
            self.current_name = name
            return {"ok": True, "messages": messages, "name": name}
        except (OSError, UnicodeError, ValueError) as error:
            return {"ok": False, "error": "会话切换失败: " + str(error)}

    def list_sessions(self):
        try:
            self.path_for("default")
            names = {"default"}
            if self.directory.exists():
                for path in self.directory.glob("*.jsonl"):
                    try:
                        checked = self.path_for(path.stem)
                        if checked.is_file():
                            names.add(path.stem)
                    except ValueError:
                        continue
            return {"ok": True, "names": sorted(names)}
        except (OSError, ValueError) as error:
            return {"ok": False, "error": "无法列出会话: " + str(error)}

    def rename(self, name):
        destination = None
        linked = False
        try:
            source = self.path_for(self.current_name)
            destination = self.path_for(name)
            if name == self.current_name:
                return {"ok": True, "name": name, "message": "名称没有变化"}
            if destination.exists() or name in self.skill_snapshots:
                raise ValueError("目标会话已经存在，不能覆盖")
            destination.parent.mkdir(parents=True, exist_ok=True)
            if source.exists():
                # 独占创建目标，避免 rename 在并发创建时覆盖另一份会话。
                os.link(source, destination)
                linked = True
                source.unlink()
            else:
                with open(destination, "x", encoding="utf-8"):
                    pass
            self.skill_snapshots.pop(self.current_name, None)
            self.skill_snapshots[name] = dict(active_skills)
            self.current_name = name
            history.HISTORY_PATH = destination
            return {"ok": True, "name": name, "message": "会话已重命名为 " + name}
        except (OSError, ValueError) as error:
            # 原文件删除失败时撤销刚建立的链接，原会话仍然有效。
            if linked and destination is not None:
                try:
                    destination.unlink()
                except OSError:
                    pass
            return {"ok": False, "error": "会话重命名失败: " + str(error)}

    def export(self, messages):
        try:
            self.path_for(self.current_name)
            path = (
                self.default_path.with_suffix(".json") if self.current_name == "default"
                else self.directory / (self.current_name + ".export.json")
            )
            if path.is_symlink():
                raise ValueError("导出路径不能是符号链接")
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as file:
                json.dump(messages, file, ensure_ascii=False, indent=2)
            return {"ok": True, "path": str(path)}
        except (OSError, ValueError) as error:
            return {"ok": False, "error": "会话导出失败: " + str(error)}
