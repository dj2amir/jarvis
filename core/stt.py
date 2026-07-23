"""
Speech-to-Text Module (Ears)

Captures microphone audio and converts to text using:
  - OpenAI Whisper API (primary, needs internet + API key)
  - faster-whisper (local fallback, slower but private)

Microphone capture via:
  - sounddevice (primary, needs PortAudio)
  - arecord (fallback, command-line tool)

Features:
  - Voice Activity Detection (silence threshold)
  - Wake word detection (Porcupine)
  - Noise threshold gating
"""

import os
import sys
import time
import tempfile
import subprocess
import threading
import wave
import numpy as np
from pathlib import Path
from typing import Optional, Callable


class STT:
    """Speech-to-Text engine."""

    def __init__(self, settings=None):
        self.settings = settings or {}
        
        # Provider config
        self.provider = self.settings.get("voice.stt_provider", "openai")
        self.sample_rate = self.settings.get("voice.audio_sample_rate", 16000)
        self.silence_threshold = self.settings.get("voice.silence_threshold", 500)
        self.silence_timeout = self.settings.get("voice.silence_timeout", 1.5)  # seconds
        self.max_record_seconds = self.settings.get("voice.max_record_seconds", 30)
        self.device = self.settings.get("voice.audio_input_device", None)
        
        # Wake word
        self.wake_word_enabled = self.settings.get("voice.wake_word_enabled", False)
        self.wake_word = self.settings.get("voice.wake_word", "jarvis")
        self._wake_word_detected = threading.Event()
        self._is_listening = False
        
        # Try to find a working capture method
        self._capture_method = self._detect_capture_method()
        
        # Setup provider
        self._client = None
        self._local_model = None
        self._setup_provider()
        
        print(f"👂 STT ready | Provider: {self.provider} | Capture: {self._capture_method}")
    
    def _detect_capture_method(self):
        """Detect which audio capture method is available."""
        # Try sounddevice first
        try:
            import sounddevice as sd
            sd.query_devices()  # Will raise if PortAudio not available
            return "sounddevice"
        except Exception:
            pass
        
        # Try arecord
        try:
            result = subprocess.run(
                ["arecord", "--version"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                return "arecord"
        except Exception:
            pass
        
        return None  # No capture method available
    
    def _setup_provider(self):
        """Initialize the STT provider."""
        if self.provider == "openai":
            try:
                import openai
                self._client = openai.OpenAI()
                print("  → Using OpenAI Whisper API")
            except Exception as e:
                print(f"  ⚠️ OpenAI not available: {e}")
                self.provider = "local"
        
        if self.provider == "local":
            try:
                from faster_whisper import WhisperModel
                self._local_model = WhisperModel(
                    "base", device="cpu", compute_type="int8"
                )
                print("  → Using local faster-whisper")
            except Exception as e:
                print(f"  ⚠️ faster-whisper not available: {e}")
                self.provider = None
    
    def is_available(self) -> bool:
        """Check if microphone capture is available."""
        return self._capture_method is not None and self.provider is not None
    
    def listen(self, timeout: float = None) -> Optional[str]:
        """
        Record from microphone and transcribe.
        
        Args:
            timeout: Max seconds to wait for speech (None = wait indefinitely)
        
        Returns:
            Transcribed text or None if no speech detected.
        """
        if not self.is_available():
            print("⚠️ STT not available (no microphone or no provider)")
            return None
        
        audio_data = self._record_audio(timeout)
        if audio_data is None:
            return None
        
        text = self._transcribe(audio_data)
        return text
    
    def listen_with_wake_word(self, callback: Callable[[str], None]):
        """
        Background thread: continuously listen for wake word,
        then record command and call callback with transcription.
        """
        if not self.wake_word_enabled:
            print("⚠️ Wake word not enabled")
            return
        
        def _listener():
            print(f"🔊 Listening for wake word: '{self.wake_word}'...")
            # NOTE: Full Porcupine wake word detection is planned for future.
            # Current implementation uses continuous recording + transcription
            # which is not real-time. For production, integrate pvporcupine.
            while True:
                audio = self._record_audio(timeout=None)
                if audio is not None:
                    text = self._transcribe(audio)
                    if text and self.wake_word in text.lower():
                        print(f"🔊 Wake word detected!")
                        self._wake_word_detected.set()
                        callback(text)
        
        thread = threading.Thread(target=_listener, daemon=True)
        thread.start()
    
    def _record_audio(self, timeout: float = None) -> Optional[np.ndarray]:
        """
        Record audio from microphone with silence detection.
        
        Returns audio data as numpy array, or None if no speech.
        """
        if self._capture_method == "sounddevice":
            return self._record_sounddevice(timeout)
        elif self._capture_method == "arecord":
            return self._record_arecord(timeout)
        else:
            print("⚠️ No audio capture method available")
            return None
    
    def _record_sounddevice(self, timeout: float = None) -> Optional[np.ndarray]:
        """Record using sounddevice (requires PortAudio)."""
        try:
            import sounddevice as sd
            
            print("🎤 Listening... (speak now)")
            
            # Use a stream with callback for silence detection
            audio_buffer = []
            silence_start = None
            speech_detected = False
            recording = False
            start_time = time.time()
            
            def callback(indata, frames, time_info, status):
                nonlocal silence_start, speech_detected, recording
                
                if status:
                    return
                
                # Calculate RMS for silence detection
                rms = np.sqrt(np.mean(indata ** 2))
                
                if rms > self.silence_threshold / 10000:
                    if not recording:
                        recording = True
                        print("  🎤 Recording...")
                    speech_detected = True
                    silence_start = None
                    audio_buffer.append(indata.copy())
                elif recording:
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start > self.silence_timeout:
                        raise sd.CallbackStop()
                    audio_buffer.append(indata.copy())
            
            # Determine max duration
            max_time = timeout or self.max_record_seconds
            
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32,
                device=self.device,
                callback=callback,
            ):
                sd.sleep(int(max_time * 1000))
            
            if not speech_detected or not audio_buffer:
                print("  No speech detected")
                return None
            
            audio = np.concatenate(audio_buffer)
            print(f"  ✅ Recorded {len(audio) / self.sample_rate:.1f}s")
            return audio
            
        except Exception as e:
            print(f"  ⚠️ Sounddevice error: {e}")
            return None
    
    def _record_arecord(self, timeout: float = None) -> Optional[np.ndarray]:
        """Record using arecord command-line tool (fallback)."""
        try:
            max_time = timeout or self.max_record_seconds
            tmp_path = tempfile.mktemp(suffix=".wav")
            
            print("🎤 Listening... (speak now)")
            
            result = subprocess.run([
                "arecord", "-q",
                "-r", str(self.sample_rate),
                "-c", "1",
                "-f", "S16_LE",
                "-d", str(int(max_time)),
                tmp_path
            ], timeout=max_time + 5, capture_output=True)
            
            if result.returncode != 0 or not Path(tmp_path).exists():
                print("  ⚠️ arecord failed")
                return None
            
            # Read the WAV file
            with wave.open(tmp_path, 'rb') as wf:
                frames = wf.readframes(wf.getnframes())
                audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Clean up
            Path(tmp_path).unlink(missing_ok=True)
            
            # Simple silence detection on the recorded file
            rms = np.sqrt(np.mean(audio ** 2))
            if rms < self.silence_threshold / 100000:
                print("  No speech detected")
                return None
            
            print(f"  ✅ Recorded {len(audio) / self.sample_rate:.1f}s")
            return audio
            
        except subprocess.TimeoutExpired:
            print("  ⏰ Recording timeout")
            return None
        except Exception as e:
            print(f"  ⚠️ arecord error: {e}")
            return None
    
    def _transcribe(self, audio: np.ndarray) -> Optional[str]:
        """Transcribe audio to text."""
        if self.provider == "openai":
            return self._transcribe_openai(audio)
        elif self.provider == "local":
            return self._transcribe_local(audio)
        else:
            return None
    
    def _transcribe_openai(self, audio: np.ndarray) -> Optional[str]:
        """Transcribe using OpenAI Whisper API."""
        if not self._client:
            return None
        
        try:
            # Save audio to temp file for API
            tmp_path = tempfile.mktemp(suffix=".wav")
            self._save_wav(tmp_path, audio)
            
            with open(tmp_path, "rb") as f:
                response = self._client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language="en",
                )
            
            Path(tmp_path).unlink(missing_ok=True)
            return response.text.strip()
            
        except Exception as e:
            print(f"  ⚠️ Whisper API error: {e}")
            return None
    
    def _transcribe_local(self, audio: np.ndarray) -> Optional[str]:
        """Transcribe using local faster-whisper model."""
        if not self._local_model:
            return None
        
        try:
            segments, info = self._local_model.transcribe(audio, beam_size=5)
            text = " ".join(segment.text for segment in segments)
            return text.strip()
        except Exception as e:
            print(f"  ⚠️ Local whisper error: {e}")
            return None
    
    def _save_wav(self, path: str, audio: np.ndarray):
        """Save numpy audio array to WAV file using standard library."""
        # Convert float32 [-1, 1] to int16
        audio_int16 = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
        with wave.open(path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_int16.tobytes())
    
    def wait_for_wake_word(self, timeout: float = None) -> bool:
        """Wait for wake word to be detected."""
        return self._wake_word_detected.wait(timeout=timeout)
    
    def reset_wake_word(self):
        """Reset wake word detection flag."""
        self._wake_word_detected.clear()
