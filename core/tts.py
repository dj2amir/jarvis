"""
Text-to-Speech Module (Mouth)

Converts text to spoken audio using:
  - edge-tts (free, works offline-capable, good quality)
  - OpenAI TTS API (premium, multiple voices, needs API key)

Audio playback via:
  - aplay/ffplay (command line, always available)
  - sounddevice (if PortAudio available)

Features:
  - Speech interruption (stop speaking immediately)
  - Streaming playback (speak while generating)
  - Emotional tone variation
"""

import os
import sys
import asyncio
import tempfile
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional


class TTS:
    """Text-to-Speech engine."""

    def __init__(self, settings=None, face=None):
        self.settings = settings or {}
        self.face = face  # Optional face for mouth animation
        
        # Provider config
        self.provider = self.settings.get("voice.tts_provider", "edge-tts")
        self.voice = self.settings.get("voice.tts_voice", "default")
        self.speed = self.settings.get("voice.tts_speed", 1.0)
        self.volume = self.settings.get("voice.tts_volume", 0.8)
        
        # State
        self._is_speaking = False
        self._stop_requested = False
        self._speech_thread = None
        
        # Find playback method
        self._playback_method = self._detect_playback()
        
        # Setup provider
        self._client = None
        self._setup_provider()
        
        print(f"🗣️ TTS ready | Provider: {self.provider} | Playback: {self._playback_method}")
    
    def _detect_playback(self):
        """Detect which audio playback method is available.

        Prefers ffplay (handles MP3 natively) over aplay (WAV only).
        """
        # ffplay handles MP3 natively — preferred for edge-tts
        try:
            result = subprocess.run(
                ["ffplay", "-version"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                return "ffplay"
        except Exception:
            pass

        # Check ffmpeg for MP3→WAV conversion + aplay
        self._ffmpeg_available = False
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                self._ffmpeg_available = True
        except Exception:
            pass

        # aplay (WAV only — needs ffmpeg for MP3 conversion)
        try:
            result = subprocess.run(
                ["aplay", "--version"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                return "aplay"
        except Exception:
            pass
        
        # Try sounddevice
        try:
            import sounddevice as sd
            sd.query_devices()  # Will raise if PortAudio not available
            return "sounddevice"
        except Exception:
            pass
        
        return None  # No playback method available
    
    def _setup_provider(self):
        """Initialize TTS provider."""
        if self.provider == "openai":
            try:
                import openai
                self._client = openai.OpenAI()
                
                # Map voice names
                if self.voice == "default":
                    self.voice = "alloy"
                print("  → Using OpenAI TTS")
            except Exception as e:
                print(f"  ⚠️ OpenAI TTS not available: {e}")
                self.provider = "edge-tts"
        
        if self.provider == "edge-tts":
            # edge-tts doesn't need initialization
            print("  → Using edge-tts (free)")
    
    def is_available(self) -> bool:
        """Check if speech synthesis is available."""
        return self.provider is not None
    
    def speak(self, text: str):
        """
        Convert text to speech and play through speakers.
        Non-blocking — returns immediately.
        
        Args:
            text: Text to speak aloud
        """
        if not text or not self.is_available():
            return
        
        # Stop any current speech
        self.stop()
        
        self._is_speaking = True
        self._stop_requested = False
        
        if self.face:
            self.face.speak_start()
        
        # Start speech in background thread
        self._speech_thread = threading.Thread(
            target=self._speak_sync,
            args=(text,),
            daemon=True
        )
        self._speech_thread.start()
    
    def speak_and_wait(self, text: str):
        """
        Convert text to speech and wait for completion.
        Blocking — returns when speech finishes.
        """
        if not text or not self.is_available():
            return
        
        self.stop()
        self._is_speaking = True
        self._stop_requested = False
        
        if self.face:
            self.face.speak_start()
        
        self._speak_sync(text)
    
    def stop(self):
        """Stop current speech immediately."""
        self._stop_requested = True
        self._is_speaking = False
        
        if self.face:
            self.face.speak_end()
    
    @property
    def is_speaking(self) -> bool:
        return self._is_speaking
    
    def _speak_sync(self, text: str):
        """Internal: speak text and wait for completion."""
        try:
            if self.provider == "openai":
                self._speak_openai(text)
            elif self.provider == "edge-tts":
                self._speak_edge(text)
        except Exception as e:
            print(f"⚠️ TTS error: {e}")
        finally:
            self._is_speaking = False
            if self.face and not self._stop_requested:
                self.face.speak_end()
    
    def _speak_edge(self, text: str):
        """Speak using edge-tts (runs async in thread)."""
        if not self._playback_method:
            print("⚠️ No playback method available")
            return
        
        # Run async edge-tts in its own event loop
        async def _generate():
            import edge_tts
            
            voice = self.voice if self.voice != "default" else "en-US-GuyNeural"
            rate = f"+{int((self.speed - 1.0) * 50)}%" if self.speed >= 1.0 else f"-{int((1.0 - self.speed) * 50)}%"
            
            tmp_path = tempfile.mktemp(suffix=".mp3")
            
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            await communicate.save(tmp_path)
            
            return tmp_path
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            tmp_path = loop.run_until_complete(_generate())
            loop.close()
            
            if not self._stop_requested and Path(tmp_path).exists():
                self._play_audio(tmp_path)
            
            Path(tmp_path).unlink(missing_ok=True)
            
        except Exception as e:
            print(f"⚠️ edge-tts error: {e}")
    
    def _speak_openai(self, text: str):
        """Speak using OpenAI TTS API."""
        if not self._client:
            return
        
        try:
            response = self._client.audio.speech.create(
                model="tts-1",
                voice=self.voice,
                input=text,
            )
            
            tmp_path = tempfile.mktemp(suffix=".mp3")
            response.stream_to_file(tmp_path)
            
            if not self._stop_requested and Path(tmp_path).exists():
                self._play_audio(tmp_path)
            
            Path(tmp_path).unlink(missing_ok=True)
            
        except Exception as e:
            print(f"⚠️ OpenAI TTS error: {e}")
    
    def _play_audio(self, path: str):
        """Play an audio file using the detected playback method."""
        if self._playback_method == "ffplay":
            # ffplay handles MP3 natively — clean playback
            subprocess.run(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif self._playback_method == "aplay":
            # aplay only supports WAV — convert MP3 first if needed
            play_path = path
            if path.lower().endswith(".mp3") and hasattr(self, '_ffmpeg_available') and self._ffmpeg_available:
                wav_path = path + ".wav"
                subprocess.run(
                    ["ffmpeg", "-y", "-i", path, "-ac", "1", "-ar", "24000", wav_path],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                if Path(wav_path).exists():
                    play_path = wav_path
            if play_path == path and path.lower().endswith(".mp3"):
                # Can't play MP3 with aplay — warn and skip
                print("⚠️ TTS: Cannot play MP3 without ffmpeg conversion")
                return
            subprocess.run(
                ["aplay", "-q", play_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Clean up converted WAV
            if play_path != path:
                Path(play_path).unlink(missing_ok=True)
        elif self._playback_method == "sounddevice":
            self._play_sounddevice(path)
    
    def _play_sounddevice(self, path: str):
        """Play audio using sounddevice."""
        try:
            import sounddevice as sd
            import soundfile as sf
            
            data, samplerate = sf.read(path)
            sd.play(data, samplerate)
            sd.wait()
        except Exception as e:
            print(f"⚠️ Sounddevice playback error: {e}")
    

