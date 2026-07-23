# JARVIS — Installation Guide

## 📋 Prerequisites

- **Python 3.10 or higher** ([Download](https://www.python.org/downloads/))
- **Microphone** (for voice features)
- **API keys** for AI providers (optional for face-only mode)

## 💻 Windows

### Option 1: Run from Source (Recommended)

```powershell
# 1. Clone or download
git clone https://github.com/dj2amir/jarvis.git
cd jarvis

# 2. Run (auto-sets up everything)
.\deploy\windows\run.bat
```

### Option 2: Build Standalone .exe

```powershell
.\deploy\windows\build.bat
# Output: deploy\windows\dist\JARVIS\JARVIS.exe
```

## 🐧 Linux

### Option 1: Quick Run

```bash
chmod +x deploy/linux/run.sh
./deploy/linux/run.sh
```

### Option 2: Full Install

```bash
chmod +x deploy/linux/install.sh
sudo ./deploy/linux/install.sh
```

## 📱 Android (Termux)

See: `deploy/android/README.md`

```bash
# In Termux:
pkg install git
git clone https://github.com/dj2amir/jarvis.git
cd jarvis
bash deploy/android/install-termux.sh
python main.py
```

## 🎯 Verify Installation

After setup, test the face:

```bash
python -c "from core.face import Face; Face().animate_demo()"
```

You should see the animated ASCII face cycling through emotions.

## 🔑 Setting Up API Keys

1. Copy `.env.example` to `.env`
2. Edit `.env` and add at least one provider key:
   - `OPENAI_API_KEY` — from [platform.openai.com](https://platform.openai.com/api-keys)
   - `ANTHROPIC_API_KEY` — from [console.anthropic.com](https://console.anthropic.com/)
   - `GOOGLE_API_KEY` — from [aistudio.google.com](https://aistudio.google.com/app/apikey)

Without API keys, JARVIS can show its face but won't be able to think or speak.

## 🧪 Test It

```bash
# See the face
python -c "from core.face import Face; Face().animate_demo()"

# Interactive face mode
python test_face.py --interactive
```
