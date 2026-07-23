#!/usr/bin/env python3
"""
Full Voice Pipeline Test.

Tests the complete chain:
  Microphone → Recording → faster-whisper → STT

Run with: python3 test_voice_pipeline.py
"""

import sys
import os
import time
from pathlib import Path

import numpy as np

# Add project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def step(msg):
    print(f"\n{'='*55}")
    print(f"  {msg}")
    print(f"{'='*55}")


def test_microphone():
    """Step 1: Test microphone capture."""
    step("Step 1: Microphone Capture")
    
    import sounddevice as sd
    import numpy as np
    
    devices = sd.query_devices()
    default = sd.default.device[0]
    info = sd.query_devices(default)
    
    print(f"  Default input device: [{default}] {info['name']}")
    print(f"  Samplerate: {int(info['default_samplerate'])} Hz")
    print(f"  Channels: {info['max_input_channels']}")
    
    # Record 3 seconds
    print(f"\n  🎤 Recording for 3 seconds... (speak now if you want)")
    samplerate = 16000
    audio = sd.rec(int(3 * samplerate), samplerate=samplerate, 
                   channels=1, dtype=np.float32)
    sd.wait()
    
    rms = float(np.sqrt(np.mean(audio ** 2)))
    max_val = float(np.max(np.abs(audio)))
    
    print(f"  Recording stats:")
    print(f"    RMS:   {rms:.4f}")
    print(f"    Max:   {max_val:.4f}")
    print(f"    Duration: {len(audio)/samplerate:.1f}s")
    
    if rms < 0.001:
        print(f"\n  ⚠️  Very quiet (RMS={rms:.4f}). Make sure your mic is on and speak louder!")
        print(f"     Try: pactl set-source-volume @DEFAULT_SOURCE@ 100%")
    elif rms < 0.01:
        print(f"\n  ⚠️  Quiet (RMS={rms:.4f}). You might need to speak up.")
    else:
        print(f"\n  ✅ Good audio level!")
    
    return audio, samplerate


def test_faster_whisper(audio, samplerate):
    """Step 2: Test faster-whisper transcription."""
    step("Step 2: faster-whisper Transcription")
    
    # Convert float32 [-1,1] to int16
    import numpy as np
    audio_int16 = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    
    print(f"  Loading faster-whisper model (base, CPU)...")
    
    # Clear proxies for model (already downloaded, but just in case)
    proxy_keys = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", 
                  "https_proxy", "ALL_PROXY", "all_proxy"]
    saved = {k: os.environ.pop(k, None) for k in proxy_keys if k in os.environ}
    
    try:
        from faster_whisper import WhisperModel
        
        start = time.time()
        model = WhisperModel("base", device="cpu", compute_type="int8")
        load_time = time.time() - start
        print(f"  Model loaded in {load_time:.1f}s")
        
        print(f"  Transcribing...")
        start = time.time()
        segments, info = model.transcribe(audio_int16, beam_size=5, language="en")
        transcribe_time = time.time() - start
        
        text = " ".join(segment.text for segment in segments).strip()
        
        print(f"  Transcribed in {transcribe_time:.1f}s")
        print(f"  Result: \"{text}\"" if text else "  Result: (empty — no speech detected)")
        
        return text
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        for k, v in saved.items():
            os.environ[k] = v


def test_stt_module():
    """Step 3: Test the full STT class."""
    step("Step 3: STT Module Integration")
    
    sys.path.insert(0, '.')
    from core.settings import Settings
    from core.stt import STT
    
    settings = Settings()
    stt = STT(settings)
    
    print(f"  STT provider: {stt.provider}")
    print(f"  Capture method: {stt._capture_method}")
    print(f"  Available: {stt.is_available()}")
    
    if stt.is_available():
        print(f"\n  🎤 Testing stt.listen(timeout=5)...")
        print(f"  Speak now for 5 seconds...")
        text = stt.listen(timeout=5)
        
        if text:
            print(f"\n  ✅ Transcription: \"{text}\"")
        else:
            print(f"\n  ⚠️  No speech detected or transcription failed")
    
    return stt


def check_main():
    """Step 4: Check main.py imports work."""
    step("Step 4: Full Pipeline Import Check")
    
    try:
        os.chdir(Path(__file__).parent)
        sys.path.insert(0, '.')
        
        from core.settings import Settings
        from core.face import Face
        from core.stt import STT
        from core.tts import TTS
        from core.brain import Brain
        from core.memory import Memory
        from core.wake_word import WakeWordEngine
        
        settings = Settings()
        face = Face(settings)
        stt = STT(settings)
        tts = TTS(settings, face=face)
        
        print(f"  ✅ All modules import OK")
        print(f"  🎤 STT: {stt.provider} ({stt._capture_method})")
        print(f"  🗣️  TTS: {tts.provider} ({tts._playback_method})")
        print(f"  🎭 Face: {face.mode} ({face.style_name})")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 55)
    print("  🎤 JARVIS — Full Voice Pipeline Test")
    print("=" * 55)
    
    # Step 4 first (quick import check)
    check_main()
    
    # Step 1: Mic test
    audio, samplerate = test_microphone()
    
    # Step 2: faster-whisper test
    text = test_faster_whisper(audio, samplerate)
    
    # Step 3: STT integration test
    stt = test_stt_module()
    
    # Results
    print("\n" + "=" * 55)
    print("  📋 TEST RESULTS")
    print("=" * 55)
    
    audio_rms = float(np.sqrt(np.mean(audio ** 2)))
    audio_ok = audio_rms > 0.001
    whisper_ok = text is not None and len(text) > 0
    stt_ok = stt is not None and stt.is_available()
    
    mic_icon = "✅" if audio_ok else "⚠️"
    whisper_icon = "✅" if whisper_ok else "⚠️"
    whisper_text = f'"{text}"' if whisper_ok else "no speech"
    stt_icon = "✅" if stt_ok else "❌"
    pipe_icon = "✅" if audio_ok and stt_ok else "⚠️"
    
    print(f"  Microphone capture:  {mic_icon}  (RMS: {audio_rms:.4f})")
    print(f"  faster-whisper:      {whisper_icon}  {whisper_text}")
    print(f"  STT module:          {stt_icon}")
    print(f"  Full pipeline:       {pipe_icon}")
    
    if not audio_ok:
        print(f"\n  💡 Mic too quiet! Try:")
        print(f"     - Speak closer to the microphone")
        print(f"     - Run: pactl set-source-volume @DEFAULT_SOURCE@ 150%")
        print(f"     - Check: pavucontrol (GUI) → Input Devices tab")


if __name__ == "__main__":
    main()
