"""
Vision Actions — let JARVIS see your screen and webcam.

Tools:
  - capture_screen: Take a screenshot and save to file
  - describe_screen: Capture screen and describe what's visible
  - capture_webcam: Take a webcam snapshot and save to file
  - describe_webcam: Capture webcam and describe what JARVIS sees
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
    {
        "name": "capture_webcam",
        "description": "Take a picture using the webcam and save to a file. Returns the file path.",
        "parameters": {
            "save_path": "Optional path to save the webcam photo (default: auto-generated in ~/Pictures/jarvis/)"
        },
    },
    {
        "name": "describe_webcam",
        "description": "Capture an image from the webcam and return a description of what the camera sees. Use this when the user asks what you can see or who is in front of the camera.",
        "parameters": {},
    },
]


def execute(name: str, **kwargs):
    if name == "capture_screen":
        return _capture_screen(kwargs.get("save_path", ""))
    elif name == "describe_screen":
        return _describe_screen()
    elif name == "capture_webcam":
        return _capture_webcam(kwargs.get("save_path", ""))
    elif name == "describe_webcam":
        return _describe_webcam()
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


def _capture_webcam(save_path: str = "") -> str:
    """Take a webcam snapshot and save to file."""
    try:
        from core.vision import capture_webcam_file, is_webcam_available

        if not is_webcam_available():
            return "Webcam not available. Install OpenCV (pip install opencv-python) or fswebcam (sudo apt install fswebcam)."

        if not save_path:
            pics_dir = Path.home() / "Pictures" / "jarvis"
            pics_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = str(pics_dir / f"webcam_{timestamp}.png")

        result = capture_webcam_file(save_path)
        if result:
            return f"Webcam photo saved to {result}"
        return "Webcam capture failed. Check your camera connection."
    except Exception as e:
        return f"Webcam capture error: {e}"


def _describe_webcam() -> str:
    """Capture webcam and describe what's visible."""
    try:
        from core.vision import capture_webcam, is_webcam_available

        if not is_webcam_available():
            return "Webcam not available. Install OpenCV or fswebcam."

        img = capture_webcam()
        if img is None:
            return "Failed to capture from webcam."

        width, height = img.size
        return (
            f"Webcam captured: {width}x{height}px. "
            f"The user's webcam has been captured — ask them what "
            f"they want you to look for or describe."
        )

    except Exception as e:
        return f"Webcam description error: {e}"
