"""
Action Modules — JARVIS's hands.

Each module in this directory exports:
  - TOOLS: list of tool definitions [{name, description, parameters}]
  - execute(name, kwargs) -> str

Modules are auto-discovered on import — just drop a new .py file and it works.
"""

from pathlib import Path
import importlib

_MODULES = {}

# Auto-discover all action modules (except __init__)
for f in sorted(Path(__file__).parent.glob("*.py")):
    if f.stem.startswith("_"):
        continue
    try:
        mod = importlib.import_module(f"actions.{f.stem}")
        if hasattr(mod, "TOOLS") and hasattr(mod, "execute"):
            _MODULES[f.stem] = mod
    except Exception as e:
        print(f"  ⚠️ Failed to load action: {f.stem} — {e}")


def get_all_tools():
    """Build a flat tool catalog with module info for all loaded actions."""
    catalog = []
    for mod_name, mod in _MODULES.items():
        for tool in mod.TOOLS:
            catalog.append({
                **tool,
                "module": mod_name,
            })
    return catalog


def execute(name: str, **kwargs) -> str:
    """Execute a tool by name across all action modules.

    Returns: result string or error message.
    """
    for mod_name, mod in _MODULES.items():
        try:
            result = mod.execute(name, **kwargs)
            if result is not None:
                return str(result)
        except Exception as e:
            return f"Error executing {name}: {e}"
    return f"Unknown action: {name}"


def list_tools() -> str:
    """Return a human-readable list of all available tools."""
    tools = get_all_tools()
    if not tools:
        return "No tools available."
    lines = ["Available tools:"]
    for t in tools:
        desc = t.get("description", "")
        params = ", ".join(t.get("parameters", {}).keys())
        lines.append(f"  • {t['name']} ({params}) — {desc}")
    return "\n".join(lines)
