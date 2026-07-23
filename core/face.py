"""
Face Engine — Animated face for JARVIS.

Modes:
  - terminal: ASCII art rendered to terminal (works immediately)
  - pygame:   Animated vector face on LCD/display (future)

Styles:
  - robot:      Round eyes, geometric mouth (classic robot look)
  - anonymous:  Minimalist mask style (V for Vendetta inspired)
  - minimal:    Simple dots and lines (smallest footprint)
"""

import time
import sys
import random
from enum import Enum


class Emotion(Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    SURPRISED = "surprised"
    THINKING = "thinking"
    LISTENING = "listening"
    SPEAKING = "speaking"
    SLEEPING = "sleeping"
    ERROR = "error"


class FaceStyle(Enum):
    ROBOT = "robot"
    ANONYMOUS = "anonymous"
    MINIMAL = "minimal"


def _normalize_emotion(emotion):
    """Convert Emotion enum or string to lowercase string."""
    if isinstance(emotion, Emotion):
        return emotion.value
    return str(emotion).lower()


class TerminalFace:
    """ASCII art face rendered in the terminal."""

    DESIGNS = {
        "robot": {
            "neutral": (
                " ┌──────┐ \n"
                " │ ◉  ◉ │ \n"
                " │      │ \n"
                " │  __  │ \n"
                " └──────┘ "
            ),
            "happy": (
                " ┌──────┐ \n"
                " │ ◕  ◕ │ \n"
                " │  ⌣  │ \n"
                " │  ⌣  │ \n"
                " └──────┘ "
            ),
            "sad": (
                " ┌──────┐ \n"
                " │ ◉  ◉ │ \n"
                " │      │ \n"
                " │  ⌒  │ \n"
                " └──────┘ "
            ),
            "angry": (
                " ┌──────┐ \n"
                " │ >  < │ \n"
                " │      │ \n"
                " │  ⌒  │ \n"
                " └──────┘ "
            ),
            "surprised": (
                " ┌──────┐ \n"
                " │ ◎  ◎ │ \n"
                " │  ○  │ \n"
                " │  O  │ \n"
                " └──────┘ "
            ),
            "thinking": (
                " ┌──────┐ \n"
                " │ ◔  ◔ │ \n"
                " │  ¿  │ \n"
                " │  ⌠  │ \n"
                " └──────┘ "
            ),
            "listening": (
                " ┌──────┐ \n"
                " │ ◉  ◉ │ \n"
                " │  ·  │ \n"
                " │  ⌣  │ \n"
                " └──────┘ "
            ),
            "speaking": (
                " ┌──────┐ \n"
                " │ ◉  ◉ │ \n"
                " │  ⌣  │ \n"
                " │  ω  │ \n"
                " └──────┘ "
            ),
            "sleeping": (
                " ┌──────┐ \n"
                " │ ∪  ∪ │ \n"
                " │      │ \n"
                " │  zz  │ \n"
                " └──────┘ "
            ),
            "error": (
                " ┌──────┐ \n"
                " │ X  X │ \n"
                " │      │ \n"
                " │  ⌂  │ \n"
                " └──────┘ "
            ),
        },
        "anonymous": {
            "neutral": (
                " ┌──────┐ \n"
                " │ █  █ │ \n"
                " │ █▀▀▀█ │ \n"
                " │ █  █ │ \n"
                " └──────┘ "
            ),
            "happy": (
                " ┌──────┐ \n"
                " │ █  █ │ \n"
                " │ █▜▝▀█ │ \n"
                " │ █▟▙▟█ │ \n"
                " └──────┘ "
            ),
            "thinking": (
                " ┌──────┐ \n"
                " │ █  █ │ \n"
                " │ █▀▀▀█ │ \n"
                " │ █▖  █ │ \n"
                " └──────┘ "
            ),
            "surprised": (
                " ┌──────┐ \n"
                " │ █  █ │ \n"
                " │ █▀▀▀█ │ \n"
                " │ █  █ │ \n"
                " └──────┘ "
            ),
            "listening": (
                " ┌──────┐ \n"
                " │ █  █ │ \n"
                " │ █▀▀▀█ │ \n"
                " │ █  █ │ \n"
                " └──────┘ "
            ),
            "speaking": (
                " ┌──────┐ \n"
                " │ █  █ │ \n"
                " │ █▀▀▀█ │ \n"
                " │ █▟▙▟█ │ \n"
                " └──────┘ "
            ),
            "error": (
                " ┌──────┐ \n"
                " │ X  X │ \n"
                " │ █▀▀▀█ │ \n"
                " │ █  █ │ \n"
                " └──────┘ "
            ),
        },
        "minimal": {
            "neutral": (
                " ┌──────┐ \n"
                " │ ─  ─ │ \n"
                " │      │ \n"
                " │  —   │ \n"
                " └──────┘ "
            ),
            "happy": (
                " ┌──────┐ \n"
                " │ ⌣  ⌣ │ \n"
                " │      │ \n"
                " │  ⌣   │ \n"
                " └──────┘ "
            ),
            "sad": (
                " ┌──────┐ \n"
                " │ ⌢  ⌢ │ \n"
                " │      │ \n"
                " │  ⌒   │ \n"
                " └──────┘ "
            ),
            "angry": (
                " ┌──────┐ \n"
                " │ >  < │ \n"
                " │      │ \n"
                " │  ⌒   │ \n"
                " └──────┘ "
            ),
            "thinking": (
                " ┌──────┐ \n"
                " │ /  \\ │ \n"
                " │  ?   │ \n"
                " │  ~   │ \n"
                " └──────┘ "
            ),
            "surprised": (
                " ┌──────┐ \n"
                " │ ○  ○ │ \n"
                " │      │ \n"
                " │  O   │ \n"
                " └──────┘ "
            ),
            "speaking": (
                " ┌──────┐ \n"
                " │ ─  ─ │ \n"
                " │  ⌣  │ \n"
                " │  ω   │ \n"
                " └──────┘ "
            ),
            "listening": (
                " ┌──────┐ \n"
                " │ ─  ─ │ \n"
                " │  ·  │ \n"
                " │  ⌣  │ \n"
                " └──────┘ "
            ),
            "sleeping": (
                " ┌──────┐ \n"
                " │ ∪  ∪ │ \n"
                " │      │ \n"
                " │  zz  │ \n"
                " └──────┘ "
            ),
            "error": (
                " ┌──────┐ \n"
                " │ X  X │ \n"
                " │      │ \n"
                " │  ⌂   │ \n"
                " └──────┘ "
            ),
        },
    }

    BLINK_OPEN = (
        " ┌──────┐ \n"
        " │ ◉  ◉ │ \n"
        " │      │ \n"
        " │  __  │ \n"
        " └──────┘ "
    )
    BLINK_HALF = (
        " ┌──────┐ \n"
        " │ ―  ― │ \n"
        " │      │ \n"
        " │  __  │ \n"
        " └──────┘ "
    )
    BLINK_CLOSED = (
        " ┌──────┐ \n"
        " │ ─  ─ │ \n"
        " │      │ \n"
        " │  __  │ \n"
        " └──────┘ "
    )

    def __init__(self):
        self.current_emotion = "neutral"
        self.style = "robot"

    def set_style(self, style):
        if style in self.DESIGNS:
            self.style = style

    def set_emotion(self, emotion):
        self.current_emotion = _normalize_emotion(emotion)

    def render(self, blink_frame=None):
        """Render the face as an ASCII string.

        Args:
            blink_frame: None (normal), 0 (open), 1 (half), 2 (closed)
        """
        if blink_frame is not None:
            if blink_frame == 0:
                face = self.BLINK_OPEN
            elif blink_frame == 1:
                face = self.BLINK_HALF
            else:
                face = self.BLINK_CLOSED
            label = "BLINK"
        else:
            style_designs = self.DESIGNS.get(self.style, self.DESIGNS["robot"])
            face = style_designs.get(self.current_emotion, style_designs["neutral"])
            label = self.current_emotion.upper()

        return f" [{label}]\n{face}\n"


class Face:
    """Unified face interface.

    Example:
        >>> face = Face()
        >>> face.show_emotion("happy")
        >>> face.set_style("anonymous")
        >>> face.listen_start()
        >>> face.think()
        >>> face.speak_start()
        >>> face.speak_end()
    """

    CURSOR_UP = "\033[6A"
    CLEAR_LINE = "\033[2K"
    CLEAR_DOWN = "\033[J"
    HOME = "\033[H"  # Move cursor to top-left

    def __init__(self, settings=None):
        self.settings = settings or {}
        self.mode = self.settings.get("face.mode", "terminal")
        self.style_name = self.settings.get("face.style", "robot")

        self.current_emotion = "neutral"

        # ── Blink state machine (driven by real time deltas) ──
        self._blink_interval = random.uniform(2.0, 6.0)
        self._blink_phase = "idle"        # idle | lowering | closed | raising
        self._blink_t = 0.0               # progress in seconds within phase
        self._blink_phase_duration = 0.08  # seconds per blink phase
        self._last_blink_completed = time.monotonic()
        self._last_blink_tick = time.monotonic()

        # Face tracking target (for future eye tracking)
        self._look_x = 0.5
        self._look_y = 0.5

        self._backend = TerminalFace()
        self._backend.set_style(self.style_name)

        self._first_render = True

        print(f"🎭 JARVIS face ready! Mode: {self.mode} | Style: {self.style_name}")

    # ── Public API ──────────────────────────────────────────────

    def set_style(self, style):
        """Switch face style: 'robot', 'anonymous', or 'minimal'."""
        self.style_name = style
        self._backend.set_style(style)

    def show_emotion(self, emotion):
        """Display an emotion on the face.

        Args:
            emotion: Emotion enum OR lowercase string like "happy"
        """
        self.current_emotion = _normalize_emotion(emotion)
        self._backend.set_emotion(self.current_emotion)
        self._update_display()

    def look_at(self, x, y):
        """Set target for eye tracking (0.0-1.0 normalized)."""
        self._look_x = max(0.0, min(1.0, x))
        self._look_y = max(0.0, min(1.0, y))

    def speak_start(self):
        self.show_emotion("speaking")

    def speak_end(self):
        self.show_emotion("neutral")

    def listen_start(self):
        self.show_emotion("listening")

    def think(self):
        self.show_emotion("thinking")

    # ── Blink state machine (real-time deltas) ──────────────────

    def _tick_blink(self, now):
        """Advance blink state machine using real time deltas.
        
        Returns blink_frame: None (normal render), 0 (open), 1 (half), 2 (closed).
        """
        if self._blink_phase == "idle":
            elapsed = now - self._last_blink_completed
            if elapsed >= self._blink_interval:
                self._blink_phase = "lowering"
                self._blink_t = 0.0
                self._last_blink_tick = now
                self._blink_interval = random.uniform(2.0, 6.0)
                return 0
            return None

        # Use real time delta for progression
        dt = now - self._last_blink_tick
        self._last_blink_tick = now
        self._blink_t += dt

        if self._blink_phase == "lowering":
            if self._blink_t >= self._blink_phase_duration:
                self._blink_phase = "closed"
                self._blink_t = 0.0
                self._last_blink_tick = now
                return 2
            return 1  # half-closed

        if self._blink_phase == "closed":
            if self._blink_t >= self._blink_phase_duration * 0.5:
                self._blink_phase = "raising"
                self._blink_t = 0.0
                self._last_blink_tick = now
                return 2  # still closed
            return 2

        if self._blink_phase == "raising":
            if self._blink_t >= self._blink_phase_duration:
                self._blink_phase = "idle"
                self._blink_t = 0.0
                self._last_blink_completed = now
                return 0  # open
            return 1  # half

        return None

    # ── Terminal display ────────────────────────────────────────

    def _update_display(self):
        """Render face to terminal with proper cursor positioning."""
        if self.mode != "terminal":
            return

        blink_frame = self._tick_blink(time.monotonic())
        rendered = self._backend.render(blink_frame=blink_frame)

        if self._first_render:
            self._first_render = False
            sys.stdout.write(rendered)
        else:
            # Move cursor up 6 lines, clear from there down, write face
            sys.stdout.write(self.CURSOR_UP)
            sys.stdout.write(self.CLEAR_DOWN)
            sys.stdout.write(rendered)

        sys.stdout.flush()

    # ── Demo mode (prints descriptions THEN face in a clean area) ─

    def animate_demo(self):
        """Cycle through all emotions with descriptions."""
        emotions = [
            ("neutral",   1.0),
            ("happy",     1.0),
            ("thinking",  1.5),
            ("listening", 0.8),
            ("speaking",  1.5),
            ("surprised", 0.8),
            ("sad",       0.8),
            ("angry",     0.6),
            ("sleeping",  1.5),
            ("error",     1.0),
            ("neutral",   0.5),
        ]

        # Clear screen and show header
        sys.stdout.write("\033[2J\033[H")  # Clear entire screen, home cursor
        sys.stdout.write("=" * 40 + "\n")
        sys.stdout.write("  JARVIS FACE DEMO\n")
        sys.stdout.write("=" * 40 + "\n\n")
        sys.stdout.flush()

        self._first_render = True

        for emotion, duration in emotions:
            # Print description on a new line above the face area
            sys.stdout.write(f"  [{emotion.upper():12s}]\n\n")
            sys.stdout.flush()

            self.show_emotion(emotion)
            time.sleep(duration)

        sys.stdout.write("\n" + "=" * 40 + "\n")
        sys.stdout.write("  ✅ Demo complete. JARVIS is ready.\n")
        sys.stdout.write("=" * 40 + "\n")
        sys.stdout.flush()
