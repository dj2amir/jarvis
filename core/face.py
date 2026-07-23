"""
Face Engine — Animated face for JARVIS.

Modes:
  - terminal: ANSI-colored ASCII art rendered to terminal

Styles & Color Themes:
  - robot:      Cyan/blue glow, box-drawing borders, geometric eyes
  - anonymous:  White/gray block mask, V-inspired
  - minimal:    Simple clean lines, single color

Features:
  - 10 emotions with unique expressions
  - Real-time blinking (eye state machine)
  - Speaking mouth animation (multi-frame)
  - Idle breathing animation (subtle pulse)
  - ANSI color support
"""

import time
import sys
import random
import threading
from enum import Enum


# ── ANSI color constants ─────────────────────────────────────────
class Color:
    RESET     = "\033[0m"
    BOLD      = "\033[1m"
    DIM       = "\033[2m"
    CYAN      = "\033[96m"
    GREEN     = "\033[92m"
    YELLOW    = "\033[93m"
    RED       = "\033[91m"
    MAGENTA   = "\033[95m"
    BLUE      = "\033[94m"
    WHITE     = "\033[97m"
    GRAY      = "\033[90m"
    BG_CYAN   = "\033[46m"
    BG_GRAY   = "\033[100m"
    # Bright variants
    BRIGHT_CYAN  = "\033[96;1m"
    BRIGHT_GREEN = "\033[92;1m"


# ── Emotion enum ─────────────────────────────────────────────────

class Emotion(Enum):
    NEUTRAL    = "neutral"
    HAPPY      = "happy"
    SAD        = "sad"
    ANGRY      = "angry"
    SURPRISED  = "surprised"
    THINKING   = "thinking"
    LISTENING  = "listening"
    SPEAKING   = "speaking"
    SLEEPING   = "sleeping"
    ERROR      = "error"


class FaceStyle(Enum):
    ROBOT     = "robot"
    ANONYMOUS = "anonymous"
    MINIMAL   = "minimal"


def _normalize_emotion(emotion):
    if isinstance(emotion, Emotion):
        return emotion.value
    return str(emotion).lower()


# ═══════════════════════════════════════════════════════════════════
#  TerminalFace — The rendering backend
# ═══════════════════════════════════════════════════════════════════

class TerminalFace:
    """High-detail ASCII face rendered in the terminal.

    Each emotion is a 9-row × 21-column design using box-drawing
    characters (╭╮╰╯│─) for the head shape, with Detailed ASCII art
    inside.
    """

    # ── Color themes per style ───────────────────────────────────
    STYLE_COLORS = {
        "robot": {
            "border": Color.CYAN,
            "eyes":   Color.BRIGHT_CYAN,
            "mask":   Color.BRIGHT_CYAN,   # alias for {m}
            "label":  Color.CYAN,
            "accent": Color.BLUE,
            "dim":    Color.GRAY,
        },
        "anonymous": {
            "border": Color.WHITE,
            "eyes":   Color.BOLD,
            "mask":   Color.BOLD,          # bold white for mask blocks
            "label":  Color.GRAY,
            "accent": Color.WHITE,
            "dim":    Color.GRAY,
        },
        "minimal": {
            "border": Color.WHITE,
            "eyes":   Color.WHITE,
            "mask":   Color.WHITE,
            "label":  Color.GRAY,
            "accent": Color.WHITE,
            "dim":    Color.GRAY,
        },
    }

    # ── Head shape (shared across emotions for each style) ───────
    HEAD_TOP    = "╭───────────────────╮"
    HEAD_BOTTOM = "╰───────────────────╯"

    # ── Full emotion designs ─────────────────────────────────────
    # Each is a tuple of (line_1, ..., line_7) — 7 content rows.
    # Lines support {c} for color and {x} for reset placeholders.

    ROBOT = {
        "neutral": (
            "│  ╭───╮   ╭───╮   │",
            "│  │ {c}◉{x} │   │ {c}◉{x} │   │",
            "│  ╰───╯   ╰───╯   │",
            "│                   │",
            "│                   │",
            "│      ╭─────╮      │",
            "│      │     │      │",
        ),
        "happy": (
            "│  ╭───╮   ╭───╮   │",
            "│  │ {c}◕{x} │   │ {c}◕{x} │   │",
            "│  ╰───╯   ╰───╯   │",
            "│       {c}⌣{x}        │",
            "│                   │",
            "│      ╭─────╮      │",
            "│      │ {c}⌣{x}  │      │",
        ),
        "sad": (
            "│  ╭───╮   ╭───╮   │",
            "│  │ {c}◉{x} │   │ {c}◉{x} │   │",
            "│  ╰───╯   ╰───╯   │",
            "│                   │",
            "│                   │",
            "│      ╭─────╮      │",
            "│      │ {d}⌒{x}  │      │",
        ),
        "angry": (
            "│  ╭───╮   ╭───╮   │",
            "│  │ {c}>{x} │   │ {c}<{x} │   │",
            "│  ╰───╯   ╰───╯   │",
            "│      {c}⤊{x} {c}⤊{x}      │",
            "│                   │",
            "│      ╭─────╮      │",
            "│      │ {d}⌒{x}  │      │",
        ),
        "surprised": (
            "│  ╭───╮   ╭───╮   │",
            "│  │ {c}◎{x} │   │ {c}◎{x} │   │",
            "│  ╰───╯   ╰───╯   │",
            "│       {c}○{x}        │",
            "│                   │",
            "│      ╭─────╮      │",
            "│      │ {c}O{x}   │      │",
        ),
        "thinking": (
            "│  ╭───╮   ╭───╮   │",
            "│  │ {c}◔{x} │   │ {c}◔{x} │   │",
            "│  ╰───╯   ╰───╯   │",
            "│       {c}¿{x}        │",
            "│                   │",
            "│      ╭─────╮      │",
            "│      │ {c}⌠{x}  │      │",
        ),
        "listening": (
            "│  ╭───╮   ╭───╮   │",
            "│  │ {c}◉{x} │   │ {c}◉{x} │   │",
            "│  ╰───╯   ╰───╯   │",
            "│      {c}·{x} {c}·{x}       │",
            "│                   │",
            "│      ╭─────╮      │",
            "│      │ {c}⌣{x}  │      │",
        ),
        "speaking": (
            "│  ╭───╮   ╭───╮   │",
            "│  │ {c}◉{x} │   │ {c}◉{x} │   │",
            "│  ╰───╯   ╰───╯   │",
            "│                   │",
            "│                   │",
            "│      ╭─────╮      │",
            "│      │ {c}ω{x}   │      │",
        ),
        "sleeping": (
            "│  ╭───╮   ╭───╮   │",
            "│  │ {d}∪{x} │   │ {d}∪{x} │   │",
            "│  ╰───╯   ╰───╯   │",
            "│      {d}z Z Z{x}    │",
            "│                   │",
            "│      ╭─────╮      │",
            "│      │     │      │",
        ),
        "error": (
            "│  ╭───╮   ╭───╮   │",
            "│  │ {c}X{x} │   │ {c}X{x} │   │",
            "│  ╰───╯   ╰───╯   │",
            "│      {c}!{x} {c}!{x}       │",
            "│                   │",
            "│      ╭─────╮      │",
            "│      │ {d}⌂{x}  │      │",
        ),
    }

    ANONYMOUS = {
        "neutral": (
            "│  ╭─────╮ ╭─────╮  │",
            "│  │ {m}█{x} {m}█{x} │ │ {m}█{x} {m}█{x} │  │",
            "│  │ {m}█{x} {m}█{x} │ │ {m}█{x} {m}█{x} │  │",
            "│  ╰─────╯ ╰─────╯  │",
            "│   {m}█{x}▀▀▀▀▀▀▀{m}█{x}   │",
            "│   {m}█{x}       {m}█{x}   │",
            "│   {m}█{x}▄▄▄▄▄▄▄{m}█{x}   │",
        ),
        "happy": (
            "│  ╭─────╮ ╭─────╮  │",
            "│  │ {m}█{x} {m}█{x} │ │ {m}█{x} {m}█{x} │  │",
            "│  │ {m}█{x} {m}█{x} │ │ {m}█{x} {m}█{x} │  │",
            "│  ╰─────╯ ╰─────╯  │",
            "│   {m}█{x}▜▝▀▀▀▀▘▛{m}█{x}   │",
            "│   {m}█{x}▟▙▄▄▄▄▙▟{m}█{x}   │",
            "│   {m}█{x}▟▙▟▙▟▙▟{m}█{x}   │",
        ),
        "sad": (
            "│  ╭─────╮ ╭─────╮  │",
            "│  │ {m}█{x} {m}█{x} │ │ {m}█{x} {m}█{x} │  │",
            "│  │ {m}█{x} {m}█{x} │ │ {m}█{x} {m}█{x} │  │",
            "│  ╰─────╯ ╰─────╯  │",
            "│   {d}█{x}{d}▀{x}{d}▀{x}{d}▀{x}{d}▀{x}{d}▀{x}{d}█{x}   │",
            "│   {d}█{x}       {d}█{x}   │",
            "│   {d}█{x}{d}▄{x}{d}▄{x}{d}▄{x}{d}▄{x}{d}▄{x}{d}█{x}   │",
        ),
        "angry": (
            "│  ╭─────╮ ╭─────╮  │",
            "│  │ {e}>{x} {e}>{x} │ │ {e}<{x} {e}<{x} │  │",
            "│  │ {e}>{x} {e}>{x} │ │ {e}<{x} {e}<{x} │  │",
            "│  ╰─────╯ ╰─────╯  │",
            "│   {e}█{x}{e}▀{x}{e}▀{x}{e}▀{x}{e}▀{x}{e}▀{x}{e}█{x}   │",
            "│   {e}█{x}       {e}█{x}   │",
            "│   {e}█{x}{e}▄{x}{e}▄{x}{e}▄{x}{e}▄{x}{e}▄{x}{e}█{x}   │",
        ),
        "surprised": (
            "│  ╭─────╮ ╭─────╮  │",
            "│  │ {a}○{x} {a}○{x} │ │ {a}○{x} {a}○{x} │  │",
            "│  │ {a}○{x} {a}○{x} │ │ {a}○{x} {a}○{x} │  │",
            "│  ╰─────╯ ╰─────╯  │",
            "│   {m}█{x}▀▀▀▀▀▀▀{m}█{x}   │",
            "│   {m}█{x}       {m}█{x}   │",
            "│   {m}█{x}▄▄▄▄▄▄▄{m}█{x}   │",
        ),
        "thinking": (
            "│  ╭─────╮ ╭─────╮  │",
            "│  │ {m}█{x} {m}█{x} │ │ {m}█{x} {m}█{x} │  │",
            "│  │ {m}█{x} {m}█{x} │ │ {m}█{x} {m}█{x} │  │",
            "│  ╰─────╯ ╰─────╯  │",
            "│   {m}█{x}▀▀▀▀▀▀▀{m}█{x}   │",
            "│   {m}█{x}▖     ▘{m}█{x}   │",
            "│   {m}█{x}▄▄▄▄▄▄▄{m}█{x}   │",
        ),
        "listening": (
            "│  ╭─────╮ ╭─────╮  │",
            "│  │ {m}█{x} {m}█{x} │ │ {m}█{x} {m}█{x} │  │",
            "│  │ {m}█{x} {m}█{x} │ │ {m}█{x} {m}█{x} │  │",
            "│  ╰─────╯ ╰─────╯  │",
            "│   {g}·{x} {g}·{x} {g}·{x} {g}·{x} {g}·{x} {g}·{x} {g}·{x}   │",
            "│   {m}█{x}       {m}█{x}   │",
            "│   {m}█{x}▄▄▄▄▄▄▄{m}█{x}   │",
        ),
        "speaking": (
            "│  ╭─────╮ ╭─────╮  │",
            "│  │ {m}█{x} {m}█{x} │ │ {m}█{x} {m}█{x} │  │",
            "│  │ {m}█{x} {m}█{x} │ │ {m}█{x} {m}█{x} │  │",
            "│  ╰─────╯ ╰─────╯  │",
            "│   {m}█{x}▀▀▀▀▀▀▀{m}█{x}   │",
            "│   {m}█{x}▟▙▄▄▄▄▙▟{m}█{x}   │",
            "│   {m}█{x}▟▙▟▙▟▙▟{m}█{x}   │",
        ),
        "sleeping": (
            "│  ╭─────╮ ╭─────╮  │",
            "│  │ {d}∪{x} {d}∪{x} │ │ {d}∪{x} {d}∪{x} │  │",
            "│  │ {d}∪{x} {d}∪{x} │ │ {d}∪{x} {d}∪{x} │  │",
            "│  ╰─────╯ ╰─────╯  │",
            "│      {d}z Z Z{x}    │",
            "│   {d}█{x}       {d}█{x}   │",
            "│   {d}█{x}{d}▄{x}{d}▄{x}{d}▄{x}{d}▄{x}{d}▄{x}{d}█{x}   │",
        ),
        "error": (
            "│  ╭─────╮ ╭─────╮  │",
            "│  │ {e}X{x} {e}X{x} │ │ {e}X{x} {e}X{x} │  │",
            "│  │ {e}X{x} {e}X{x} │ │ {e}X{x} {e}X{x} │  │",
            "│  ╰─────╯ ╰─────╯  │",
            "│   {e}█{x}{e}▀{x}{e}▀{x}{e}▀{x}{e}▀{x}{e}▀{x}{e}█{x}   │",
            "│   {e}█{x}       {e}█{x}   │",
            "│   {e}█{x}{e}▄{x}{e}▄{x}{e}▄{x}{e}▄{x}{e}▄{x}{e}█{x}   │",
        ),
    }

    MINIMAL = {
        "neutral": (
            "│                   │",
            "│      ─   ─      │",
            "│                   │",
            "│                   │",
            "│                   │",
            "│        —         │",
            "│                   │",
        ),
        "happy": (
            "│                   │",
            "│      ⌣   ⌣      │",
            "│                   │",
            "│                   │",
            "│                   │",
            "│       ⌣          │",
            "│                   │",
        ),
        "sad": (
            "│                   │",
            "│      ⌢   ⌢      │",
            "│                   │",
            "│                   │",
            "│                   │",
            "│       ⌒          │",
            "│                   │",
        ),
        "angry": (
            "│                   │",
            "│      >   <       │",
            "│                   │",
            "│                   │",
            "│                   │",
            "│       ⌒          │",
            "│                   │",
        ),
        "surprised": (
            "│                   │",
            "│      ○   ○      │",
            "│                   │",
            "│                   │",
            "│                   │",
            "│       O          │",
            "│                   │",
        ),
        "thinking": (
            "│                   │",
            "│      /   \\\\      │",
            "│                   │",
            "│        ?         │",
            "│                   │",
            "│        ~         │",
            "│                   │",
        ),
        "listening": (
            "│                   │",
            "│      ─   ─      │",
            "│                   │",
            "│       ·          │",
            "│                   │",
            "│       ⌣          │",
            "│                   │",
        ),
        "speaking": (
            "│                   │",
            "│      ─   ─      │",
            "│                   │",
            "│                   │",
            "│       ⌣          │",
            "│       ω          │",
            "│                   │",
        ),
        "sleeping": (
            "│                   │",
            "│      ∪   ∪      │",
            "│                   │",
            "│     z Z Z        │",
            "│                   │",
            "│                   │",
            "│                   │",
        ),
        "error": (
            "│                   │",
            "│      X   X       │",
            "│                   │",
            "│                   │",
            "│                   │",
            "│       ⌂          │",
            "│                   │",
        ),
    }

    # ── Speaking animation frames (multi-frame mouth) ──────────
    SPEAK_FRAMES = {
        "robot": [
            (
                "│                   │",
                "│      ╭─────╮      │",
                "│      │ {c}⌣{x}  │      │",
                "│      ╰─────╯      │",
            ),
            (
                "│                   │",
                "│      ╭─────╮      │",
                "│      │ {c}ω{x}   │      │",
                "│      ╰─────╯      │",
            ),
            (
                "│                   │",
                "│      ╭─────╮      │",
                "│      │ {c}○{x}   │      │",
                "│      ╰─────╯      │",
            ),
            (
                "│                   │",
                "│      ╭─────╮      │",
                "│      │ {c}ω{x}   │      │",
                "│      ╰─────╯      │",
            ),
        ],
        "anonymous": [
            (
                "│   {c}█{x}▀▀▀▀▀▀▀{c}█{x}   │",
                "│   {c}█{x}▟▙▄▄▄▄▙▟{c}█{x}   │",
            ),
            (
                "│   {c}█{x}▟▙▟▙▟▙▟{c}█{x}   │",
                "│   {c}█{x}▟▙▄▄▄▄▙▟{c}█{x}   │",
            ),
        ],
        "minimal": [
            ("│       ⌣          │",),
            ("│       ω          │",),
            ("│       O          │",),
            ("│       ω          │",),
        ],
    }

    # ── Tissue/breathing animation ──────────────────────────────
    BREATHE_FRAMES = [" ", " ", " ", " ", " ", " ", " ", " ", " ", " ",
                      " ", " ", " ", " ", " ", " ", " ", " ", " ", " ",
                      " ", " ", " ", " ", " ", " ", "▸", "▸", "▸", "▸",
                      "▸", "▸", "▸", "▸", "▸", "▸", "▸", "▸", "▸", "▸",
                      "▸", "▸", "▸", "▸", "▸", "▸", "▸", "▸", "▸", "▸",
                      "▸", "▸", "▸", "▸", "▸", "▸", "▸", "▸", "▸", "▸",
                      "▸", "▸", "▸", "▸", "▸", "▸", "▸", "▸", "▸", "▸",
                      "▸", "▸", "▸", "▸", "▸", "▸", "▸", "▸", "▸", "▸",
                      "▸", "▸", "▸", "▸", "▸", "▸", "▸", "▸", "▸", "▸",
                      " ", " ", " ", " ", " ", " ", " ", " ", " ", " "]

    def __init__(self):
        self.current_emotion = "neutral"
        self.style = "robot"
        self._speak_frame = 0
        self._breathe_idx = 0

    def set_style(self, style):
        if style in self.STYLE_COLORS:
            self.style = style

    def set_emotion(self, emotion):
        self.current_emotion = _normalize_emotion(emotion)

    def get_designs(self):
        """Return the design dict for the current style."""
        if self.style == "robot":
            return self.ROBOT
        elif self.style == "anonymous":
            return self.ANONYMOUS
        return self.MINIMAL

    def _apply_colors(self, line: str, theme: dict) -> str:
        """Replace {c} {d} {g} {m} {a} {e} {x} color placeholders."""
        line = line.replace("{c}", theme.get("eyes", ""))
        line = line.replace("{m}", theme.get("mask", theme.get("eyes", "")))
        line = line.replace("{d}", theme.get("dim", ""))
        line = line.replace("{g}", Color.GREEN)
        line = line.replace("{a}", theme.get("accent", ""))
        line = line.replace("{e}", Color.RED)
        line = line.replace("{x}", Color.RESET)
        return line

    def render(self, blink_frame=None, speak_frame=None, breathe_frame=None):
        """Render the face as a colored ANSI string.

        Args:
            blink_frame: None (normal), 0 (open), 1 (half), 2 (closed)
            speak_frame: if not None, use speaking animation frame
            breathe_frame: if not None, add breathing indicator

        Returns:
            Colored ANSI string (multiple lines)
        """
        theme = self.STYLE_COLORS.get(self.style, self.STYLE_COLORS["robot"])
        designs = self.get_designs()

        # Pick the emotion design
        if blink_frame is not None:
            emotion_key = "neutral"
        else:
            emotion_key = self.current_emotion
            if emotion_key not in designs:
                emotion_key = "neutral"

        raw_lines = list(designs.get(emotion_key, designs["neutral"]))

        # If speaking and we have anim frames, overlay mouth
        if speak_frame is not None and self.style in self.SPEAK_FRAMES:
            frames = self.SPEAK_FRAMES[self.style]
            frame = frames[speak_frame % len(frames)]
            # Overlay the mouth area (last 3-4 lines of the face)
            for i, fline in enumerate(frame):
                line_idx = len(raw_lines) - len(frame) + i
                if 0 <= line_idx < len(raw_lines):
                    raw_lines[line_idx] = fline

        # Build the full face
        border_color = theme.get("border", "")
        label_color = theme.get("label", "")

        label = emotion_key.upper()
        if blink_frame is not None:
            label = "BLINK"

        lines = []
        lines.append(f"{border_color}{self.HEAD_TOP}{Color.RESET}")
        for raw_line in raw_lines:
            colored = self._apply_colors(raw_line, theme)
            lines.append(f"{border_color}{colored}{Color.RESET}")
        lines.append(f"{border_color}{self.HEAD_BOTTOM}{Color.RESET}")

        # Add breathing indicator
        breath_char = ""
        if breathe_frame is not None:
            bf = breathe_frame % len(self.BREATHE_FRAMES)
            breath_char = self.BREATHE_FRAMES[bf]

        header = f" [{label_color}{label}{Color.RESET}]{breath_char}"
        return header + "\n" + "\n".join(lines) + "\n"


# ═══════════════════════════════════════════════════════════════════
#  Face — High-level controller
# ═══════════════════════════════════════════════════════════════════

class Face:
    """Unified face interface with animations.

    Features:
      - Emotion display (neutral, happy, thinking, etc.)
      - Real-time blinking (time-delta driven)
      - Speaking mouth animation (frame cycling)
      - Idle breathing indicator
      - 3 visual styles with ANSI color themes

    Usage:
        face = Face()
        face.show_emotion("happy")
        face.set_style("anonymous")
        face.listen_start()
        face.think()
        face.speak_start()
        face.speak_end()
    """

    FACE_HEIGHT = 9  # rows in the new, larger face

    CURSOR_UP   = f"\033[{FACE_HEIGHT + 1}A"  # +1 for label line
    CLEAR_DOWN  = "\033[J"

    def __init__(self, settings=None):
        self.settings = settings or {}
        self.mode = self.settings.get("face.mode", "terminal")
        self.style_name = self.settings.get("face.style", "robot")

        self.current_emotion = "neutral"
        self._is_speaking = False

        # ── Blink state machine ────────────────────────────────
        self._blink_interval = random.uniform(2.0, 6.0)
        self._blink_phase = "idle"
        self._blink_t = 0.0
        self._blink_phase_duration = 0.08
        self._last_blink_completed = time.monotonic()
        self._last_blink_tick = time.monotonic()

        # ── Speak animation state ──────────────────────────────
        self._speak_frame = 0
        self._speak_last_tick = time.monotonic()
        self._speak_frame_interval = 0.12  # seconds per frame

        # ── Breathing animation ────────────────────────────────
        self._breathe_idx = 0
        self._breathe_last_tick = time.monotonic()
        self._breathe_interval = 0.1

        # ── Backend ────────────────────────────────────────────
        self._backend = TerminalFace()
        self._backend.set_style(self.style_name)

        self._first_render = True

        print(f"🎭 JARVIS face ready! Mode: {self.mode} | Style: {self.style_name}")

    # ── Public API ──────────────────────────────────────────────

    def set_style(self, style):
        self.style_name = style
        self._backend.set_style(style)
        self._update_display()

    def show_emotion(self, emotion):
        self.current_emotion = _normalize_emotion(emotion)
        self._backend.set_emotion(self.current_emotion)
        if emotion != "speaking":
            self._is_speaking = False
        self._update_display()

    def look_at(self, x, y):
        """Eye tracking target (0.0-1.0 normalized). Stub for future use."""
        pass

    def speak_start(self):
        """Start speaking animation.

        Begins cycling the mouth animation in a background thread
        until speak_end() is called.
        """
        self._is_speaking = True
        self._speak_frame = 0
        self._speak_last_tick = time.monotonic()
        self.current_emotion = "speaking"
        self._backend.set_emotion("speaking")
        self._update_display()

        # Start background render loop for mouth animation
        self._speak_stop_event = threading.Event()
        self._speak_thread = threading.Thread(
            target=self._speak_render_loop,
            daemon=True,
            name="face-speak",
        )
        self._speak_thread.start()

    def speak_end(self):
        """Stop speaking animation and return to neutral."""
        self._is_speaking = False
        # Signal the render loop to stop
        if hasattr(self, '_speak_stop_event'):
            self._speak_stop_event.set()
        self.current_emotion = "neutral"
        self._backend.set_emotion("neutral")
        self._update_display()

    def _speak_render_loop(self):
        """Background thread: cycle mouth animation frames."""
        while self._is_speaking and not self._speak_stop_event.is_set():
            self._update_display()
            self._speak_stop_event.wait(0.12)  # ~8 fps

    def listen_start(self):
        self.show_emotion("listening")

    def think(self):
        self.show_emotion("thinking")

    def is_thinking(self):
        return self.current_emotion == "thinking"

    # ── Tick: advance all animations ────────────────────────────

    def _tick(self, now):
        """Advance blink, speak, and breathe animations."""
        blink_frame = self._tick_blink(now)
        speak_frame = self._tick_speak(now)
        breathe_frame = self._tick_breathe(now)
        return blink_frame, speak_frame, breathe_frame

    def _tick_blink(self, now):
        if self._blink_phase == "idle":
            elapsed = now - self._last_blink_completed
            if elapsed >= self._blink_interval:
                self._blink_phase = "lowering"
                self._blink_t = 0.0
                self._last_blink_tick = now
                self._blink_interval = random.uniform(2.0, 6.0)
                return 0
            return None

        dt = now - self._last_blink_tick
        self._last_blink_tick = now
        self._blink_t += dt

        if self._blink_phase == "lowering":
            if self._blink_t >= self._blink_phase_duration:
                self._blink_phase = "closed"
                self._blink_t = 0.0
                self._last_blink_tick = now
                return 2
            return 1

        if self._blink_phase == "closed":
            if self._blink_t >= self._blink_phase_duration * 0.5:
                self._blink_phase = "raising"
                self._blink_t = 0.0
                self._last_blink_tick = now
                return 2
            return 2

        if self._blink_phase == "raising":
            if self._blink_t >= self._blink_phase_duration:
                self._blink_phase = "idle"
                self._blink_t = 0.0
                self._last_blink_completed = now
                return 0
            return 1

        return None

    def _tick_speak(self, now):
        if not self._is_speaking:
            return None
        dt = now - self._speak_last_tick
        if dt >= self._speak_frame_interval:
            self._speak_frame += 1
            self._speak_last_tick = now
        return self._speak_frame

    def _tick_breathe(self, now):
        dt = now - self._breathe_last_tick
        if dt >= self._breathe_interval:
            self._breathe_idx += 1
            self._breathe_last_tick = now
        return self._breathe_idx

    # ── Terminal display ────────────────────────────────────────

    def _update_display(self):
        if self.mode != "terminal":
            return

        now = time.monotonic()
        blink_frame, speak_frame, breathe_frame = self._tick(now)

        rendered = self._backend.render(
            blink_frame=blink_frame,
            speak_frame=speak_frame,
            breathe_frame=breathe_frame,
        )

        if self._first_render:
            self._first_render = False
            sys.stdout.write("\n")
            sys.stdout.write(rendered)
        else:
            sys.stdout.write(self.CURSOR_UP)
            sys.stdout.write(self.CLEAR_DOWN)
            sys.stdout.write(rendered)

        sys.stdout.flush()

    # ── Demo mode ───────────────────────────────────────────────

    def animate_demo(self):
        """Cycle through all emotions with descriptions."""
        emotions = [
            ("neutral",   1.2),
            ("happy",     1.2),
            ("thinking",  1.5),
            ("listening", 1.0),
            ("speaking",  1.8),
            ("surprised", 0.8),
            ("sad",       0.8),
            ("angry",     0.6),
            ("sleeping",  1.5),
            ("error",     1.0),
            ("neutral",   0.5),
        ]

        # Clear screen
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.write("=" * 50 + "\n")
        sys.stdout.write("  🤖 JARVIS FACE DEMO\n")
        sys.stdout.write("=" * 50 + "\n\n")
        sys.stdout.flush()

        self._first_render = True

        for emotion, duration in emotions:
            # Print label above the face
            label = emotion.upper()
            sys.stdout.write(f"\n  [{label:12s}]\n")
            sys.stdout.flush()

            self.show_emotion(emotion)
            time.sleep(duration)

        sys.stdout.write("\n" + "=" * 50 + "\n")
        sys.stdout.write("  ✅ Demo complete. JARVIS is ready.\n")
        sys.stdout.write("=" * 50 + "\n")
        sys.stdout.flush()
