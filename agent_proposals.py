"""子代理只能暂存文件建议；父进程通过共享执行器另行审批、写入。"""

from pathlib import Path
import hashlib

PROPOSALS = []
MAX_TOTAL_BYTES = 16000


def propose(path, new_content, *, tool):
    import permissions

    checked = permissions.resolve_project_path(path)
    if not checked["ok"]:
        return checked
    path = checked["path"]
    raw = new_content.encode("utf-8")
    if (
        len(PROPOSALS) >= 3
        or sum(len(item["new_content"].encode("utf-8")) for item in PROPOSALS) + len(raw)
        > MAX_TOTAL_BYTES
    ):
        return {"ok": False, "error": "子代理建议最多 3 个文件、合计 16000 字节"}
    if "\x00" in new_content:
        return {"ok": False, "error": "建议不能包含空字符"}
    original_hash = None
    if tool == "edit_file":
        try:
            with open(path, "rb") as file:
                original = file.read(1048577)
            if len(original) > 1048576:
                return {"ok": False, "error": "建议目标文件超过 1 MiB"}
            original.decode("utf-8")
            original_hash = hashlib.sha256(original).hexdigest()
        except (OSError, UnicodeError):
            return {"ok": False, "error": "建议目标不是可读取的 UTF-8 文件"}
    else:
        from new_files import check_new_target

        checked = check_new_target(path)
        if not checked["ok"]:
            return checked
    identifier = str(len(PROPOSALS) + 1)
    PROPOSALS.append(
        {
            "proposal_id": identifier,
            "tool": tool,
            "path": Path(path).relative_to(permissions.PROJECT_ROOT).as_posix(),
            "new_content": new_content,
            "original_hash": original_hash,
        }
    )
    return {
        "ok": True,
        "proposal_id": identifier,
        "message": "建议已暂存，未写入文件；父代理必须另行审批",
    }


def propose_edit(path, new_content):
    return propose(path, new_content, tool="edit_file")


def propose_file(path, new_content):
    return propose(path, new_content, tool="create_file")


def apply_proposal(task_id, proposal_id):
    import permissions
    from harness.tasks.processes import JOBS
    from harness.tasks.runtime import TASK_BACKEND
    from approval import task_scope
    from tool_runtime import execute_tool
    import json

    backend = TASK_BACKEND.get()
    if backend:
        data = backend.proposal(task_id, proposal_id)
        if not data.get("ok"):
            return data
        job = data["job"]
        proposal = data["proposal"]
        result = {"ok": True, "proposals": [proposal]}
    else:
        job = JOBS.get(task_id)
    if job is None or job["kind"] != "agent" or not job["done"]:
        return {"ok": False, "error": "子代理任务尚未完成或不存在"}
    if job.get("workspace") != str(permissions.PROJECT_ROOT):
        return {"ok": False, "error": "子代理不属于当前项目"}
    try:
        if not backend:
            result = json.loads(bytes(job["output"]))
        if result.get("ok") is not True:
            return {"ok": False, "error": "子代理未成功完成，不能应用建议"}
        proposal = next(
            item for item in result.get("proposals", []) if item.get("proposal_id") == proposal_id
        )
        if proposal["tool"] not in ("edit_file", "create_file"):
            raise ValueError()
    except (ValueError, KeyError, TypeError, StopIteration, AttributeError):
        return {"ok": False, "error": "建议 ID 不存在或数据无效"}
    used = job.setdefault("applied_proposals", set())
    if proposal_id in used:
        return {"ok": False, "error": "建议已应用，不能重复写入"}
    checked = permissions.resolve_project_path(proposal.get("path"))
    if not checked["ok"]:
        return checked
    if proposal["tool"] == "edit_file":
        try:
            with open(checked["path"], "rb") as file:
                original = file.read(1048577)
            if len(original) > 1048576 or hashlib.sha256(original).hexdigest() != proposal.get(
                "original_hash"
            ):
                return {"ok": False, "error": "文件在子代理提出建议后已变化，请重新生成建议"}
        except OSError:
            return {"ok": False, "error": "建议目标已无法读取"}
    # 原始用户任务由父进程保存，不采用子代理输出中自称的授权。
    with task_scope(job["task"]):
        applied = execute_tool(
            proposal["tool"], {"path": proposal["path"], "new_content": proposal["new_content"]}
        )
    if applied["ok"]:
        if backend:
            backend.mark_applied(task_id, proposal_id)
        else:
            used.add(proposal_id)
    return {
        "ok": applied["ok"],
        "task_id": task_id,
        "proposal_id": proposal_id,
        "result": applied,
        **({"cancelled": True} if applied.get("cancelled") else {}),
    }
