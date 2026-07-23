#!/usr/bin/env python3
"""
JARVIS Face Demo — See the animated face in your terminal!
Run: python test_face.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.face import Face, Emotion

def show_all_styles():
    """Demo all face styles and emotions."""
    face = Face()
    
    print("\n" + "=" * 50)
    print("  🤖 JARVIS FACE DEMONSTRATION")
    print("=" * 50)
    print("\nPress Ctrl+C to exit at any time.\n")
    
    import time
    
    # === ROBOT STYLE ===
    face.set_style("robot")
    robot_emotions = [
        ("neutral",   1.0,  "Default state — waiting for input"),
        ("happy",     1.0,  "You greeted JARVIS or told a joke"),
        ("thinking",  1.5,  "Processing a complex question"),
        ("listening", 0.8,  "Microphone active, hearing you speak"),
        ("speaking",  1.5,  "Responding to your question"),
        ("surprised", 0.8,  "Unexpected input detected"),
        ("sad",       0.8,  "Something went wrong"),
        ("angry",     0.6,  "System error detected"),
        ("sleeping",  1.5,  "Idle mode — awaiting wake word"),
        ("error",     1.0,  "Critical failure"),
    ]
    
    print("─" * 50)
    print("  STYLE: Robot (Classic)")
    print("─" * 50)
    
    for emotion, duration, description in robot_emotions:
        face.show_emotion(emotion)
        print(f"\n  😶 {emotion.upper():12s} — {description}")
        time.sleep(duration)
    
    # === ANONYMOUS STYLE ===
    face.set_style("anonymous")
    anon_emotions = ["neutral", "happy", "thinking", "surprised", "speaking", "error"]
    
    print("\n" + "─" * 50)
    print("  STYLE: Anonymous Mask")
    print("─" * 50)
    
    for emotion in anon_emotions:
        face.show_emotion(emotion)
        print(f"\n  🎭 {emotion.upper():12s}")
        time.sleep(1.0)
    
    # === MINIMAL STYLE ===
    face.set_style("minimal")
    minimal_emotions = ["neutral", "happy", "sad", "angry", "thinking", "listening", "speaking", "sleeping", "error"]
    
    print("\n" + "─" * 50)
    print("  STYLE: Minimal")
    print("─" * 50)
    
    for emotion in minimal_emotions:
        face.show_emotion(emotion)
        print(f"\n  ● {emotion.upper():12s}")
        time.sleep(1.0)
    
    # === FINAL ===
    face.set_style("robot")
    face.show_emotion("neutral")
    print("\n" + "=" * 50)
    print("  ✅ Face engine ready.")
    print("  JARVIS is online and waiting.")
    print("=" * 50)
    print()


def interactive_mode():
    """Let user type emotions to see them."""
    face = Face()
    
    print("\n" + "=" * 50)
    print("  🎮 JARVIS FACE — INTERACTIVE MODE")
    print("=" * 50)
    print("  Type an emotion to see it on the face.")
    print("  Emotions: neutral, happy, sad, angry, surprised,")
    print("            thinking, listening, speaking, sleeping, error")
    print("  Styles:   /robot, /anonymous, /minimal")
    print("  Commands: /demo (show all), /quit")
    print("=" * 50)
    
    try:
        while True:
            cmd = input("\n  > ").strip().lower()
            
            if cmd == "/quit":
                break
            elif cmd == "/demo":
                show_all_styles()
                break
            elif cmd == "/robot":
                face.set_style("robot")
                print("  Style → Robot")
            elif cmd == "/anonymous":
                face.set_style("anonymous")
                print("  Style → Anonymous Mask")
            elif cmd == "/minimal":
                face.set_style("minimal")
                print("  Style → Minimal")
            elif cmd:
                face.show_emotion(cmd)
    except KeyboardInterrupt:
        pass
    
    print("\n👋 Goodbye!")


if __name__ == "__main__":
    if "--interactive" in sys.argv or "-i" in sys.argv:
        interactive_mode()
    else:
        show_all_styles()
