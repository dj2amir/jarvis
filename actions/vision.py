"""
Vision Actions — let JARVIS see your screen.

Tools:
  - capture_screen: Take a screenshot and save to file
  - describe_screen: Capture screen and describe what's visible (needs vision-capable LLM)
"""

from datetime import datetime
from pathlib import Path

TOOLS = [
    {
        "name": "capture_screen",
        "description": "Take a screenshot of the current screen and save to a file. Returns the file path.",
        "parameters": {
            "save_path": "Optional path to save the screenshot (default: auto-generated in ~/Pictures/jarvis/)"
        },
    },
    {
        "name": "describe_screen",
        "description": "Capture the screen and return a text description of what is currently visible on the display. Use this to help the user with what they're looking at.",
        "parameters": {},
    },
]


def execute(name: str, **kwargs):
    if name == "capture_screen":
        return _capture_screen(kwargs.get("save_path", ""))
    elif name == "describe_screen":
        return _describe_screen()
    return None


def _capture_screen(save_path: str = "") -> str:
    """Take a screenshot and save to file."""
    try:
        from core.vision import capture_screen, capture_screen_file

        if not save_path:
            pics_dir = Path.home() / "Pictures" / "jarvis"
            pics_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = str(pics_dir / f"screenshot_{timestamp}.png")

        result = capture_screen_file(save_path)
        if result:
            return f"Screenshot saved to {result}"
        return "Screen capture failed: no capture method available. Install gnome-screenshot, grim, or ImageMagick."
    except Exception as e:
        return f"Screen capture error: {e}"


def _describe_screen() -> str:
    """Capture screen and describe what's visible."""
    try:
        from core.vision import capture_screen, is_available, available_strategy

        if not is_available():
            return (
                "Screen capture is not available on this system. "
                "Install one of: gnome-screenshot, grim, or ImageMagick."
            )

        img = capture_screen()
        if img is None:
            return "Failed to capture screen."

        width, height = img.size
        return (
            f"Screen captured: {width}x{height}px. "
            f"Strategy: {available_strategy() or 'auto'}. "
            f"Ask the user what they need help with on their screen."
        )

    except Exception as e:
        return f"Screen description error: {e}"
