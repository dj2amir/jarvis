"""
System Actions — control your computer.

Tools:
  - open_app: Open an application by name
  - run_shell: Execute a terminal command
  - system_info: Get CPU, RAM, disk usage
"""

import subprocess
import os
import platform
import psutil

TOOLS = [
    {
        "name": "open_app",
        "description": "Open an application by name (e.g. firefox, spotify, code)",
        "parameters": {
            "app_name": "Name of the application to open"
        },
    },
    {
        "name": "run_shell",
        "description": "Execute a terminal/shell command and return output",
        "parameters": {
            "command": "The shell command to run"
        },
    },
    {
        "name": "system_info",
        "description": "Get system information (CPU, RAM, disk usage)",
        "parameters": {},
    },
]


def execute(name: str, **kwargs):
    if name == "open_app":
        return _open_app(kwargs.get("app_name", ""))
    elif name == "run_shell":
        return _run_shell(kwargs.get("command", ""))
    elif name == "system_info":
        return _system_info()
    return None


def _open_app(app_name: str) -> str:
    if not app_name:
        return "No app name provided."
    try:
        # Try using xdg-open on Linux, open on Mac, start on Windows
        system = platform.system()
        if system == "Linux":
            subprocess.Popen(["xdg-open", app_name],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif system == "Darwin":
            subprocess.Popen(["open", "-a", app_name],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif system == "Windows":
            subprocess.Popen(["start", app_name], shell=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"Opened {app_name}"
    except Exception as e:
        return f"Failed to open {app_name}: {e}"


def _run_shell(command: str) -> str:
    if not command:
        return "No command provided."
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=10
        )
        output = result.stdout.strip()
        err = result.stderr.strip()
        if output:
            return output
        elif err:
            return f"Error: {err}"
        else:
            return "Command completed (no output)."
    except subprocess.TimeoutExpired:
        return "Command timed out after 10 seconds."
    except Exception as e:
        return f"Command failed: {e}"


def _system_info() -> str:
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return (
        f"CPU: {cpu}% | "
        f"RAM: {ram.percent}% ({ram.used // (1024**3)}/{ram.total // (1024**3)} GB) | "
        f"Disk: {disk.percent}% ({disk.free // (1024**3)} GB free)"
    )
