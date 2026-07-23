"""
File Actions — read, write, list files.

Tools:
  - read_file: Read contents of a file
  - write_file: Write or append text to a file
  - list_dir: List files in a directory
"""

from pathlib import Path

TOOLS = [
    {
        "name": "read_file",
        "description": "Read and return the contents of a file",
        "parameters": {
            "file_path": "Path to the file to read"
        },
    },
    {
        "name": "write_file",
        "description": "Write text content to a file (creates or overwrites)",
        "parameters": {
            "file_path": "Path to the file",
            "content": "Text content to write"
        },
    },
    {
        "name": "list_dir",
        "description": "List files and directories at a given path",
        "parameters": {
            "dir_path": "Directory path to list (defaults to current dir)"
        },
    },
]


def execute(name: str, **kwargs):
    if name == "read_file":
        return _read_file(kwargs.get("file_path", ""))
    elif name == "write_file":
        return _write_file(kwargs.get("file_path", ""), kwargs.get("content", ""))
    elif name == "list_dir":
        return _list_dir(kwargs.get("dir_path", "."))
    return None


def _read_file(file_path: str) -> str:
    if not file_path:
        return "No file path provided."
    try:
        path = Path(file_path).expanduser()
        if not path.exists():
            return f"File not found: {file_path}"
        if path.stat().st_size > 50_000:
            return f"File too large ({path.stat().st_size} bytes). First 100 lines:\n" + \
                   "\n".join(path.read_text().split("\n")[:100])
        return path.read_text()
    except Exception as e:
        return f"Read error: {e}"


def _write_file(file_path: str, content: str) -> str:
    if not file_path:
        return "No file path provided."
    try:
        path = Path(file_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return f"Written {len(content)} chars to {file_path}"
    except Exception as e:
        return f"Write error: {e}"


def _list_dir(dir_path: str) -> str:
    try:
        path = Path(dir_path).expanduser()
        if not path.exists():
            return f"Directory not found: {dir_path}"
        items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        lines = [f"Contents of {path}:"]
        for item in items[:50]:
            prefix = "📁" if item.is_dir() else "📄"
            lines.append(f"  {prefix} {item.name}")
        return "\n".join(lines)
    except Exception as e:
        return f"List error: {e}"
