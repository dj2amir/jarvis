# Tier 0 — Environment & Setup

> **Goal:** Create the project scaffold, virtual environment, dependencies, and folder structure.
> **Est. time:** 30 min · **Depends on:** Nothing

## ✅ Checklist
- [ ] Create `jarvis-core/` project folder
- [ ] Create Python virtual environment
- [ ] Create `.env` file with template API keys
- [ ] Create `requirements.txt` with all dependencies
- [ ] Create full folder structure with `__init__.py` files
- [ ] Create `config/settings.yaml` with default configuration
- [ ] Create placeholder files for all core modules
- [ ] Verify project runs without errors: `python -c "from core import *; print('JARVIS core loaded')"`

## 📁 Folder Structure to Create

```
jarvis-core/
├── .env
├── .gitignore
├── main.py                     # Entry point
├── requirements.txt
├── core/
│   ├── __init__.py
│   ├── brain.py                # LLM reasoning
│   ├── stt.py                  # Speech-to-Text
│   ├── tts.py                  # Text-to-Speech
│   ├── face.py                 # Animated face engine
│   ├── vision.py               # Camera + perception
│   ├── memory.py               # Memory system
│   ├── tools.py                # Tool registry & execution
│   ├── settings.py             # Universal settings & provider config
│   ├── security.py             # Sandbox & guardrails
│   ├── hardware.py             # Physical body control
│   └── personality.py          # Character & tone
├── config/
│   ├── __init__.py
│   ├── settings.yaml
│   └── providers.yaml
├── custom_tools/
│   ├── __init__.py
│   └── .gitkeep
├── memory_store/
│   └── .gitkeep
├── logs/
│   └── .gitkeep
├── assets/
│   └── face/                   # Face sprites, configs
│       └── .gitkeep
└── .agent/                     # Agent instruction files
```

## 📦 requirements.txt

```txt
# ============================
# LLM & AI Providers
# ============================
openai>=1.0.0
anthropic>=0.30.0
google-genai>=1.0.0
# Local LLM via Ollama API (compatible with OpenAI SDK)
ollama>=0.1.0

# ============================
# Voice
# ============================
sounddevice>=0.4.6
numpy>=1.24.0
scipy>=1.10.0
edge-tts>=6.0.0
faster-whisper>=1.0.0
pvporcupine>=3.0.0              # Wake word
soundfile>=0.12.0               # Audio file I/O
pyaudio>=0.2.14                 # Audio playback fallback

# ============================
# Vision
# ============================
opencv-python>=4.8.0
mediapipe>=0.10.0
ultralytics>=8.0.0              # YOLO
Pillow>=10.0.0                  # Image processing

# ============================
# Memory & Retrieval
# ============================
chromadb>=0.4.0
sentence-transformers>=2.2.0

# ============================
# Face / UI
# ============================
pygame>=2.5.0                   # Face rendering

# ============================
# System & Utils
# ============================
psutil>=5.9.0
python-dotenv>=1.0.0
requests>=2.31.0
pyyaml>=6.0
rich>=13.0.0                    # Terminal UI
colorama>=0.4.6                # Terminal colors
loguru>=0.7.0                  # Better logging

# ============================
# Hardware (Physical Body)
# ============================
# gpiozero>=2.0.0               # Raspberry Pi GPIO
# pigpio>=1.78                  # PWM servo control
```

## 🏗️ main.py — Entry Point (Skeleton)

Create `main.py` as:

```python
#!/usr/bin/env python3
"""
JARVIS — Self-Evolving AI Assistant
"""

import sys
import logging
from core.settings import Settings
from core.brain import Brain
from core.stt import STT
from core.tts import TTS


def main():
    settings = Settings.load()
    brain = Brain(settings)
    stt = STT(settings)
    tts = TTS(settings)
    
    print("🤖 JARVIS ready. Say 'Hey JARVIS' or press Enter to start.")
    
    try:
        while True:
            # Listen
            text = stt.listen()
            if not text:
                continue
            
            # Think
            response = brain.think(text)
            
            # Speak
            tts.speak(response)
            
    except KeyboardInterrupt:
        print("\n👋 Shutting down.")
        sys.exit(0)


if __name__ == "__main__":
    main()
```

## 🔑 .env Template

```
# === AI Providers ===
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=

# === Voice ===
# Default STT provider: openai, faster-whisper, deepgram
STT_PROVIDER=openai
# Default TTS provider: openai, edge-tts, elevenlabs
TTS_PROVIDER=edge-tts

# === Wake Word ===
# Porcupine access key (free from picovoice.ai)
PORCUPINE_ACCESS_KEY=
WAKE_WORD=jarvis

# === Hardware ===
# Face display mode: terminal, pygame, hardware
FACE_MODE=terminal
```

## ✅ Verification

Run: `python -c "from core import *; print('JARVIS core loaded')"`

## 🔗 Next Agent

When complete → move to `.agent/tier1-voice.agent.md`
