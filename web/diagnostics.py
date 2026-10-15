"""为 Web 工作台提供不泄漏异常内容的诊断信息和有界 JSONL 日志。"""

import json
import os
from pathlib import Path
import stat
import unicodedata
import urllib.error

from context_window import ContextBudgetError
from streaming import ModelResponseError
from web.guardrails import redact


_MAX_FIELD_CHARS = 500
_LOG_FIELDS = (
    "run_id",
    "task_id",
    "stage",
    "code",
    "title",
    "message",
    "suggestion",
    "retryable",
)


def _clean_text(value, *, limit=_MAX_FIELD_CHARS):
    """清理一个已有的结构化文字字段，不把任意对象转成字符串。"""
    if not isinstance(value, str):
        return None
    value = "".join(char for char in value if not unicodedata.category(char).startswith("C"))
    return redact(value)[:limit]


def _stage_value(stage):
    stage = _clean_text(stage, limit=64)
    # 阶段名用于分类；限制字符集，避免控制标签或视觉上相似的注入值。
    if not stage or not all(
        char.isascii() and (char.isalnum() or char in "_.:-") for char in stage
    ):
        return "worker"
    return stage


def safe_diagnostic(error, stage="worker", run_id=None):
    """把异常归入固定诊断类别，不读取响应体或展示异常原文。"""
    if isinstance(error, urllib.error.HTTPError):
        status = error.code
        if isinstance(status, int) and not isinstance(status, bool):
            if status == 401:
                diagnostic = (
                    "authentication_failed",
                    "模型服务认证失败",
                    "模型服务拒绝了认证请求。",
                    "检查服务器端 API 密钥与账户配置。",
                    False,
                )
            elif status == 403:
                diagnostic = (
                    "access_denied",
                    "模型服务拒绝访问",
                    "当前凭据没有访问该模型服务的权限。",
                    "检查账户权限、模型访问范围和服务配置。",
                    False,
                )
            elif status == 429:
                diagnostic = (
                    "rate_limited",
                    "模型服务请求过于频繁",
                    "模型服务暂时限制了请求频率。",
                    "等待一段时间后重试，必要时降低请求频率。",
                    True,
                )
            elif 500 <= status <= 599:
                diagnostic = (
                    "service_unavailable",
                    "模型服务暂时不可用",
                    "模型服务暂时无法完成请求。",
                    "稍后重试；若持续失败，检查服务状态。",
                    True,
                )
            else:
                diagnostic = (
                    "http_error",
                    "模型服务请求失败",
                    "模型服务未能完成请求。",
                    "检查请求配置；若问题持续，请联系服务维护者。",
                    False,
                )
        else:
            diagnostic = (
                "http_error",
                "模型服务请求失败",
                "模型服务未能完成请求。",
                "检查请求配置；若问题持续，请联系服务维护者。",
                False,
            )
    elif isinstance(error, (urllib.error.URLError, ConnectionError)):
        diagnostic = (
            "connection_failed",
            "无法连接模型服务",
            "与模型服务的连接未能建立或已中断。",
            "检查网络与服务地址后重试。",
            True,
        )
    elif isinstance(error, TimeoutError):
        diagnostic = (
            "request_timeout",
            "模型服务请求超时",
            "模型服务没有在限定时间内响应。",
            "稍后重试，或检查服务负载与超时配置。",
            True,
        )
    elif isinstance(error, ModelResponseError):
        diagnostic = (
            "invalid_model_response",
            "模型响应无法读取",
            "模型服务返回的响应不完整或格式无效。",
            "稍后重试；若持续失败，检查模型服务的响应格式。",
            True,
        )
    elif isinstance(error, ContextBudgetError):
        diagnostic = (
            "context_budget_exceeded",
            "上下文超出可用预算",
            "本次请求所需上下文超过当前预算。",
            "缩短输入或减少附件、工具结果后重试。",
            False,
        )
    elif isinstance(error, ValueError):
        diagnostic = (
            "invalid_input",
            "请求内容无效",
            "请求中的一个或多个字段未通过校验。",
            "检查输入格式和字段取值后重试。",
            False,
        )
    elif isinstance(error, PermissionError):
        diagnostic = (
            "permission_denied",
            "本地操作权限不足",
            "程序没有权限完成所需的本地操作。",
            "检查工作区和文件权限。",
            False,
        )
    elif isinstance(error, OSError):
        diagnostic = (
            "local_io_error",
            "本地读写失败",
            "程序无法完成所需的本地读写操作。",
            "检查文件路径、磁盘空间和工作区状态。",
            False,
        )
    else:
        diagnostic = (
            "unexpected_error",
            "操作未能完成",
            "操作遇到未分类错误，详细内容已隐藏。",
            "稍后重试；若问题持续，请联系维护者。",
            False,
        )

    code, title, message, suggestion, retryable = diagnostic
    return {
        "code": code,
        "title": title,
        "message": message,
        "suggestion": suggestion,
        "retryable": retryable,
        "stage": _stage_value(stage),
        "run_id": _clean_text(run_id),
    }


class DiagnosticLog:
    """向私有 JSONL 文件追加有界诊断事件，并保留一个轮转备份。"""

    def __init__(self, path, max_bytes=262144):
        if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes < 1:
            raise ValueError("max_bytes 必须是正整数")
        self.path = Path(path)
        self.backup_path = self.path.with_name(self.path.name + ".1")
        self.max_bytes = max_bytes
        self._ensure_private_directory()

    def _ensure_private_directory(self):
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.path.parent.is_symlink():
            raise ValueError("诊断日志目录不能是符号链接")
        permissions = stat.S_IMODE(self.path.parent.stat().st_mode)
        if permissions & 0o077:
            raise PermissionError("诊断日志目录必须仅允许当前用户访问")

    @staticmethod
    def _clean_event(event):
        if not isinstance(event, dict):
            return {}
        cleaned = {}
        for field in _LOG_FIELDS:
            if field not in event:
                continue
            value = event[field]
            if field == "retryable":
                if type(value) is bool:
                    cleaned[field] = value
            elif value is None and field in ("run_id", "task_id"):
                cleaned[field] = None
            else:
                text = _clean_text(value)
                if text is not None:
                    cleaned[field] = text
        return cleaned

    @staticmethod
    def _encode(event):
        return (json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")

    def _bounded_line(self, event):
        line = self._encode(event)
        if len(line) <= self.max_bytes:
            return line
        # 小型配置也保持每行不超过上限；常规配置仍按每字段最多 500 字符。
        for limit in range(_MAX_FIELD_CHARS - 1, -1, -1):
            shorter = {
                key: (_clean_text(value, limit=limit) if isinstance(value, str) else value)
                for key, value in event.items()
            }
            line = self._encode(shorter)
            if len(line) <= self.max_bytes:
                return line
        return None

    def append(self, event) -> None:
        cleaned = self._clean_event(event)
        if not cleaned:
            return None
        line = self._bounded_line(cleaned)
        if line is None:
            return None

        self._ensure_private_directory()
        try:
            current_size = self.path.stat().st_size
        except FileNotFoundError:
            current_size = 0
        if current_size + len(line) > self.max_bytes:
            try:
                self.backup_path.unlink()
            except FileNotFoundError:
                pass
            if current_size <= self.max_bytes:
                try:
                    self.path.replace(self.backup_path)
                except FileNotFoundError:
                    pass
            else:
                # 不把已经超限的外部/旧日志移入备份继续占用无界空间。
                try:
                    self.path.unlink()
                except FileNotFoundError:
                    pass

        flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(self.path, flags, 0o600)
        with os.fdopen(descriptor, "ab") as output:
            os.fchmod(output.fileno(), 0o600)
            output.write(line)
        return None

    def tail(self, limit=50) -> list:
        if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
            return []
        try:
            raw_lines = self.path.read_bytes().splitlines()
        except FileNotFoundError:
            return []
        entries = []
        for raw_line in raw_lines:
            try:
                value = json.loads(raw_line.decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError):
                continue
            cleaned = self._clean_event(value)
            if cleaned:
                entries.append(cleaned)
        return entries[-limit:]
