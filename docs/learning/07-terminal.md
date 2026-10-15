# 07：终端体验怎样和核心执行分开

## 1. 为什么纯 input 后来需要这些文件

input 能读一行，但补全、多行、↑↓选择、实时筛选、权限面板需要按键事件和绘制布局。项目用 prompt-toolkit 提供底层终端能力，自己的代码决定候选、选择状态和返回结果。

| 文件 | 输入 | 输出/职责 |
| --- | --- | --- |
| terminal_input | 模式、当前会话 | 一条输入或选择路径；管理确认界面范围 |
| path_input | 路径命令字符串/目录前缀 | 路径与关键词、受边界限制候选 |
| terminal_dialog | title、choices | 所选值或 None |
| file_catalog | PROJECT_ROOT、query | 有限文件索引、模糊排序 |
| file_picker | 已扫描 paths | 多选路径列表或 None |
| attachments | paths | 一条整批附件消息或错误 |
| tool_display | 工具名/结果/diff | 终端状态，不决定执行权限 |
| console_output | 模型片段 | 回答打印和去重 |

## 2. 增强模式与普通模式

`TerminalInput.__init__` 只在非 plain 且 stdin/stdout.isatty 时创建 PromptSession；重定向/管道/--plain 用 input。这样自动脚本不会被终端UI阻塞。

增强模式 multiline=True、InMemoryHistory、completer、key_bindings；输入历史只在本次进程内，用于上下键回看，不是会话 JSONL。底部toolbar是函数，读取当前 model_config，所以切模型/流式后能显示新值。

Enter：有补全候选时选/接受候选，下一次才发送；Alt+Enter（escape+enter）插入换行。没有补全时 `validate_and_handle` 提交当前buffer。这个 Enter 双阶段避免按补全时误发半条命令。

## 3. 路径解析与补全

`parse_path_arguments` 用 shlex 从 StringIO 读第一token，剩下stream.read 保留关键词里的空格。例如 `/search "a file.py" hello world` 得到 path=`a file.py`、keyword=`hello world`。不是简单 split 整个输入。

`ProjectCompleter.get_completions` 没进入路径参数时复用 WordCompleter 补 `/` 命令；路径参数取 parent/prefix，调用 path_candidates。有空格自动加引号，目录保持开引号便于继续补子目录；包含引号/控制字符的候选暂不补。

`path_candidates` 最多扫1000项、展示200候选，目录优先；不读文件正文，跳链接、私有与忽略目录。扫描受限时提示不完整，不能认为未列出的文件不存在。

## 4. 选择面板的状态是怎样更新的

terminal_dialog.choose 的 choices 是 `(value,label)` 列表；selected 是高亮索引。回调上下键改变selected，render根据selected给行加reverse样式，Enter返回value，Esc/Ctrl+C/Ctrl+D返回None。

权限面板 choices 第一项是 False，因此默认拒绝；yes_no=True 提供y/n快捷键。request_confirmation 判断是否处于 enhanced_confirmation ContextVar 范围；否则普通 input 只有明确y允许。

file_picker 多了 marked set（跨筛选勾选集合）、filtered匹配列表、query Buffer、status提示。nonlocal只对重新赋值外层变量使用。刷新query后selected归0，但marked不清，所以筛选前勾选仍保留。

| 按键 | 回调 | 改什么 |
| --- | --- | --- |
| ↑/↓ | up/down | selected ±1，限制范围 |
| PageUp/Down | page_up/page_down | selected ±10 |
| Tab | toggle | marked.add/remove，最多10 |
| Enter | accept | 有marked返回整批，否则高亮单个 |
| Esc等 | cancel | 返回None，不读取附件 |

`Application`+`Layout`+HSplit/VSplit+Window负责显示结构；FormattedTextControl(render) 动态取行，BufferControl负责编辑查询。它是事件驱动，不是在 while里一直 print整屏。

## 5. 文件名模糊匹配不是 AI 搜索

`scan_files` 使用stack深度遍历目录，scandir读目录项，跳链接/私有/依赖。最多5000文件、20000目录项、约2秒。返回files/truncated/reason/warnings。

`fuzzy_score` 对query的每个token，按顺序在path里找字符。`mdl` 可以匹配 `model.py`：字符不必连续但顺序必须一致。gap表示字符之间空隙；优先basename包含完整query，再按gap、路径长度、路径排序。

`matching_files` 保存(score,path)后排序，再返回path列表。它仅搜名字，不计算embedding、不查询模型、不搜索正文。

## 6. 选择文件之后为什么还要再次读取验证

目录索引不等于授权读取。选择期间文件可能被删除、变大或目标改变；prepare_attachments 再resolve，检查大小，再通过 `tools.read_file`→execute_tool实际读取。

附件最多10个，单个32KiB，本批连文件名和分隔标记共32KiB。dict.fromkeys(paths)去重同时保序。所有文件成功后拼一条user消息，失败不保存部分。

`script.attach_files` 拿到完整message才追加磁盘与内存。上传代码文件变成模型可见文字；不是上传二进制到服务储存，更没有自动发送整仓库。

`/read` 只是人看；`/attach`加入聊天；模型 read_file 是tool结果；三种读取在用途/历史记录上不同。

## 7. 输出与权限不能相互替代

工具开始显示不等于获准执行；工具失败摘要也不等于完整错误栈。tool_display只负责视图，runtime负责结果与权限。`show_diff`统计+-行并展示整体差异，审批后才发布；safe_text转义控制字符防终端逃逸显示，不改实际文件字节。

ConsoleOutput保存这一轮已经打印的片段，最终重复文字跳过显示，但最终assistant消息仍保存到历史。终端不重复打印与聊天只保存一份最终回答是两套控制逻辑。

## 8. 调试界面时如何定位

| 现象 | 先看 |
| --- | --- |
| Tab没有路径候选 | PATH_COMMANDS、get_completions、path_candidates |
| Enter补全后没有发出去 | create_key_bindings 的候选接受分支，是预期两次Enter |
| 勾选跨筛选消失 | file_picker.refresh 是否误清marked |
| 选择后没加入历史 | prepare_attachments 返回ok，attach_files是否执行 |
| 普通模式没有面板 | isatty/--plain/session is None |
| 模型回答重复 | ConsoleOutput.begin/write/final 与主循环 |
| 读取显示后未知命令 | 命令分支末尾continue是否存在 |

界面问题尽量先在这层查，不直接改agent核心。
