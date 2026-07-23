#!/usr/bin/env python3
"""
JARVIS — Self-Evolving AI Assistant
Main entry point.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.face import Face


def main():
    face = Face()
    
    print("\n" + "=" * 50)
    print("  🤖 JARVIS — Self-Evolving AI Assistant")
    print("=" * 50)
    print("  Say 'Hey JARVIS' to wake me up.")
    print("  Or type a command below.")
    print("  Press Ctrl+C to exit.")
    print("=" * 50 + "\n")
    
    face.show_emotion("neutral")
    
    try:
        while True:
            # For now, show face demo
            # TODO: Integrate STT (Tier 1), Brain (Tier 2), TTS (Tier 1)
            cmd = input("\n  > ").strip().lower()
            
            if cmd in ("exit", "quit", "bye"):
                face.show_emotion("sleeping")
                print("\n  JARVIS: Going offline. Goodbye.")
                break
            elif cmd == "face":
                face.animate_demo()
            elif cmd == "happy":
                face.show_emotion("happy")
            elif cmd == "thinking":
                face.show_emotion("thinking")
            elif cmd == "help":
                print("  Commands: face (demo), happy, thinking, exit")
            else:
                face.show_emotion("listening")
                face.show_emotion("thinking")
                face.show_emotion("speaking")
                face.show_emotion("neutral")
                
    except KeyboardInterrupt:
        face.show_emotion("sleeping")
        print("\n\n  👋 JARVIS: Shutting down.")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
