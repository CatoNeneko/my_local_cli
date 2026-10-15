# config.py：源码导读

模型、预算、权限、沙箱、MCP、Hook与审批配置字典；不保存真实API密钥。

实际源码：[config.py](../../../config.py)。

快照 SHA256：`2c7a99933f32c98dd741c5f6f57a0132cd4d0c41b5e81e2254da5f6c5426810a`；78 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 1 | `model_config = {'provider': 'ollama', 'api_key_env': 'OPENAI_API_KEY', 'base_url': 'http://localhost:11434', 'model': 'qwen3.8-27b-mtp:latest', 'stream': True, 'max_respo…（见完整源码）` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 10 | `agent_config = {'max_rounds': 8, 'max_tool_calls': 12}` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 16 | `context_config = {'max_request_chars': 64000, 'max_history_turns': 12, 'auto_compact': True, 'compact_threshold': 0.8, 'compact_keep_turns': 2, 'compact_input_chars': 240…（见完整源码）` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 27 | `search_config = {'max_files': 500, 'max_file_bytes': 1048576, 'max_total_bytes': 8388608, 'max_matches': 100, 'max_output_chars': 16000, 'timeout_seconds': 3, 'ignored_di…（见完整源码）` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 37 | `sandbox_config = {'timeout_seconds': 30, 'max_output_bytes': 65536, 'max_output_chars': 16000}` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 44 | `permission_config = {'blocked_names': ['.git', '.aws', '.codex', '.agents', '.idea', '.conda-env', '.venv', '.venv.windows', '.browser-runtime', '.browser-artifacts', '.e…（见完整源码）` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 57 | `mcp_config = {'demo': {'command': '.conda-env/bin/python', 'args': ['mcp_servers/demo_server.py'], 'timeout_seconds': 10}, 'browser': {'command': '.conda-env/bin/python',…（见完整源码）` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 71 | `hooks_config = {'before_tool': ['deny_configured_tools'], 'after_tool': ['report_write_result'], 'denied_tools': []}` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 78 | `approval_config = {'mode': 'manual', 'review_timeout_seconds': 20}` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

本文件没有函数定义。配置/入口可能在文件级执行；空文件则没有行为。


## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。


## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | model_config = {
0002 |     "provider": "ollama",
0003 |     "api_key_env": "OPENAI_API_KEY",
0004 |     "base_url": "http://localhost:11434",
0005 |     "model": "qwen3.8-27b-mtp:latest",
0006 |     "stream": True,
0007 |     "max_response_bytes": 1048576
0008 | }
0009 | 
0010 | agent_config = {
0011 |     "max_rounds": 8,
0012 |     "max_tool_calls": 12
0013 | }
0014 | 
0015 | # 字符数是可观察的近似预算，不是模型 tokenizer 的精确 token 数。
0016 | context_config = {
0017 |     "max_request_chars": 64000,
0018 |     "max_history_turns": 12,
0019 |     "auto_compact": True,
0020 |     "compact_threshold": 0.8,
0021 |     "compact_keep_turns": 2,
0022 |     "compact_input_chars": 24000,
0023 |     "compact_max_batches": 6,
0024 |     "compact_timeout_seconds": 30
0025 | }
0026 | 
0027 | search_config = {
0028 |     "max_files": 500,
0029 |     "max_file_bytes": 1048576,
0030 |     "max_total_bytes": 8388608,
0031 |     "max_matches": 100,
0032 |     "max_output_chars": 16000,
0033 |     "timeout_seconds": 3,
0034 |     "ignored_directories": ["__pycache__", "node_modules", "dist", "build", ".pytest_cache"]
0035 | }
0036 | 
0037 | sandbox_config = {
0038 |     "timeout_seconds": 30,
0039 |     "max_output_bytes": 65536,
0040 |     "max_output_chars": 16000
0041 | }
0042 | 
0043 | 
0044 | permission_config = {
0045 |     "blocked_names": [
0046 |         ".git", ".aws", ".codex", ".agents", ".idea", ".conda-env",
0047 |         ".venv", ".venv.windows", ".browser-runtime", ".browser-artifacts", ".env", "history.json", "history.jsonl",
0048 |         "tool_events.jsonl", "sessions", ".ai-cli"
0049 |     ],
0050 |     "confirmation": {
0051 |         "model": {"read": False, "write": True, "execute": True},
0052 |         "user": {"read": False, "write": True, "execute": True}
0053 |     }
0054 | }
0055 | 
0056 | # 仅由本地配置指定启动命令；不接受模型提供的命令。
0057 | mcp_config = {
0058 |     "demo": {
0059 |         "command": ".conda-env/bin/python",
0060 |         "args": ["mcp_servers/demo_server.py"],
0061 |         "timeout_seconds": 10
0062 |     },
0063 |     "browser": {
0064 |         "command": ".conda-env/bin/python",
0065 |         "args": ["mcp_servers/browser_server.py"],
0066 |         "timeout_seconds": 30
0067 |     }
0068 | }
0069 | 
0070 | # Hook 名称对应 hooks.py 中的可信本地函数；工具参数不能指定 Hook。
0071 | hooks_config = {
0072 |     "before_tool": ["deny_configured_tools"],
0073 |     "after_tool": ["report_write_result"],
0074 |     "denied_tools": []
0075 | }
0076 | 
0077 | # 程序化工具调用默认保留人工审批；交互 CLI 默认启用 auto。
0078 | approval_config = {"mode": "manual", "review_timeout_seconds": 20}
```
