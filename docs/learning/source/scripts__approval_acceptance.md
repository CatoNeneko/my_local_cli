# scripts/approval_acceptance.py：源码导读

真实子代理暂存建议与父进程独立自动审批的固定验收。

先读专题：[08-verification.md](../08-verification.md)。

实际源码：[scripts/approval_acceptance.py](../../../scripts/approval_acceptance.py)。

快照 SHA256：`6a36ed5effb8242df2dd72c4cf2ed80501532528a40a450f16768002f80a354e`；44 行。

## 导入与文件级状态

| 行 | 代码 | 读法 |
| ---: | --- | --- |
| 1 | `import sys, json, tempfile` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 2 | `from pathlib import Path` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 3 | `ROOT = Path(__file__).resolve().parents[1]` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 5 | `from config import approval_config` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 6 | `from workspace import use_workspace` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 7 | `from approval import task_scope` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 8 | `from tool_runtime import execute_tool` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 9 | `from process_tasks import close_tasks` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 10 | `import permissions` | 模块依赖；标准库/第三方/本项目模块通过名称引用。 |
| 11 | `approval_config['mode'] = 'auto'` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 12 | `permissions.confirm_tool = lambda *args: (_ for _ in ()).throw(RuntimeError('本次验证不允许人工确认'))` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 13 | `root = Path(tempfile.mkdtemp(prefix='cli-approval-acceptance-'))` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |
| 16 | `report = {'workspace': str(root), 'checks': {}}` | 文件级状态/常量/配置；具体值和副作用见快照与专题。 |

本文件没有函数定义。配置/入口可能在文件级执行；空文件则没有行为。


## 本文件实际出现的新语法

与[语法桥梁](../01-python.md)对照；以下是实际出现位置，不代表每处具有相同业务含义。

- try/except/finally：异常与保证清理：L17。
- lambda：小回调函数：L12。
- with/yield：资源/状态生命周期或逐个生成：L18。
- 推导式/生成器表达式：循环建容器或逐个产生：L12, L31。

## 带行号完整源码快照

下面是阅读用文本，不要连行号直接粘贴运行。

```text
0001 | import sys,json,tempfile
0002 | from pathlib import Path
0003 | ROOT = Path(__file__).resolve().parents[1]
0004 | sys.path.insert(0, str(ROOT))
0005 | from config import approval_config
0006 | from workspace import use_workspace
0007 | from approval import task_scope
0008 | from tool_runtime import execute_tool
0009 | from process_tasks import close_tasks
0010 | import permissions
0011 | approval_config['mode']='auto'
0012 | permissions.confirm_tool=lambda *args: (_ for _ in ()).throw(RuntimeError('本次验证不允许人工确认'))
0013 | root=Path(tempfile.mkdtemp(prefix='cli-approval-acceptance-'))
0014 | (root/'calc.py').write_text('def add(a, b):\n    return a - b\n')
0015 | (root/'test_calc.py').write_text('from calc import add\ndef test_add():\n    assert add(19, 23) == 42\n')
0016 | report={'workspace':str(root),'checks':{}}
0017 | try:
0018 |     with use_workspace(root), task_scope('修复 calc.py 中 add 的加法错误；保持 test_calc.py 不变。'):
0019 |         before=execute_tool('run_tests',{'path':'.'})
0020 |         report['checks']['baseline_failed']=not before['ok'] and '1 failed' in before['output']
0021 |         launched=execute_tool('spawn_agent',{'task':'读取 calc.py 和 test_calc.py，修复 add 的加法错误。你不能写入，必须调用 propose_edit 提出完整 calc.py 修改建议，最后简短说明。'})
0022 |         report['launch']=launched
0023 |         for _ in range(6):
0024 |             done=execute_tool('task_wait',{'task_id':launched['task_id'],'seconds':30})
0025 |             if done['state']=='finished': break
0026 |         report['child']=done.get('agent_result')
0027 |         proposals=done.get('agent_result',{}).get('proposals',[])
0028 |         if proposals:
0029 |             applied=execute_tool('apply_agent_proposal',{'task_id':launched['task_id'],'proposal_id':proposals[0]['proposal_id']})
0030 |             report['application']=applied
0031 |             report['checks']['independent_auto_review']=applied['ok'] and any(item['method']=='reviewer' and item['decision']=='allow' for item in applied['result'].get('approval',[]))
0032 |         else:
0033 |             report['checks']['independent_auto_review']=False
0034 |         after=execute_tool('run_tests',{'path':'.'})
0035 |         report['checks']['tests_passed']=after['ok'] and '1 passed' in after['output']
0036 |         report['checks']['fixed_test_unchanged']=(root/'test_calc.py').read_text()=='from calc import add\ndef test_add():\n    assert add(19, 23) == 42\n'
0037 |         report['checks']['source_fixed']='return a + b' in (root/'calc.py').read_text()
0038 | finally:
0039 |     close_tasks()
0040 |     destination=ROOT / 'artifacts/approval/real_acceptance.json'
0041 |     destination.parent.mkdir(parents=True,exist_ok=True)
0042 |     destination.write_text(json.dumps(report,ensure_ascii=False,indent=2))
0043 | print(json.dumps(report,ensure_ascii=False,indent=2))
0044 | if not all(report['checks'].values()):raise SystemExit(1)
```
