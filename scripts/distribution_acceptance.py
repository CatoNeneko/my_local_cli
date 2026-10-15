"""离线构建 wheel，并在临时环境和仓库外验证安装后的入口与资源。"""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run(argv, cwd, environment):
    result = subprocess.run(
        argv, cwd=cwd, env=environment, text=True, capture_output=True, timeout=90
    )
    if result.returncode:
        raise RuntimeError("离线分发检查失败:\n" + result.stderr[-5000:])
    return result.stdout


def main():
    with tempfile.TemporaryDirectory(prefix="cli-install-") as directory:
        temporary = Path(directory)
        environment = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith(("AI_CLI_", "PYTHONPATH"))
        }
        environment.update(
            XDG_CONFIG_HOME=str(temporary / "config"),
            PYTHONDONTWRITEBYTECODE="1",
            PIP_NO_CACHE_DIR="1",
        )
        wheels = temporary / "wheels"
        run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                "--no-index",
                "--no-deps",
                "--no-build-isolation",
                "--wheel-dir",
                str(wheels),
                str(ROOT),
            ],
            temporary,
            environment,
        )
        wheel = next(wheels.glob("local_ai_cli-*.whl"))
        env_path = temporary / "env"
        run(
            [sys.executable, "-m", "venv", "--system-site-packages", str(env_path)],
            temporary,
            environment,
        )
        python = env_path / "bin/python"
        run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--no-index",
                "--no-deps",
                "--force-reinstall",
                str(wheel),
            ],
            temporary,
            environment,
        )
        executable = env_path / "bin/ai-cli"
        version = run([str(executable), "--version"], temporary, environment).strip()
        help_text = run([str(executable), "--help"], temporary, environment)
        report = json.loads(run([str(executable), "--doctor", "--json"], temporary, environment))
        probe = r"""
import json,sys
from pathlib import Path
from fastapi.testclient import TestClient
from web.app import create_app
from web.settings import Settings
from workspace import APP_ROOT
from mcp_client import prepare_server_connection
from tool_registry import TOOL_REGISTRY
import harness.files.changesets
root=Path.cwd()
assert APP_ROOT != root and APP_ROOT.is_relative_to(Path(sys.prefix))
assert 'apply_changes' in TOOL_REGISTRY
assert (APP_ROOT/'subagent_worker.py').is_file()
assert (APP_ROOT/'mcp_servers/demo_server.py').is_file()
assert prepare_server_connection('demo')['ok']
settings=Settings(root/'state',root)
with TestClient(create_app(settings)) as client:
    assert client.get('/api/health').status_code==200
    assert client.get('/').status_code==200
    response=client.get('/static/markdown.js')
    assert response.status_code==200 and 'HarnessMarkdown' in response.text
    response=client.post('/api/sessions',json={'title':'installed','workspace':str(root)})
    assert response.status_code==201,response.text
print(json.dumps({'installed_outside_checkout':True,'static_assets':True,'mcp_resource':True,
                  'worker_resource':True,'session_api':True}))
"""
        installed = json.loads(run([str(python), "-I", "-c", probe], temporary, environment))
        result = {
            "fixture_only": True,
            "real_model_called": False,
            "version": version,
            "cli_help": "--doctor" in help_text,
            "doctor_ok": report["ok"],
            **installed,
        }
        destination = ROOT / "artifacts/upgrade/distribution.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
