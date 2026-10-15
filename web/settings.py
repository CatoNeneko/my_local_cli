"""服务配置仅来自启动环境，不接受浏览器提交模型地址、密钥或命令。"""

from dataclasses import dataclass
import os
from pathlib import Path

from harness.configuration import load_configuration, validate_model_url


@dataclass(frozen=True)
class Settings:
    state_dir: Path
    workspace_root: Path
    model: str = ""
    base_url: str = "https://api.openai.com/v1"
    api_key_env: str = "OPENAI_API_KEY"
    max_workers: int = 2
    run_timeout: int = 600
    approval_mode: str = "manual"
    mcp_enabled: bool = False
    provider: str = "openai"
    stream: bool = True

    @classmethod
    def from_env(cls, config_path=None, workspace=None):
        root = (
            Path(workspace or os.environ.get("AI_CLI_WORKSPACE_ROOT", Path.cwd()))
            .expanduser()
            .resolve()
        )
        configuration = load_configuration(config_path)
        return cls(
            state_dir=Path(os.environ.get("AI_CLI_WEB_STATE", root / ".ai-cli" / "web")).resolve(),
            workspace_root=root,
            **configuration.model_settings(),
            max_workers=configuration.max_workers,
            run_timeout=configuration.run_timeout,
            approval_mode=configuration.approval_mode,
            mcp_enabled=configuration.mcp_enabled,
        )

    def validate(self):
        if not self.workspace_root.is_dir():
            raise ValueError("允许的工作目录不存在")
        if not 1 <= self.max_workers <= 8 or not 30 <= self.run_timeout <= 3600:
            raise ValueError("并发数应为 1–8，总超时应为 30–3600 秒")
        if self.approval_mode not in ("manual", "auto"):
            raise ValueError("审批模式只能为 manual 或 auto")
        validate_model_url(self.base_url)
        if self.provider not in ("openai", "ollama"):
            raise ValueError("模型协议只能为 openai 或 ollama")
        return self

    def model_settings(self):
        return {
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "api_key_env": self.api_key_env,
            "stream": self.stream,
        }

    @property
    def model_ready(self):
        return bool(self.model and os.environ.get(self.api_key_env))

    def workspace(self, value):
        if not Path(value).expanduser().is_absolute():
            raise ValueError("请提供 Linux/WSL 绝对路径")
        candidate = Path(value).expanduser().resolve()
        if not candidate.is_dir() or not candidate.is_relative_to(self.workspace_root):
            raise ValueError("工作目录必须位于服务启动时允许的根目录内")
        if any(part.startswith(".") for part in candidate.relative_to(self.workspace_root).parts):
            raise ValueError("不能选择隐藏控制目录")
        return str(candidate)
