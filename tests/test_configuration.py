"""统一启动配置的优先级、拒绝策略与离线启动行为。"""

import builtins
from dataclasses import FrozenInstanceError
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import sys

import pytest

import cli
from harness.configuration import AppConfiguration, load_configuration, validate_model_url
from web.settings import Settings


@pytest.fixture
def user_config(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    path = tmp_path / ".config" / "local-ai-cli" / "config.toml"
    path.parent.mkdir(parents=True)
    return path


def test_defaults_are_frozen_and_do_not_enable_local_services(user_config):
    settings = load_configuration(environ={})
    assert settings == AppConfiguration()
    assert settings.provider == "openai" and settings.model == ""
    assert settings.base_url == "https://api.openai.com/v1"
    assert settings.approval_mode == "manual" and settings.mcp_enabled is False
    assert settings.stream is True
    with pytest.raises(FrozenInstanceError):
        settings.model = "changed"
    assert set(settings.model_settings()) == {
        "provider",
        "model",
        "base_url",
        "api_key_env",
        "stream",
    }


def test_configuration_precedence_and_none_cli_values(user_config):
    user_config.write_text(
        '[model]\nname="file-model"\nbase_url="https://file.invalid/v1/"\nstream=false\n'
        '[runtime]\napproval_mode="auto"\nmcp_enabled=true\n'
        "[web]\nmax_workers=3\nrun_timeout=120\n"
    )
    settings = load_configuration(
        environ={"AI_CLI_MODEL": "env-model", "AI_CLI_MAX_WORKERS": "4"},
        overrides={"model": "cli-model", "approval_mode": None, "mcp_enabled": False},
    )
    assert settings.model == "cli-model" and settings.max_workers == 4
    assert settings.base_url == "https://file.invalid/v1"
    assert settings.approval_mode == "auto" and settings.mcp_enabled is False
    assert settings.stream is False and settings.run_timeout == 120
    assert load_configuration(environ={"AI_CLI_MODEL": "env-model"}).model == "env-model"
    assert load_configuration(environ={}).model == "file-model"


def test_explicit_config_wins_over_environment_file_and_does_not_trust_project(
    user_config, tmp_path, monkeypatch
):
    user_config.write_text('[model]\nname="user-model"\n')
    project = tmp_path / "project"
    project.mkdir()
    (project / "config.toml").write_text('[model]\nname="untrusted"\n')
    monkeypatch.chdir(project)
    assert load_configuration(environ={}).model == "user-model"
    explicit = tmp_path / "explicit.toml"
    explicit.write_text('[model]\nname="explicit-model"\n')
    assert load_configuration(explicit, environ={"AI_CLI_CONFIG": "missing"}).model == (
        "explicit-model"
    )
    assert load_configuration(environ={"AI_CLI_CONFIG": str(explicit)}).model == "explicit-model"


def test_xdg_location_is_user_configuration(user_config, tmp_path):
    root = tmp_path / "user-settings"
    path = root / "local-ai-cli" / "config.toml"
    path.parent.mkdir(parents=True)
    path.write_text('[model]\nname="xdg-model"\n')
    assert load_configuration(environ={"XDG_CONFIG_HOME": str(root)}).model == "xdg-model"


@pytest.mark.parametrize(
    "document",
    [
        '[model]\napi_key="SECRET_SENTINEL"',
        '[model]\nSECRET_SENTINEL="unknown"',
        "[SECRET_SENTINEL]\nvalue=true",
        'model="SECRET_SENTINEL"',
        '[model]\nstream="SECRET_SENTINEL"',
        "[web]\nmax_workers=true",
        '[model]\nname=["SECRET_SENTINEL"]',
        "[runtime]\nmcp_enabled=1",
        '[model]\nname="SECRET_SENTINEL',
    ],
)
def test_invalid_toml_never_echoes_values_or_unknown_names(user_config, document):
    user_config.write_text(document)
    with pytest.raises(ValueError) as error:
        load_configuration(environ={})
    assert "SECRET_SENTINEL" not in str(error.value)


@pytest.mark.parametrize(
    "address",
    [
        "file:///SECRET_SENTINEL",
        "https://user:SECRET_SENTINEL@example.invalid/v1",
        "https://SECRET_SENTINEL@example.invalid/v1",
        "https://example.invalid/v1?api_key=SECRET_SENTINEL",
        "https://example.invalid/v1#SECRET_SENTINEL",
        "https://example.invalid/v1?",
        "https://example.invalid/v1#",
        "https://example.invalid:SECRET_SENTINEL/v1",
        "https:///SECRET_SENTINEL",
        "https://example.invalid/SECRET_SENTINEL\n",
        "\x00https://SECRET_SENTINEL.invalid",
    ],
)
def test_unsafe_urls_are_rejected_without_echo(address):
    with pytest.raises(ValueError) as error:
        validate_model_url(address)
    assert "SECRET_SENTINEL" not in str(error.value)


@pytest.mark.parametrize("address", ["http://localhost:11434/", "https://example.invalid/v1/"])
def test_explicit_http_endpoints_are_valid(address):
    assert validate_model_url(address) == address.rstrip("/")


@pytest.mark.parametrize(
    "environ",
    [
        {"AI_CLI_STREAM": "SECRET_SENTINEL"},
        {"AI_CLI_MCP": "SECRET_SENTINEL"},
        {"AI_CLI_MAX_WORKERS": "SECRET_SENTINEL"},
        {"AI_CLI_RUN_TIMEOUT": "29"},
        {"AI_CLI_API_KEY_ENV": "SECRET_SENTINEL=bad"},
        {"AI_CLI_MODEL": 12},
        {"AI_CLI_APPROVAL_MODE": "SECRET_SENTINEL"},
    ],
)
def test_invalid_environment_is_actionable_without_echo(user_config, environ):
    with pytest.raises(ValueError) as error:
        load_configuration(environ=environ)
    assert "SECRET_SENTINEL" not in str(error.value)


def test_missing_explicit_file_invalid_utf8_and_overrides_raise_value_error(user_config):
    with pytest.raises(ValueError, match="不存在"):
        load_configuration(user_config, environ={})
    user_config.write_bytes(b"\xff")
    with pytest.raises(ValueError):
        load_configuration(environ={})
    user_config.unlink()
    for overrides in ({"stream": "false"}, {"api_key": None}, {"max_workers": True}):
        with pytest.raises(ValueError):
            load_configuration(environ={}, overrides=overrides)


def test_web_uses_shared_configuration_and_keeps_explicit_readiness(
    user_config, tmp_path, monkeypatch
):
    user_config.write_text(
        '[model]\nname="file-model"\napi_key_env="CONFIG_TEST_KEY"\nstream=false\n'
        "[web]\nmax_workers=3\n"
    )
    for name in list(os.environ):
        if name.startswith("AI_CLI_") or name == "XDG_CONFIG_HOME":
            monkeypatch.delenv(name)
    monkeypatch.setenv("AI_CLI_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("CONFIG_TEST_KEY", "SECRET_SENTINEL")
    settings = Settings.from_env().validate()
    assert settings.model == "file-model" and settings.max_workers == 3
    assert settings.provider == "openai" and settings.stream is False
    assert settings.model_ready is True
    assert "SECRET_SENTINEL" not in repr(settings.model_settings())
    assert Settings(tmp_path / "state", tmp_path).model_ready is False
    with pytest.raises(ValueError):
        Settings(
            tmp_path / "state", tmp_path, base_url="https://u:secret@example.invalid"
        ).validate()


@pytest.mark.parametrize("flag", ["--help", "--version"])
def test_cli_help_and_version_do_not_load_config_or_services(monkeypatch, capsys, flag):
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name in {"script", "config", "harness.configuration", "model_client", "mcp_client"}:
            raise AssertionError("离线参数不应加载模型或配置服务")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    with pytest.raises(SystemExit) as error:
        cli.main([flag])
    assert error.value.code == 0
    assert "ai-cli" in capsys.readouterr().out


def test_cli_requires_model_before_importing_runtime(user_config, monkeypatch, capsys):
    monkeypatch.setattr("harness.configuration.os.environ", {})
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "script":
            raise AssertionError("缺少模型时不能启动运行时")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    with pytest.raises(SystemExit) as error:
        cli.main([])
    assert error.value.code == 2
    assert "--model" in capsys.readouterr().err


def test_cli_applies_shared_settings_before_runtime(user_config, monkeypatch):
    import config

    user_config.write_text('[model]\nname="file-model"\nstream=false\n')
    monkeypatch.setattr("harness.configuration.os.environ", {})
    monkeypatch.setattr(config, "model_config", dict(config.model_config))
    monkeypatch.setattr(config, "approval_config", dict(config.approval_config))
    run = Mock()
    monkeypatch.setitem(sys.modules, "script", SimpleNamespace(main=run))
    cli.main(["--model", "cli-model", "--plain"])
    assert config.model_config["model"] == "cli-model"
    assert config.model_config["provider"] == "openai"
    assert config.model_config["stream"] is False
    assert config.approval_config["mode"] == "manual"
    assert run.call_args.kwargs["no_mcp"] is True
