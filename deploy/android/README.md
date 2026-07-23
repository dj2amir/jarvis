# JARVIS — Android Deployment (Termux)

JARVIS runs on Android via **Termux** — a terminal emulator for Android.

## Installation

### Step 1: Install Termux

**DO NOT** use the Google Play version (it's outdated).

Download Termux from **F-Droid** (free, open-source):
- https://f-droid.org/packages/com.termux/
- Install the APK and open Termux

### Step 2: Install Termux:API (Optional, for voice)

```bash
pkg install termux-api termux-api-static
```

Then in Termux app settings, grant Microphone permission.

### Step 3: Clone and Install JARVIS

```bash
# Install git first
pkg install git

# Clone the repo
git clone https://github.com/dj2amir/jarvis.git
cd jarvis

# Run the installer
bash deploy/android/install-termux.sh
```

### Step 4: Run JARVIS

```bash
python main.py
```

## Limitations on Android

| Feature | Status | Notes |
|---------|--------|-------|
| **Voice (Speech-to-Text)** | ✅ Works | Via Whisper API or faster-whisper |
| **Voice (Text-to-Speech)** | ✅ Works | Via edge-tts or OpenAI TTS |
| **Face (ASCII terminal)** | ✅ Works | Terminal mode works on any device |
| **Face (Pygame LCD)** | ❌ Limited | Requires display output |
| **Camera / Vision** | ⚠️ Partial | OpenCV works but camera access varies |
| **Self-Evolution (Code Gen)** | ✅ Works | Full Python support |
| **Memory (ChromaDB)** | ✅ Works | Local vector database |
| **Physical Body (Hardware)** | ❌ N/A | Android cannot control servos/GPIO |

## Notes

- The face works in **terminal mode** (ASCII art) on Android's terminal
- For best voice quality, use a headset with microphone
- ChromaDB runs locally — no server needed
- You can run this in the background and switch back anytime
