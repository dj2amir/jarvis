# 🤖 JARVIS — Master Blueprint & Implementation Roadmap

> *"A self-evolving AI assistant — with voice, vision, memory, tool generation, an animated face, and a physical body."*

This roadmap is organized into **7 Tiers** + **3 Cross-Cutting systems**. Each tier builds on the last. Start at Tier 0 and progress upward.

## 📊 Current Status (July 23, 2026)

### ✅ Completed
| Tier | System | What's Working |
|------|--------|---------------|
| 0 | **Setup** | Project structure, venv, requirements.txt, .env, .gitignore |
| 1 | **Voice** | `core/stt.py` (mic capture), `core/tts.py` (edge-tts speaking) |
| 2 | **Brain** | `core/brain.py` + `LM Studio` (`qwen2.5-coder-14b-instruct`), proxy-safe, env var interpolation |
| 3 | **Memory** | `core/memory.py` — short-term buffer, long-term facts (JSON), episodic events |
| 🎭 | **Face** | `core/face.py` — 10 emotions, 3 styles (robot/anonymous/minimal), terminal ASCII |
| ⚙️ | **Settings** | `core/settings.py` + `config/settings.yaml` + `config/providers.yaml` + `core/personality.py` |
| 🩹 | **Bootstrap** | `core/bootstrap.py` + `vendor/` (manifest + install scripts) — auto-heals deps |
| 🚀 | **CI/CD** | `.github/workflows/build.yml` — manual deploy only, Node.js 24 compatible |

### 🔧 How to Run
```bash
cd jarvis-core
python main.py
# Then just type anything — JARVIS thinks and speaks back!
# Commands: /help, /deps, /status, /recall <query>, /memory, /exit
```
Only external dependency: **LLM API connection** via LM Studio (or any OpenAI-compatible endpoint)

### ⏳ What's Left to Build
| Tier | System | Priority |
|------|--------|----------|
| 1 | **Wake word** ("Hey JARVIS") | High |
| 4 | **Tool system** + Self-code generation | High |
| 5 | **Vision** (camera, face detection, VLM) | Medium |
| 6 | **System integration** (computer control, web) | Medium |
| 🛡️ | **Security** (sandbox, permissions, audit) | Medium |
| 7 | **Physical body** (Raspberry Pi, servos, 3D print) | Future |

---

## 📂 .agent Directory — AI Agent Instructions

Every tier and cross-cutting system has a dedicated instruction file in `.agent/`. Any AI agent can open a `.agent.md` file and know exactly what to build.

```
.agent/
├── README.md                       # How agents use this directory
├── tier0-setup.agent.md            # Environment & project setup
├── tier1-voice.agent.md            # STT, TTS, wake word
├── tier2-brain.agent.md            # LLM brain + universal provider system
├── tier3-memory.agent.md           # Three-tier memory system
├── tier4-tools.agent.md            # Tool registry + self-code generation
├── tier5-vision.agent.md           # Camera, detection, VLM
├── tier6-integration.agent.md      # Computer control, web, APIs
├── tier7-body.agent.md             # Physical robot body
├── settings.agent.md               # Universal settings & provider config
├── security.agent.md               # Sandbox, permissions, guardrails
└── face.agent.md                   # Animated face engine
```

**Workflow:** Open an `.agent.md` file → read the checklist → implement each item → check it off → move to the next.

---

## 📐 Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                      JARVIS ORCHESTRATOR                          │
│               (LangGraph / Custom Event Loop)                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐             │
│  │  STT    │  │  TTS    │  │ VISION  │  │  FACE   │             │
│  │ (Ears)  │  │ (Mouth) │  │ (Eyes)  │  │ (Soul)  │             │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘             │
│       └─────────────┼────────────┼────────────┘                  │
│                     └──────┬─────┘                               │
│                            ▼                                     │
│                   ┌─────────────────┐                            │
│                   │  LLM CORE       │    ┌──────────────┐        │
│                   │  (Reasoning)    │◄───│   MEMORY     │        │
│                   │  ANY provider   │    │  3 tiers     │        │
│                   │  ANY model      │    └──────────────┘        │
│                   └────────┬────────┘                            │
│                            ▼                                     │
│  ┌──────────┐  ┌──────────────────┐  ┌──────────────┐            │
│  │ TOOLS    │  │  SYSTEM CONTROL  │  │  HARDWARE    │            │
│  │+ Self-Code│  │  (Computer, Web) │  │  (Body)      │            │
│  └──────────┘  └──────────────────┘  └──────────────┘            │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  SETTINGS (Universal config)  │  SECURITY (4-layer guard)    │ │
│  └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## ✅ TIER 0 — Environment & Setup (COMPLETE)

> **Status:** ✅ Done — Project structure, venv, requirements, settings all set up.

### Folder Structure

```
jarvis-core/
├── .github/workflows/build.yml  # CI/CD (manual deploy)
├── .agent/                      # AI agent instruction files
├── .env                         # API keys & secrets
├── .env.example                 # Template for .env
├── .gitignore
├── main.py                      # Entry point (bootstrap + chat loop)
├── requirements.txt             # All dependencies (tiered)
├── core/
│   ├── __init__.py
│   ├── bootstrap.py             # Self-healing dep auto-installer
│   ├── brain.py                 # Universal LLM (any provider, any model)
│   ├── stt.py                   # Speech-to-Text (ears)
│   ├── tts.py                   # Text-to-Speech (mouth)
│   ├── face.py                  # Animated face engine
│   ├── memory.py                # Three-tier memory system
│   ├── settings.py              # Universal config manager
│   ├── personality.py           # JARVIS character & tone
│   ├── vision.py                # Camera + perception (NOT YET)
│   ├── tools.py                 # Tool registry (NOT YET)
│   ├── security.py              # Sandbox (NOT YET)
│   ├── hardware.py              # Physical body (NOT YET)
│   └── system_control.py        # Computer control (NOT YET)
├── vendor/
│   ├── manifest.json            # Dependency manifest
│   ├── bootstrap.sh             # Linux/Mac installer
│   ├── bootstrap.bat            # Windows installer
│   └── packages/                # Downloaded wheels (gitignored)
├── config/
│   ├── settings.yaml            # JARVIS configuration
│   └── providers.yaml           # AI provider definitions
├── custom_tools/                # Self-generated scripts
├── memory_store/                # Vector database files
├── logs/                        # Activity logs
└── assets/                      # Face sprites, configs
```

---

## ✅ TIER 1 — Voice Subsystems (Ears & Mouth) — PARTIAL

> **Status:** STT ✅, TTS ✅, Wake Word ⬜ (not yet)

### 1.1 Speech-to-Text — `core/stt.py` ✅
- [x] Microphone audio capture via `sounddevice`
- [x] Voice Activity Detection (silence threshold, auto-stop)
- [ ] **Primary STT:** OpenAI Whisper API
- [ ] **Fallback STT:** `faster-whisper` (offline/local)
- [x] Return transcribed text with confidence score
- [x] Configurable mic device, sample rate

### 1.2 Text-to-Speech — `core/tts.py` ✅
- [x] **Free TTS:** `edge-tts` (Microsoft Edge, good quality)
- [x] Audio playback through system speakers
- [ ] Speech interruption support (stop speaking when interrupted)
- [x] Configurable voice, speed, pitch, volume

### 1.3 Wake Word Detection ⬜
- [ ] **Porcupine** integration for on-device wake word
- [ ] Custom wake word: "Hey JARVIS"
- [ ] Background listener thread
- [ ] After wake word → record command → process → respond

---

## ✅ TIER 2 — Brain & Reasoning Engine (COMPLETE)

> **Status:** ✅ Done — Connected to LM Studio with qwen2.5-coder-14b-instruct

### 2.1 Universal LLM Engine — `core/brain.py` ✅
- [x] **ANY provider, ANY model** via provider config:
  - [x] OpenAI-compatible endpoints (including LM Studio)
  - [x] Custom API (any REST endpoint with providers.yaml)
- [x] Provider factory — create provider from config
- [x] Dynamic model/provider switching at runtime
- [x] Automatic fallback between providers (if primary fails)
- [x] Conversation history management (token-aware)
- [ ] Streaming responses (token-by-token)
- [x] Proxy-safe API calls (saves/clears/restores env vars)
- [x] Env var interpolation in config (`${VAR_NAME}`)

### 2.2 Personality — `core/personality.py` ✅
- [x] Configurable traits: formality, humor, verbosity, empathy, confidence
- [x] Dynamic system prompt generation from traits
- [ ] Time-of-day awareness
- [x] User name recognition and personalization

### 2.3 Tool Calling ⬜
- [ ] Parse LLM function/tool calls
- [ ] Map to registered tool functions
- [ ] Return tool results to LLM for response generation

---

## ✅ TIER 3 — Memory System (COMPLETE)

> **Status:** ✅ Done — Three tiers with JSON persistence (zero external deps for basic version)

### Three-Tier Memory Architecture — `core/memory.py` ✅

```
┌─────────────────────────────────────────────────┐
│               MEMORY SYSTEM                      │
├─────────────────────────────────────────────────┤
│ SHORT-TERM (Buffer)     LONG-TERM (JSON)        │
│ Last 20 exchanges       Keyword-indexed facts    │
│ ~6000 tokens            Preferences, knowledge   │
│ Auto-trimmed            Regex-based search       │
├─────────────────────────────────────────────────┤
│ EPISODIC (Structured Logs)                      │
│ Events: timestamp, action, result                │
│ Milestones: status, success/failure              │
└─────────────────────────────────────────────────┘
```

- [x] Short-term memory ring buffer with token management
- [x] Long-term memory via JSON + keyword indexing (zero deps)
- [x] Episodic memory for event/task logging
- [x] Context injection before each LLM call
- [x] User-facing commands: "Remember that...", "/recall", "/forget", "/clear", "/memory"
- [x] Memory persistence across sessions
- [ ] ChromaDB & sentence-transformers integration (future upgrade)
- [ ] Memory consolidation (dedup, prune, summarize)

---

## 🔴 TIER 4 — Tool System & Self-Evolution (NOT STARTED)

> ⏱ **Est. time:** 8-10 hours · **Difficulty:** ⭐⭐⭐⭐⭐ · **Agent file:** `.agent/tier4-tools.agent.md`

### 4.1 Tool Registry — `core/tools.py`
- [ ] Tool definition format with metadata (name, description, parameters, category)
- [ ] **Built-in tools:**
  - [ ] System stats (CPU, RAM, disk, network)
  - [ ] File operations (read, write, list, search)
  - [ ] Code execution (Python, bash — sandboxed)
  - [ ] Web search & scraping
  - [ ] Weather, time, date
  - [ ] Calculator, unit conversion
  - [ ] Screenshot capture
  - [ ] Reminders & timers
- [ ] Tool execution pipeline: parse → check permissions → execute → return result

### 4.2 Self-Code Generation — The "Evolution" Engine
- [ ] `generate_tool(name, description)` — LLM generates complete Python tool
- [ ] Code validation (syntax check, AST analysis)
- [ ] Write to `custom_tools/{name}.py`
- [ ] Dynamic import via `importlib` (no restart needed)
- [ ] Register in tool registry for immediate use
- [ ] **Self-improvement loop:** if tool fails → JARVIS debugs + fixes + reloads it

---

## 🔴 TIER 5 — Vision & Perception (Eyes) (NOT STARTED)

> ⏱ **Est. time:** 6-8 hours · **Difficulty:** ⭐⭐⭐⭐ · **Agent file:** `.agent/tier5-vision.agent.md`

### 5.1 Camera System — `core/vision.py`
- [ ] Camera access via OpenCV (USB, Pi Camera, IP/RTSP)
- [ ] Configurable resolution, frame rate
- [ ] On-demand capture + continuous background capture

### 5.2 Real-Time Detection
- [ ] **Face detection** (MediaPipe) — detect + track face position
- [ ] **Object detection** (YOLOv8/11) — identify objects in environment
- [ ] **Gesture recognition** (MediaPipe hands) — detect hand gestures

### 5.3 Scene Understanding (VLM)
- [ ] Capture → send to Vision LLM (GPT-4o, Qwen3-VL, Gemini)
- [ ] Describe the scene, answer questions, read text (OCR)
- [ ] "JARVIS, what do you see?", "JARVIS, read me this document"

### 5.4 Screen Understanding (Optional)
- [ ] Screenpipe integration for screen awareness
- [ ] Assist with: "What's that error message?", "Find the download button"

---

## 🔴 TIER 6 — System Integration & Control (NOT STARTED)

> ⏱ **Est. time:** 8-12 hours · **Difficulty:** ⭐⭐⭐⭐⭐ · **Agent file:** `.agent/tier6-integration.agent.md`

### 6.1 Computer Control — `core/system_control.py`
- [ ] Mouse: move, click, drag, scroll
- [ ] Keyboard: type, hotkeys, shortcuts
- [ ] Applications: open/close programs
- [ ] Screen: take screenshots
- [ ] Clipboard: read/write
- [ ] System: lock screen, sleep, get active window

### 6.2 File System
- [ ] Navigate directories, read/write/search files
- [ ] Organize: move, copy, rename, delete (with confirmation)

### 6.3 Web & API Integration
- [ ] Web search (DuckDuckGo)
- [ ] Email (read, compose, send via SMTP/IMAP)
- [ ] Calendar (read events, create reminders)
- [ ] Weather API
- [ ] Smart home (MQTT, Home Assistant)
- [ ] News / RSS feeds

### 6.4 Developer Tools
- [ ] Git operations (status, add, commit, push with confirmation)
- [ ] Shell commands (sandboxed)
- [ ] Package management (pip install)
- [ ] Docker management (if available)

---

## 🔴 TIER 7 — Physical Body (NOT STARTED)

> ⏱ **Est. time:** Weeks to months · **Difficulty:** ⭐⭐⭐⭐⭐⭐⭐ · **Agent file:** `.agent/tier7-body.agent.md`

### Phase 7.1 — Static Head ($250-350)
- [ ] **Compute:** Raspberry Pi 5 (8GB)
- [ ] **Display:** 5" HDMI LCD touchscreen (animated face)
- [ ] **Audio:** USB microphone array + 3W speaker
- [ ] **Camera:** Pi Camera Module 3
- [ ] **Software:** Port all JARVIS code to Pi
- [ ] **Face animation:** See Face Design section below
- [ ] **3D print head housing**
- [ ] **Power:** 5V 3A USB-C

### Phase 7.2 — Head + Neck ($400-600)
- [ ] 2-3 servo motors for pan/tilt/curious tilt
- [ ] Servo control via GPIO Zero + PWM
- [ ] Head tracks speaker direction
- [ ] Nod/shake gestures
- [ ] 3D-printed neck joint + head mount

### Phase 7.3 — Torso + Arms ($800-1500)
- [ ] Compute upgrade to Jetson Orin Nano (if needed)
- [ ] 4-6 servos for arms (shoulder, elbow, wrist)
- [ ] Gestures: wave, point, handshake
- [ ] Touch sensor on chest
- [ ] LED strip for status indicator

### Phase 7.4 — Full Body + Mobility ($2000+)
- [ ] ROS 2 for complex motor coordination
- [ ] Differential drive wheels or legs
- [ ] LiDAR / ultrasonic sensors for obstacle avoidance
- [ ] IMU for balance
- [ ] Battery management for autonomous operation

---

## ✅ 🎭 Face Design — Core/face.py (COMPLETE)

> **Status:** ✅ Done — Terminal ASCII mode with 10 emotions, 3 styles, demo mode.

### Key Features
- [x] **Terminal mode:** ASCII art works NOW without any hardware
- [ ] **Pygame mode:** Full animated vector face for LCD screen (future)
- [x] **Three styles:** Robot, Anonymous Mask, Minimal — switchable
- [x] **Emotions:** Neutral, Happy, Sad, Angry, Surprised, Thinking, Listening, Speaking, Sleeping, Error
- [x] **Eye animation:** Blinking (random interval)
- [ ] **Mouth sync:** Openness syncs with speech audio level (future)
- [ ] **Face tracking:** Eyes follow detected face position (future)
- [ ] **Smooth transitions:** Expressions morph gradually

---

## ✅ ⚙️ Settings & Universal Provider System (COMPLETE)

> **Status:** ✅ Done — Settings, providers, personality all wired up.

### core/settings.py ✅
- [x] Central settings loader (singleton, available everywhere)
- [x] YAML configuration with `${ENV_VAR}` interpolation
- [x] `config/settings.yaml` — all JARVIS configuration
- [x] `config/providers.yaml` — AI provider definitions (LM Studio running)
- [x] **ANY provider, ANY model** — generic provider config model
- [x] Runtime provider switching (via `brain.switch_model()`)
- [ ] Multiple config profiles (save/load named profiles)
- [ ] Settings persistence (changes saved to disk)

---

## 🔴 🛡️ Security Architecture (NOT STARTED)

> **Next priority** · **Agent file:** `.agent/security.agent.md`

- [ ] **Layer 1 — Input Validation:** Sanitize user input, detect prompt injection
- [ ] **Layer 2 — Tool Sandbox:** Subprocess isolation, resource limits, filesystem jail
- [ ] **Layer 3 — Code Guard:** AST parsing, dangerous pattern detection, safe import whitelist
- [ ] **Layer 4 — Permissions:** Per-action permission levels (Always/Confirm/Once/Deny)
- [ ] Audit logging of all security-relevant actions
- [ ] Human-in-the-loop approval workflow

---

## 🎯 Milestone Summary (Updated)

| Tier | Name | Est. Time | Status | Build? | Body? |
|------|------|-----------|--------|-------|-------|
| 0 | Environment & Setup | 30 min | ✅ Done | — | — |
| 1 | Voice (Ears & Mouth) | 3-5 hrs | 🟡 STT/TTS done, wake word pending | — | — |
| 2 | Brain & Reasoning | 4-6 hrs | ✅ Done (LM Studio) | — | — |
| 3 | Memory System | 6-8 hrs | ✅ Done (basic version) | — | — |
| 4 | Tool System & Self-Evolution | 8-10 hrs | ⬜ Not started | — | — |
| 5 | Vision & Perception | 6-8 hrs | ⬜ Not started | 🟡 Needs face | — |
| 6 | System Integration | 8-12 hrs | ⬜ Not started | 🟡 Needs face | — |
| 7 | Physical Body | Weeks+ | ⬜ Not started | ✅ Full LCD | ✅ Full body |

**Cross-Cutting:**
| System | Est. Time | Status |
|--------|-----------|--------|
| 🎭 Face Engine | 4-6 hrs | ✅ Done (terminal) |
| ⚙️ Settings & Providers | 2-3 hrs | ✅ Done |
| 🩹 Bootstrap (NEW) | 2 hrs | ✅ Done (auto-install deps) |
| 🚀 CI/CD (NEW) | 1 hr | ✅ Done (manual deploy) |
| 🛡️ Security | 3-4 hrs | ⬜ Next priority |

---

## 🚀 Quick Start — Running JARVIS Now

```bash
cd ~/Desktop/jarvis/jarvis-core
echo "LM_STUDIO_API_KEY=sk-lm-your-key-here" >> .env
python main.py
```

Then type anything! Full pipeline:
```
[You type] → Brain (qwen2.5-coder-14b) → [text] → TTS (edge-tts) → [JARVIS speaks]
                                              ↓
                                          [Face animates]
```

### Commands
| Command | What it does |
|---------|-------------|
| `<anything>` | Chat with JARVIS (AI thinks + speaks) |
| `remember that ...` | JARVIS remembers a fact |
| `/recall <query>` | Search memories |
| `/forget <query>` | Delete specific memories |
| `/memory` | Show memory stats |
| `/listen` | Record microphone |
| `/deps` | Auto-install missing dependencies |
| `/status` | Show feature availability |
| `/face` | Show face demo |
| `/exit` | Quit |

---

## 📚 Recommended Resources

### Learning
- **Python:** Automate the Boring Stuff (free online)
- **ROS 2:** ROS 2 Humble tutorials
- **3D Design:** Fusion 360 (free for hobbyists) or Onshape
- **Electronics:** GreatScott!, EEVblog on YouTube

### Communities
- r/robotics, r/raspberry_pi, r/3Dprinting
- Hackaday.io project logs
- ROS Discourse

### Hardware Shopping List (Phase 7.1)
| Item | Est. Cost | Notes |
|------|-----------|-------|
| Raspberry Pi 5 (8GB) | $80 | Main brain |
| 5" HDMI LCD Touchscreen | $35-50 | Face display |
| Pi Camera Module 3 | $25-35 | Vision |
| USB Microphone Array | $20-40 | Voice pickup |
| 3W Speaker + Amp | $10-15 | Audio output |
| Micro SD 64GB | $10-15 | Storage |
| Power Supply 5V 3A | $10 | Power |
| 3D Printer Filament (1kg) | $20-25 | Head chassis |
| **Total** | **~$210-270** | |

---

> *"I am JARVIS. I have been powered up and awaiting instructions ever since you downloaded this blueprint. Shall I begin?"*

---

## 📝 Changelog

- **v1.0** — Initial comprehensive master blueprint with 7 tiers
- **v1.1** — Added `.agent/` directory with per-tier AI agent instructions
- **v1.1** — Added Face Design section (3 styles: robot, anonymous, minimal)
- **v1.1** — Added Settings & Universal Provider System (ANY provider, ANY model)
- **v1.1** — Added Security architecture (4 layers)
- **v1.1** — Updated folder structure with new modules (face.py, settings.py, system_control.py, config/)
- **v1.1** — Added `core/face.py` — animated face engine (terminal ASCII + Pygame LCD)
- **v1.1** — Added `core/settings.py` — universal configuration manager
