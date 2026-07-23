"""
GUI Face — PyQt6 Animated Robot Face for JARVIS.

Features:
  - Robot face with eyes, mouth, antenna (custom QPainter)
  - 8 emotion states with animated transitions
  - Real-time blinking
  - Live microphone level meter
  - Collapsible settings panel
  - Dark theme, glow effects, smooth animations
  - Thread-safe: runs Qt in background thread on Linux
"""

import threading
import queue
import time
import math
import random
from typing import Optional

# ── Optional PyQt6 import ────────────────────────────────────────
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QSlider, QComboBox, QFrame, QSizePolicy,
        QGraphicsDropShadowEffect, QCheckBox,
    )
    from PyQt6.QtCore import (
        Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QSize,
        pyqtProperty, pyqtSignal, QRectF, QThread,
    )
    from PyQt6.QtGui import (
        QPainter, QColor, QPen, QBrush, QRadialGradient, QLinearGradient,
        QFont, QFontMetrics, QPainterPath, QConicalGradient,
    )
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════
# Color palette
# ═══════════════════════════════════════════════════════════════════

COLORS = {
    "bg":           QColor(18, 18, 22),
    "head_border":  QColor(0, 200, 220),
    "head_fill":    QColor(25, 25, 32),
    "eye_outer":    QColor(0, 180, 200),
    "eye_inner":    QColor(0, 220, 255),
    "pupil":        QColor(0, 160, 200),
    "pupil_glow":   QColor(0, 220, 255, 60),
    "mouth":        QColor(0, 200, 220),
    "antenna":      QColor(0, 200, 220),
    "antenna_tip":  QColor(0, 255, 255),
    "mic_bar":      QColor(0, 200, 220),
    "mic_bg":       QColor(40, 40, 50),
    "text":         QColor(180, 200, 210),
    "text_dim":     QColor(100, 110, 120),
    "accent":       QColor(0, 200, 220),
    "error":        QColor(255, 80, 80),
    "warning":      QColor(255, 180, 40),
    "happy_gold":   QColor(255, 200, 40),
    "sleep_dim":    QColor(60, 60, 80),
}


# ═══════════════════════════════════════════════════════════════════
# RobotFaceWidget — The animated face
# ═══════════════════════════════════════════════════════════════════

class RobotFaceWidget(QWidget):
    """Custom-painted animated robot face."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 380)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # State
        self._emotion = "neutral"
        self._emotion_target = "neutral"
        self._emotion_progress = 1.0  # 0=old, 1=new
        self._blink_state = 0.0  # 0=open, 1=closed
        self._blink_dir = 0  # 0=none, 1=closing, -1=opening
        self._mic_level = 0.0
        self._speak_phase = 0.0
        self._breathe = 0.0
        self._antenna_bounce = 0.0
        self._time = 0.0

        # Blink timer
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._tick_blink)
        self._blink_timer.start(16)  # ~60fps

        # Animation timer
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick_anim)
        self._anim_timer.start(33)  # ~30fps

        # Random blink schedule
        self._next_blink = random.uniform(2.0, 5.0)
        self._blink_accum = 0.0

        # Glow effect
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(30)
        glow.setColor(QColor(0, 200, 220, 80))
        glow.setOffset(0, 0)
        self.setGraphicsEffect(glow)

    def set_emotion(self, emotion: str):
        self._emotion_target = emotion
        self._emotion_progress = 0.0

    def set_mic_level(self, level: float):
        self._mic_level = max(0.0, min(1.0, level))

    def set_speaking(self, active: bool):
        pass  # handled by emotion

    # ── Tick animations ──────────────────────────────────────────

    def _tick_blink(self):
        dt = 0.016
        self._blink_accum += dt

        if self._blink_dir == 0:
            if self._blink_accum >= self._next_blink:
                self._blink_dir = 1  # start closing
                self._blink_accum = 0.0
                self._next_blink = random.uniform(1.5, 5.0)
        elif self._blink_dir == 1:
            self._blink_state += dt * 10  # fast close
            if self._blink_state >= 1.0:
                self._blink_state = 1.0
                self._blink_dir = -1  # start opening
        elif self._blink_dir == -1:
            self._blink_state -= dt * 8  # slower open
            if self._blink_state <= 0.0:
                self._blink_state = 0.0
                self._blink_dir = 0
                self._blink_accum = 0.0

    def _tick_anim(self):
        dt = 0.033
        self._time += dt

        # Emotion transition
        if self._emotion_progress < 1.0:
            self._emotion_progress = min(1.0, self._emotion_progress + dt * 4)
            if self._emotion_progress >= 1.0:
                self._emotion = self._emotion_target

        # Breathing
        self._breathe = math.sin(self._time * 1.5) * 0.3 + 0.5

        # Antenna bounce
        self._antenna_bounce = abs(math.sin(self._time * 2.5)) * 0.5

        # Speak phase
        if self._emotion_target == "speaking":
            self._speak_phase += dt * 12
        else:
            self._speak_phase *= 0.9

        self.update()

    # ── Paint ────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx, cy = w / 2, h / 2
        head_r = min(w, h) * 0.38

        # Background
        p.fillRect(self.rect(), COLORS["bg"])

        # ── Antenna ───────────────────────────────────────────
        ant_top = cy - head_r - 15
        ant_bottom = cy - head_r + 5
        ant_mid_x = cx + math.sin(self._time * 3) * 3 * self._antenna_bounce
        ant_tip_y = ant_top - 12 - self._antenna_bounce * 8

        # Antenna line
        pen = QPen(COLORS["antenna"], 3)
        p.setPen(pen)
        p.drawLine(QPoint(int(cx), int(ant_bottom)), QPoint(int(ant_mid_x), int(ant_tip_y)))

        # Antenna ball
        p.setBrush(QBrush(COLORS["antenna_tip"]))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPoint(int(ant_mid_x), int(ant_tip_y)), 6, 6)

        # Antenna glow
        glow = QRadialGradient(ant_mid_x, ant_tip_y, 20)
        glow.setColorAt(0, QColor(0, 255, 255, 50))
        glow.setColorAt(1, QColor(0, 255, 255, 0))
        p.setBrush(QBrush(glow))
        p.drawEllipse(QPoint(int(ant_mid_x), int(ant_tip_y)), 20, 20)

        # ── Head ──────────────────────────────────────────────
        head_rect = QRectF(cx - head_r, cy - head_r, head_r * 2, head_r * 2)

        # Head border glow
        glow_grad = QRadialGradient(cx, cy, head_r * 1.1)
        glow_grad.setColorAt(0.85, QColor(0, 200, 220, 30))
        glow_grad.setColorAt(1.0, QColor(0, 200, 220, 0))
        p.setBrush(QBrush(glow_grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(head_rect.adjusted(-8, -8, 8, 8))

        # Head fill
        head_grad = QRadialGradient(cx - head_r * 0.2, cy - head_r * 0.3, head_r * 1.0)
        head_grad.setColorAt(0, QColor(35, 35, 45))
        head_grad.setColorAt(0.8, QColor(22, 22, 30))
        head_grad.setColorAt(1, QColor(15, 15, 22))

        p.setBrush(QBrush(head_grad))
        pen = QPen(COLORS["head_border"], 3)
        p.setPen(pen)
        p.drawEllipse(head_rect)

        # ── Eyes ──────────────────────────────────────────────
        eye_y = cy - head_r * 0.2
        eye_spacing = head_r * 0.38
        eye_outer_r = head_r * 0.18
        eye_inner_r = eye_outer_r * 0.55

        # Interpolate emotion for smooth transitions
        emo = self._emotion if self._emotion_progress < 0.5 else self._emotion_target

        # Eye shape modifiers per emotion
        eye_scale_y = 1.0
        pupil_scale = 0.7
        eye_h_spacing = eye_spacing

        if emo == "happy":
            eye_scale_y = 0.5
            pupil_scale = 0.9
        elif emo == "surprised":
            eye_scale_y = 1.3
            pupil_scale = 0.4
            eye_h_spacing = eye_spacing * 1.05
        elif emo == "angry":
            eye_scale_y = 0.6
        elif emo == "sad":
            eye_scale_y = 0.7
            pupil_scale = 0.5
        elif emo == "sleeping":
            self._blink_state = 0.9

        # Draw both eyes
        for side in [-1, 1]:
            ex = cx + side * eye_h_spacing

            # Outer eye
            outer_rx = eye_outer_r
            outer_ry = eye_outer_r * eye_scale_y * (1.0 - self._blink_state)

            if outer_ry < 1:
                outer_ry = 1

            outer_rect = QRectF(ex - outer_rx, eye_y - outer_ry, outer_rx * 2, outer_ry * 2)
            p.setBrush(QBrush(COLORS["eye_outer"]))
            p.setPen(QPen(COLORS["eye_inner"], 2))
            p.drawEllipse(outer_rect)

            # Inner eye glow
            if outer_ry > 2:
                inner_glow = QRadialGradient(ex, eye_y, outer_rx * 0.8)
                inner_glow.setColorAt(0, QColor(0, 255, 255, 40))
                inner_glow.setColorAt(1, QColor(0, 200, 220, 0))
                p.setBrush(QBrush(inner_glow))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(outer_rect)

            # Pupil
            pupil_r = eye_inner_r * pupil_scale
            if pupil_r > 0 and outer_ry > 2:
                pupil_y = eye_y
                # Look direction per emotion
                if emo == "thinking":
                    pupil_x = ex + eye_outer_r * 0.25 * side
                else:
                    pupil_x = ex

                p.setBrush(QBrush(COLORS["pupil"]))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPoint(int(pupil_x), int(pupil_y)),
                            int(pupil_r))

                # Pupil highlight
                hl = QRadialGradient(pupil_x - pupil_r * 0.3, eye_y - pupil_r * 0.3, pupil_r)
                hl.setColorAt(0, QColor(255, 255, 255, 100))
                hl.setColorAt(1, QColor(255, 255, 255, 0))
                p.setBrush(QBrush(hl))
                p.drawEllipse(QPoint(int(pupil_x), int(pupil_y)),
                            int(pupil_r))

        # ── Mouth ──────────────────────────────────────────────
        mouth_y = cy + head_r * 0.35
        mouth_w = head_r * 0.5

        p.setPen(QPen(COLORS["mouth"], 3))
        p.setBrush(Qt.BrushStyle.NoBrush)

        path = QPainterPath()

        if emo == "neutral":
            path.moveTo(cx - mouth_w * 0.5, mouth_y)
            path.lineTo(cx + mouth_w * 0.5, mouth_y)
        elif emo == "happy":
            path.moveTo(cx - mouth_w * 0.6, mouth_y)
            path.quadTo(cx - mouth_w * 0.3, mouth_y + head_r * 0.15,
                       cx, mouth_y + head_r * 0.12)
            path.quadTo(cx + mouth_w * 0.3, mouth_y + head_r * 0.15,
                       cx + mouth_w * 0.6, mouth_y)
        elif emo == "sad":
            path.moveTo(cx - mouth_w * 0.5, mouth_y + head_r * 0.06)
            path.quadTo(cx, mouth_y - head_r * 0.05,
                       cx + mouth_w * 0.5, mouth_y + head_r * 0.06)
        elif emo == "surprised":
            p.drawEllipse(QPoint(int(cx), int(mouth_y)), int(head_r * 0.12), int(head_r * 0.15))
        elif emo == "angry":
            path.moveTo(cx - mouth_w * 0.5, mouth_y)
            path.quadTo(cx, mouth_y - head_r * 0.08,
                       cx + mouth_w * 0.5, mouth_y)
            path.moveTo(cx - mouth_w * 0.3, mouth_y + head_r * 0.08)
            path.quadTo(cx, mouth_y + head_r * 0.15,
                       cx + mouth_w * 0.3, mouth_y + head_r * 0.08)
        elif emo == "speaking":
            # Animated mouth
            sph = (math.sin(self._speak_phase) + 1) * 0.5
            oval_h = head_r * 0.08 + sph * head_r * 0.18
            oval_w = head_r * 0.08 + sph * head_r * 0.06
            p.drawEllipse(QPoint(int(cx), int(mouth_y)), int(oval_w), int(oval_h))
        elif emo == "thinking":
            path.moveTo(cx - mouth_w * 0.3, mouth_y + head_r * 0.05)
            path.lineTo(cx + mouth_w * 0.15, mouth_y)
            path.lineTo(cx + mouth_w * 0.3, mouth_y - head_r * 0.05)
        elif emo == "listening":
            path.moveTo(cx, mouth_y - head_r * 0.04)
            path.lineTo(cx - mouth_w * 0.25, mouth_y + head_r * 0.06)
            path.lineTo(cx - mouth_w * 0.1, mouth_y + head_r * 0.02)
            path.lineTo(cx + mouth_w * 0.1, mouth_y + head_r * 0.02)
            path.lineTo(cx + mouth_w * 0.25, mouth_y + head_r * 0.06)
        elif emo == "sleeping":
            path.moveTo(cx - mouth_w * 0.3, mouth_y)
            path.quadTo(cx, mouth_y - head_r * 0.1,
                       cx + mouth_w * 0.3, mouth_y)
        elif emo == "error":
            path.moveTo(cx - mouth_w * 0.35, mouth_y - head_r * 0.05)
            path.lineTo(cx + mouth_w * 0.35, mouth_y + head_r * 0.05)
            path.moveTo(cx + mouth_w * 0.35, mouth_y - head_r * 0.05)
            path.lineTo(cx - mouth_w * 0.35, mouth_y + head_r * 0.05)

        p.drawPath(path)

        # ── Emotion label ──────────────────────────────────────
        p.setPen(COLORS["text"])
        font = QFont("Courier New", 10)
        font.setBold(True)
        p.setFont(font)
        label = emo.upper()
        fm = QFontMetrics(font)
        tw = fm.horizontalAdvance(label)
        p.drawText(int(cx - tw / 2), int(cy + head_r + 30), label)

        # ── Breathing dots below mouth ─────────────────────────
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(3):
            dot_x = cx + (i - 1) * 15
            dot_y = cy + head_r + 12
            alpha = int(30 + self._breathe * 80)
            p.setBrush(QBrush(QColor(0, 200, 220, alpha)))
            p.drawEllipse(QPoint(int(dot_x), int(dot_y)), 2, 2)

        p.end()


# ═══════════════════════════════════════════════════════════════════
# MicLevelWidget — Audio level indicator
# ═══════════════════════════════════════════════════════════════════

class MicLevelWidget(QWidget):
    """Live microphone level bar with peak hold."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self._level = 0.0
        self._peak = 0.0
        self._peak_hold = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._decay_peak)
        self._timer.start(50)

    def set_level(self, level: float):
        self._level = max(0.0, min(1.0, level))
        if self._level > self._peak:
            self._peak = self._level
            self._peak_hold = 30  # hold peak for ~1.5s
        self.update()

    def _decay_peak(self):
        if self._peak_hold > 0:
            self._peak_hold -= 1
        else:
            self._peak = max(0.0, self._peak - 0.02)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Background
        p.fillRect(self.rect(), COLORS["bg"])

        # Mic label
        p.setPen(COLORS["text_dim"])
        p.setFont(QFont("Courier New", 8))
        p.drawText(10, h // 2 + 3, "MIC")

        bar_x = 50
        bar_w = w - bar_x - 20
        bar_h = 8
        bar_y = (h - bar_h) // 2

        # Bar background
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(COLORS["mic_bg"]))
        p.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 4, 4)

        # Bar fill
        level_w = int(bar_w * self._level)
        if level_w > 0:
            bar_grad = QLinearGradient(bar_x, 0, bar_x + bar_w, 0)
            bar_grad.setColorAt(0, QColor(0, 150, 200))
            bar_grad.setColorAt(0.6, QColor(0, 220, 255))
            bar_grad.setColorAt(0.85, QColor(255, 200, 40))
            bar_grad.setColorAt(1.0, QColor(255, 80, 80))
            p.setBrush(QBrush(bar_grad))
            p.drawRoundedRect(QRectF(bar_x, bar_y, level_w, bar_h), 4, 4)

        # Peak hold
        peak_x = bar_x + int(bar_w * self._peak)
        p.setPen(QPen(COLORS["accent"], 2))
        p.drawLine(peak_x, bar_y - 3, peak_x, bar_y + bar_h + 3)

        # Level text
        p.setPen(COLORS["text"])
        p.setFont(QFont("Courier New", 9))
        p.drawText(bar_x + bar_w + 5, h // 2 + 4, f"{int(self._level * 100)}%")

        p.end()


# ═══════════════════════════════════════════════════════════════════
# SettingsPanel — Collapsible settings
# ═══════════════════════════════════════════════════════════════════

class SettingsPanel(QFrame):
    """Collapsible settings panel for model, style, etc."""

    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background: #1a1a24;
                border: 1px solid #2a2a3a;
                border-radius: 8px;
            }
            QLabel { color: #b4c8d2; font-family: 'Courier New'; }
            QComboBox {
                background: #252535; color: #00c8dc; border: 1px solid #3a3a4a;
                border-radius: 4px; padding: 4px 8px; font-family: 'Courier New';
            }
            QSlider::groove:horizontal {
                height: 6px; background: #2a2a3a; border-radius: 3px;
            }
            QSlider::handle:horizontal {
                width: 14px; height: 14px; margin: -4px 0;
                background: #00c8dc; border-radius: 7px;
            }
            QPushButton {
                background: #252535; color: #00c8dc; border: 1px solid #3a4a5a;
                border-radius: 4px; padding: 6px 14px; font-family: 'Courier New';
            }
            QPushButton:hover { background: #303045; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        # Title
        title = QLabel("SETTINGS")
        title.setStyleSheet("font-weight: bold; font-size: 11px; color: #00c8dc;")
        layout.addWidget(title)

        # Model selector
        layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["qwen2.5-vl-7b", "llama3", "mistral", "custom"])
        layout.addWidget(self.model_combo)

        # Temperature slider
        layout.addWidget(QLabel("Temperature:"))
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(0, 100)
        self.temp_slider.setValue(70)
        layout.addWidget(self.temp_slider)

        # Always on top
        self.always_on_top = QCheckBox("Always on top")
        self.always_on_top.setStyleSheet("color: #b4c8d2;")
        self.always_on_top.setChecked(True)
        layout.addWidget(self.always_on_top)

        # Minimize to tray
        self.min_tray = QCheckBox("Minimize to tray")
        self.min_tray.setStyleSheet("color: #b4c8d2;")
        layout.addWidget(self.min_tray)

        layout.addStretch()


# ═══════════════════════════════════════════════════════════════════
# GuiFaceWindow — Main window
# ═══════════════════════════════════════════════════════════════════

class GuiFaceWindow(QMainWindow):
    """Main JARVIS face window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("JARVIS")
        self.setMinimumSize(380, 520)
        self.resize(420, 600)
        self.setStyleSheet("background-color: #121216;")

        # Make frameless and draggable
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self._drag_pos = None

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(8)

        # Title bar
        title_bar = QHBoxLayout()
        self._title_label = QLabel("🤖 JARVIS")
        self._title_label.setStyleSheet("color: #00c8dc; font-family: 'Courier New'; font-size: 14px; font-weight: bold;")
        title_bar.addWidget(self._title_label)
        title_bar.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #666; border: none;
                font-size: 16px; font-family: sans-serif;
            }
            QPushButton:hover { color: #ff5050; }
        """)
        close_btn.clicked.connect(self.hide)
        title_bar.addWidget(close_btn)
        main_layout.addLayout(title_bar)

        # Robot face
        self.face_widget = RobotFaceWidget()
        main_layout.addWidget(self.face_widget, stretch=1)

        # Mic level
        self.mic_widget = MicLevelWidget()
        main_layout.addWidget(self.mic_widget)

        # Settings panel (collapsed by default)
        self.settings = SettingsPanel()
        self.settings.setVisible(False)
        self.settings.always_on_top.toggled.connect(self._toggle_always_on_top)
        main_layout.addWidget(self.settings)

        # Toggle settings button
        btn_layout = QHBoxLayout()
        self._settings_btn = QPushButton("⚙ Settings")
        self._settings_btn.clicked.connect(self._toggle_settings)
        btn_layout.addWidget(self._settings_btn)

        emotion_label = QLabel("| Type /gui to close")
        emotion_label.setStyleSheet("color: #666; font-family: 'Courier New'; font-size: 9px;")
        btn_layout.addWidget(emotion_label)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

    def _toggle_settings(self):
        visible = not self.settings.isVisible()
        self.settings.setVisible(visible)
        self._settings_btn.setText("⚙ Hide" if visible else "⚙ Settings")

    def _toggle_always_on_top(self, checked):
        flags = self.windowFlags()
        if checked:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    # ── Drag window ──────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


# ═══════════════════════════════════════════════════════════════════
# GuiFace — Thread-safe controller
# ═══════════════════════════════════════════════════════════════════

class GuiFace:
    """Thread-safe GUI face controller.

    Runs PyQt6 in a background thread. Communicates via a queue.
    """

    def __init__(self):
        if not PYQT6_AVAILABLE:
            raise ImportError("PyQt6 not installed. Run: pip install PyQt6")

        self._ready = threading.Event()
        self._window: Optional[GuiFaceWindow] = None
        self._app: Optional[QApplication] = None
        self._thread: Optional[threading.Thread] = None
        self._queue = queue.Queue()

        # Start Qt in background thread
        self._start()

    def _start(self):
        def _run_qt():
            self._app = QApplication.instance() or QApplication([])
            self._window = GuiFaceWindow()
            self._window.show()
            self._ready.set()

            # Timer to process queue
            timer = QTimer()
            timer.timeout.connect(self._process_queue)
            timer.start(50)  # 20Hz polling

            self._app.exec()

        self._thread = threading.Thread(target=_run_qt, daemon=True, name="jarvis-gui")
        self._thread.start()

    def _process_queue(self):
        """Process commands from the main thread."""
        try:
            while True:
                cmd, args, kwargs = self._queue.get_nowait()
                if cmd == "emotion":
                    self._window.face_widget.set_emotion(args[0])
                elif cmd == "mic":
                    self._window.mic_widget.set_level(args[0])
                elif cmd == "title":
                    self._window._title_label.setText(args[0])
                elif cmd == "hide":
                    self._window.hide()
                elif cmd == "show":
                    self._window.show()
                elif cmd == "close":
                    self._window.close()
                    if self._app:
                        self._app.quit()
                self._queue.task_done()
        except queue.Empty:
            pass

    def _send(self, cmd: str, *args, **kwargs):
        if self._ready.is_set():
            self._queue.put((cmd, args, kwargs))

    # ── Public API ──────────────────────────────────────────────

    def show_emotion(self, emotion: str):
        self._send("emotion", emotion)

    def set_mic_level(self, level: float):
        self._send("mic", level)

    def set_title(self, title: str):
        self._send("title", title)

    def hide(self):
        self._send("hide")

    def show(self):
        self._send("show")

    def close(self):
        self._ready.clear()
        self._send("close")

    @property
    def is_ready(self) -> bool:
        return self._ready.is_set()
