"""同一工作区写入的跨进程互斥锁。"""

from contextlib import contextmanager
import fcntl
import os
import stat
from pathlib import Path


@contextmanager
def workspace_write_lock(workspace):
    state = Path(workspace).resolve() / ".ai-cli"
    directory = state / "locks"
    if state.is_symlink() or directory.is_symlink():
        raise ValueError("工作区锁目录不能是符号链接")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(
        directory / "write.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600
    )
    with os.fdopen(descriptor, "a") as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise ValueError("工作区锁必须是当前用户拥有的普通文件")
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
