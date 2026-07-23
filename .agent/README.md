# 🤖 JARVIS Agent Instructions

> **Purpose:** This directory contains per-tier instruction files for AI agents. Each file tells an AI agent exactly what to build, how to code it, and what standards to follow.
>
> Any AI agent can pick up any `.agent.md` file and know exactly what to implement.

## 📋 How to Use

1. **Start at Tier 0** — environment setup
2. **Progress sequentially** — each tier builds on the previous
3. **An agent can pick up any incomplete tier** — check the checklist at the top
4. **Cross-cutting concerns** (settings, security, face) must be implemented alongside their relevant tiers

## 📂 File Index

| File | Tier | Focus | Est. Time |
|------|------|-------|-----------|
| `tier0-setup.agent.md` | 0 | Environment, project structure, venv | 30 min |
| `tier1-voice.agent.md` | 1 | STT (ears), TTS (mouth), wake word | 3-5 hrs |
| `tier2-brain.agent.md` | 2 | LLM brain, multi-provider, personality | 4-6 hrs |
| `tier3-memory.agent.md` | 3 | Short & long-term memory, vector DB | 6-8 hrs |
| `tier4-tools.agent.md` | 4 | Tool system, self-code generation | 8-10 hrs |
| `tier5-vision.agent.md` | 5 | Camera, object/face detection, VLM | 6-8 hrs |
| `tier6-integration.agent.md` | 6 | Computer control, web, API integration | 8-12 hrs |
| `tier7-body.agent.md` | 7 | Physical hardware robot body | Weeks+ |
| `settings.agent.md` | Cross | Universal settings, provider config | 2-3 hrs |
| `security.agent.md` | Cross | Sandbox, permissions, code guard | 3-4 hrs |
| `face.agent.md` | Cross | Animated face engine (LCD + terminal) | 4-6 hrs |

## 🏗️ Project Structure

When complete, the project should look like:

```
jarvis-core/
├── .agent/                     # ← Agent instruction files (this directory)
├── .env                        # API keys & secrets
├── main.py                     # Entry point
├── requirements.txt            # Dependencies
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
│   ├── settings.yaml           # User configuration
│   └── providers.yaml          # AI provider definitions
├── custom_tools/               # Self-generated scripts
│   ├── __init__.py
│   └── ...
├── memory_store/               # Vector DB files
└── logs/                       # Conversation logs
```

## ✅ Completion Checklist

When an agent finishes a tier file, mark the top checklist items as `[x]` and update the `## Progress` section in `TODO.md`.

---

> *"I have been awaiting these instructions. Let us begin the work."*
