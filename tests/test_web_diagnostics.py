import io
import json
import os
import urllib.error

import pytest

from context_window import ContextBudgetError
from streaming import ModelResponseError
from web.diagnostics import DiagnosticLog, safe_diagnostic


class UnreadBody(io.BytesIO):
    def __init__(self, text):
        super().__init__(text.encode("utf-8"))
        self.read_called = False

    def read(self, *args, **kwargs):
        self.read_called = True
        return super().read(*args, **kwargs)


@pytest.mark.parametrize(
    ("status", "code", "retryable"),
    [
        (401, "authentication_failed", False),
        (403, "access_denied", False),
        (429, "rate_limited", True),
        (503, "service_unavailable", True),
    ],
)
def test_http_diagnostics_do_not_read_or_expose_url_or_body(status, code, retryable):
    url_key = "url_key_value_must_stay_private_123456"
    body_key = "body_key_value_must_stay_private_123456"
    body = UnreadBody(body_key)
    error = urllib.error.HTTPError(
        f"https://model.invalid/v1?api_key={url_key}",
        status,
        "server response containing " + body_key,
        {},
        body,
    )

    diagnostic = safe_diagnostic(error)

    assert diagnostic["code"] == code
    assert diagnostic["retryable"] is retryable
    assert not body.read_called
    assert url_key not in json.dumps(diagnostic, ensure_ascii=False)
    assert body_key not in json.dumps(diagnostic, ensure_ascii=False)


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (TimeoutError("private timeout details"), "request_timeout"),
        (ConnectionError("private connection details"), "connection_failed"),
        (ModelResponseError("private response body"), "invalid_model_response"),
        (ContextBudgetError("private context detail"), "context_budget_exceeded"),
        (ValueError("private validation input"), "invalid_input"),
        (PermissionError("private path"), "permission_denied"),
        (OSError("private filesystem detail"), "local_io_error"),
        (RuntimeError("private unexpected detail"), "unexpected_error"),
    ],
)
def test_diagnostics_use_fixed_messages_for_all_error_classes(error, code):
    diagnostic = safe_diagnostic(error, stage="worker", run_id="run-123")

    assert diagnostic["code"] == code
    assert diagnostic["stage"] == "worker"
    assert diagnostic["run_id"] == "run-123"
    assert str(error) not in json.dumps(diagnostic, ensure_ascii=False)


def test_safe_diagnostic_cleans_structured_identifiers():
    diagnostic = safe_diagnostic(
        RuntimeError("private detail"),
        stage="worker\ncode=forged",
        run_id="任务\x00sk-123456789012345678901234",
    )

    assert diagnostic["stage"] == "worker"
    assert "\x00" not in diagnostic["run_id"]
    assert "123456789012345678901234" not in diagnostic["run_id"]


def test_diagnostic_log_rotates_with_one_backup_and_private_permissions(tmp_path):
    log_path = tmp_path / "run-1" / "diagnostic.jsonl"
    log = DiagnosticLog(log_path, max_bytes=256)

    for run_id in ("one", "two", "three"):
        assert (
            log.append(
                {
                    "run_id": run_id,
                    "stage": "worker",
                    "code": "unexpected_error",
                    "message": "任务失败 " + "界" * 100,
                    "retryable": False,
                    "api_key": "must not be serialized",
                    "response_body": "must not be serialized",
                    "traceback": "must not be serialized",
                    "fullarguments": {"secret": "must not be serialized"},
                }
            )
            is None
        )

    assert log_path.stat().st_size <= 256
    assert log.backup_path.stat().st_size <= 256
    assert os.stat(log_path.parent).st_mode & 0o777 == 0o700
    assert os.stat(log_path).st_mode & 0o777 == 0o600
    assert os.stat(log.backup_path).st_mode & 0o777 == 0o600
    assert log.tail()[0]["run_id"] == "three"
    assert log.tail()[0]["message"].startswith("任务失败")
    assert len(log.tail()) == 1
    assert log.backup_path.read_text(encoding="utf-8").find("two") >= 0
    assert "must not be serialized" not in log_path.read_text(encoding="utf-8")


def test_diagnostic_log_discards_an_already_oversized_file(tmp_path):
    log_path = tmp_path / "private" / "diagnostic.jsonl"
    log_path.parent.mkdir(mode=0o700)
    log_path.write_bytes(b"x" * 512)
    log = DiagnosticLog(log_path, max_bytes=128)

    log.append({"code": "recovered"})

    assert log_path.stat().st_size <= 128
    assert not log.backup_path.exists()


def test_diagnostic_log_masks_structured_values_and_skips_malformed_tail(tmp_path):
    log_path = tmp_path / "private" / "diagnostic.jsonl"
    log = DiagnosticLog(log_path)
    secret = "sk-123456789012345678901234"
    log.append(
        {
            "run_id": "run-1",
            "task_id": "任务-一",
            "stage": "worker",
            "code": "invalid_input",
            "title": "输入\r\n标题",
            "message": "请求中包含密钥 " + secret,
            "suggestion": "检查输入",
            "retryable": False,
            "token": "drop-me",
            "fullarguments": {"drop": "me"},
            "responsebody": "drop-me",
            "traceback": "drop-me",
        }
    )
    with log_path.open("a", encoding="utf-8") as output:
        output.write("{malformed json\n")

    raw = log_path.read_text(encoding="utf-8")
    entries = log.tail(limit=1)

    assert "任务-一" in raw
    assert "请求中包含密钥" in raw
    assert secret not in raw
    assert "drop-me" not in raw
    assert "\r" not in raw and "\n标题" not in raw
    assert entries == [
        {
            "run_id": "run-1",
            "task_id": "任务-一",
            "stage": "worker",
            "code": "invalid_input",
            "title": "输入标题",
            "message": "请求中包含密钥 [REDACTED]",
            "suggestion": "检查输入",
            "retryable": False,
        }
    ]
