# cli.py：源码导读

argparse启动入口；先解析帮助/参数，再导入和运行主交互。

先读专题：[02-agent.md](../02-agent.md)。

实际源码：[cli.py](../../../cli.py)。

快照 SHA256：`f39f991daa4417caa78d7e94fc61f207d66cbc077fbc632b2824c3f7b8ce7344`；42 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `import argparse` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [build_parser](#build-parser) | [6](../../../cli.py#L6) | 创建启动命令选项与帮助，尚未连接任何模型。 |
| [main](#main) | [20](../../../cli.py#L20) | 解析argv覆盖配置，调用script.main，处理启动/退出异常。 |

<a id="build-parser"></a>
## build_parser

创建启动命令选项与帮助，尚未连接任何模型。

```python
def build_parser()
```

位置：[6行](../../../cli.py#L6) 至快照 17 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**调用表达式（静态提取，不含内层独立函数体）**：`Path.cwd`、`argparse.ArgumentParser`、`parser.add_argument`、`str`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 7 | `parser` | `argparse.ArgumentParser(prog='ai-cli', description='本地 AI 编程助手（开发中）')` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 7 | 函数体 | 将 `argparse.ArgumentParser(prog='ai-cli', description='本地 AI 编程助手（开发中）')` 赋给 `parser`。 |
| 8 | 函数体 | 计算表达式/调用产生动作：`parser.add_argument('--approval-mode', choices=('auto', 'manual'), default='auto', help='auto 自动审批低风险操作，manual 保留逐次确认')`。 |
| 9 | 函数体 | 计算表达式/调用产生动作：`parser.add_argument('--provider', choices=('ollama', 'openai'), help='模型协议')`。 |
| 10 | 函数体 | 计算表达式/调用产生动作：`parser.add_argument('--api-key-env', default='OPENAI_API_KEY', help='保存 API 密钥的环境变量名；不保存密钥')`。 |
| 11 | 函数体 | 计算表达式/调用产生动作：`parser.add_argument('--model', help='覆盖配置中的模型名称')`。 |
| 12 | 函数体 | 计算表达式/调用产生动作：`parser.add_argument('--base-url', help='覆盖模型服务地址')`。 |
| 13 | 函数体 | 计算表达式/调用产生动作：`parser.add_argument('--session', help='启动时进入指定会话，不存在则创建')`。 |
| 14 | 函数体 | 计算表达式/调用产生动作：`parser.add_argument('--plain', action='store_true', help='使用普通 input，关闭增强终端编辑')`。 |
| 15 | 函数体 | 计算表达式/调用产生动作：`parser.add_argument('--no-mcp', action='store_true', help='本次运行不启动 MCP 服务')`。 |
| 16 | 函数体 | 计算表达式/调用产生动作：`parser.add_argument('-C', '--workspace', default=str(Path.cwd()), help='工作目录，默认当前目录')`。 |
| 17 | 函数体 | 返回 `parser`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L17：`parser`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="main"></a>
## main

解析argv覆盖配置，调用script.main，处理启动/退出异常。

```python
def main(argv=None)
```

位置：[20行](../../../cli.py#L20) 至快照 38 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `argv` | `未显式注解` | 待运行程序及参数列表，每项独立，不隐式shell拼接。 |

**调用表达式（静态提取，不含内层独立函数体）**：`args.base_url.rstrip`、`build_parser`、`parser.error`、`parser.parse_args`、`print`、`run_cli`、`str`

**变量/字段定义**：左侧保存右侧结果；重新赋值可能改变后续控制流。业务用途见对应专题及以下语句。

| 行 | 变量/字段 | 来源表达式 | 用途读法 |
| ---: | --- | --- | --- |
| 21 | `parser` | `build_parser()` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 22 | `args` | `parser.parse_args(argv)` | 解析启动参数Namespace或工具参数字典，按来源区分。 |
| 25 | `approval_config['mode']` | `args.approval_mode` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 27 | `model_config['provider']` | `args.provider` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 28 | `model_config['api_key_env']` | `args.api_key_env` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 30 | `model_config['model']` | `args.model` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |
| 32 | `model_config['base_url']` | `args.base_url.rstrip('/')` | 局部状态/计算中间量；名称不足以确定类型，按来源表达式与后续分支追踪。 |

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 21 | 函数体 | 将 `build_parser()` 赋给 `parser`。 |
| 22 | 函数体 | 将 `parser.parse_args(argv)` 赋给 `args`。 |
| 23 | 函数体 | 在此处导入依赖：`from config import model_config, approval_config`；局部导入可延迟加载或避免循环。 |
| 24 | 函数体 | 在此处导入依赖：`from script import main as run_cli`；局部导入可延迟加载或避免循环。 |
| 25 | 函数体 | 将 `args.approval_mode` 赋给 `approval_config['mode']`。 |
| 26 | 函数体 | 条件 `args.provider`：真时执行body，假时进入else/后续。 |
| 27 | 函数体 / 条件为真 | 将 `args.provider` 赋给 `model_config['provider']`。 |
| 28 | 函数体 | 将 `args.api_key_env` 赋给 `model_config['api_key_env']`。 |
| 29 | 函数体 | 条件 `args.model`：真时执行body，假时进入else/后续。 |
| 30 | 函数体 / 条件为真 | 将 `args.model` 赋给 `model_config['model']`。 |
| 31 | 函数体 | 条件 `args.base_url`：真时执行body，假时进入else/后续。 |
| 32 | 函数体 / 条件为真 | 将 `args.base_url.rstrip('/')` 赋给 `model_config['base_url']`。 |
| 33 | 函数体 | 开始异常范围；except处理匹配异常，finally无论成功失败均执行。 |
| 34 | 函数体 / try | 计算表达式/调用产生动作：`run_cli(initial_session=args.session, plain=args.plain, no_mcp=args.no_mcp, workspace=args.workspace)`。 |
| 35 | 函数体 | except ValueError as error：只处理匹配类型的异常。 |
| 36 | 函数体 / except ValueError as error | 计算表达式/调用产生动作：`parser.error(str(error))`。 |
| 37 | 函数体 | except (EOFError, KeyboardInterrupt)：只处理匹配类型的异常。 |
| 38 | 函数体 / except (EOFError, KeyboardInterrupt) | 计算表达式/调用产生动作：`print('\nCLI 已退出')`。 |

**实际返回分支**：

- 没有显式return；正常结束默认None，异常或终止路径另见源码。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- try/except/finally：异常与保证清理：L33。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """命令行启动入口；先解析参数，因此 --help 不连接模型或启动 MCP。"""
0002 | import argparse
0003 | from pathlib import Path
0004 | 
0005 | 
0006 | def build_parser():
0007 |     parser = argparse.ArgumentParser(prog="ai-cli", description="本地 AI 编程助手（开发中）")
0008 |     parser.add_argument("--approval-mode", choices=("auto", "manual"), default="auto", help="auto 自动审批低风险操作，manual 保留逐次确认")
0009 |     parser.add_argument("--provider", choices=("ollama", "openai"), help="模型协议")
0010 |     parser.add_argument("--api-key-env", default="OPENAI_API_KEY", help="保存 API 密钥的环境变量名；不保存密钥")
0011 |     parser.add_argument("--model", help="覆盖配置中的模型名称")
0012 |     parser.add_argument("--base-url", help="覆盖模型服务地址")
0013 |     parser.add_argument("--session", help="启动时进入指定会话，不存在则创建")
0014 |     parser.add_argument("--plain", action="store_true", help="使用普通 input，关闭增强终端编辑")
0015 |     parser.add_argument("--no-mcp", action="store_true", help="本次运行不启动 MCP 服务")
0016 |     parser.add_argument('-C', '--workspace', default=str(Path.cwd()), help='工作目录，默认当前目录')
0017 |     return parser
0018 | 
0019 | 
0020 | def main(argv=None):
0021 |     parser = build_parser()
0022 |     args = parser.parse_args(argv)
0023 |     from config import model_config, approval_config
0024 |     from script import main as run_cli
0025 |     approval_config["mode"] = args.approval_mode
0026 |     if args.provider:
0027 |         model_config["provider"] = args.provider
0028 |     model_config["api_key_env"] = args.api_key_env
0029 |     if args.model:
0030 |         model_config["model"] = args.model
0031 |     if args.base_url:
0032 |         model_config["base_url"] = args.base_url.rstrip("/")
0033 |     try:
0034 |         run_cli(initial_session=args.session, plain=args.plain, no_mcp=args.no_mcp, workspace=args.workspace)
0035 |     except ValueError as error:
0036 |         parser.error(str(error))
0037 |     except (EOFError, KeyboardInterrupt):
0038 |         print("\nCLI 已退出")
0039 | 
0040 | 
0041 | if __name__ == "__main__":
0042 |     main()
```
