"""
Vision Engine — Screen Capture for JARVIS.

Multi-strategy approach that works on:
  - Wayland: grim (wlroots), gnome-screenshot (GNOME), import (ImageMagick)
  - X11: PIL.ImageGrab (direct)

Also supports webcam capture via OpenCV when available.
"""

import subprocess
import os
import shutil
import tempfile
import base64
from pathlib import Path
from typing import Optional, Tuple
from io import BytesIO

import numpy as np

# Try importing PIL (already available)
from PIL import Image


def _which(cmd: str) -> bool:
    """Check if a command exists in PATH (stdlib, no subprocess)."""
    return shutil.which(cmd) is not None


def _temp_capture_path() -> str:
    """Create a temp file for screen capture, returns path."""
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    return path


def _capture_with_tool(tool_cmd: list, path: str) -> Optional[Image.Image]:
    """Run a screen capture tool and load the result as a PIL Image."""
    try:
        subprocess.run(tool_cmd, check=True, capture_output=True, timeout=5)
        img = Image.open(path)
        return img.convert("RGB")
    except Exception:
        return None


def _capture_grim() -> Optional[Image.Image]:
    """Capture screen on wlroots/Sway via grim."""
    path = _temp_capture_path()
    try:
        return _capture_with_tool(["grim", path], path)
    finally:
        try: os.unlink(path)
        except OSError: pass


def _capture_gnome() -> Optional[Image.Image]:
    """Capture screen on GNOME Wayland via gnome-screenshot."""
    path = _temp_capture_path()
    try:
        return _capture_with_tool(["gnome-screenshot", "-f", path], path)
    finally:
        try: os.unlink(path)
        except OSError: pass


def _capture_imagemagick() -> Optional[Image.Image]:
    """Capture screen via ImageMagick's import command."""
    path = _temp_capture_path()
    try:
        return _capture_with_tool(["import", "-window", "root", path], path)
    finally:
        try: os.unlink(path)
        except OSError: pass


def _capture_pil() -> Optional[Image.Image]:
    """Capture screen via PIL.ImageGrab (X11 only)."""
    try:
        from PIL import ImageGrab
        return ImageGrab.grab()
    except Exception:
        return None


def capture_screen() -> Optional[Image.Image]:
    """Capture the entire screen.

    Tries multiple strategies in order:
      1. grim (wlroots/Sway Wayland)
      2. gnome-screenshot (GNOME Wayland)
      3. import (ImageMagick, X11/Wayland hybrid)
      4. PIL.ImageGrab (X11 direct)

    Returns: PIL Image in RGB mode, or None if all strategies fail.
    """
    strategies = [
        ("grim", _capture_grim),
        ("gnome-screenshot", _capture_gnome),
        ("import (ImageMagick)", _capture_imagemagick),
        ("PIL.ImageGrab", _capture_pil),
    ]

    for name, func in strategies:
        try:
            if name == "PIL.ImageGrab":
                img = func()
            elif _which(name.split()[0]):
                img = func()
            else:
                continue
            if img:
                return img
        except Exception:
            continue

    return None


def capture_screen_base64(max_size: Tuple[int, int] = (1280, 720)) -> Optional[str]:
    """Capture screen and return as base64 JPEG.

    Resizes to max_size while preserving aspect ratio.

    Returns: base64-encoded JPEG string, or None on failure.
    """
    img = capture_screen()
    if img is None:
        return None

    # Resize if too large
    img.thumbnail(max_size, Image.LANCZOS)

    # Encode as JPEG base64
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=75)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def capture_screen_file(path: str, max_size: Tuple[int, int] = (1920, 1080)) -> Optional[str]:
    """Capture screen and save to a file.

    Returns: the file path on success, None on failure.
    """
    img = capture_screen()
    if img is None:
        return None

    img.thumbnail(max_size, Image.LANCZOS)
    img.save(path, format="PNG")
    return path


def is_available() -> bool:
    """Check if screen capture is available via any strategy."""
    return (
        _which("grim") or
        _which("gnome-screenshot") or
        _which("import") or
        _is_pil_grab_available()
    )


def _is_pil_grab_available() -> bool:
    """Check if PIL.ImageGrab works (X11 only)."""
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        return img is not None
    except Exception:
        return False


def available_strategy() -> Optional[str]:
    """Return the name of the first available capture strategy."""
    for cmd in ["grim", "gnome-screenshot", "import"]:
        if _which(cmd):
            return cmd
    if _is_pil_grab_available():
        return "PIL.ImageGrab"
    return None
