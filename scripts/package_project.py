"""生成供上传的源码包；使用显式目录与文件清单，不包含本机历史、凭据或环境。"""

from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = """AGENTS.md README.md README.en.md CHANGELOG.md environment.yml requirements.txt requirements-dev.txt pyproject.toml config.example.toml .gitignore ai-cli
agent.py agent_proposals.py api_adapter.py approval.py browser_runtime.py attachments.py audit.py cli.py
command_help.py compaction.py config.py console_output.py context_window.py file_catalog.py file_picker.py
file_tools.py history.py hooks.py mcp_client.py mcp_manager.py mcp_tools.py model_client.py
new_files.py patches.py path_input.py permissions.py project_instructions.py
project_search.py sandbox.py script.py sessions.py skill_files.py skill_generation.py skills.py
streaming.py subagent_worker.py terminal_dialog.py terminal_input.py tool_display.py
tool_registry.py tool_runtime.py tools.py workspace.py""".split()


def source_files(root=ROOT):
    selected = [root / name for name in ROOT_FILES]
    for directory, pattern in (
        ("tests", "test_*.py"),
        ("docs", "*.md"),
        ("examples/acceptance_seed", "*"),
        ("examples/acceptance_verify", "*.txt"),
    ):
        selected.extend(
            path
            for path in sorted((root / directory).glob(pattern))
            if path != root / "docs/INTERVIEW.md"
        )
    selected.extend(sorted((root / "docs/learning").rglob("*.md")))
    selected.extend(
        root / name for name in ("docs/learning/architecture.svg", "docs/learning/index.html")
    )
    selected.extend(sorted((root / "web").glob("*.py")))
    selected.extend(sorted((root / "harness").rglob("*.py")))
    selected.extend(sorted((root / "web/static").glob("*.html")))
    selected.extend(sorted((root / "web/static").glob("*.js")))
    selected.extend(sorted((root / "web/static").glob("*.css")))
    selected.extend(
        root / name
        for name in (
            "web.env.example",
            "scripts/web_acceptance.py",
            "scripts/task_agent_acceptance.py",
            "scripts/writable_agent_acceptance.py",
            "scripts/evaluate_workbench.py",
            "scripts/glm_api_probe.py",
            "scripts/live_api_acceptance.py",
            "scripts/ui_readability_acceptance.py",
            "scripts/distribution_acceptance.py",
            "scripts/changeset_acceptance.py",
            "scripts/update_learning_index.py",
        )
    )
    selected.extend(
        root / name
        for name in (
            "scripts/acceptance.py",
            "scripts/approval_acceptance.py",
            "scripts/compaction_acceptance.py",
            "scripts/browser_acceptance.py",
            "scripts/package_project.py",
            "mcp_servers/__init__.py",
            "mcp_servers/demo_server.py",
            "mcp_servers/browser_server.py",
            ".github/workflows/tests.yml",
        )
    )
    return [
        path
        for path in selected
        if path.is_file()
        and not any(
            item.is_symlink() for item in (path, *path.parents) if item.is_relative_to(root)
        )
    ]


def build_package(destination, root=ROOT):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    paths = source_files(root)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            archive.write(path, "local-ai-cli/" + path.relative_to(root).as_posix())
    return len(paths)


if __name__ == "__main__":
    target = ROOT / "artifacts/distribution/local-ai-cli-source.zip"
    count = build_package(target)
    print(f"已打包 {count} 个源码文件: {target}")
