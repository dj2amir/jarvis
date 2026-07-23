#!/usr/bin/env python3
"""
Microphone Test & Calibration Tool.
Run this to check if JARVIS can hear you and find the right sensitivity.
"""

import sys
import os
import struct
import subprocess
import tempfile
import time
import wave
from pathlib import Path

import numpy as np

SAMPLE_RATE = 16000
CHUNK_SECONDS = 0.5
VAD_THRESHOLD = 40.0

def check_arecord():
    """Check if arecord is available and can capture."""
    try:
        result = subprocess.run(
            ["arecord", "--version"],
            capture_output=True, text=True, timeout=2
        )
        print(f"✅ arecord available: {result.stdout.strip().split(chr(10))[0]}")
        return True
    except Exception as e:
        print(f"❌ arecord not available: {e}")
        return False


def check_sounddevice():
    """Check if sounddevice works."""
    try:
        import sounddevice as sd
        devs = sd.query_devices()
        default = sd.default.device[0]
        info = sd.query_devices(default)
        print(f"✅ sounddevice: default input = [{default}] {info['name']}")
        print(f"   Samplerate: {int(info['default_samplerate'])} Hz")
        print(f"   Channels: {info['max_input_channels']}")
        return True
    except Exception as e:
        print(f"❌ sounddevice error: {e}")
        return False


def test_arecord_capture(duration=3):
    """Record audio via arecord and return stats."""
    tmp = tempfile.mktemp(suffix=".wav")
    try:
        print(f"\n🎤 Recording {duration}s via arecord... (speak now)")
        
        result = subprocess.run(
            ["arecord", "-q",
             "-r", str(SAMPLE_RATE),
             "-c", "1",
             "-f", "S16_LE",
             "-d", str(duration),
             tmp],
            timeout=duration + 5, capture_output=True
        )
        
        if result.returncode != 0:
            print(f"❌ arecord failed (code {result.returncode})")
            print(f"   Error: {result.stderr.decode()}")
            return None
        
        # Read the WAV file
        with wave.open(tmp, 'rb') as wf:
            frames = wf.readframes(wf.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16)
        
        return audio
    
    except Exception as e:
        print(f"❌ arecord error: {e}")
        return None
    finally:
        Path(tmp).unlink(missing_ok=True)


def test_live_audio(duration=5):
    """Record live audio and show energy levels in real-time."""
    try:
        import sounddevice as sd
        
        print(f"\n🎤 Live microphone monitor ({duration}s)")
        print(f"   Speak normally — watch the energy level:")
        print(f"   {'Level':<8} {'RMS':<10} {'Status':<15}")
        print(f"   {'─'*8} {'─'*10} {'─'*15}")
        
        max_rms = 0
        speech_count = 0
        total_chunks = 0
        
        def callback(indata, frames, time_info, status):
            nonlocal max_rms, speech_count, total_chunks
            if status:
                return
            
            rms = float(np.sqrt(np.mean(indata.astype(np.float64) ** 2)))
            max_rms = max(max_rms, rms)
            total_chunks += 1
            
            if rms > VAD_THRESHOLD / 32768:  # Scale for float32
                bar = "█" * min(int(rms * 500), 30)
                speech_count += 1
                status_text = "🔊 SPEECH"
            else:
                bar = "░" * min(int(rms * 500), 30)
                status_text = "🔇 silence"
            
            print(f"\r   {rms:<8.4f} {bar:<30} {status_text}", end="")
        
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype=np.float32,
            callback=callback,
        ):
            sd.sleep(int(duration * 1000))
        
        print(f"\n\n📊 Results:")
        print(f"   Max RMS (float32): {max_rms:.4f}")
        print(f"   Max RMS (int16 scale): {max_rms * 32768:.1f}")
        print(f"   Speech chunks: {speech_count}/{total_chunks}")
        
        # Recommend threshold
        if max_rms > 0:
            recommended = max(10, int(max_rms * 32768 * 0.3))
            print(f"\n💡 Recommended VAD_ENERGY_THRESHOLD: {recommended}")
            print(f"   (Current: {VAD_THRESHOLD})")
        
        return max_rms
        
    except Exception as e:
        print(f"❌ sounddevice live test error: {e}")
        return None


def test_transcribe(audio_int16):
    """Test transcription via LM Studio Whisper API."""
    print(f"\n🧪 Testing LM Studio Whisper transcription...")
    
    # Read provider config
    config_path = Path(__file__).parent / "config" / "providers.yaml"
    if config_path.exists():
        import yaml
        with open(config_path) as f:
            cfg = yaml.safe_load(f) or {}
        primary = cfg.get("primary", {})
        base_url = primary.get("base_url", "")
        api_key = primary.get("api_key", "")
        # Interpolate env vars
        if api_key.startswith("${") and api_key.endswith("}"):
            api_key = os.environ.get(api_key[2:-1], "")
    else:
        base_url = os.environ.get("LM_STUDIO_URL", "http://10.10.10.18:1234/v1")
        api_key = os.environ.get("LM_STUDIO_API_KEY", "sk-no-key")
    
    if not base_url:
        print("❌ No LM Studio URL configured")
        return False
    
    try:
        from openai import OpenAI
        
        # Save and clear proxy env vars
        proxy_keys = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy",
                      "https_proxy", "ALL_PROXY", "all_proxy"]
        saved = {k: os.environ.pop(k, None) for k in proxy_keys if k in os.environ}
        
        client = OpenAI(api_key=api_key or "sk-no-key", base_url=base_url)
        
        # Save audio to WAV
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(tmp, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_int16.tobytes())
        tmp.close()
        
        with open(tmp.name, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-1", file=f, language="en"
            )
        
        Path(tmp.name).unlink(missing_ok=True)
        
        # Restore proxies
        for k, v in saved.items():
            os.environ[k] = v
        
        if result.text and result.text.strip():
            print(f"✅ Transcription: \"{result.text.strip()}\"")
            return True
        else:
            print("❌ Empty transcription")
            return False
    
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        return False


def main():
    print("=" * 55)
    print("  🎤 JARVIS — Microphone Test & Calibration")
    print("=" * 55)
    print()
    
    # Step 1: Check tools
    print("📋 Step 1: Checking audio tools...")
    arecord_ok = check_arecord()
    sd_ok = check_sounddevice()
    
    if not arecord_ok and not sd_ok:
        print("\n❌ No working audio capture method found!")
        print("   Install portaudio: sudo apt-get install portaudio19-dev")
        sys.exit(1)
    
    # Step 2: Live monitor (sounddevice)
    if sd_ok:
        print(f"\n📋 Step 2: Live microphone monitor (speak during this test)...")
        test_live_audio(duration=5)
    
    # Step 3: Test arecord capture
    if arecord_ok:
        print(f"\n📋 Step 3: Testing arecord capture...")
        audio = test_arecord_capture(duration=5)
        
        if audio is not None:
            # Show RMS stats
            rms = float(np.sqrt(np.mean(audio.astype(np.float64) ** 2)))
            max_val = float(np.max(np.abs(audio)))
            print(f"\n📊 Audio stats (int16):")
            print(f"   RMS:     {rms:.1f}")
            print(f"   Max:     {max_val}")
            print(f"   Length:  {len(audio) / SAMPLE_RATE:.1f}s")
            print(f"   Samples: {len(audio)}")
            
            # Check if above VAD threshold
            if rms > VAD_THRESHOLD:
                print(f"   ✅ Above wake word VAD threshold ({VAD_THRESHOLD})")
            else:
                print(f"   ❌ Below wake word VAD threshold ({VAD_THRESHOLD})")
                print(f"   💡 Need to lower VAD_ENERGY_THRESHOLD to ~{int(rms * 0.7)}")
            
            # Step 4: Test transcription
            print(f"\n📋 Step 4: Testing LM Studio Whisper...")
            test_transcribe(audio)
    
    print()
    print("=" * 55)
    print("  ✅ Test complete")
    print("=" * 55)


if __name__ == "__main__":
    main()
