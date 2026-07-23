# Tier 1 — Voice Subsystems (Ears & Mouth)

> **Goal:** JARVIS can hear you speak and talk back.
> **Est. time:** 3-5 hours · **Depends on:** Tier 0

## ✅ Checklist
- [ ] `core/stt.py` — Microphone capture via sounddevice
- [ ] `core/stt.py` — Whisper API integration
- [ ] `core/stt.py` — faster-whisper local fallback
- [ ] `core/stt.py` — Voice Activity Detection (silence timeout)
- [ ] `core/stt.py` — Wake word detection via Porcupine
- [ ] `core/tts.py` — OpenAI TTS integration
- [ ] `core/tts.py` — edge-tts free TTS integration
- [ ] `core/tts.py` — Audio playback via sounddevice/pygame
- [ ] `core/tts.py` — Speech interruption support
- [ ] `core/tts.py` — Configurable voice, speed, pitch
- [ ] Test: "You say something → STT converts → text printed"
- [ ] Test: "Text → TTS generates → audio plays through speakers"

---

## 📄 core/stt.py — Speech-to-Text

### Architecture

```python
"""
Speech-to-Text Module (Ears)

Providers:
  - openai:    OpenAI Whisper API (high accuracy, needs internet)
  - local:     faster-whisper (offline, privacy, slower on CPU)
  - deepgram:  Deepgram API (real-time, domain-specific)
"""

import sounddevice as sd
import numpy as np
import wave
import tempfile
import os
import threading
import time
from typing import Optional, Callable


class STT:
    def __init__(self, settings):
        self.provider = settings.get("stt_provider", "openai")
        self.sample_rate = settings.get("audio_sample_rate", 16000)
        self.channels = 1
        self.silence_threshold = settings.get("silence_threshold", 500)
        self.silence_timeout = settings.get("silence_timeout", 1.5)  # seconds
        self.max_record_seconds = settings.get("max_record_seconds", 30)
        self.device = settings.get("audio_input_device", None)
        
        # Wake word
        self.wake_word_enabled = settings.get("wake_word_enabled", True)
        self.wake_word = settings.get("wake_word", "jarvis")
        self._wake_word_detected = threading.Event()
        
        self._setup_provider()
    
    def _setup_provider(self):
        """Initialize the selected STT provider."""
        if self.provider == "openai":
            import openai
            self._client = openai.OpenAI()
        elif self.provider == "local":
            from faster_whisper import WhisperModel
            self._model = WhisperModel("base", device="cpu", compute_type="int8")
        # ... etc
    
    def listen(self) -> Optional[str]:
        """
        Record from microphone and transcribe.
        Returns transcribed text or None if no speech detected.
        """
        audio_data = self._record_audio()
        if audio_data is None:
            return None
        text = self._transcribe(audio_data)
        return text
    
    def listen_with_wake_word(self, callback: Callable[[str], None]):
        """
        Background thread: continuously listen for wake word,
        then record command and call callback with transcription.
        """
        # ... implementation
        pass
    
    def _record_audio(self) -> Optional[np.ndarray]:
        """
        Record audio with silence detection.
        Starts recording when sound > threshold.
        Stops when silence > silence_timeout.
        """
        # Use sounddevice InputStream with callback
        # Detect voice activity
        # Return audio buffer
        pass
    
    def _transcribe(self, audio: np.ndarray) -> str:
        """Send audio to STT provider and return text."""
        if self.provider == "openai":
            return self._transcribe_openai(audio)
        elif self.provider == "local":
            return self._transcribe_local(audio)
        # ...
```

### Key Implementation Details

1. **Voice Activity Detection (VAD):**
   - Calculate RMS of audio chunks
   - If RMS > threshold → speech detected, start recording
   - If RMS < threshold for `silence_timeout` seconds → stop recording
   - Save only the speech segment (trim silence from start and end)

2. **Wake Word Detection:**
   - Initialize Porcupine with wake word
   - Run in a background thread reading mic constantly
   - When wake word detected → set event flag
   - Main loop: when flag set → start recording command

3. **Audio Format:**
   - Sample rate: 16000 Hz (Whisper standard)
   - Channels: 1 (mono)
   - Format: float32 numpy array → saved as WAV temp file for API

---

## 📄 core/tts.py — Text-to-Speech

### Architecture

```python
"""
Text-to-Speech Module (Mouth)

Providers:
  - openai:    OpenAI TTS API (high quality, multiple voices)
  - edge-tts:  Microsoft Edge TTS (free, good quality, offline-capable)
  - elevenlabs: ElevenLabs (premium, emotional, expressive)
"""

import asyncio
import threading
from typing import Optional


class TTS:
    def __init__(self, settings):
        self.provider = settings.get("tts_provider", "edge-tts")
        self.voice = settings.get("tts_voice", "default")
        self.speed = settings.get("tts_speed", 1.0)
        self.volume = settings.get("tts_volume", 0.8)
        self._is_speaking = False
        self._stop_requested = False
        
        self._setup_provider()
    
    def _setup_provider(self):
        """Initialize the selected TTS provider."""
        if self.provider == "openai":
            import openai
            self._client = openai.OpenAI()
        elif self.provider == "edge-tts":
            # edge-tts is async, no init needed
            pass
        # ...
    
    def speak(self, text: str):
        """Convert text to speech and play through speakers."""
        if not text:
            return
        
        self._is_speaking = True
        self._stop_requested = False
        
        if self.provider == "openai":
            thread = threading.Thread(target=self._speak_openai, args=(text,))
        elif self.provider == "edge-tts":
            thread = threading.Thread(target=self._speak_edge, args=(text,))
        # ...
        
        thread.daemon = True
        thread.start()
    
    def stop(self):
        """Stop current speech immediately."""
        self._stop_requested = True
        self._is_speaking = False
    
    @property
    def is_speaking(self) -> bool:
        return self._is_speaking
```

### Speech Interruption

When wake word is detected while JARVIS is speaking:
1. Call `tts.stop()` immediately
2. Clear any buffered audio
3. Start listening for the new command

---

## 🔧 Settings Keys (used from settings.yaml)

```yaml
voice:
  stt_provider: openai              # openai | local | deepgram
  tts_provider: edge-tts            # openai | edge-tts | elevenlabs
  audio_sample_rate: 16000
  audio_input_device: null           # null = default device
  silence_threshold: 500
  silence_timeout: 1.5
  max_record_seconds: 30
  wake_word_enabled: true
  wake_word: jarvis
  tts_voice: alloy                  # OpenAI: alloy, echo, fable, onyx, nova, shimmer
  tts_speed: 1.0
  tts_volume: 0.8
```

## 🔗 Next Agent

When complete → move to `.agent/settings.agent.md` (cross-cutting), then `.agent/tier2-brain.agent.md`
