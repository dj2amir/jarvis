#!/usr/bin/env python3
"""
JARVIS — Self-Evolving AI Assistant
Main entry point.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.settings import Settings
from core.face import Face
from core.stt import STT
from core.tts import TTS
from core.brain import Brain
from core.memory import Memory


def main():
    settings = Settings()
    face = Face(settings)
    memory = Memory(settings)
    stt = STT(settings)
    tts = TTS(settings, face=face)
    brain = Brain(settings, face=face, memory=memory)
    
    print("\n" + "=" * 50)
    print("  🤖 JARVIS — Self-Evolving AI Assistant")
    print("=" * 50)
    print()
    
    if stt.is_available():
        print("  🎤 Microphone: Ready")
    else:
        print("  🎤 Microphone: Not available")
    
    if tts.is_available():
        print("  🔊 Speaker: Ready")
    else:
        print("  🔊 Speaker: Not available")
    
    if brain.is_available():
        print(f"  🧠 Brain: Connected")
    else:
        print("  🧠 Brain: Not connected")
    
    if memory.is_enabled:
        print(f"  💾 Memory: Active ({len(memory.short_term)} messages in session)")
    
    print()
    print("  Commands:")
    print("    <ask anything>    — JARVIS thinks and responds")
    print("    remember that ... — JARVIS remembers a fact")
    print("    /recall <query>   — Search JARVIS's memories")
    print("    /listen           — Record microphone")
    print("    /face             — Show face demo")
    print("    /memory           — Show memory stats")
    print("    /exit             — Quit")
    print()
    
    memory.log_event("milestone", "JARVIS started", success=True)
    face.show_emotion("neutral")
    
    try:
        while True:
            cmd = input("\n  > ").strip()
            
            if not cmd:
                continue
            
            lower = cmd.lower()
            
            # ── System commands ──
            if lower in ("/exit", "/quit", "/bye"):
                face.show_emotion("sleeping")
                tts.speak("Going offline. Goodbye.")
                print("\n  JARVIS: Going offline. Goodbye.")
                break
            
            elif lower == "/face":
                face.animate_demo()
            
            elif lower == "/listen":
                face.listen_start()
                print("  🎤 Listening...")
                text = stt.listen(timeout=5)
                if text:
                    print(f"\n  You said: {text}")
                    response = brain.think(text)
                    if response:
                        print(f"\n  JARVIS: {response}")
                        tts.speak(response)
                else:
                    print("\n  No speech detected.")
                    face.show_emotion("neutral")
            
            elif lower == "/memory":
                print(f"\n  💾 Memory Stats:")
                print(f"  {memory.stats()}")
            
            elif lower.startswith("/recall "):
                query = cmd[8:]
                print(f"  🔍 Searching memories for: {query}")
                results = memory.long_term.search(query, max_results=5)
                if results:
                    print()
                    for r in results:
                        print(f"  [{r['category']}] {r['content'][:100]}")
                else:
                    print("  No memories found.")
            
            elif lower == "/help":
                print("  Commands:")
                print("    <ask anything>    — JARVIS thinks with AI")
                print("    remember that ... — JARVIS remembers a fact")
                print("    /recall <query>   — Search memories")
                print("    /listen           — Speak with microphone")
                print("    /face             — Show face demo")
                print("    /memory           — Show memory stats")
                print("    /exit             — Quit")
            
            elif lower == "/clear":
                memory.forget_all()
                memory.short_term.clear()
                print("  🧹 All memories cleared.")
            
            elif lower == "/stats":
                facts = memory.get_all_facts()
                print(f"\n  📊 Facts stored: {len(facts)}")
                for f in facts[-5:]:
                    print(f"  [{f['category']}] {f['content'][:80]}")
            
            elif lower.startswith("/forget "):
                query = cmd[8:]
                results = memory.long_term.search(query, 3)
                if results:
                    for r in results:
                        memory.forget(r["id"])
                        print(f"  🗑️ Forgotten: {r['content'][:60]}...")
                else:
                    print("  No matching memories found.")
            
            elif lower.startswith("/"):
                print(f"  Unknown command: {cmd}")
            
            # ── AI conversation ──
            else:
                print(f"\n  You: {cmd}")
                
                response = brain.think(cmd)
                
                if response:
                    print(f"\n  JARVIS: {response}")
                    face.show_emotion("speaking")
                    tts.speak_and_wait(response)
                    face.show_emotion("neutral")
                
    except KeyboardInterrupt:
        face.show_emotion("sleeping")
        tts.speak("Shutting down.")
        print("\n\n  👋 JARVIS: Shutting down.")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
