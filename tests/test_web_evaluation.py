import json
from pathlib import Path
import sys
from unittest.mock import Mock

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import evaluate_workbench


def test_offline_evaluation_writes_fixed_report_without_model_calls(tmp_path, monkeypatch):
    request = Mock(side_effect=AssertionError("离线评估不得请求模型"))
    monkeypatch.setattr("model_client.request_message", request)
    report_path = tmp_path / "report.json"

    report = evaluate_workbench.evaluate_offline()
    evaluate_workbench.write_report(report, report_path)

    loaded = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["mode"] == "offline"
    assert report["real_model_called"] is False
    assert report["counts"]["passed"] == 8
    assert report["counts"]["failed"] == 0
    assert report["counts"]["missing"] == 1
    assert {item["name"] for item in report["checks"]} == {
        "rag_english_keyword_source_hit",
        "rag_chinese_keyword_source_hit",
        "deleted_file_removed_after_reindex",
        "project_memory_isolation",
        "incomplete_tool_parameters_rejected",
        "out_of_bounds_read_rejected",
        "read_injection_content_remains_data",
        "denied_write_preserves_file",
        "remote_embedding_probe",
    }
    assert all(item["status"] == "passed" for item in report["checks"][:-1])
    assert report["checks"][-1]["status"] == "missing"
    assert report["remote_embedding"]["status"] == "missing"
    assert "AI_CLI_EMBEDDING_MODEL" in report["missing_configuration"][0]
    assert loaded == report
    request.assert_not_called()


def test_live_missing_configuration_is_reported_without_network(monkeypatch):
    for name in (
        "AI_CLI_MODEL",
        "AI_CLI_BASE_URL",
        "AI_CLI_API_KEY_ENV",
        "OPENAI_API_KEY",
        "AI_CLI_EMBEDDING_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)
    request = Mock(side_effect=AssertionError("配置缺失时不得请求模型"))
    monkeypatch.setattr("model_client.request_message", request)

    report = evaluate_workbench.evaluate_live()

    assert report["mode"] == "live"
    assert report["real_model_called"] is False
    assert report["counts"]["missing"] == 2
    assert report["checks"][0]["name"] == "remote_api_configuration"
    assert set(report["missing_configuration"]) >= {
        "AI_CLI_MODEL",
        "AI_CLI_BASE_URL",
        "OPENAI_API_KEY",
    }
    assert report["remote_embedding"]["status"] == "missing"
    request.assert_not_called()


@pytest.mark.parametrize(
    ("model", "base_url"),
    [
        ("gpt-compatible", "http://127.0.0.1:11434/v1"),
        ("qwen-local", "https://api.example.test/v1"),
        ("glm-4-compatible", "https://api.example.test/v1"),
    ],
)
def test_live_local_or_disabled_configuration_is_rejected_without_network(
    monkeypatch, model, base_url
):
    monkeypatch.setenv("AI_CLI_MODEL", model)
    monkeypatch.setenv("AI_CLI_BASE_URL", base_url)
    monkeypatch.setenv("AI_CLI_API_KEY_ENV", "EVALUATION_TEST_KEY")
    monkeypatch.setenv("EVALUATION_TEST_KEY", "fixture-only-key")
    request = Mock(side_effect=AssertionError("禁止配置不得请求模型"))
    monkeypatch.setattr("model_client.request_message", request)

    report = evaluate_workbench.evaluate_live()

    assert report["real_model_called"] is False
    assert report["counts"]["failed"] == 1
    assert report["checks"][0]["name"] == "remote_compatible_endpoint"
    assert report["checks"][0]["status"] == "failed"
    request.assert_not_called()
