"""
Wake Word Detection Engine.

Listens for speech and fires a callback to wake JARVIS.

Three modes (auto-selected):
  1. porcupine   — Picovoice Porcupine (<200ms, needs free access key)
  2. energy-only — Pure energy detection, NO keys, NO API, NO transcription
  3. vad+stt     — Energy + Whisper transcription (legacy, needs Whisper)

The engine auto-selects Porcupine if PICOVOICE_ACCESS_KEY is set, otherwise
uses energy-only mode which triggers on any sustained speech.

Energy-only flow:
  ┌──────────────┐
  │ arecord pipe │ ── raw PCM ──► RMS > threshold?
  └──────────────┘                    │
                              ┌──────▼──────┐
                              │  YES: fire! │  ──► callback()
                              └─────────────┘
      (no keys, no cloud, no transcription — 100% local)
"""

import os
import io
import struct
import tempfile
import subprocess
import threading
import time
import wave
from pathlib import Path
from typing import Optional, Callable, List
import numpy as np


# ── Constants ────────────────────────────────────────────────────────

PORCUPINE_FRAME_LENGTH = 512       # samples per frame @ 16kHz
VAD_CHUNK_SECONDS = 0.5            # seconds per VAD energy check
VAD_ENERGY_THRESHOLD = 12.0       # RMS threshold (raw int16) — tune for your mic
VAD_MIN_DURATION = 1.0             # minimum speech before transcription
VAD_MAX_DURATION = 3.0             # max speech per wake check
VAD_SILENCE_TIMEOUT = 1.2          # silence seconds → end of utterance
WAKE_COOLDOWN = 3.0                # ignore wake triggers within this window
WAVE_MAX_SECONDS = 10.0            # safety limit per recording


class WakeWordEngine:
    """Detects 'Hey JARVIS' (or configured wake word) from microphone.

    Usage:
        engine = WakeWordEngine(settings, face)
        engine.start(on_wake=my_callback)
        ...
        engine.stop()
    """

    def __init__(self, settings: Optional[dict] = None, face=None):
        self.settings = settings or {}
        self.face = face

        # ── Configuration ─────────────────────────────────────
        self.wake_word = self.settings.get("voice.wake_word", "jarvis").lower()
        self.enabled = self.settings.get("voice.wake_word_enabled", True)
        self.sample_rate = self.settings.get("voice.audio_sample_rate", 16000)

        # ── State ─────────────────────────────────────────────
        self._active = False
        self._thread: Optional[threading.Thread] = None
        self._on_wake: Optional[Callable[[], None]] = None
        self._last_detection = 0.0
        self._porcupine = None
        self._mode: str = "energy-only"  # default: no keys, no API, just energy
        self._cooldown = WAKE_COOLDOWN

        # ── Try Porcupine (fast mode) ─────────────────────────
        self._init_porcupine()

        if self.enabled:
            print(f"🔊 Wake word engine ready | word='{self.wake_word}' | mode={self._mode}")

    # ── Public API ────────────────────────────────────────────────

    def start(self, on_wake: Callable[[], None]):
        """Start the background wake word listener.

        Args:
            on_wake: Called (from listener thread) when wake word detected.
                     Keep this function short — it runs inside the audio loop.
        """
        if not self.enabled:
            print("⚠️ Wake word disabled in settings")
            return
        self._on_wake = on_wake
        self._active = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="wake-word")
        self._thread.start()

    def stop(self):
        """Gracefully stop the listener."""
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def mode(self) -> str:
        return self._mode

    # ── Main dispatch ─────────────────────────────────────────────

    def _run(self):
        try:
            if self._mode == "porcupine":
                self._listen_porcupine()
            elif self._mode == "energy-only":
                self._listen_energy_only()
            else:
                self._listen_vad_stt()
        except Exception as e:
            print(f"⚠️ Wake word listener crashed: {e}")
            self._active = False

    # ── Porcupine mode (fast, <200ms) ─────────────────────────────

    def _init_porcupine(self):
        """Try to initialise Porcupine; silently fall back on failure."""
        access_key = os.environ.get("PICOVOICE_ACCESS_KEY", "")
        if not access_key:
            return
        try:
            import pvporcupine
            # Pick the built-in keyword — "jarvis" ships with the library
            keyword = self.wake_word
            if keyword not in pvporcupine.KEYWORDS:
                # Use the closest match or fall back to "computer"
                keyword = "jarvis" if "jarvis" in pvporcupine.KEYWORDS else "computer"
            self._porcupine = pvporcupine.create(
                access_key=access_key,
                keywords=[keyword],
            )
            self._mode = "porcupine"
            print(f"  → Porcupine: instant wake word detection")
        except Exception as e:
            print(f"  ⚠️ Porcupine init failed: {e}")

    def _listen_porcupine(self):
        """Continuous Porcupine detection via arecord pipe.

        Reads raw PCM 16-bit frames from arecord and feeds them into
        the Porcupine engine one frame at a time (<1 ms per frame).
        """
        frame_bytes = PORCUPINE_FRAME_LENGTH * 2  # 16-bit sample = 2 bytes
        proc = self._spawn_arecord_pipe()

        try:
            while self._active:
                data = proc.stdout.read(frame_bytes)
                if not data or len(data) < frame_bytes:
                    # Underrun — pipe may have closed
                    proc.kill()
                    proc = self._spawn_arecord_pipe()
                    continue

                # Unpack 512 int16 samples
                audio_frame = struct.unpack_from(
                    "<" + "h" * PORCUPINE_FRAME_LENGTH, data
                )
                result = self._porcupine.process(audio_frame)
                if result >= 0:
                    self._fire_wake()
        finally:
            proc.kill()

    # ── Energy-only mode (no keys, no API, 100% local) ──────────

    def _listen_energy_only(self):
        """Energy-based wake detection — NO keys, NO cloud, NO transcription.

        Continuously monitors audio energy.  When sustained speech is
        detected (at least 1 second of voice followed by 0.5s silence),
        fires the wake callback immediately.

        No audio data is sent anywhere.  Works 100% offline.
        """
        chunk_samples = int(self.sample_rate * VAD_CHUNK_SECONDS)
        chunk_bytes = chunk_samples * 2  # 16-bit

        proc = self._spawn_arecord_pipe()
        was_speech = False
        speech_frames = 0
        silence_frames = 0
        min_speech = int(1.0 / VAD_CHUNK_SECONDS)     # 1 second of speech
        min_silence = int(0.5 / VAD_CHUNK_SECONDS)    # 0.5s of silence after

        try:
            while self._active:
                data = proc.stdout.read(chunk_bytes)
                if not data or len(data) < chunk_bytes:
                    proc.kill()
                    proc = self._spawn_arecord_pipe()
                    continue

                samples = np.frombuffer(data, dtype=np.int16).astype(np.float64)
                rms = float(np.sqrt(np.mean(samples ** 2)))
                is_speech = rms > VAD_ENERGY_THRESHOLD

                if is_speech:
                    speech_frames += 1
                    silence_frames = 0
                    was_speech = True
                elif was_speech:
                    silence_frames += 1
                    # Enough speech followed by enough silence = wake!
                    if speech_frames >= min_speech and silence_frames >= min_silence:
                        self._fire_wake()
                        speech_frames = 0
                        silence_frames = 0
                        was_speech = False
                # Safety: max speech duration resets
                if was_speech and speech_frames > int(10.0 / VAD_CHUNK_SECONDS):
                    speech_frames = 0
                    silence_frames = 0
                    was_speech = False

        finally:
            proc.kill()

    # ── VAD + STT mode (legacy, needs Whisper) ─────────────────────

    def _listen_vad_stt(self):
        """Energy-based voice detection + Whisper transcription.

        Continuously monitors audio energy.  When sustained speech is
        detected, captures the utterance and transcribes it via the
        Whisper API (LM Studio).  If the transcript contains the wake
        word, fires the callback.
        """
        chunk_samples = int(self.sample_rate * VAD_CHUNK_SECONDS)
        chunk_bytes = chunk_samples * 2  # 16-bit

        proc = self._spawn_arecord_pipe()
        # State for voice activity
        was_speech = False
        speech_buffers: List[bytes] = []
        silence_frames = 0
        speech_frames = 0
        max_speech_frames = int(VAD_MAX_DURATION / VAD_CHUNK_SECONDS)

        try:
            while self._active:
                # Read one VAD chunk
                data = proc.stdout.read(chunk_bytes)
                if not data or len(data) < chunk_bytes:
                    proc.kill()
                    proc = self._spawn_arecord_pipe()
                    continue

                # Compute RMS energy (int16 domain, fast)
                samples = np.frombuffer(data, dtype=np.int16).astype(np.float64)
                rms = float(np.sqrt(np.mean(samples ** 2)))

                is_speech = rms > VAD_ENERGY_THRESHOLD

                if is_speech:
                    speech_buffers.append(data)
                    speech_frames += 1
                    silence_frames = 0
                    was_speech = True
                elif was_speech:
                    # In silence after speech — accumulate gap before ending
                    speech_buffers.append(data)
                    silence_frames += 1
                    if silence_frames >= int(VAD_SILENCE_TIMEOUT / VAD_CHUNK_SECONDS):
                        # End of utterance — transcribe
                        self._check_utterance(speech_buffers)
                        speech_buffers = []
                        speech_frames = 0
                        silence_frames = 0
                        was_speech = False

                # Safety: max utterance length
                if was_speech and speech_frames >= max_speech_frames:
                    self._check_utterance(speech_buffers)
                    speech_buffers = []
                    speech_frames = 0
                    silence_frames = 0
                    was_speech = False

        finally:
            proc.kill()

    def _check_utterance(self, buffers: List[bytes]):
        """Transcribe captured audio and check for wake word."""
        if not buffers or not self._active:
            return

        # Concatenate raw PCM → WAV bytes
        raw = b"".join(buffers)
        wav_bytes = self._raw_to_wav(raw, self.sample_rate)

        # Transcribe (cheap: ~1-2 seconds via LM Studio Whisper)
        text = self._transcribe_wav(wav_bytes)
        if text and self.wake_word in text.lower():
            self._fire_wake()

    # ── Audio utilities ──────────────────────────────────────────

    def _spawn_arecord_pipe(self):
        """Start arecord in raw pipe mode."""
        return subprocess.Popen(
            [
                "arecord", "-q",
                "-r", str(self.sample_rate),
                "-c", "1",
                "-f", "S16_LE",
                "-t", "raw",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=4096,
        )

    @staticmethod
    def _raw_to_wav(raw_pcm: bytes, sample_rate: int) -> bytes:
        """Wrap raw PCM int16 data in a WAV container (in-memory)."""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(raw_pcm)
        return buf.getvalue()

    def _transcribe_wav(self, wav_bytes: bytes) -> Optional[str]:
        """Transcribe WAV audio bytes via LM Studio Whisper API."""
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=os.environ.get("OPENAI_API_KEY", "sk-no-key"),
                base_url=os.environ.get(
                    "LM_STUDIO_URL", "http://10.10.10.18:1234/v1"
                ),
            )
            # Write to temp file for the API (it needs a filename)
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp.write(wav_bytes)
            tmp.close()
            with open(tmp.name, "rb") as f:
                result = client.audio.transcriptions.create(
                    model="whisper-1", file=f, language="en"
                )
            Path(tmp.name).unlink(missing_ok=True)
            return result.text.strip() if result.text else None
        except Exception as e:
            # Rate limits, API errors, etc. — just skip this frame
            return None

    # ── Wake event ───────────────────────────────────────────────

    def _fire_wake(self):
        """Fire the wake callback (with cooldown)."""
        now = time.time()
        if now - self._last_detection < self._cooldown:
            return
        self._last_detection = now

        if self.face:
            self.face.show_emotion("surprised")
            time.sleep(0.25)

        if self._on_wake:
            try:
                self._on_wake()
            except Exception as e:
                print(f"⚠️ Wake callback error: {e}")
