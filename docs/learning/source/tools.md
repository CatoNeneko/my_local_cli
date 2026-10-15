# tools.py：源码导读

旧接口兼容包装；仍转统一execute_tool，模型请求动态读取声明。

先读专题：[03-tools.md](../03-tools.md)。

实际源码：[tools.py](../../../tools.py)。

快照 SHA256：`2f88fce730f18229b93e973050c820379555d78c46fa08e5aaa88b9eda45d489`；23 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 2 | `from tool_registry import get_tool_definitions` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `from tool_runtime import execute_tool` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 7 | `tool_definitions = get_tool_definitions()` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

## 函数地图

| 定义 | 行 | 职责 |
| --- | ---: | --- |
| [read_file](#read-file) | [10](../../../tools.py#L10) | 底层有限二进制读取再UTF-8解码；tools同名函数是统一执行包装。 |
| [search_file](#search-file) | [14](../../../tools.py#L14) | 底层读文件后逐行字面匹配；tools同名函数是统一执行包装。 |
| [list_files](#list-files) | [18](../../../tools.py#L18) | 底层列目录并隐藏不合法项；tools同名函数是source=user的统一执行包装。 |
| [search_project](#search-project) | [22](../../../tools.py#L22) | 有界递归正文搜索；tools同名函数提供path/glob默认值并转统一执行。 |

<a id="read-file"></a>
## read_file

底层有限二进制读取再UTF-8解码；tools同名函数是统一执行包装。

```python
def read_file(path)
```

位置：[10行](../../../tools.py#L10) 至快照 11 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |

**调用表达式（静态提取，不含内层独立函数体）**：`execute_tool`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 11 | 函数体 | 返回 `execute_tool('read_file', {'path': path}, source='user')`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L11：`execute_tool('read_file', {'path': path}, source='user')`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="search-file"></a>
## search_file

底层读文件后逐行字面匹配；tools同名函数是统一执行包装。

```python
def search_file(path, keyword)
```

位置：[14行](../../../tools.py#L14) 至快照 15 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| `keyword` | `未显式注解` | 字面查找的非空文字，非正则表达式。 |

**调用表达式（静态提取，不含内层独立函数体）**：`execute_tool`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 15 | 函数体 | 返回 `execute_tool('search_file', {'path': path, 'keyword': keyword}, source='user')`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L15：`execute_tool('search_file', {'path': path, 'keyword': keyword}, source='user')`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="list-files"></a>
## list_files

底层列目录并隐藏不合法项；tools同名函数是source=user的统一执行包装。

```python
def list_files(path)
```

位置：[18行](../../../tools.py#L18) 至快照 19 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |

**调用表达式（静态提取，不含内层独立函数体）**：`execute_tool`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 19 | 函数体 | 返回 `execute_tool('list_files', {'path': path}, source='user')`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L19：`execute_tool('list_files', {'path': path}, source='user')`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

<a id="search-project"></a>
## search_project

有界递归正文搜索；tools同名函数提供path/glob默认值并转统一执行。

```python
def search_project(path, keyword, glob='*')
```

位置：[22行](../../../tools.py#L22) 至快照 23 行；参数中的 `self` 是当前对象，`*` 后是只能按名字传的参数。

**参数用途**：准确缺省值与位置/关键字规则在上方签名，注解不等于普通Python自动执行校验。

| 参数 | 类型注解（若有） | 用途 |
| --- | --- | --- |
| `path` | `未显式注解` | 文件或目录目标；原始相对/绝对形式以本函数签名和resolve检查为准。 |
| `keyword` | `未显式注解` | 字面查找的非空文字，非正则表达式。 |
| `glob` | `未显式注解` | 文件名/相对路径匹配模式，例如*.py。 |

**调用表达式（静态提取，不含内层独立函数体）**：`execute_tool`

**逐条控制流**：按行号阅读，所属分支说明哪些条件下才会执行。内层独立函数的主体在它自己的小节解释。

| 行 | 所属范围/分支 | 语句读法 |
| ---: | --- | --- |
| 23 | 函数体 | 返回 `execute_tool('search_project', {'path': path, 'keyword': keyword, 'glob': glob}, source='user')`，结束当前函数；具体分支见完整源码。 |

**实际返回分支**：

- L23：`execute_tool('search_project', {'path': path, 'keyword': keyword, 'glob': glob}, source='user')`。
- 若走到函数末尾且没有执行return，Python默认返回None；不能把这条语言规则当成所有分支都会走到末尾。

## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。


## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | """兼容入口。注册位于 tool_registry，执行位于 tool_runtime。"""
0002 | from tool_registry import get_tool_definitions
0003 | from tool_runtime import execute_tool
0004 | 
0005 | 
0006 | # 兼容旧导入；模型请求使用 getter，以便以后动态添加 MCP 工具。
0007 | tool_definitions = get_tool_definitions()
0008 | 
0009 | 
0010 | def read_file(path):
0011 |     return execute_tool("read_file", {"path": path}, source="user")
0012 | 
0013 | 
0014 | def search_file(path, keyword):
0015 |     return execute_tool("search_file", {"path": path, "keyword": keyword}, source="user")
0016 | 
0017 | 
0018 | def list_files(path):
0019 |     return execute_tool("list_files", {"path": path}, source="user")
0020 | 
0021 | 
0022 | def search_project(path, keyword, glob="*"):
0023 |     return execute_tool("search_project", {"path": path, "keyword": keyword, "glob": glob}, source="user")
```
