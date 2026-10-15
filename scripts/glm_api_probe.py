"""仅由已授权 WSL gateway 入口运行的有界真实 API 联测。"""

import contextlib
import fcntl
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import time
import urllib.error
import urllib.request
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
MARKER = "probe-result: cedar-bridge-7319"


def run_probe(gateway):
    from config import model_config
    from model_client import request_message
    from tool_registry import TOOL_REGISTRY
    from tool_runtime import execute_tool
    from workspace import use_workspace

    report = {
        "provider": "must-openhub",
        "model": gateway.MODEL,
        "real_model_called": False,
        "requests": [],
        "checks": {},
    }
    key = gateway.credential()
    endpoint = gateway.BASE + "/chat/completions"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), gateway.NoRedirect())

    class Transport:
        @contextlib.contextmanager
        def open(self, request, timeout=30):
            if request.full_url != endpoint or len(report["requests"]) >= 4:
                raise ValueError("probe transport boundary")
            payload = json.loads(request.data)
            if payload["model"] != gateway.MODEL:
                raise ValueError("probe model boundary")
            payload.update(max_tokens=1024, thinking={"type": "disabled"})
            request.data = json.dumps(payload, ensure_ascii=False).encode()
            fd = os.open(
                gateway.STATE / "gateway-request.lock",
                os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC,
                0o600,
            )
            record = {
                "stream": payload["stream"],
                "http_status": None,
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None,
            }
            captured = bytearray()
            try:
                info = os.fstat(fd)
                if info.st_uid != os.getuid() or not stat.S_ISREG(info.st_mode):
                    raise ValueError("probe lock boundary")
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                if gateway.cooldown_status()["active"]:
                    raise RuntimeError("gateway cooldown active")
                report["requests"].append(record)
                report["real_model_called"] = True
                try:
                    with opener.open(request, timeout=min(timeout, 30)) as response:
                        record["http_status"] = response.status

                        class Capture:
                            def read(self, size=-1):
                                data = response.read(size)
                                captured.extend(data)
                                return data

                            def readline(self, size=-1):
                                data = response.readline(size)
                                captured.extend(data)
                                return data

                        yield Capture()
                except urllib.error.HTTPError as error:
                    record["http_status"] = error.code
                    if error.code == 429 or error.code >= 500:
                        gateway.set_cooldown(error.code)
                    error.close()
                    raise RuntimeError("gateway HTTP failure") from None
                except (TimeoutError, urllib.error.URLError, OSError):
                    gateway.set_cooldown(None)
                    raise
                finally:
                    # 只保留服务实际提供的用量，不保存请求、回复或凭据。
                    try:
                        if payload["stream"]:
                            parts = [
                                json.loads(line[5:])
                                for line in captured.decode().splitlines()
                                if line.startswith("data:") and "[DONE]" not in line
                            ]
                            usages = [
                                part["usage"]
                                for part in parts
                                if isinstance(part.get("usage"), dict)
                            ]
                            usage = usages[-1] if usages else {}
                        else:
                            usage = json.loads(captured).get("usage") or {}
                        for name in ("prompt_tokens", "completion_tokens", "total_tokens"):
                            value = usage.get(name)
                            if type(value) is int and value >= 0:
                                record[name] = value
                    except (ValueError, UnicodeError, KeyError, TypeError):
                        pass
                    with gateway.lock("usage.lock"):
                        with (gateway.STATE / "provider_usage.jsonl").open("a") as log:
                            log.write(
                                json.dumps(
                                    record
                                    | {
                                        "provider": "must-openhub",
                                        "model": gateway.MODEL,
                                        "job_id": "cli-api-probe",
                                        "timestamp": time.time(),
                                    }
                                )
                                + "\n"
                            )
            finally:
                os.close(fd)

    environment = {"CLI_GLM_PROBE_KEY": key}
    config = {
        "provider": "openai",
        "base_url": gateway.BASE,
        "model": gateway.MODEL,
        "api_key_env": "CLI_GLM_PROBE_KEY",
        "max_response_bytes": 262144,
    }
    with tempfile.TemporaryDirectory(prefix="cli-api-probe-") as temporary:
        root = Path(temporary)
        (root / "fixture.txt").write_text(MARKER)
        with (
            use_workspace(root),
            patch.dict(os.environ, environment),
            patch.dict(model_config, config),
            patch.dict(TOOL_REGISTRY, {"read_file": TOOL_REGISTRY["read_file"]}, clear=True),
            patch.object(urllib.request, "build_opener", return_value=Transport()),
        ):
            for stream in (False, True):
                label = "stream" if stream else "nonstream"
                messages = [
                    {
                        "role": "system",
                        "content": "这是读取工具联测。必须调用 read_file 读取 fixture.txt，禁止猜测内容。取得结果后只复述文件内容。",
                    },
                    {"role": "user", "content": "请读取 fixture.txt 并告诉我实际内容。"},
                ]
                try:
                    first = request_message(
                        messages, include_context=False, stream=stream, timeout=30
                    )
                    calls = first.get("tool_calls", [])
                    valid = (
                        len(calls) == 1
                        and calls[0]["function"]["name"] == "read_file"
                        and calls[0]["function"]["arguments"] == {"path": "fixture.txt"}
                    )
                    report["checks"][label + "_tool_call"] = valid
                    if not valid:
                        break
                    with contextlib.redirect_stdout(sys.stderr):
                        result = execute_tool("read_file", {"path": "fixture.txt"})
                    report["checks"][label + "_runtime_read"] = (
                        result.get("ok") is True and result.get("content") == MARKER
                    )
                    messages.extend(
                        [
                            first,
                            {
                                "role": "tool",
                                "tool_call_id": calls[0]["id"],
                                "tool_name": "read_file",
                                "content": json.dumps(result),
                            },
                        ]
                    )
                    final = request_message(
                        messages, include_context=False, use_tools=False, stream=stream, timeout=30
                    )
                    report["checks"][label + "_observed_result"] = MARKER in final[
                        "content"
                    ] and not final.get("tool_calls")
                except Exception as error:
                    report["checks"][label + "_completed"] = False
                    report["error_type"] = type(error).__name__
                    break
    report["passed"] = len(report["checks"]) == 6 and all(report["checks"].values())
    destination = ROOT / "artifacts/evaluation/glm-api-probe.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report
