<div align="center">
  <h1>🤖 JARVIS</h1>
  <p><em>A self-evolving AI assistant — with voice, vision, memory, tool generation, an animated face, and a physical body.</em></p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" alt="Python">
    <img src="https://img.shields.io/badge/Platform-Windows%20|%20Linux%20|%20Android-green" alt="Platform">
    <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
    <img src="https://img.shields.io/badge/Status-Development-orange" alt="Status">
  </p>
</div>

---

## ✨ Features

| Capability | Status | Description |
|-----------|--------|-------------|
| 🗣️ **Voice (STT/TTS)** | 🟢 Planned | Speak to JARVIS, hear it respond |
| 🧠 **AI Brain** | 🟢 Planned | Connects to ANY AI provider with ANY model |
| 🎭 **Animated Face** | 🟢 **Ready!** | ASCII art face in terminal — 3 styles, 10 emotions |
| 💾 **Memory** | 🟡 Planned | Remembers you across conversations |
| 🔧 **Self-Evolution** | 🟡 Planned | JARVIS can write its own tools |
| 👁️ **Vision** | 🔴 Planned | Sees through your webcam |
| 🖥️ **System Control** | 🔴 Planned | Controls your computer |
| 🦾 **Physical Body** | 🔴 Future | Raspberry Pi + servos + LCD face |

---

## 🚀 Quick Start

```bash
# Clone the repo
git clone https://github.com/dj2amir/jarvis.git
cd jarvis

# Set up and run
pip install -r requirements.txt
cp .env.example .env   # Add your API keys
python main.py         # Launch JARVIS
```

> **Already want to see the face?**
> ```bash
> python -c "from core.face import Face; Face().animate_demo()"
> ```

---

## 🎭 Live Demo: The Animated Face

The face works **right now** in your terminal — no hardware needed:

```
 [HAPPY]          [THINKING]         [SPEAKING]         [SLEEPING]
 ┌──────┐         ┌──────┐          ┌──────┐           ┌──────┐
 │ ◕  ◕ │         │ ◔  ◔ │          │ ◉  ◉ │           │ ∪  ∪ │
 │  ⌣  │         │  ¿  │          │  ⌣  │           │      │
 │  ⌣  │         │  ⌠  │          │  ω  │           │  zz  │
 └──────┘         └──────┘          └──────┘           └──────┘
```

**3 styles to choose from:** Robot · Anonymous Mask · Minimal

---

## 📦 Deployment

| Platform | Method | Instructions |
|----------|--------|--------------|
| 🪟 **Windows** | Source + PyInstaller | `deploy/windows/README.md` |
| 🐧 **Linux** | Source + AppImage | `deploy/linux/README.md` |
| 📱 **Android** | Termux | `deploy/android/README.md` |

---

## 🏗️ Project Structure

```
jarvis/
├── core/                    # Core intelligence modules
│   ├── face.py              # Animated face engine ✅
│   ├── settings.py          # Universal configuration
│   ├── personality.py       # JARVIS character
│   ├── brain.py             # LLM reasoning (TODO)
│   ├── stt.py               # Speech-to-Text (TODO)
│   ├── tts.py               # Text-to-Speech (TODO)
│   ├── vision.py            # Camera & perception (TODO)
│   ├── memory.py            # Memory system (TODO)
│   └── tools.py             # Tool generation (TODO)
├── .agent/                  # AI agent instructions per tier
├── deploy/                  # Platform deployment scripts
│   ├── windows/             # Windows .exe build
│   ├── linux/               # Linux installer
│   └── android/             # Termux installer
├── config/                  # Configuration files
├── custom_tools/            # Self-generated tools
└── .agent/                  # AI agent instructions
```

---

## 🔧 Build Your Own JARVIS

This project has **7 tiers** of increasing complexity. Each tier has an instruction file in `.agent/` that tells any AI agent exactly what to build.

| Tier | What You Get | Time |
|------|-------------|------|
| 0 | Project setup | 30 min |
| 1 | Voice (hear + speak) | 3-5 hrs |
| 2 | AI Brain (any model) | 4-6 hrs |
| 3 | Memory (remembers you) | 6-8 hrs |
| 4 | Self-Evolution (writes code) | 8-10 hrs |
| 5 | Vision (sees the world) | 6-8 hrs |
| 6 | System Control (your computer) | 8-12 hrs |
| 7 | Physical Body (robot) | Weeks+ |

---

## 📄 License

MIT License — Use freely, build cool things.

---

<div align="center">
  <p><em>"I am JARVIS. I have been powered up and awaiting instructions."</em></p>
</div>
