# mcp_servers/demo_server.py：源码导读

FastMCP最小stdio加法示例，展示工具注册和返回。

先读专题：[05-extensions.md](../05-extensions.md)。

实际源码：[mcp_servers/demo_server.py](../../../mcp_servers/demo_server.py)。

快照 SHA256：`5b504f8aad63f6d0a43b8166e701a24c8c6751bdbd42d86cf3cf3112c85f0cf4`；14 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `from mcp.server.fastmcp import FastMCP` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 4 | `server = FastMCP('CLI Demo')` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [add](#add) | [8](../../../mcp_servers/demo_server.py#L8) | 示例MCP真实相加返回整数。 |

<a id="add"></a>
## add

示例MCP真实相加返回整数。

```python
def add(a: int, b: int) -> int
```

位置：[8行](../../../mcp_servers/demo_server.py#L8) 至快照 10 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `a` | `int` | 由可信调用方传入的值；精确行为看后续检查与使用。 |
| `b` | `int` | 由可信调用方传入的值；精确行为看后续检查与使用。 |

**调用表达式（静态提取，不含内层独立函数体）**：`server.tool`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 9 | 函数体 | 文档字符串：说明职责，不作为普通语句动作执行。 |
| 10 | 函数体 | 返回 `a + b`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L10：`a + b`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。


## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """示例 stdio MCP 服务，提供可发现、可调用的加法工具。"""
0002 | from mcp.server.fastmcp import FastMCP
0003 | 
0004 | server = FastMCP("CLI Demo")
0005 | 
0006 | 
0007 | @server.tool()
0008 | def add(a: int, b: int) -> int:
0009 |     """返回两个整数的和。"""
0010 |     return a + b
0011 | 
0012 | 
0013 | if __name__ == "__main__":
0014 |     server.run(transport="stdio")
```
