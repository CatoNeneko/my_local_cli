model_config = {
    "provider": "ollama",
    "api_key_env": "OPENAI_API_KEY",
    "base_url": "http://localhost:11434",
    "model": "qwen3.8-27b-mtp:latest",
    "stream": True,
    "max_response_bytes": 1048576
}

agent_config = {
    "max_rounds": 8,
    "max_tool_calls": 12
}

# 字符数是可观察的近似预算，不是模型 tokenizer 的精确 token 数。
context_config = {
    "max_request_chars": 64000,
    "max_history_turns": 12,
    "auto_compact": True,
    "compact_threshold": 0.8,
    "compact_keep_turns": 2,
    "compact_input_chars": 24000,
    "compact_max_batches": 6,
    "compact_timeout_seconds": 30
}

search_config = {
    "max_files": 500,
    "max_file_bytes": 1048576,
    "max_total_bytes": 8388608,
    "max_matches": 100,
    "max_output_chars": 16000,
    "timeout_seconds": 3,
    "ignored_directories": ["__pycache__", "node_modules", "dist", "build", ".pytest_cache"]
}

sandbox_config = {
    "timeout_seconds": 30,
    "max_output_bytes": 65536,
    "max_output_chars": 16000
}


permission_config = {
    "blocked_names": [
        ".git", ".aws", ".codex", ".agents", ".idea", ".conda-env",
        ".venv", ".venv.windows", ".browser-runtime", ".browser-artifacts", ".env", "history.json", "history.jsonl",
        "tool_events.jsonl", "sessions", ".ai-cli"
    ],
    "confirmation": {
        "model": {"read": False, "write": True, "execute": True},
        "user": {"read": False, "write": True, "execute": True}
    }
}

# 仅由本地配置指定启动命令；不接受模型提供的命令。
mcp_config = {
    "demo": {
        "command": ".conda-env/bin/python",
        "args": ["mcp_servers/demo_server.py"],
        "timeout_seconds": 10
    },
    "browser": {
        "command": ".conda-env/bin/python",
        "args": ["mcp_servers/browser_server.py"],
        "timeout_seconds": 30
    }
}

# Hook 名称对应 hooks.py 中的可信本地函数；工具参数不能指定 Hook。
hooks_config = {
    "before_tool": ["deny_configured_tools"],
    "after_tool": ["report_write_result"],
    "denied_tools": []
}

# 程序化工具调用默认保留人工审批；交互 CLI 默认启用 auto。
approval_config = {"mode": "manual", "review_timeout_seconds": 20}
