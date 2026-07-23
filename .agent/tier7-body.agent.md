# Tier 7 — Physical Body

> **Goal:** JARVIS lives in a physical robot body with a screen face, moving head, and interactive presence.
> **Est. time:** Weeks to months · **Depends on:** Tiers 1-6 + hardware

## ✅ Checklist
- [ ] `core/hardware.py` — Hardware abstraction layer
- [ ] Phase 1: Static Head with animated face on LCD
- [ ] Phase 2: Head + Neck with servo motors
- [ ] Phase 3: Torso + Arms with gesture capability
- [ ] Phase 4: Mobile base, full autonomy
- [ ] 3D print head chassis
- [ ] Face animation runs on LCD (via face.agent.md)
- [ ] Servo control via GPIO Zero
- [ ] Head tracking (follows detected face)
- [ ] Power management (battery, voltage regulation)
- [ ] Integration with main JARVIS loop

---

## 📄 core/hardware.py — Hardware Abstraction

```python
"""
Hardware Module — Physical body control abstraction.

Supports:
- GPIO Zero (Raspberry Pi)
- Pigpio (PWM servo control)
- Simulation mode (no hardware, for testing)
"""

from typing import Optional, Tuple
import time
import threading
from enum import Enum


class HardwareMode(Enum):
    SIMULATION = "simulation"
    GPIO_ZERO = "gpiozero"
    PIGPIO = "pigpio"
    NONE = "none"


class Hardware:
    """Physical body interface for JARVIS."""
    
    def __init__(self, settings):
        self.mode = HardwareMode(settings.get("hardware_mode", "simulation"))
        self.enabled = settings.get("hardware_enabled", False)
        
        # Servo configuration
        self.servo_pins = settings.get("servo_pins", {
            "head_pan": 12,
            "head_tilt": 13,
            "neck_tilt": 14,
        })
        
        # Servo positions (degrees)
        self.head_pan = 90     # Center
        self.head_tilt = 90    # Center
        self.neck_tilt = 90    # Center
        
        self._servos = {}
        self._setup_hardware()
    
    def _setup_hardware(self):
        if self.mode == HardwareMode.SIMULATION:
            print("🔧 Hardware: SIMULATION mode")
        elif self.mode == HardwareMode.GPIO_ZERO:
            from gpiozero import Servo
            for name, pin in self.servo_pins.items():
                self._servos[name] = Servo(pin)
            print("🔧 Hardware: GPIO Zero initialized")
        elif self.mode == HardwareMode.PIGPIO:
            import pigpio
            self._pi = pigpio.pi()
            for name, pin in self.servo_pins.items():
                self._pi.set_servo_pulsewidth(pin, 1500)  # Center
            print("🔧 Hardware: Pigpio initialized")
        else:
            print("🔧 Hardware: DISABLED")
    
    def set_head_pan(self, degrees: int):
        """Set head pan (left-right). 0=left, 90=center, 180=right."""
        self.head_pan = max(0, min(180, degrees))
        self._move_servo("head_pan", self.head_pan)
    
    def set_head_tilt(self, degrees: int):
        """Set head tilt (up-down). 0=down, 90=center, 180=up."""
        self.head_tilt = max(0, min(180, degrees))
        self._move_servo("head_tilt", self.head_tilt)
    
    def look_at(self, x: float, y: float, screen_w: int = 640, screen_h: int = 480):
        """
        Move head to look at a point on screen.
        x, y: normalized face position (0.0 to 1.0)
        """
        pan = int(x * 180)
        tilt = int((1 - y) * 180)  # Invert Y
        self.set_head_pan(pan)
        self.set_head_tilt(tilt)
    
    def nod(self, times: int = 1):
        """Nod head up and down."""
        for _ in range(times):
            self.set_head_tilt(60)
            time.sleep(0.2)
            self.set_head_tilt(120)
            time.sleep(0.2)
        self.set_head_tilt(90)
    
    def shake(self, times: int = 1):
        """Shake head left and right."""
        for _ in range(times):
            self.set_head_pan(60)
            time.sleep(0.15)
            self.set_head_pan(120)
            time.sleep(0.15)
        self.set_head_pan(90)
    
    def wave(self):
        """Wave gesture (if arm servos are configured)."""
        if "arm_shoulder" not in self._servos:
            return
        for _ in range(3):
            self._move_servo("arm_shoulder", 45)
            time.sleep(0.3)
            self._move_servo("arm_shoulder", 135)
            time.sleep(0.3)
        self._move_servo("arm_shoulder", 90)
    
    def center_all(self):
        """Move all servos to center position."""
        for name in self.servo_pins:
            self._move_servo(name, 90)
    
    def _move_servo(self, name: str, degrees: int):
        """Move a servo to a specific angle."""
        if self.mode == HardwareMode.SIMULATION:
            return  # No actual movement in simulation
        
        if self.mode == HardwareMode.GPIO_ZERO:
            if name in self._servos:
                # GPIO Zero: -1 to 1 range
                value = (degrees / 180.0) * 2 - 1
                self._servos[name].value = value
        
        elif self.mode == HardwareMode.PIGPIO:
            if name in self.servo_pins:
                # Pigpio: pulse width 500-2500 µs
                pulse = 1500 + (degrees - 90) * 1000 // 180
                self._pi.set_servo_pulsewidth(self.servo_pins[name], pulse)
    
    def cleanup(self):
        """Safe shutdown of hardware."""
        if self.mode == HardwareMode.PIGPIO:
            self._pi.stop()
        print("🔧 Hardware: Cleanup complete")
```

---

## 🖨️ 3D Printing Resources

### Chassis Design Tips
- Use **Fusion 360** (free for hobbyists) or **Onshape** (browser-based)
- Design in modular parts: face plate, neck mount, torso shell
- Print with PLA filament (cheap, easy)
- Use M3 screws and brass inserts for assembly
- Leave ventilation holes for Raspberry Pi cooling

### Recommended STL / Design files
Search these on Thingiverse / Printables:
- "Raspberry Pi robot head" — many designs available
- "Animated robot face" — LCD screen mounts
- "Pan tilt camera mount" — for neck mechanism

## 🔧 Settings Keys

```yaml
hardware:
  enabled: false                    # Set to true when Pi is ready
  mode: simulation                  # simulation | gpiozero | pigpio
  servo_pins:
    head_pan: 12
    head_tilt: 13
    neck_tilt: 14
  face_display:
    type: pygame                    # pygame | hardware (SPI)
    width: 480
    height: 320
    fullscreen: true
    framerate: 30
```

## 🔗 Next Agent

When complete → project is feature-complete. Start integration testing.
