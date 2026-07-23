# Tier 6 — System Integration & Control

> **Goal:** JARVIS can control your computer, browse the web, and integrate with services.
> **Est. time:** 8-12 hours · **Depends on:** Tier 4

## ✅ Checklist
- [ ] Mouse control (move, click, drag, scroll)
- [ ] Keyboard control (type, hotkeys, shortcuts)
- [ ] Application launch (open/close programs)
- [ ] Screen capture (screenshot)
- [ ] File system operations (read, write, move, copy, delete)
- [ ] File search (find files by name, content, date)
- [ ] Web search (DuckDuckGo / Google)
- [ ] Email integration (read, compose, send)
- [ ] Calendar integration (read events, create)
- [ ] Weather integration
- [ ] Smart home control (MQTT / Home Assistant)
- [ ] Git operations (status, add, commit, push)
- [ ] Package management (install pip packages)
- [ ] Clipboard operations (read/write)

---

## 📄 core/system_control.py

Create `core/system_control.py` for computer control functions.

### Mouse & Keyboard (via PyAutoGUI)

> **Dependency:** `pyautogui` — install via `pip install pyautogui`
> **Safety:** Move mouse to top-left corner to abort (pyautogui FAILSAFE)

```python
"""
System Control — Mouse, keyboard, screen, file operations.
"""

import pyautogui
import subprocess
import platform
import shutil
from pathlib import Path
from typing import List, Optional

# Safety: pyautogui fail-safe (move mouse to corner to abort)
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


class SystemControl:
    """Computer control capabilities for JARVIS."""
    
    def __init__(self, settings):
        self.system = platform.system()
        self.settings = settings
        self.enabled = settings.get("system_control_enabled", True)
    
    # =========== MOUSE ===========
    
    def mouse_move(self, x: int, y: int, duration: float = 0.5):
        pyautogui.moveTo(x, y, duration=duration)
    
    def mouse_click(self, x: int = None, y: int = None, 
                    button: str = "left", clicks: int = 1):
        if x and y:
            pyautogui.click(x, y, button=button, clicks=clicks)
        else:
            pyautogui.click(button=button, clicks=clicks)
    
    def mouse_drag(self, x: int, y: int, duration: float = 0.5):
        pyautogui.drag(x, y, duration=duration)
    
    def mouse_scroll(self, clicks: int):
        pyautogui.scroll(clicks)
    
    def mouse_position(self) -> tuple:
        return pyautogui.position()
    
    # =========== KEYBOARD ===========
    
    def keyboard_type(self, text: str):
        pyautogui.write(text, interval=0.05)
    
    def keyboard_hotkey(self, *keys: str):
        pyautogui.hotkey(*keys)
    
    def keyboard_press(self, key: str):
        pyautogui.press(key)
    
    # =========== SCREEN ===========
    
    def screenshot(self, path: str = None) -> str:
        if path is None:
            path = f"./logs/screenshots/shot_{int(__import__('time').time())}.png"
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        pyautogui.screenshot(path)
        return path
    
    def screen_size(self) -> tuple:
        return pyautogui.size()
    
    # =========== APPS ===========
    
    def open_app(self, app_name: str):
        if self.system == "Darwin":  # macOS
            subprocess.Popen(["open", "-a", app_name])
        elif self.system == "Linux":
            subprocess.Popen([app_name])
        elif self.system == "Windows":
            subprocess.Popen(["start", app_name], shell=True)
    
    def open_url(self, url: str):
        import webbrowser
        webbrowser.open(url)
    
    # =========== FILES ===========
    
    def file_read(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")
    
    def file_write(self, path: str, content: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content, encoding="utf-8")
    
    def file_copy(self, src: str, dst: str):
        shutil.copy2(src, dst)
    
    def file_move(self, src: str, dst: str):
        shutil.move(src, dst)
    
    def file_delete(self, path: str):
        p = Path(path)
        if p.is_file():
            p.unlink()
        elif p.is_dir():
            shutil.rmtree(p)
    
    def file_list(self, directory: str = ".") -> List[str]:
        return [str(p) for p in Path(directory).iterdir()]
    
    def file_search(self, pattern: str, directory: str = ".") -> List[str]:
        return [str(p) for p in Path(directory).rglob(pattern)]
    
    # =========== CLIPBOARD ===========
    
    def clipboard_get(self) -> str:
        import pyperclip
        return pyperclip.paste()
    
    def clipboard_set(self, text: str):
        import pyperclip
        pyperclip.copy(text)
    
    # =========== SYSTEM ===========
    
    def lock_screen(self):
        if self.system == "Darwin":
            subprocess.run(["pmset", "displaysleepnow"])
        elif self.system == "Linux":
            subprocess.run(["gnome-screensaver-command", "-l"])
        elif self.system == "Windows":
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
    
    def sleep_computer(self):
        if self.system == "Darwin":
            subprocess.run(["pmset", "sleepnow"])
        elif self.system == "Linux":
            subprocess.run(["systemctl", "suspend"])
    
    def get_active_window_title(self) -> str:
        """Get the title of the currently active window."""
        if self.system == "Linux":
            try:
                result = subprocess.run(
                    ["xdotool", "getactivewindow", "getwindowname"],
                    capture_output=True, text=True
                )
                return result.stdout.strip()
            except:
                pass
        # Fallback: use pygetwindow if available
        try:
            import pygetwindow as gw
            return gw.getActiveWindow().title
        except:
            return "(unknown)"
```

---

## 📄 core/web_integration.py

Create `core/web_integration.py` for web services.

```python
"""
Web Integration — Email, calendar, weather, smart home.
"""

import smtplib
import imaplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Optional


class WebIntegration:
    """Web service integrations."""
    
    def __init__(self, settings):
        self.settings = settings
    
    # =========== EMAIL ===========
    
    def send_email(self, to: str, subject: str, body: str):
        """Send an email via SMTP."""
        config = self.settings.get("email", {})
        
        msg = MIMEMultipart()
        msg["From"] = config.get("address")
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        
        with smtplib.SMTP(config.get("smtp_server"), config.get("smtp_port", 587)) as server:
            server.starttls()
            server.login(config.get("address"), config.get("password"))
            server.send_message(msg)
    
    def read_emails(self, count: int = 5) -> List[dict]:
        """Read recent emails via IMAP."""
        config = self.settings.get("email", {})
        emails = []
        
        with imaplib.IMAP4_SSL(config.get("imap_server")) as mail:
            mail.login(config.get("address"), config.get("password"))
            mail.select("inbox")
            _, data = mail.search(None, "ALL")
            
            for num in data[0].split()[-count:]:
                _, msg_data = mail.fetch(num, "(RFC822)")
                # Parse email...
                emails.append({"id": num, "subject": "(parsed subject)"})
        
        return emails
    
    # =========== SMART HOME ===========
    
    def send_mqtt(self, topic: str, payload: str):
        """Send MQTT message to smart home devices."""
        try:
            import paho.mqtt.client as mqtt
            config = self.settings.get("mqtt", {})
            client = mqtt.Client()
            client.connect(config.get("host", "localhost"), config.get("port", 1883))
            client.publish(topic, payload)
            client.disconnect()
            return f"Published to {topic}: {payload}"
        except Exception as e:
            return f"MQTT error: {e}"
```

---

## 📄 Integrating with Tools

These system control functions should be wrapped as ToolDefinitions and registered in the ToolRegistry. Add them in `core/tools.py`:

```python
ToolDefinition(
    name="open_application",
    description="Open an application or program",
    parameters={
        "name": {"type": "string", "description": "Application name", "required": True}
    },
    function=lambda name: SystemControl().open_app(name),
    category="system",
    auto_approve=False,
)
```

## 🔧 Settings Keys

```yaml
system_control:
  enabled: true
  auto_approve_mouse: false
  auto_approve_keyboard: false
  auto_approve_files: false

email:
  address: ""
  smtp_server: ""
  smtp_port: 587
  imap_server: ""
  password: ""

mqtt:
  host: localhost
  port: 1883
  enabled: false
```

## 🔗 Next Agent

When complete → move to `.agent/tier7-body.agent.md`
