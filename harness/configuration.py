"""CLI 与 Web 共用的可信启动配置；不读取工作区内的项目配置。"""

from dataclasses import asdict, dataclass
import os
from pathlib import Path
import re
import tomllib
from urllib.parse import urlsplit


@dataclass(frozen=True)
class AppConfiguration:
    provider: str = "openai"
    model: str = ""
    base_url: str = "https://api.openai.com/v1"
    api_key_env: str = "OPENAI_API_KEY"
    stream: bool = True
    approval_mode: str = "manual"
    mcp_enabled: bool = False
    max_workers: int = 2
    run_timeout: int = 600

    def model_settings(self):
        """只返回模型参数；密钥始终由客户端从命名的环境变量读取。"""
        return {name: getattr(self, name) for name in _MODEL_FIELDS}


_MODEL_FIELDS = ("provider", "model", "base_url", "api_key_env", "stream")
_SECTIONS = {
    "model": {
        "provider": "provider",
        "name": "model",
        "base_url": "base_url",
        "api_key_env": "api_key_env",
        "stream": "stream",
    },
    "runtime": {"approval_mode": "approval_mode", "mcp_enabled": "mcp_enabled"},
    "web": {"max_workers": "max_workers", "run_timeout": "run_timeout"},
}
_ENV_FIELDS = {
    "AI_CLI_PROVIDER": "provider",
    "AI_CLI_MODEL": "model",
    "AI_CLI_BASE_URL": "base_url",
    "AI_CLI_API_KEY_ENV": "api_key_env",
    "AI_CLI_STREAM": "stream",
    "AI_CLI_APPROVAL_MODE": "approval_mode",
    "AI_CLI_MCP": "mcp_enabled",
    "AI_CLI_MAX_WORKERS": "max_workers",
    "AI_CLI_RUN_TIMEOUT": "run_timeout",
}


def validate_model_url(value):
    """禁止凭据、查询参数与 fragment；错误不能回显可能含密钥的地址。"""
    message = "模型服务地址必须为有效 HTTP(S) URL，且不能包含凭据、查询参数或片段"
    if (
        not isinstance(value, str)
        or not value
        or any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        raise ValueError(message)
    try:
        parsed = urlsplit(value)
        if (
            parsed.scheme not in ("http", "https")
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or "?" in value
            or "#" in value
            or "\\" in value
        ):
            raise ValueError(message)
        # 访问 port 会验证端口是否为整数且处于合法范围。
        parsed.port
    except ValueError:
        raise ValueError(message) from None
    return value.rstrip("/")


def _validate(values):
    defaults = asdict(AppConfiguration())
    for field, value in values.items():
        if field not in defaults:
            raise ValueError("配置包含未知或禁止的字段；密钥只能保存在环境变量中")
        if type(value) is not type(defaults[field]):
            raise ValueError(f"配置字段 {field} 类型不正确")
        if field == "provider" and value not in ("openai", "ollama"):
            raise ValueError("模型协议只能为 openai 或 ollama")
        if field == "approval_mode" and value not in ("manual", "auto"):
            raise ValueError("审批模式只能为 manual 或 auto")
        if field == "api_key_env" and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
            raise ValueError("密钥环境变量名格式不正确")
        if field == "model" and value and not value.strip():
            raise ValueError("模型名称不能只有空白")
        if field == "base_url":
            validate_model_url(value)
        if field == "max_workers" and not 1 <= value <= 8:
            raise ValueError("并发数应为 1–8")
        if field == "run_timeout" and not 30 <= value <= 3600:
            raise ValueError("总超时应为 30–3600 秒")
    return values


def _read_toml(path, required):
    try:
        with path.open("rb") as file:
            document = tomllib.load(file)
    except FileNotFoundError:
        if not required:
            return {}
        raise ValueError("指定的配置文件不存在") from None
    except (OSError, ValueError, UnicodeError):
        # TOML 的原始异常可能带上用户填写的值，不能直接转发。
        raise ValueError("无法读取配置文件或 TOML 格式无效") from None
    values = {}
    for section, content in document.items():
        if section not in _SECTIONS or not isinstance(content, dict):
            raise ValueError("配置包含未知配置节或配置节类型错误")
        for key, value in content.items():
            if key not in _SECTIONS[section]:
                raise ValueError("配置包含未知或禁止的字段；密钥只能保存在环境变量中")
            values[_SECTIONS[section][key]] = value
    return _validate(values)


def _environment_values(environ):
    defaults = asdict(AppConfiguration())
    values = {}
    for name, field in _ENV_FIELDS.items():
        if name not in environ:
            continue
        value = environ[name]
        if not isinstance(value, str):
            raise ValueError(f"环境变量 {name} 类型不正确")
        expected = type(defaults[field])
        if expected is bool:
            choices = {"1": True, "true": True, "0": False, "false": False}
            if value.lower() not in choices:
                raise ValueError(f"环境变量 {name} 必须为 1、0、true 或 false")
            value = choices[value.lower()]
        elif expected is int:
            try:
                value = int(value)
            except ValueError:
                raise ValueError(f"环境变量 {name} 必须为整数") from None
        values[field] = value
    return _validate(values)


def load_configuration(config_path=None, overrides=None, environ=None):
    """优先级：内置默认值 < 用户 TOML < 环境变量 < 非 None 的显式参数。"""
    environ = os.environ if environ is None else environ
    selected = config_path if config_path is not None else environ.get("AI_CLI_CONFIG")
    if selected is None:
        config_root = Path(environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        path = config_root / "local-ai-cli" / "config.toml"
    else:
        try:
            path = Path(selected).expanduser()
        except (TypeError, ValueError, RuntimeError):
            raise ValueError("配置文件路径无效") from None
    values = asdict(AppConfiguration())
    values.update(_read_toml(path, required=selected is not None))
    values.update(_environment_values(environ))
    if overrides is not None and (
        not isinstance(overrides, dict) or any(name not in values for name in overrides)
    ):
        raise ValueError("覆盖参数包含未知或禁止的字段；密钥只能保存在环境变量中")
    explicit = {name: value for name, value in (overrides or {}).items() if value is not None}
    values.update(_validate(explicit))
    values["base_url"] = validate_model_url(values["base_url"])
    return AppConfiguration(**values)
