# Face — Animated Face Engine

> **Goal:** JARVIS has an expressive animated face that works in terminal mode AND on a physical LCD screen. Can show emotions, track faces, and sync mouth with speech.
> **Est. time:** 4-6 hours · **Cross-cutting:** Works with Tier 7 (hardware) and Tier 1 (voice)

## ✅ Checklist
- [ ] `core/face.py` — Face engine with multiple rendering modes
- [ ] Mode: `terminal` — ASCII art face in terminal
- [ ] Mode: `pygame` — Animated face on any display
- [ ] Mode: `hardware` — Direct LCD/OLED rendering (future)
- [ ] Robot face style (round eyes, geometric mouth)
- [ ] Anonymous mask style (minimalist, visor-like)
- [ ] Minimal style (simple dots/lines)
- [ ] Emotions: neutral, happy, sad, angry, surprised, thinking, listening, speaking
- [ ] Eye animation (blinking, pupil movement, saccades)
- [ ] Mouth animation (syncs with speech audio level)
- [ ] Face tracking (eyes follow detected face position)
- [ ] Expression transitions (smooth morphing between emotions)
- [ ] Test: "Face displays in terminal mode correctly"

---

## 🎭 Face Styles

### Robot Style
```
😐 Neutral        😊 Happy          🤔 Thinking         😲 Surprised
 ┌──────┐         ┌──────┐          ┌──────┐            ┌──────┐
 │ ◉  ◉ │         │ ◕  ◕ │          │ ◔  ◔ │            │ ◎  ◎ │
 │      │         │  ⌣  │          │  ¿  │            │  ○  │
 │  __  │         │  ⌣  │          │  ⌠  │            │  O  │
 └──────┘         └──────┘          └──────┘            └──────┘
```

### Anonymous Mask Style (V for Vendetta inspired)
```
😐 Neutral        😊 Happy          🤔 Thinking         😲 Surprised
 ┌──────┐         ┌──────┐          ┌──────┐            ┌──────┐
 │ █  █ │         │ █  █ │          │ █  █ │            │ █  █ │
 │ █▀▀▀█ │         │ █▜▝▀█ │          │ █▀▀▀█ │            │ █▀▀▀█ │
 │ █  █ │         │ █▟▙▟█ │          │ █▖  █ │            │ █  █ │
 └──────┘         └──────┘          └──────┘            └──────┘
```

### Minimal Style (single-line visor)
```
😐 Neutral        😊 Happy          🤔 Thinking         😲 Surprised
 ┌──────┐         ┌──────┐          ┌──────┐            ┌──────┐
 │ ─  ─ │         │ ⌣  ⌣ │          │ /  \\ │            │ ○  ○ │
 │      │         │      │          │  ?   │            │      │
 │  —   │         │  ⌣   │          │  ~   │            │  O   │
 └──────┘         └──────┘          └──────┘            └──────┘
```

---

## 📄 core/face.py — Face Engine

```python
"""
Face Engine — Animated face for JARVIS.

Modes:
  - terminal: ASCII art rendered to terminal
  - pygame:   Animated vector face on LCD/display
  - hardware: Direct framebuffer render (future)

Styles:
  - robot:      Round eyes, geometric mouth (classic robot look)
  - anonymous:  Minimalist mask style (V for Vendetta inspired)
  - minimal:    Simple dots and lines (smallest footprint)
"""

import time
import math
import threading
import random
from enum import Enum
from typing import Optional, Callable
from pathlib import Path


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


class FaceMode(Enum):
    TERMINAL = "terminal"
    PYGAME = "pygame"
    HARDWARE = "hardware"


class FaceStyle(Enum):
    ROBOT = "robot"
    ANONYMOUS = "anonymous"
    MINIMAL = "minimal"


# ================================================
# TERMINAL ASCII FACE
# ================================================

class TerminalFace:
    """ASCII art face rendered in the terminal."""
    
    # Face designs for each emotion × style combination
    DESIGNS = {
        FaceStyle.ROBOT: {
            Emotion.NEUTRAL: (
                " ┌──────┐ \n"
                " │ ◉  ◉ │ \n"
                " │      │ \n"
                " │  __  │ \n"
                " └──────┘ "
            ),
            Emotion.HAPPY: (
                " ┌──────┐ \n"
                " │ ◕  ◕ │ \n"
                " │  ⌣  │ \n"
                " │  ⌣  │ \n"
                " └──────┘ "
            ),
            Emotion.THINKING: (
                " ┌──────┐ \n"
                " │ ◔  ◔ │ \n"
                " │  ¿  │ \n"
                " │  ⌠  │ \n"
                " └──────┘ "
            ),
            Emotion.SURPRISED: (
                " ┌──────┐ \n"
                " │ ◎  ◎ │ \n"
                " │  ○  │ \n"
                " │  O  │ \n"
                " └──────┘ "
            ),
            Emotion.SAD: (
                " ┌──────┐ \n"
                " │ ◉  ◉ │ \n"
                " │      │ \n"
                " │  ⌒  │ \n"
                " └──────┘ "
            ),
            Emotion.ANGRY: (
                " ┌──────┐ \n"
                " │ >  < │ \n"
                " │      │ \n"
                " │  ⌒  │ \n"
                " └──────┘ "
            ),
            Emotion.LISTENING: (
                " ┌──────┐ \n"
                " │ ◉  ◉ │ \n"
                " │  ·  │ \n"
                " │  ⌣  │ \n"
                " └──────┘ "
            ),
            Emotion.SPEAKING: (
                " ┌──────┐ \n"
                " │ ◉  ◉ │ \n"
                " │  ⌣  │ \n"
                " │  ω  │ \n"
                " └──────┘ "
            ),
            Emotion.SLEEPING: (
                " ┌──────┐ \n"
                " │ ∪  ∪ │ \n"
                " │      │ \n"
                " │  zz  │ \n"
                " └──────┘ "
            ),
            Emotion.ERROR: (
                " ┌──────┐ \n"
                " │ X  X │ \n"
                " │      │ \n"
                " │  ⌂  │ \n"
                " └──────┘ "
            ),
        },
        
        FaceStyle.ANONYMOUS: {
            Emotion.NEUTRAL: (
                " ┌──────┐ \n"
                " │ █  █ │ \n"
                " │ █▀▀▀█ │ \n"
                " │ █  █ │ \n"
                " └──────┘ "
            ),
            Emotion.HAPPY: (
                " ┌──────┐ \n"
                " │ █  █ │ \n"
                " │ █▜▝▀█ │ \n"
                " │ █▟▙▟█ │ \n"
                " └──────┘ "
            ),
            Emotion.THINKING: (
                " ┌──────┐ \n"
                " │ █  █ │ \n"
                " │ █▀▀▀█ │ \n"
                " │ █▖  █ │ \n"
                " └──────┘ "
            ),
            Emotion.SURPRISED: (
                " ┌──────┐ \n"
                " │ █  █ │ \n"
                " │ █▀▀▀█ │ \n"
                " │ █  █ │ \n"
                " └──────┘ "
            ),
        },
        
        FaceStyle.MINIMAL: {
            Emotion.NEUTRAL: (
                " ┌──────┐ \n"
                " │ ─  ─ │ \n"
                " │      │ \n"
                " │  —   │ \n"
                " └──────┘ "
            ),
            Emotion.HAPPY: (
                " ┌──────┐ \n"
                " │ ⌣  ⌣ │ \n"
                " │      │ \n"
                " │  ⌣   │ \n"
                " └──────┘ "
            ),
            Emotion.SAD: (
                " ┌──────┐ \n"
                " │ ⌢  ⌢ │ \n"
                " │      │ \n"
                " │  ⌒   │ \n"
                " └──────┘ "
            ),
            Emotion.ANGRY: (
                " ┌──────┐ \n"
                " │ >  < │ \n"
                " │      │ \n"
                " │  ⌒   │ \n"
                " └──────┘ "
            ),
            Emotion.THINKING: (
                " ┌──────┐ \n"
                " │ /  \\ │ \n"
                " │  ?   │ \n"
                " │  ~   │ \n"
                " └──────┘ "
            ),
            Emotion.SURPRISED: (
                " ┌──────┐ \n"
                " │ ○  ○ │ \n"
                " │      │ \n"
                " │  O   │ \n"
                " └──────┘ "
            ),
            Emotion.SPEAKING: (
                " ┌──────┐ \n"
                " │ ─  ─ │ \n"
                " │  ⌣  │ \n"
                " │  ω   │ \n"
                " └──────┘ "
            ),
            Emotion.LISTENING: (
                " ┌──────┐ \n"
                " │ ─  ─ │ \n"
                " │  ·  │ \n"
                " │  ⌣  │ \n"
                " └──────┘ "
            ),
            Emotion.SLEEPING: (
                " ┌──────┐ \n"
                " │ ∪  ∪ │ \n"
                " │      │ \n"
                " │  zz  │ \n"
                " └──────┘ "
            ),
            Emotion.ERROR: (
                " ┌──────┐ \n"
                " │ X  X │ \n"
                " │      │ \n"
                " │  ⌂   │ \n"
                " └──────┘ "
            ),
        },
    }
    
    def __init__(self):
        self.current_emotion = Emotion.NEUTRAL
        self.style = FaceStyle.ROBOT
    
    def set_emotion(self, emotion: Emotion):
        self.current_emotion = emotion
    
    def render(self) -> str:
        """Render the face as an ASCII string."""
        style_designs = self.DESIGNS.get(self.style, self.DESIGNS[FaceStyle.ROBOT])
        face = style_designs.get(self.current_emotion, style_designs[Emotion.NEUTRAL])
        
        # Add emotion label
        label = self.current_emotion.value.upper()
        return f" [{label}] \n{face}\n"


# ================================================
# PYGAME VECTOR FACE
# ================================================

class PygameFace:
    """
    Animated vector face rendered via Pygame.
    Smooth animations, eye tracking, mouth sync.
    """
    
    def __init__(self, width: int = 480, height: int = 320):
        self.width = width
        self.height = height
        self.style = FaceStyle.ROBOT
        self.current_emotion = Emotion.NEUTRAL
        self.target_emotion = Emotion.NEUTRAL
        
        # Eye positions (normalized 0.0-1.0)
        self.pupil_x = 0.5
        self.pupil_y = 0.5
        self.target_pupil_x = 0.5
        self.target_pupil_y = 0.5
        
        # Blink state
        self.blink_state = 0.0  # 0=open, 1=closed
        self.is_blinking = False
        self.blink_timer = 0.0
        
        # Mouth state
        self.mouth_openness = 0.0  # 0=closed, 1=open
        self.mouth_shape = "neutral"  # neutral, smile, frown, oval, open
        
        # Transition smoothing
        self.transition_speed = 0.1
        
        self._running = False
        self._screen = None
        self._clock = None
    
    def start(self, fullscreen: bool = False):
        """Start the Pygame display loop."""
        import pygame
        pygame.init()
        flags = pygame.FULLSCREEN if fullscreen else 0
        self._screen = pygame.display.set_mode(
            (self.width, self.height),
            flags
        )
        self._clock = pygame.time.Clock()
        self._running = True
        
        pygame.display.set_caption("JARVIS")
        
        # Hide mouse cursor
        pygame.mouse.set_visible(False)
        
        self._loop()
    
    def stop(self):
        self._running = False
        import pygame
        pygame.quit()
    
    def set_emotion(self, emotion: Emotion):
        """Set target emotion (will transition smoothly)."""
        self.target_emotion = emotion
    
    def look_at(self, x: float, y: float):
        """Set target pupil position (0.0-1.0 normalized)."""
        self.target_pupil_x = max(0.2, min(0.8, x))
        self.target_pupil_y = max(0.2, min(0.8, y))
    
    def set_mouth_openness(self, openness: float):
        """Set mouth openness based on audio level (0.0-1.0)."""
        self.mouth_openness = max(0.0, min(1.0, openness))
        if self.mouth_openness > 0.1:
            self.mouth_shape = "open"
        else:
            self.mouth_shape = "neutral"
    
    def _loop(self):
        """Main Pygame render loop."""
        import pygame
        
        while self._running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._running = False
            
            # Smooth emotion transition
            if self.current_emotion != self.target_emotion:
                self.current_emotion = self.target_emotion
            
            # Smooth pupil movement (easing)
            self.pupil_x += (self.target_pupil_x - self.pupil_x) * 0.1
            self.pupil_y += (self.target_pupil_y - self.pupil_y) * 0.1
            
            # Random blinking
            self.blink_timer += self._clock.get_time() / 1000.0
            if not self.is_blinking and self.blink_timer > random.uniform(2.0, 6.0):
                self.is_blinking = True
                self.blink_timer = 0.0
            if self.is_blinking:
                self.blink_state += 0.2
                if self.blink_state >= 1.0:
                    self.blink_state = 0.0
                    self.is_blinking = False
            
            # Clear screen
            self._screen.fill((0, 0, 0))  # Black background
            
            # Draw face based on style
            if self.style == FaceStyle.ROBOT:
                self._draw_robot_face()
            elif self.style == FaceStyle.ANONYMOUS:
                self._draw_anonymous_face()
            else:
                self._draw_minimal_face()
            
            pygame.display.flip()
            self._clock.tick(30)  # 30 FPS
    
    def _draw_robot_face(self):
        """Draw robot-style face (round eyes, geometric mouth)."""
        import pygame
        
        w, h = self.width, self.height
        center_x = w // 2
        center_y = h // 2
        
        # Face background (dark gray circle)
        face_radius = min(w, h) * 0.4
        pygame.draw.circle(self._screen, (30, 30, 30), 
                          (center_x, center_y), int(face_radius))
        
        # Eyes
        eye_y = center_y - int(face_radius * 0.2)
        eye_spacing = int(face_radius * 0.35)
        eye_radius = int(face_radius * 0.15)
        
        # Blink effect
        if self.is_blinking:
            eye_height = int(eye_radius * (1 - self.blink_state))
        else:
            eye_height = eye_radius
        
        # Left eye socket
        pygame.draw.ellipse(self._screen, (60, 60, 60),
                           (center_x - eye_spacing - eye_radius, eye_y - eye_height,
                            eye_radius * 2, eye_height * 2), 2)
        
        # Right eye socket
        pygame.draw.ellipse(self._screen, (60, 60, 60),
                           (center_x + eye_spacing - eye_radius, eye_y - eye_height,
                            eye_radius * 2, eye_height * 2), 2)
        
        if not self.is_blinking:
            # Pupils (track face position)
            pupil_radius = int(eye_radius * 0.5)
            l_pupil_x = center_x - eye_spacing + int((self.pupil_x - 0.5) * eye_radius * 0.5)
            r_pupil_x = center_x + eye_spacing + int((self.pupil_x - 0.5) * eye_radius * 0.5)
            pupil_y = eye_y + int((self.pupil_y - 0.5) * eye_radius * 0.3)
            
            # Eye glow
            glow_color = (100, 200, 255)  # Blue glow
            pygame.draw.circle(self._screen, glow_color, (l_pupil_x, pupil_y), pupil_radius)
            pygame.draw.circle(self._screen, glow_color, (r_pupil_x, pupil_y), pupil_radius)
            # Pupil highlight
            pygame.draw.circle(self._screen, (200, 230, 255), 
                             (l_pupil_x - 2, pupil_y - 2), pupil_radius // 3)
            pygame.draw.circle(self._screen, (200, 230, 255),
                             (r_pupil_x - 2, pupil_y - 2), pupil_radius // 3)
        
        # Mouth
        mouth_y = center_y + int(face_radius * 0.3)
        mouth_width = int(face_radius * 0.4)
        
        if self.mouth_shape == "neutral":
            # Simple line
            pygame.draw.line(self._screen, (200, 200, 200),
                           (center_x - mouth_width, mouth_y),
                           (center_x + mouth_width, mouth_y), 3)
        elif self.mouth_shape == "smile":
            # Smile arc
            pygame.draw.arc(self._screen, (200, 200, 200),
                          (center_x - mouth_width, mouth_y - 10,
                           mouth_width * 2, 20),
                          0.2, 2.94, 3)
        elif self.mouth_shape == "open":
            # Open mouth (size based on openness)
            mh = 5 + int(self.mouth_openness * 25)
            pygame.draw.ellipse(self._screen, (50, 50, 50),
                              (center_x - mouth_width // 2, mouth_y,
                               mouth_width, mh))
            pygame.draw.ellipse(self._screen, (200, 200, 200),
                              (center_x - mouth_width // 2, mouth_y,
                               mouth_width, mh), 2)
    
    def _draw_anonymous_face(self):
        """Draw anonymous mask style face."""
        # Simplified: draw a mask-like shape with visor eyes
        import pygame
        w, h = self.width, self.height
        center_x = w // 2
        center_y = h // 2
        
        # Face shape (wider oval, mask-like)
        face_w = int(w * 0.5)
        face_h = int(h * 0.7)
        pygame.draw.ellipse(self._screen, (45, 45, 50),
                          (center_x - face_w // 2, center_y - face_h // 2,
                           face_w, face_h))
        pygame.draw.ellipse(self._screen, (80, 80, 90),
                          (center_x - face_w // 2, center_y - face_h // 2,
                           face_w, face_h), 2)
        
        # Visor/eye bar
        visor_y = center_y - int(face_h * 0.15)
        visor_w = int(face_w * 0.7)
        visor_h = int(face_h * 0.15)
        pygame.draw.rect(self._screen, (60, 60, 70),
                        (center_x - visor_w // 2, visor_y - visor_h // 2,
                         visor_w, visor_h), border_radius=5)
        
        # Eyes within visor
        eye_y = visor_y
        eye_spacing = int(visor_w * 0.25)
        eye_size = int(visor_h * 0.5)
        
        if not self.is_blinking:
            glow_color = (150, 220, 255)
            for side in [-1, 1]:
                pygame.draw.circle(
                    self._screen, glow_color,
                    (center_x + side * eye_spacing, eye_y), eye_size
                )
                # Inner glow
                pygame.draw.circle(
                    self._screen, (200, 240, 255),
                    (center_x + side * eye_spacing - 2, eye_y - 2),
                    eye_size // 3
                )
    
    def _draw_minimal_face(self):
        """Draw minimal style face (simple dots/lines)."""
        import pygame
        w, h = self.width, self.height
        center_x = w // 2
        center_y = h // 2
        
        # Simple circle frame
        r = min(w, h) * 0.35
        pygame.draw.circle(self._screen, (40, 40, 40),
                          (center_x, center_y), int(r))
        pygame.draw.circle(self._screen, (60, 60, 60),
                          (center_x, center_y), int(r), 2)
        
        # Dots for eyes
        eye_y = center_y - int(r * 0.2)
        eye_offset = int(r * 0.25)
        
        if self.is_blinking:
            # Lines for closed eyes
            pygame.draw.line(self._screen, (150, 150, 150),
                           (center_x - eye_offset - 5, eye_y),
                           (center_x - eye_offset + 5, eye_y), 2)
            pygame.draw.line(self._screen, (150, 150, 150),
                           (center_x + eye_offset - 5, eye_y),
                           (center_x + eye_offset + 5, eye_y), 2)
        else:
            pygame.draw.circle(self._screen, (100, 200, 255),
                             (center_x - eye_offset, eye_y), 4)
            pygame.draw.circle(self._screen, (100, 200, 255),
                             (center_x + eye_offset, eye_y), 4)
        
        # Mouth line
        mouth_y = center_y + int(r * 0.3)
        mouth_w = int(r * 0.3)
        pygame.draw.line(self._screen, (150, 150, 150),
                        (center_x - mouth_w, mouth_y),
                        (center_x + mouth_w, mouth_y), 2)


# ================================================
# FACE ENGINE — Unified Interface
# ================================================

class Face:
    """
    Unified face interface.
    Delegates to the appropriate rendering backend.
    """
    
    def __init__(self, settings):
        mode_name = settings.get("face.mode", "terminal")
        self.mode = FaceMode(mode_name)
        self.style_name = settings.get("face.style", "robot")
        
        # Map string to enum
        style_map = {
            "robot": FaceStyle.ROBOT,
            "anonymous": FaceStyle.ANONYMOUS,
            "minimal": FaceStyle.MINIMAL,
        }
        self.style = style_map.get(self.style_name, FaceStyle.ROBOT)
        
        self.current_emotion = Emotion.NEUTRAL
        self._face_tracking = settings.get("vision.face_tracking", False)
        
        if self.mode == FaceMode.TERMINAL:
            self._backend = TerminalFace()
        
        elif self.mode == FaceMode.PYGAME:
            self._backend = PygameFace(
                settings.get("face.width", 480),
                settings.get("face.height", 320),
            )
            self._backend.style = self.style
        
        elif self.mode == FaceMode.HARDWARE:
            # TODO: Implement hardware LCD/OLED rendering
            self._backend = TerminalFace()  # Fallback
    
    def start(self):
        """Start face rendering."""
        if self.mode == FaceMode.PYGAME:
            thread = threading.Thread(target=self._backend.start, daemon=True)
            thread.start()
        # Terminal mode doesn't need a thread
    
    def stop(self):
        """Stop face rendering."""
        if self.mode == FaceMode.PYGAME:
            self._backend.stop()
    
    def show_emotion(self, emotion: str):
        """Display an emotion on the face."""
        try:
            emotion_enum = Emotion(emotion.lower())
        except ValueError:
            emotion_enum = Emotion.NEUTRAL
        
        self.current_emotion = emotion_enum
        
        if self.mode == FaceMode.TERMINAL:
            # Clear terminal line, show face
            print("\033[2K\r", end="")  # Clear line
            self._backend.set_emotion(emotion_enum)
            print(self._backend.render())
        
        elif self.mode == FaceMode.PYGAME:
            self._backend.set_emotion(emotion_enum)
    
    def look_at(self, x: float, y: float):
        """Make face look at a position (for eye tracking)."""
        if self.mode == FaceMode.PYGAME:
            self._backend.look_at(x, y)
    
    def speak_start(self):
        """Called when JARVIS starts speaking."""
        self.show_emotion("speaking")
    
    def speak_end(self):
        """Called when JARVIS stops speaking."""
        self.show_emotion("neutral")
    
    def listen_start(self):
        """Called when JARVIS is listening."""
        self.show_emotion("listening")
    
    def process_audio_level(self, level: float):
        """Update mouth animation based on audio level."""
        if self.mode == FaceMode.PYGAME:
            self._backend.set_mouth_openness(level)
    
    def think(self):
        """Show thinking expression."""
        self.show_emotion("thinking")
```

---

## 🎨 Face Animation Features

### Eye Tracking Logic
```python
# When face is detected in camera frame:
# 1. Get face position from Vision module
# 2. Normalize to 0.0-1.0 range
# 3. Pass to Face.look_at(x, y)
# 4. Pupils smoothly follow with easing

face_pos = vision.find_face_position()
if face_pos:
    x_norm = face_pos[0] / frame_width
    y_norm = face_pos[1] / frame_height
    jarvis_face.look_at(x_norm, y_norm)
```

### Mouth Sync with Speech
```python
# During TTS playback:
# 1. Get audio amplitude in real-time
# 2. Normalize to 0.0-1.0
# 3. Pass to Face.set_mouth_openness()

# In TTS module:
def _play_audio(self, audio_data):
    # Start playback
    # In callback/thread:
    while playing:
        chunk = get_current_audio_chunk()
        level = calculate_rms(chunk)  # 0.0-1.0
        face.process_audio_level(level)
        time.sleep(0.03)  # ~30fps
```

## 🔧 Settings Keys

```yaml
face:
  mode: terminal                   # terminal | pygame | hardware
  style: robot                     # robot | anonymous | minimal
  width: 480                       # Pygame mode only
  height: 320                      # Pygame mode only
  framerate: 30                    # Pygame mode only
  fullscreen: false                # Pygame mode only
  blink_interval: [2.0, 6.0]      # Random blink range (seconds)
  eye_tracking: true               # Follow detected face
  mouth_sync: true                 # Sync with speech audio
```
