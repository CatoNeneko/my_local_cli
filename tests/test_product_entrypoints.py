import json
import os
import urllib.request
from unittest.mock import Mock

import pytest

import cli
import model_client
from web.guardrails import redact


def test_browser_mcp_honors_trusted_browser_install_location(tmp_path, monkeypatch):
    from mcp_client import prepare_server_connection

    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(tmp_path / "browser-cache"))
    connection = prepare_server_connection("browser")
    assert connection["ok"]
    assert connection["parameters"].env["PLAYWRIGHT_BROWSERS_PATH"] == str(
        tmp_path / "browser-cache"
    )


def test_web_help_and_version_do_not_start_services(monkeypatch, capsys):
    from web.__main__ import main
    import builtins

    original = builtins.__import__

    def guarded(name, *args, **kwargs):
        if name in ("uvicorn", "web.app", "model_client"):
            raise AssertionError("服务不应在帮助命令中加载")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)
    for option in ("--help", "--version"):
        with pytest.raises(SystemExit) as error:
            main([option])
        assert error.value.code == 0
    assert "--config" in capsys.readouterr().out


def test_redaction_honors_api_key_variable_from_trusted_configuration(monkeypatch):
    monkeypatch.setitem(model_client.model_config, "api_key_env", "CUSTOM_TOML_KEY")
    monkeypatch.setenv("CUSTOM_TOML_KEY", "custom-credential-never-log")
    assert redact("body: custom-credential-never-log") == "body: [REDACTED]"


def test_doctor_is_offline_and_usable_before_model_configuration(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    for name in tuple(os.environ):
        if name.startswith("AI_CLI_"):
            monkeypatch.delenv(name)
    monkeypatch.setattr(urllib.request, "urlopen", Mock(side_effect=AssertionError("network")))
    assert cli.main(["--doctor", "--json", "-C", str(tmp_path)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["ok"]
    assert any(item["name"] == "model" and item["status"] == "warning" for item in result["checks"])
    assert not (tmp_path / ".ai-cli").exists()


def test_configuration_display_does_not_read_or_print_api_secret(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("AI_CLI_CONFIG", raising=False)
    monkeypatch.setenv("AI_CLI_API_KEY_ENV", "PRODUCT_TEST_KEY")
    monkeypatch.setenv("PRODUCT_TEST_KEY", "secret-never-print")
    assert cli.main(["--show-config", "--model", "example"]) == 0
    output = capsys.readouterr().out
    assert "secret-never-print" not in output
    assert json.loads(output)["api_key_env"] == "PRODUCT_TEST_KEY"


@pytest.mark.parametrize(
    "base,endpoint",
    [
        ("https://api.example", "https://api.example/v1/chat/completions"),
        ("https://api.example/v1", "https://api.example/v1/chat/completions"),
        ("https://api.example/openhub/v1", "https://api.example/openhub/v1/chat/completions"),
        ("https://api.example/api/paas/v4/", "https://api.example/api/paas/v4/chat/completions"),
    ],
)
def test_compatible_api_preserves_custom_gateway_path(base, endpoint, monkeypatch):
    for name, value in {
        "provider": "openai",
        "model": "fixture",
        "base_url": base,
        "api_key_env": "PRODUCT_UNUSED_KEY",
    }.items():
        monkeypatch.setitem(model_client.model_config, name, value)
    monkeypatch.delenv("PRODUCT_UNUSED_KEY", raising=False)
    response = Mock()
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    response.read.return_value = (
        b'{"choices":[{"message":{"content":"ok"},"finish_reason":"stop"}]}'
    )
    opener = Mock(return_value=response)
    monkeypatch.setattr(urllib.request, "urlopen", opener)
    assert (
        model_client.request_message(
            [{"role": "user", "content": "test"}], use_tools=False, include_context=False
        )["content"]
        == "ok"
    )
    assert opener.call_args.args[0].full_url == endpoint
