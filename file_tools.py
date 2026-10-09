from pathlib import Path
from permissions import resolve_project_path

MAX_READ_BYTES = 1048576


def list_files(path):
    path_result = resolve_project_path(path)
    if not path_result["ok"]:
        return path_result

    directory = Path(path_result["path"])
    entries = []

    try:
        for entry in directory.iterdir():
            checked = resolve_project_path(str(entry))
            if not checked["ok"]:
                continue
            if entry.is_dir():
                kind = "directory"
            else:
                kind = "file"

            entries.append({
                "name": entry.name,
                "type": kind
            })

        return {"ok": True, "entries": entries}

    except FileNotFoundError:
        return {"ok": False, "error": "目录不存在"}
    except NotADirectoryError:
        return {"ok": False, "error": "路径不是目录"}
    except PermissionError:
        return {"ok": False, "error": "没有访问目录的权限"}

def read_file(path):

    path_result = resolve_project_path(path)

    if not path_result["ok"]:
        return path_result

    path = path_result["path"]

    try:
        with open(path, 'rb') as file:
            content = file.read(MAX_READ_BYTES + 1)
        if len(content) > MAX_READ_BYTES:
            return {'ok': False, 'error': '读取文件超过 1 MiB 上限，请用项目搜索定位内容'}
        return {'ok': True, 'content': content.decode('utf-8')}
    except FileNotFoundError:
        return {'ok': False, 'error': 'file not found'}
    except IsADirectoryError:
        return {'ok': False, 'error': 'this is a folder'}
    except PermissionError:
        return {'ok': False, 'error': 'permission denied'}
    except UnicodeDecodeError:
        return {'ok': False, 'error': 'this is not utf-8'}

def search_file(path, keyword):

    result = read_file(path)
    if not result['ok']:
        return result

    matches = []
    line_number = 1

    for line in result['content'].splitlines():
        if keyword in line:
            matches.append({'line_number': line_number, 'content': line})
        line_number += 1
    return {'ok': True, 'matches': matches}
