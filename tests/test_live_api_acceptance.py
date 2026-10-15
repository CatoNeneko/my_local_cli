"""联测报告与退出状态的离线验证；不请求任何模型。"""

import copy

import pytest

from scripts import live_api_acceptance as suite


def report_with_checks():
    return {
        "checks": [{"name": name, "passed": True} for name in suite.REQUIRED_CHECKS],
        "requests": [],
    }


def test_summary_uses_latest_attempt_without_erasing_history():
    report = report_with_checks()
    report["checks"].insert(0, {"name": "real_writable_subagent", "passed": False})
    original = copy.deepcopy(report)

    result = suite.summarize_report(report)

    assert result["passed"] is True
    assert result["passed_checks"] == 7
    assert result["failed_attempt_count"] == 1
    assert result["attempt_count"] == 8
    assert report == original
    report["checks"].append({"name": "real_writable_subagent", "passed": False})
    assert suite.summarize_report(report)["passed"] is False


def test_summary_requires_all_seven_checks():
    report = report_with_checks()
    report["checks"].pop()

    result = suite.summarize_report(report)

    assert result["completed_checks"] == 6
    assert result["passed_checks"] == 6
    assert result["passed"] is False


@pytest.mark.parametrize("missing", [None, False, "unknown"])
def test_summary_does_not_count_missing_usage_as_zero(missing):
    report = report_with_checks()
    report["requests"] = [
        {"prompt_tokens": 10, "completion_tokens": 4, "total_tokens": 14},
        {"prompt_tokens": missing, "completion_tokens": 2, "total_tokens": None},
    ]

    usage = suite.summarize_report(report)["usage"]

    assert usage["prompt_tokens"] is None
    assert usage["completion_tokens"] == 6
    assert usage["total_tokens"] is None
    assert usage["subprocess_usage"] is None


def test_summary_only_totals_measured_parent_requests():
    report = report_with_checks()
    assert suite.summarize_report(report)["usage"]["total_tokens"] is None
    report["requests"] = [{"prompt_tokens": 10, "completion_tokens": 4, "total_tokens": 14}]

    usage = suite.summarize_report(report)["usage"]

    assert usage["total_tokens"] == 14
    assert usage["scope"] == "instrumented_parent_process_requests_only"
    assert usage["subprocess_usage"] is None


@pytest.mark.parametrize("succeeded", [False, True])
def test_main_returns_failure_unless_full_suite_passes(monkeypatch, tmp_path, succeeded):
    def protocol(report, key_env):
        report["checks"].extend(
            {"name": name, "passed": succeeded} for name in suite.REQUIRED_CHECKS[:2]
        )

    def workflow(report, key_env):
        report["checks"].extend(
            {"name": name, "passed": True} for name in suite.REQUIRED_CHECKS[2:]
        )

    monkeypatch.setenv("DEEPSEEK_API_KEY", "not-a-real-credential")
    monkeypatch.setattr(suite, "protocol", protocol)
    monkeypatch.setattr(suite, "workflow", workflow)
    monkeypatch.setattr(suite, "REPORT_PATH", tmp_path / "report.json")

    assert suite.main(["--live"]) == (0 if succeeded else 1)


def test_main_requires_environment_in_noninteractive_mode(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setattr(suite.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(suite.getpass, "getpass", lambda *args: pytest.fail("must not prompt"))

    with pytest.raises(SystemExit) as caught:
        suite.main(["--live"])

    assert caught.value.code == 2
