import json
from copy import deepcopy
from unittest.mock import Mock

import pytest
import compaction
import context_window
import history
import model_client
from config import context_config
from sessions import SessionManager
from workspace import use_workspace


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setitem(context_config, "max_request_chars", 64000)
    monkeypatch.setitem(context_config, "max_history_turns", 12)
    monkeypatch.setitem(context_config, "auto_compact", True)
    monkeypatch.setitem(context_config, "compact_keep_turns", 2)
    monkeypatch.setitem(context_config, "compact_input_chars", 24000)
    monkeypatch.setattr(compaction, "FAILURES", {})
    summarize = Mock(
        return_value={"content": "用户目标是修复 calc.py；原测试未改。工具结果表明 1 passed。"}
    )
    monkeypatch.setattr(model_client, "request_message", summarize)
    with use_workspace(tmp_path):
        yield tmp_path, summarize


def turns(count=5):
    result = []
    for number in range(count):
        result += [
            {"role": "user", "content": f"任务{number}: 修复 calc.py"},
            {"role": "assistant", "content": f"答复{number}"},
        ]
    return result


def stored_messages(count=5):
    messages = turns(count)
    history.append_messages(messages)
    return messages


def test_manual_checkpoint_preserves_raw_history_and_recent_turns(project):
    _, summarize = project
    messages = stored_messages()
    raw = history.HISTORY_PATH.read_bytes()
    original = deepcopy(messages)
    result = compaction.compact_messages(messages, [])
    assert result["ok"] and result["changed"]
    assert history.HISTORY_PATH.read_bytes().startswith(raw)
    assert messages[:-1] == original
    assert history.load_history() == messages
    context = context_window.prepare_context(messages, [])
    assert context["messages"][-4:] == original[-4:]
    assert context["summarized_messages"] == 6
    assert context["summary_chars"] > 0
    assert not any("任务0:" in row["content"] for row in context["messages"])
    assert any(
        row["role"] == "assistant" and row["content"].startswith(compaction.SUMMARY_LABEL)
        for row in context["messages"]
    )
    assert summarize.call_args.kwargs["use_tools"] is False
    assert summarize.call_args.kwargs["include_context"] is False


def test_restart_rename_switch_and_clear_preserve_session_independence(project):
    path, _ = project
    manager = SessionManager()
    messages = stored_messages()
    assert compaction.compact_messages(messages, [])["ok"]
    assert manager.rename("work")["ok"]
    manager.switch("other")
    assert not compaction.context_view(history.load_history())["summary"]
    restored = manager.switch("work")["messages"]
    assert compaction.context_view(restored)["summary"]
    # 新进程管理器从默认入口进入重命名后的会话。
    history.HISTORY_PATH = manager.default_path
    restarted = SessionManager()
    assert compaction.context_view(restarted.switch("work")["messages"])["summary"]
    history.clear_history()
    assert not compaction.context_view(history.load_history())["summary"]


def test_recompression_uses_previous_summary_and_new_old_messages_only(project):
    _, summarize = project
    messages = stored_messages()
    assert compaction.compact_messages(messages, [])["ok"]
    old_summary = compaction.context_view(messages)["summary"]
    more = [{"role": "user", "content": "新任务"}, {"role": "assistant", "content": "新的答复"}]
    history.append_messages(more)
    messages.extend(more)
    assert compaction.compact_messages(messages, [])["ok"]
    payload = json.loads(summarize.call_args.args[0][1]["content"])
    assert payload["previous_summary"] == old_summary
    assert "任务3:" in str(payload["records"]) and "任务0:" not in str(payload["records"])


@pytest.mark.parametrize(
    "reply",
    [
        None,
        {"content": ""},
        {"content": 3},
        {"content": "x" * 4001},
        {"content": "summary", "tool_calls": [{}]},
    ],
)
def test_bad_summary_never_changes_history_or_memory(project, reply):
    _, summarize = project
    messages = stored_messages()
    before = deepcopy(messages)
    raw = history.HISTORY_PATH.read_bytes()
    summarize.return_value = reply
    assert not compaction.compact_messages(messages, [])["ok"]
    assert messages == before and history.HISTORY_PATH.read_bytes() == raw


@pytest.mark.parametrize("error", [TimeoutError, KeyboardInterrupt])
def test_failed_or_cancelled_summary_keeps_history(project, error):
    _, summarize = project
    messages = stored_messages()
    before = deepcopy(messages)
    summarize.side_effect = error
    result = compaction.compact_messages(messages, [])
    assert not result["ok"]
    assert bool(result.get("cancelled")) == (error is KeyboardInterrupt)
    assert history.load_history() == before and messages == before


def test_history_changed_during_summary_is_not_overwritten(project):
    _, summarize = project
    messages = stored_messages()

    def change(*args, **kwargs):
        history.append_message({"role": "user", "content": "另一个进程写入"})
        return {"content": "摘要"}

    summarize.side_effect = change
    assert not compaction.compact_messages(messages, [])["ok"]
    assert history.load_history()[-1]["content"] == "另一个进程写入"
    assert not any(compaction.is_checkpoint(row) for row in messages)


def test_changed_history_invalidates_prefix_digest(project):
    _, _ = project
    messages = stored_messages()
    assert compaction.compact_messages(messages, [])["ok"]
    messages[0]["content"] = "已变化"
    assert not compaction.context_view(messages)["summary"]
    assert context_window.prepare_context(messages, [])["summarized_messages"] == 0


def test_auto_compaction_trigger_and_off_setting(project, monkeypatch):
    _, summarize = project
    monkeypatch.setitem(context_config, "max_history_turns", 3)
    messages = stored_messages()
    compaction.maybe_compact(messages, [])
    assert compaction.context_view(messages)["summary"]
    assert summarize.call_count == 1
    monkeypatch.setitem(context_config, "auto_compact", False)
    more = turns(5)
    history.append_messages(more)
    messages.extend(more)
    compaction.maybe_compact(messages, [])
    assert summarize.call_count == 1


def test_auto_threshold_uses_full_request_before_old_turns_are_dropped(project, monkeypatch):
    _, summarize = project
    monkeypatch.setitem(context_config, "compact_threshold", 0.01)
    messages = stored_messages()
    compaction.maybe_compact(messages, [])
    summarize.assert_called_once()


def test_auto_failure_not_retried_for_same_old_prefix(project, monkeypatch):
    _, summarize = project
    monkeypatch.setitem(context_config, "max_history_turns", 3)
    messages = stored_messages()
    summarize.side_effect = TimeoutError
    compaction.maybe_compact(messages, [])
    compaction.maybe_compact(messages, [])
    assert summarize.call_count == 1
    assert not compaction.context_view(messages)["summary"]


def test_recent_tool_calls_and_ids_stay_complete(project):
    messages = stored_messages(3)
    chain = [
        {"role": "user", "content": "读取"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {"id": "call1", "function": {"name": "read_file", "arguments": {"path": "a.py"}}}
            ],
        },
        {
            "role": "tool",
            "tool_name": "read_file",
            "tool_call_id": "call1",
            "content": '{"ok":true}',
        },
        {"role": "assistant", "content": "已读取"},
    ]
    history.append_messages(chain)
    messages.extend(chain)
    assert compaction.compact_messages(messages, [])["ok"]
    prepared = context_window.prepare_context(messages, [])
    assert prepared["messages"][-4:] == chain
    assert context_window.valid_turn(chain)


def test_incomplete_or_oversized_latest_chain_is_never_discarded(project, monkeypatch):
    _, summarize = project
    messages = stored_messages()
    unfinished = [
        {"role": "user", "content": "读取"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [{"function": {"name": "read_file", "arguments": {"path": "a.py"}}}],
        },
    ]
    history.append_messages(unfinished)
    messages.extend(unfinished)
    assert not compaction.compact_messages(messages, [])["ok"]
    summarize.assert_not_called()
    assert messages[-2:] == unfinished


def test_oversized_latest_input_cannot_be_fixed_by_summary(project):
    _, summarize = project
    messages = stored_messages()
    oversized = {"role": "user", "content": "x" * 70000}
    history.append_message(oversized)
    messages.append(oversized)
    assert not compaction.compact_messages(messages, [])["ok"]
    summarize.assert_not_called()


def test_summary_excerpts_large_old_record_and_marks_loss(project):
    _, summarize = project
    messages = turns(5)
    messages[1]["content"] = "old output " * 2000
    history.append_messages(messages)
    result = compaction.compact_messages(messages, [])
    assert result["ok"] and result["excerpted_records"] == 1
    payload = json.loads(summarize.call_args.args[0][1]["content"])
    assert any(row["truncated"] for row in payload["records"])


def test_short_history_needs_no_model_and_raw_list_is_unchanged(project):
    _, summarize = project
    messages = stored_messages(2)
    result = compaction.compact_messages(messages, [])
    assert result["ok"] and not result["changed"]
    summarize.assert_not_called()


def test_memory_only_messages_cannot_write_checkpoint(project):
    _, summarize = project
    assert not compaction.compact_messages(turns(5), [])["ok"]
    summarize.assert_not_called()


def test_multiple_summary_batches_merge_prior_summary_without_tools(project):
    _, summarize = project
    messages = turns(10)
    for index in range(1, len(messages), 2):
        messages[index]["content"] = "long old record " + "x" * 3900
    history.append_messages(messages)

    def summarize_batch(rows, **kwargs):
        payload = json.loads(rows[1]["content"])
        if summarize.call_count > 1:
            assert payload["previous_summary"].startswith("batch ")
        return {"content": "batch " + str(summarize.call_count)}

    summarize.side_effect = summarize_batch
    result = compaction.compact_messages(messages, [])
    assert result["ok"] and result["batches"] > 1
    assert all(
        call.kwargs["use_tools"] is False and call.kwargs["include_context"] is False
        for call in summarize.call_args_list
    )


def test_checkpoint_save_failure_does_not_activate_summary(project, monkeypatch):
    _, _ = project
    messages = stored_messages()
    before = deepcopy(messages)
    monkeypatch.setattr(history, "append_message", Mock(side_effect=OSError))
    assert not compaction.compact_messages(messages, [])["ok"]
    assert messages == before
    assert not compaction.context_view(messages)["summary"]


def test_cli_manual_and_auto_controls_operate_on_current_session(project, monkeypatch, capsys):
    import script

    _, summarize = project
    stored_messages()

    class NoServices:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(script, "MCPManager", NoServices)
    inputs = iter(
        [
            "/compact status",
            "/compact auto off",
            "/compact",
            "/context",
            "/compact auto on",
            "/exit",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    script.main(plain=True, no_mcp=True)
    text = capsys.readouterr().out
    assert "自动压缩: off" in text and "自动压缩: on" in text
    assert "已摘要消息:" in text
    assert context_config["auto_compact"] is True
    assert compaction.context_view(history.load_history())["summary"]
    summarize.assert_called_once()
