# JARVIS — Windows Deployment

## Quick Start (No Build Required)

```powershell
# 1. Install Python 3.10+ from python.org
# 2. Open PowerShell in this directory
# 3. Run:
.\run.bat
```

## Build Standalone .exe

```powershell
# Build JARVIS.exe (portable, no Python needed)
.\build.bat

# Output: dist\JARVIS\JARVIS.exe
# You can copy the entire dist\JARVIS folder to any Windows PC
```

## System Requirements

- **OS:** Windows 10 or Windows 11 (64-bit)
- **RAM:** 4GB minimum (8GB recommended for voice/vision features)
- **Storage:** 1GB for the standalone build
- **Microphone:** Required for voice features
- **Camera:** Optional, for vision features
- **Python:** Only needed if running from source (not needed for .exe)

## First Run

1. Edit `.env` and add your API keys (OpenAI, Anthropic, etc.)
2. Run `.\run.bat` (source) or `dist\JARVIS\JARVIS.exe` (standalone)
3. Say "Hey JARVIS" or type your message
