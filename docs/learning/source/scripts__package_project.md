# scripts/package_project.py：源码导读

白名单源码打包，拒绝符号链接路径，排除本机环境与状态。

先读专题：[08-verification.md](../08-verification.md)。

实际源码：[scripts/package_project.py](../../../scripts/package_project.py)。

快照 SHA256：`332bff5edf90cdf997a5e57db56abf7e31e306e808bc714489aa582a19adce35`；43 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `import zipfile` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 5 | `ROOT = Path(__file__).resolve().parents[1]` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 6 | `ROOT_FILES = 'AGENTS.md README.md environment.yml requirements.txt .gitignore ai-cli\nagent.py agent_proposals.py api_adapter.py approval.py browser_runtime.py attachment…（见完整源码）` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [source_files](#source-files) | [16](../../../scripts/package_project.py#L16) | 显式发布源码清单，拒绝文件及祖先符号链接。 |
| [build_package](#build-package) | [30](../../../scripts/package_project.py#L30) | 将白名单文件写入有统一根目录的ZIP。 |

<a id="source-files"></a>
## source_files

显式发布源码清单，拒绝文件及祖先符号链接。

```python
def source_files(root=ROOT)
```

位置：[16行](../../../scripts/package_project.py#L16) 至快照 27 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `root` | `未显式注解` | 本次目录扫描/工作项目根。 |

**调用表达式（静态提取，不含内层独立函数体）**：`(root / 'docs/learning').rglob`、`(root / directory).glob`、`any`、`item.is_relative_to`、`item.is_symlink`、`path.is_file`、`selected.extend`、`sorted`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 17 | `selected` | `[root / name for name in ROOT_FILES]` | 界面高亮索引，某些主循环分支为选择结果；看当前层次。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 17 | 函数体 | 将 `[root / name for name in ROOT_FILES]` 赋给 `selected`。 |
| 18 | 函数体 | 遍历 `(('tests', 'test_*.py'), ('docs', '*.md'), ('examples/acceptance_seed', '*'), ('examples/acceptance_verify', '*.txt'))`，每次绑定 `(directory, pattern)`。 |
| 20 | 函数体 / 循环每次 | 计算表达式/调用产生动作：`selected.extend(sorted((root / directory).glob(pattern)))`。 |
| 21 | 函数体 | 计算表达式/调用产生动作：`selected.extend(sorted((root / 'docs/learning').rglob('*.md')))`。 |
| 22 | 函数体 | 计算表达式/调用产生动作：`selected.extend((root / name for name in ('docs/learning/architecture.svg', 'docs/learning/index.html')))`。 |
| 23 | 函数体 | 计算表达式/调用产生动作：`selected.extend((root / name for name in ('scripts/acceptance.py', 'scripts/approval_acceptance.py', 'scripts/compaction_acceptance.py', 'scripts/browser_acceptance.py', …（见完整源码）`。 |
| 26 | 函数体 | 返回 `[path for path in selected if path.is_file() and (not any((item.is_symlink() for item in (path, *path.parents) if item.is_relative_to(root))))]`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L26：`[path for path in selected if path.is_file() and (not any((item.is_symlink() for item in (path, *path.parents) if item.is_relative_to(root))))]`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="build-package"></a>
## build_package

将白名单文件写入有统一根目录的ZIP。

```python
def build_package(destination, root=ROOT)
```

位置：[30行](../../../scripts/package_project.py#L30) 至快照 37 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `destination` | `未显式注解` | 新名称/导出/复制发布的目标路径。 |
| `root` | `未显式注解` | 本次目录扫描/工作项目根。 |

**调用表达式（静态提取，不含内层独立函数体）**：`Path`、`archive.write`、`destination.parent.mkdir`、`len`、`path.relative_to`、`path.relative_to(root).as_posix`、`source_files`、`zipfile.ZipFile`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 31 | `destination` | `Path(destination)` | 新名称/导出/复制发布的目标路径。 |
| 33 | `paths` | `source_files(root)` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 31 | 函数体 | 将 `Path(destination)` 赋给 `destination`。 |
| 32 | 函数体 | 计算表达式/调用产生动作：`destination.parent.mkdir(parents=True, exist_ok=True)`。 |
| 33 | 函数体 | 将 `source_files(root)` 赋给 `paths`。 |
| 34 | 函数体 | 进入资源/状态范围：`zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED)` 绑定 `archive`；退出执行清理。 |
| 35 | 函数体 / with范围 | 遍历 `paths`，每次绑定 `path`。 |
| 36 | 函数体 / with范围 / 循环每次 | 计算表达式/调用产生动作：`archive.write(path, 'local-ai-cli/' + path.relative_to(root).as_posix())`。 |
| 37 | 函数体 | 返回 `len(paths)`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L37：`len(paths)`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- with/yield：资源/状态生命周期或逐个生成：L34。
- 推导式/生成器表达式：循环建容器或逐个产生：L17, L22, L23, L26。
- 星号展开：展开已有容器：L27。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """生成供上传的源码包；使用显式目录与文件清单，不包含本机历史、凭据或环境。"""
0002 | from pathlib import Path
0003 | import zipfile
0004 | 
0005 | ROOT = Path(__file__).resolve().parents[1]
0006 | ROOT_FILES = '''AGENTS.md README.md environment.yml requirements.txt .gitignore ai-cli
0007 | agent.py agent_proposals.py api_adapter.py approval.py browser_runtime.py attachments.py audit.py cli.py
0008 | command_help.py compaction.py config.py console_output.py context_window.py file_catalog.py file_picker.py
0009 | file_tools.py history.py hooks.py mcp_client.py mcp_manager.py mcp_tools.py model_client.py
0010 | new_files.py patches.py path_input.py permissions.py process_tasks.py project_instructions.py
0011 | project_search.py sandbox.py script.py sessions.py skill_files.py skill_generation.py skills.py
0012 | streaming.py subagent_worker.py terminal_dialog.py terminal_input.py tool_display.py
0013 | tool_registry.py tool_runtime.py tools.py workspace.py'''.split()
0014 | 
0015 | 
0016 | def source_files(root=ROOT):
0017 |     selected = [root / name for name in ROOT_FILES]
0018 |     for directory, pattern in (('tests', 'test_*.py'), ('docs', '*.md'),
0019 |                                ('examples/acceptance_seed', '*'), ('examples/acceptance_verify', '*.txt')):
0020 |         selected.extend(sorted((root / directory).glob(pattern)))
0021 |     selected.extend(sorted((root / 'docs/learning').rglob('*.md')))
0022 |     selected.extend(root / name for name in ('docs/learning/architecture.svg', 'docs/learning/index.html'))
0023 |     selected.extend(root / name for name in (
0024 |         'scripts/acceptance.py', 'scripts/approval_acceptance.py', 'scripts/compaction_acceptance.py', 'scripts/browser_acceptance.py', 'scripts/package_project.py', 'mcp_servers/demo_server.py', 'mcp_servers/browser_server.py',
0025 |         '.github/workflows/tests.yml'))
0026 |     return [path for path in selected if path.is_file() and not any(
0027 |         item.is_symlink() for item in (path, *path.parents) if item.is_relative_to(root))]
0028 | 
0029 | 
0030 | def build_package(destination, root=ROOT):
0031 |     destination = Path(destination)
0032 |     destination.parent.mkdir(parents=True, exist_ok=True)
0033 |     paths = source_files(root)
0034 |     with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
0035 |         for path in paths:
0036 |             archive.write(path, 'local-ai-cli/' + path.relative_to(root).as_posix())
0037 |     return len(paths)
0038 | 
0039 | 
0040 | if __name__ == '__main__':
0041 |     target = ROOT / 'artifacts/distribution/local-ai-cli-source.zip'
0042 |     count = build_package(target)
0043 |     print(f'已打包 {count} 个源码文件: {target}')
```
