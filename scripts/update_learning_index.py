"""从当前 Python 源码刷新离线导航与逐文件索引。"""

import argparse
import ast
import json
from pathlib import Path, PurePosixPath
import re
import tomllib


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "docs/learning/index.html"
SOURCE_INDEX_PATH = ROOT / "docs/learning/09-source-index.md"
DATA_SCRIPT = re.compile(
    r"(<script\b(?=[^>]*\bid\s*=\s*[\"\']data[\"\'])[^>]*>)(.*?)(</script\s*>)",
    re.IGNORECASE | re.DOTALL,
)
EXCLUDED_PARTS = {
    ".browser-runtime",
    ".conda-env",
    ".venv",
    "artifacts",
    "build",
    "dist",
    "env",
    "node_modules",
    "tests",
    "venv",
    "__pycache__",
}
SOURCE_INDEX_INTRO = (
    "`source/` 下的逐文件说明和行号源码是较早教程留下的历史快照，可能包含旧路径和旧行为。"
    "本表与 [离线源码导航](index.html) 可由 `scripts/update_learning_index.py` 按当前源码刷新；"
    "链接指向实际源码。升级内容见 [0.2.0 升级指南](../PRODUCT_UPGRADE.md)。"
    "静态调用只是 AST 中的调用表达式，不是完整运行时调用图。"
)


def _first_line(value):
    if not isinstance(value, str):
        return ""
    lines = value.strip().splitlines()
    return lines[0].strip() if lines else ""


def _numbered(source, start=1):
    return "\n".join(
        f"{number:04d} | {line}" for number, line in enumerate(source.splitlines(), start)
    )


def _qualified_call(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _qualified_call(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    try:
        return ast.unparse(node)
    except (AttributeError, TypeError, ValueError):
        return ""


class _CallCollector(ast.NodeVisitor):
    def __init__(self):
        self.calls = []

    def visit_FunctionDef(self, node):
        return

    def visit_AsyncFunctionDef(self, node):
        return

    def visit_Lambda(self, node):
        return

    def visit_Call(self, node):
        name = _qualified_call(node.func)
        if name:
            self.calls.append(name)
        self.generic_visit(node)


def _signature(node, name):
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    type_params = getattr(node, "type_params", ())
    generic = (
        "[" + ", ".join(ast.unparse(item) for item in type_params) + "]" if type_params else ""
    )
    signature = f"{prefix} {name}{generic}({ast.unparse(node.args)})"
    if node.returns is not None:
        signature += " -> " + ast.unparse(node.returns)
    return signature + ":"


class _FunctionCollector(ast.NodeVisitor):
    def __init__(self, source_lines, old_functions):
        self.source_lines = source_lines
        self.old_functions = old_functions
        self.scope = []
        self.functions = []

    def visit_ClassDef(self, node):
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def _visit_function(self, node):
        name = ".".join((*self.scope, node.name))
        end = node.end_lineno or node.lineno
        code = "\n".join(
            f"{number:04d} | {self.source_lines[number - 1]}"
            for number in range(node.lineno, end + 1)
        )
        calls = _CallCollector()
        for statement in node.body:
            calls.visit(statement)
        old = self.old_functions.get(name, {})
        purpose = old.get("purpose") or _first_line(ast.get_docstring(node))
        self.functions.append(
            {
                "name": name,
                "line": node.lineno,
                "end": end,
                "signature": _signature(node, name),
                "purpose": purpose,
                "calls": list(dict.fromkeys(calls.calls)),
                "code": code,
            }
        )
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node):
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node):
        self._visit_function(node)


def _load_index(html):
    match = DATA_SCRIPT.search(html)
    if match is None:
        raise ValueError("离线索引中缺少 id=data 的 JSON script")
    try:
        rows = json.loads(match.group(2))
    except json.JSONDecodeError as error:
        raise ValueError("离线索引中的 JSON 无法读取") from error
    if not isinstance(rows, list):
        raise ValueError("离线索引数据必须是文件列表")
    return match, rows


def _existing_paths(root, previous):
    paths = []
    for row in previous:
        relative = row.get("file") if isinstance(row, dict) else None
        if not isinstance(relative, str):
            continue
        candidate = PurePosixPath(relative)
        if (
            candidate.is_absolute()
            or ".." in candidate.parts
            or not candidate.parts
            or candidate.parts[0] not in {"mcp_servers", "scripts"}
        ):
            continue
        paths.append(root.joinpath(*candidate.parts))
    return paths


def _source_paths(root, previous):
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    modules = project.get("tool", {}).get("setuptools", {}).get("py-modules", [])
    paths = [
        root / f"{name}.py" for name in modules if isinstance(name, str) and name.isidentifier()
    ]
    harness = root / "harness"
    web = root / "web"
    paths.extend(harness.rglob("*.py") if harness.is_dir() else ())
    paths.extend(web.glob("*.py") if web.is_dir() else ())
    paths.extend(_existing_paths(root, previous))
    # Keep the generator discoverable from its first run as well as every later run.
    paths.append(root / "scripts/update_learning_index.py")

    result = {}
    resolved_root = root.resolve()
    for path in paths:
        try:
            relative = path.relative_to(root).as_posix()
            parts = PurePosixPath(relative).parts
            resolved = path.resolve()
            if (
                any(part in EXCLUDED_PARTS for part in parts)
                or not resolved.is_relative_to(resolved_root)
                or not path.is_file()
            ):
                continue
        except (OSError, ValueError, RuntimeError):
            continue
        result[relative] = path
    return [(relative, result[relative]) for relative in sorted(result)]


def _module_row(root, relative, path, previous_by_file):
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=relative)
    except SyntaxError as error:
        raise ValueError(f"Python 源码无法解析：{relative}:{error.lineno}") from error

    previous = previous_by_file.get(relative, {})
    old_functions = {
        item.get("name"): item
        for item in previous.get("functions", [])
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    source_lines = source.splitlines()
    functions = _FunctionCollector(source_lines, old_functions)
    functions.visit(tree)
    module_purpose = previous.get("purpose") or _first_line(ast.get_docstring(tree))
    return {
        "file": relative,
        "purpose": module_purpose,
        "guide": "../../" + relative,
        "code": _numbered(source),
        "functions": functions.functions,
    }


def _safe_json(rows):
    serialized = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    return re.sub(r"</script", r"<\/script", serialized, flags=re.IGNORECASE)


def _render_html(html, match, rows):
    payload = _safe_json(rows)
    return html[: match.start(2)] + payload + html[match.end(2) :]


def _render_source_index(document, rows, root):
    title = "# 09：逐文件源码导读索引"
    section_marker = "\n## 非Python文件与目录\n"
    if not document.startswith(title + "\n") or section_marker not in document:
        raise ValueError("源码索引文档结构不符合预期")
    suffix = document[document.index(section_marker) :]
    table = [
        "| 文件 | 行数 | 函数/方法/嵌套回调数 | 职责 |",
        "| --- | ---: | ---: | --- |",
    ]
    total_functions = 0
    for row in rows:
        path = row["file"]
        count = len(row["functions"])
        total_functions += count
        source_path = root / path
        line_count = len(source_path.read_text(encoding="utf-8").splitlines())
        purpose = str(row.get("purpose", "")).replace("|", "\\|")
        table.append(f"| [{path}](../../{path}) | {line_count} | {count} | {purpose} |")
    table.append(
        f"共 **{len(rows)}** 个当前 Python 源码文件、**{total_functions}** 个函数/方法/嵌套回调定义。"
        "排除测试、环境、构建和验收产物；下列测试另列索引。"
        "函数位置、签名、静态调用与源码快照由 AST 从当前文件提取。"
    )
    return title + "\n\n" + SOURCE_INDEX_INTRO + "\n\n" + "\n".join(table) + "\n" + suffix


def build_outputs(root=ROOT):
    html_path = root / "docs/learning/index.html"
    source_index_path = root / "docs/learning/09-source-index.md"
    html = html_path.read_text(encoding="utf-8")
    match, previous = _load_index(html)
    previous_by_file = {
        row["file"]: row
        for row in previous
        if isinstance(row, dict) and isinstance(row.get("file"), str)
    }
    rows = [
        _module_row(root, relative, path, previous_by_file)
        for relative, path in _source_paths(root, previous)
    ]
    return {
        html_path: _render_html(html, match, rows),
        source_index_path: _render_source_index(
            source_index_path.read_text(encoding="utf-8"), rows, root
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="刷新当前源码的离线学习导航")
    parser.add_argument(
        "--check", action="store_true", help="只检查导航是否与当前源码一致，陈旧时返回非零"
    )
    args = parser.parse_args(argv)
    try:
        outputs = build_outputs()
    except (OSError, ValueError, tomllib.TOMLDecodeError) as error:
        parser.error(str(error))

    stale = [
        path for path, content in outputs.items() if path.read_text(encoding="utf-8") != content
    ]
    if args.check:
        if stale:
            print("源码导航已过期：" + ", ".join(str(path.relative_to(ROOT)) for path in stale))
            return 1
        print("源码导航与当前源码一致")
        return 0

    for path in stale:
        path.write_text(outputs[path], encoding="utf-8")
    if stale:
        print("已更新：" + ", ".join(str(path.relative_to(ROOT)) for path in stale))
    else:
        print("源码导航已是最新")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
