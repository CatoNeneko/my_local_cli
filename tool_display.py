"""工具状态与修改审查的终端展示；不改变工具结果或授权。"""
import sys
import unicodedata


def safe_text(value):
    """把控制字符显示为转义文字，避免文件内容操纵终端。"""
    text = str(value)
    return "".join(
        char if char in "\n\t" or unicodedata.category(char) not in ("Cc", "Cf")
        else "\\u" + format(ord(char), "04x")
        for char in text
    )


def short_text(value, limit=240):
    text = safe_text(value).replace("\n", "\\n").replace("\t", "\\t")
    return text if len(text) <= limit else text[:limit] + "…（摘要截断）"


def emit(text, color=""):
    text = safe_text(text)
    if color and sys.stdout.isatty():
        from prompt_toolkit import print_formatted_text
        from prompt_toolkit.formatted_text import FormattedText
        print_formatted_text(FormattedText([(color, text)]))
    else:
        print(text, flush=True)


def tool_started(name, arguments):
    emit("[执行中] " + short_text(name), "ansicyan")
    if isinstance(arguments, dict):
        # 不打印整份 new_content 或未知 MCP 参数中的敏感内容。
        for key, label in (("path", "目标"), ("keyword", "关键词"), ("glob", "文件过滤")):
            if key in arguments:
                emit("  " + label + ": " + short_text(arguments[key]))


def tool_finished(name, result):
    succeeded = result["ok"]
    label = '已取消' if result.get('cancelled') else "成功" if succeeded else "失败/未执行"
    emit("[" + label + "] " + short_text(name), "ansigreen" if succeeded else "ansired")
    if not succeeded:
        emit("  原因: " + short_text(result.get("error", "工具未成功")))
    elif "message" in result:
        emit("  " + short_text(result["message"]))
    elif isinstance(result.get("content"), str):
        emit("  返回文字: " + str(len(result["content"])) + " 字符")
    for key, label in (("matches", "匹配行"), ("entries", "目录项")):
        if isinstance(result.get(key), list):
            emit("  " + label + ": " + str(len(result[key])))
    if "exit_code" in result:
        emit("  退出码: " + short_text(result["exit_code"]))
    if isinstance(result.get("output"), str) and result["output"]:
        emit("  测试输出摘要: " + short_text(result["output"], 800))
    if result.get("truncated") or result.get("output_truncated"):
        emit("  注意: 工具返回的数据已截断", "ansiyellow")
    if result.get("hook_warning"):
        emit("  Hook 警告: " + short_text(result["hook_warning"]), "ansiyellow")


def show_diff(diff):
    added = sum(line.startswith("+") and not line.startswith("+++") for line in diff.splitlines())
    removed = sum(line.startswith("-") and not line.startswith("---") for line in diff.splitlines())
    emit("[待审查修改] +" + str(added) + " / -" + str(removed) + " 行", "ansiyellow")
    for line in diff.splitlines():
        color = "ansigreen" if line.startswith("+") else "ansired" if line.startswith("-") else ""
        emit(line, color)
    emit("[审查结束] 审批通过后才会写入；以上控制字符已转义显示。", "ansiyellow")
