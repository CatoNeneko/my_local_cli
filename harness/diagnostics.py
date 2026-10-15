"""只读检查 CLI 运行环境，不启动服务或执行外部命令。"""

import importlib.util
import os
from pathlib import Path
import shutil
import sys


def doctor(config, workspace):
    """检查当前解释器、工作目录和可选运行依赖，返回 JSON 可序列化结果。"""
    checks = []

    python_ok = sys.version_info >= (3, 12)
    checks.append(
        {
            "name": "python",
            "status": "pass" if python_ok else "fail",
            "message": (
                f"Python {sys.version_info.major}.{sys.version_info.minor} 可用"
                if python_ok
                else "需要 Python 3.12 或更高版本"
            ),
        }
    )
    checks.append(
        {
            "name": "interpreter",
            "status": "pass" if sys.executable else "warning",
            "message": f"当前解释器：{sys.executable}"
            if sys.executable
            else "无法确定当前解释器路径",
        }
    )

    try:
        root = Path(workspace).expanduser()
        workspace_ok = root.is_dir() and os.access(root, os.R_OK | os.W_OK)
    except (TypeError, ValueError, OSError):
        workspace_ok = False
    checks.append(
        {
            "name": "workspace",
            "status": "pass" if workspace_ok else "fail",
            "message": (
                "工作目录存在且可读写" if workspace_ok else "工作目录不存在、不是目录或不可读写"
            ),
        }
    )

    model = getattr(config, "model", None)
    model_ok = isinstance(model, str) and bool(model.strip())
    checks.append(
        {
            "name": "model",
            "status": "pass" if model_ok else "warning",
            "message": "已配置模型名称" if model_ok else "尚未配置模型名称",
        }
    )

    provider = getattr(config, "provider", "")
    provider = provider.lower() if isinstance(provider, str) else ""
    key_env = getattr(config, "api_key_env", "")
    has_api_key = (
        isinstance(key_env, str) and bool(key_env) and bool(os.environ.get(key_env, "").strip())
    )
    if provider == "ollama":
        key_status, key_message = "pass", "当前 Ollama 配置无需 API 密钥"
    elif has_api_key:
        key_status, key_message = "pass", "已检测到 API 密钥"
    else:
        key_status, key_message = "warning", "未检测到 API 密钥；兼容服务可能允许无密钥访问"
    checks.append({"name": "api_key", "status": key_status, "message": key_message})

    for command in ("bwrap", "git"):
        available = shutil.which(command) is not None
        checks.append(
            {
                "name": command,
                "status": "pass" if available else "warning",
                "message": (
                    f"已找到 {command}" if available else f"未找到 {command}；相关功能可能不可用"
                ),
            }
        )

    pty_available = os.name == "posix" and hasattr(os, "openpty")
    checks.append(
        {
            "name": "pty",
            "status": "pass" if pty_available else "warning",
            "message": "当前平台支持 PTY" if pty_available else "当前平台不支持 PTY",
        }
    )

    missing_modules = []
    for module in ("fastapi", "langgraph", "mcp"):
        try:
            found = importlib.util.find_spec(module) is not None
        except (ImportError, ValueError):
            found = False
        if not found:
            missing_modules.append(module)
    checks.append(
        {
            "name": "dependencies",
            "status": "warning" if missing_modules else "pass",
            "message": (
                "缺少可选依赖：" + ", ".join(missing_modules)
                if missing_modules
                else "FastAPI、LangGraph 和 MCP 依赖均可用"
            ),
        }
    )

    return {"ok": all(check["status"] != "fail" for check in checks), "checks": checks}
