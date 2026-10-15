import json
from types import SimpleNamespace

import harness.diagnostics as diagnostics


def make_config(*, provider="openai", model="test-model", base_url="https://example.invalid/v1"):
    return SimpleNamespace(
        provider=provider,
        model=model,
        base_url=base_url,
        api_key_env="DOCTOR_TEST_API_KEY",
    )


def mock_environment_checks(monkeypatch, *, commands=True, modules=True):
    monkeypatch.setattr(
        diagnostics.shutil,
        "which",
        lambda command: f"/usr/bin/{command}" if commands else None,
    )
    monkeypatch.setattr(
        diagnostics.importlib.util,
        "find_spec",
        lambda name: object() if modules else None,
    )


def test_doctor_is_json_safe_and_does_not_expose_credentials_or_url(monkeypatch, tmp_path):
    mock_environment_checks(monkeypatch)
    secret = "doctor-secret-value-123"
    monkeypatch.setenv("DOCTOR_TEST_API_KEY", secret)
    config = make_config(base_url=f"https://example.invalid/v1?api_key={secret}")

    result = diagnostics.doctor(config, tmp_path)
    serialized = json.dumps(result, ensure_ascii=False)

    assert result["ok"] is True
    assert secret not in serialized
    assert "example.invalid" not in serialized
    assert {check["status"] for check in result["checks"]} <= {"pass", "warning", "fail"}


def test_doctor_reports_missing_workspace_without_creating_it(monkeypatch, tmp_path):
    mock_environment_checks(monkeypatch)
    missing = tmp_path / "not-created"

    result = diagnostics.doctor(make_config(), missing)

    workspace_check = next(check for check in result["checks"] if check["name"] == "workspace")
    assert result["ok"] is False
    assert workspace_check["status"] == "fail"
    assert not missing.exists()


def test_empty_model_is_warning_and_ollama_does_not_require_a_key(monkeypatch, tmp_path):
    mock_environment_checks(monkeypatch)
    monkeypatch.delenv("DOCTOR_TEST_API_KEY", raising=False)

    result = diagnostics.doctor(make_config(provider="ollama", model=""), tmp_path)

    model_check = next(check for check in result["checks"] if check["name"] == "model")
    key_check = next(check for check in result["checks"] if check["name"] == "api_key")
    assert result["ok"] is True
    assert model_check["status"] == "warning"
    assert key_check["status"] == "pass"


def test_missing_commands_and_dependencies_are_warnings(monkeypatch, tmp_path):
    mock_environment_checks(monkeypatch, commands=False, modules=False)

    result = diagnostics.doctor(make_config(), tmp_path)

    checks = {check["name"]: check for check in result["checks"]}
    assert result["ok"] is True
    assert checks["bwrap"]["status"] == "warning"
    assert checks["git"]["status"] == "warning"
    assert checks["dependencies"]["status"] == "warning"
