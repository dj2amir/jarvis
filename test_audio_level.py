#!/usr/bin/env python3
"""
Audio Level Diagnostic — shows exactly what JARVIS hears.

Run: python3 test_audio_level.py
Speak during the recording, then check the results.
"""

import sys
import os
import time
import wave
from pathlib import Path
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def step(msg):
    print(f"\n═══ {msg} ═══")


# ── Step 1: Check audio devices ──────────────────────────────────

step("Step 1: Available Input Devices")

import sounddevice as sd

devices = sd.query_devices()
input_devices = []
for i, d in enumerate(devices):
    if d['max_input_channels'] > 0:
        name = d['name']
        sr = int(d['default_samplerate'])
        is_default = i == sd.default.device[0]
        marker = "← DEFAULT" if is_default else ""
        input_devices.append(i)
        print(f"  [{i}] {name} @ {sr}Hz {marker}")


# ── Step 2: Record 5 seconds ─────────────────────────────────────

step("Step 2: Record 5 Seconds")
print("  SPEAK NOW — say something like 'hello JARVIS testing'")

SAMPLE_RATE = 16000
DURATION = 5

audio = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, 
               channels=1, dtype=np.float32)
sd.wait()
print("  Done recording.")

# ── Step 3: Analyze levels ───────────────────────────────────────

step("Step 3: Audio Analysis")

rms = float(np.sqrt(np.mean(audio ** 2)))
peak = float(np.max(np.abs(audio)))

print(f"  Duration:    {len(audio) / SAMPLE_RATE:.1f}s")
print(f"  RMS (avg):   {rms:.6f}  (float32 scale)")
print(f"  Peak:        {peak:.6f}")
print(f"  RMS (int16): {rms * 32768:.1f}  (int16 scale)")

# ── VAD threshold comparison ─────────────────────────────────────

vad_threshold = float(os.environ.get("VAD_THRESHOLD", "100")) / 10000
print(f"\n  VAD threshold (settings): {vad_threshold:.4f}")
print(f"  Your RMS:                {rms:.6f}")

if rms > vad_threshold:
    print(f"  ✅ Your voice is ABOVE threshold — VAD should trigger!")
elif rms > 0.001:
    print(f"  ⚠️  Your voice is BELOW threshold — VAD won't trigger")
    print(f"  💡 Fix: set silence_threshold to {int(rms * 10000 * 0.5)} in config/settings.yaml")
else:
    print(f"  ❌ Very quiet — microphone may not be capturing your voice!")
    print(f"  💡 Check: pactl set-source-volume @DEFAULT_SOURCE@ 150%")
    print(f"  💡 Check: pavucontrol → Input Devices tab → verify mic is active")

# ── Step 4: Save WAV file ────────────────────────────────────────

step("Step 4: Save Recording")

wav_path = Path(__file__).parent / "test_recording.wav"
audio_int16 = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)

with wave.open(str(wav_path), 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(audio_int16.tobytes())

print(f"  Saved: {wav_path}")
print(f"  Play it back with: ffplay {wav_path}")

# ── Step 5: Test transcription ───────────────────────────────────

step("Step 5: Test Transcription")

try:
    proxy_keys = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy",
                  "https_proxy", "ALL_PROXY", "all_proxy"]
    saved = {k: os.environ.pop(k, None) for k in proxy_keys if k in os.environ}

    from faster_whisper import WhisperModel
    
    model = WhisperModel("tiny", device="cpu", compute_type="float32")
    print(f"  Model: tiny (float32)")
    
    start = time.time()
    segments, info = model.transcribe(audio_int16, beam_size=5, language="en")
    elapsed = time.time() - start
    
    text = " ".join(seg.text for seg in segments).strip()
    
    if text:
        print(f"  ✅ Transcription: \"{text}\"")
        print(f"  ⏱️  Time: {elapsed:.1f}s")
    else:
        print(f"  ⚠️  Empty transcription — model didn't detect speech")
        print(f"  This means the audio level is too low for the model")
        print(f"  Try speaking LOUDER and CLOSER to the microphone")
        print(f"  Or play back the WAV file to verify your mic works:")
        print(f"     ffplay {wav_path}")

finally:
    for k, v in saved.items():
        os.environ[k] = v


# ── Final summary ─────────────────────────────────────────────────

step("Diagnosis")

if peak < 0.01:
    print("  ❌ Your microphone is NOT capturing your voice.")
    print("")
    print("  Possible fixes:")
    print("  1. Open pavucontrol → Input Devices → make sure")
    print("     your Logitech G435 headset is NOT muted")
    print("  2. Try a different USB port for the headset receiver")
    print("  3. Make sure the headset is powered on and connected")
elif rms < vad_threshold:
    gap = int(rms * 10000 * 0.5)
    print(f"  ⚠️  Mic works but volume is too low for VAD.")
    print(f"  💡 Run: pactl set-source-volume @DEFAULT_SOURCE@ 150%")
    print(f"  💡 Or set: silence_threshold: {gap} in config/settings.yaml")
elif not text:
    print("  ⚠️  Mic works, VAD triggers, but transcription fails.")
    print("  💡 Play the recording to verify quality: ffplay test_recording.wav")
else:
    print("  ✅ Everything works! Your mic should work with JARVIS.")
    print("  💡 If it still doesn't, restart JARVIS and try again.")
