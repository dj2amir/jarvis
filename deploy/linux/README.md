# JARVIS — Linux Deployment

## Quick Start

```bash
# Run directly from source
./deploy/linux/run.sh
```

## Full Installation (Recommended)

```bash
# Installs dependencies, creates venv, adds desktop entry
chmod +x deploy/linux/install.sh
./deploy/linux/install.sh
```

After installation, you can launch JARVIS from your app menu or terminal.

## System Requirements

- **OS:** Ubuntu 22.04+, Fedora 38+, or any modern Linux distro
- **RAM:** 4GB minimum (8GB recommended for AI features)
- **Python:** 3.10+
- **Audio:** ALSA/PulseAudio (for microphone and speech)
- **Camera:** Optional, for vision features

## Manual Dependencies

If the installer doesn't work for your distro:

```bash
# Debian/Ubuntu
sudo apt install python3 python3-pip python3-venv portaudio19-dev espeak ffmpeg

# Fedora
sudo dnf install python3 python3-pip portaudio-devel espeak ffmpeg

# Arch
sudo pacman -S python python-pip portaudio espeak ffmpeg
```
