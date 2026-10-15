"""检查安装清单的运行入口、必要资源与发布边界；不触发构建或网络。"""

import ast
from fnmatch import fnmatch
from pathlib import Path
import tomllib
import zipfile

from scripts.package_project import build_package, source_files


ROOT = Path(__file__).resolve().parents[1]


def metadata():
    with (ROOT / "pyproject.toml").open("rb") as file:
        return tomllib.load(file)


def test_install_metadata_declares_cli_web_and_single_dependency_source():
    document = metadata()
    project = document["project"]
    assert project["name"] == "local-ai-cli"
    assert project["version"] == "0.2.0" and project["requires-python"] == ">=3.12"
    assert project["scripts"] == {"ai-cli": "cli:main", "ai-cli-web": "web.__main__:main"}
    assert "dependencies" in project["dynamic"]
    assert "dependencies" not in project
    assert document["tool"]["setuptools"]["dynamic"]["dependencies"]["file"] == ["requirements.txt"]
    assert document["build-system"]["build-backend"] == "setuptools.build_meta"


def test_explicit_runtime_modules_include_worker_and_cover_local_imports():
    modules = metadata()["tool"]["setuptools"]["py-modules"]
    assert len(modules) == len(set(modules))
    assert {"cli", "config", "script", "workspace", "subagent_worker"} <= set(modules)
    assert not {"demo", "secrets", "practice", "test_cli"} & set(modules)
    root_modules = {path.stem for path in ROOT.glob("*.py")}
    runtime_sources = [ROOT / f"{module}.py" for module in modules]
    runtime_sources += list((ROOT / "harness").rglob("*.py"))
    runtime_sources += list((ROOT / "web").glob("*.py"))
    runtime_sources += list((ROOT / "mcp_servers").glob("*.py"))
    for source in runtime_sources:
        assert source.is_file()
        tree = ast.parse(source.read_text(), filename=str(source))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imports = [node.module.split(".")[0]]
            else:
                continue
            for module in imports:
                if module in root_modules:
                    assert module in modules, f"{source.name} 所需模块 {module} 未分发"


def test_package_discovery_only_includes_runtime_packages_and_web_assets():
    settings = metadata()["tool"]["setuptools"]
    discovery = settings["packages"]["find"]
    for package in ("harness", "harness.tasks", "web", "mcp_servers"):
        assert any(fnmatch(package, pattern) for pattern in discovery["include"])
    for package in ("tests", "scripts", "private", "examples", "web_private"):
        assert not any(fnmatch(package, pattern) for pattern in discovery["include"])
    assert discovery["namespaces"] is False
    for package in ("harness", "web", "mcp_servers"):
        assert (ROOT / package / "__init__.py").is_file()
    patterns = settings["package-data"]["web"]
    for asset in ("static/index.html", "static/app.js", "static/style.css"):
        assert (ROOT / "web" / asset).is_file()
        assert any(fnmatch(asset, pattern) for pattern in patterns)


def test_source_archive_includes_installation_inputs_and_new_acceptance_files(tmp_path):
    expected = {
        "pyproject.toml",
        "requirements.txt",
        "environment.yml",
        "config.example.toml",
        "mcp_servers/__init__.py",
        "mcp_servers/browser_server.py",
        "tests/test_distribution.py",
        "scripts/ui_readability_acceptance.py",
        "harness/configuration.py",
        "web/static/index.html",
    }
    for name in expected | {"secrets.py", "private/token.txt", "history.jsonl"}:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("placeholder")
    assert {path.relative_to(tmp_path).as_posix() for path in source_files(tmp_path)} == expected
    destination = tmp_path / "source.zip"
    assert build_package(destination, tmp_path) == len(expected)
    with zipfile.ZipFile(destination) as archive:
        assert set(archive.namelist()) == {"local-ai-cli/" + name for name in expected}
