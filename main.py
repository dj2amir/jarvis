#!/usr/bin/env python3
"""
JARVIS — Self-Evolving AI Assistant
Main entry point.
JARVIS is self-healing: auto-installs missing deps on first run.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    # ── Self-healing bootstrap (runs first, before any imports) ──
    from core.bootstrap import get_bootstrap
    bootstrap = get_bootstrap()
    if not bootstrap.is_complete():
        bootstrap.check_and_install()

    from core.settings import Settings
    from core.face import Face
    from core.stt import STT
    from core.tts import TTS
    from core.brain import Brain
    from core.memory import Memory
    from core.wake_word import WakeWordEngine
    from core.vision import is_available as vision_available, available_strategy as vision_strategy
    from core.vision import is_webcam_available
    import actions as jarvis_actions

    settings = Settings()
    face = Face(settings)
    memory = Memory(settings)
    stt = STT(settings)
    tts = TTS(settings, face=face)
    brain = Brain(settings, face=face, memory=memory)
    wake = WakeWordEngine(settings, face=face)
    
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
    
    # Show feature status
    features = bootstrap.feature_status()
    avail = [f"{n.upper()}" for n, s in features.items() if s.get("installed")]
    if avail:
        print(f"  🔧 Features: {' · '.join(avail)}")
    missing_tiers = [n for n, s in features.items() if not s.get("installed") and not s.get("required")]
    if missing_tiers:
        print(f"  💡 Optional: {' · '.join(missing_tiers)} (auto-installs when needed)")
    
    wake_mode = "Porcupine" if wake.mode == "porcupine" else "Voice-Energy"
    if wake.enabled:
        print(f"  🔊 Wake word: Active (mode: {wake_mode})")
    else:
        print("  🔊 Wake word: Disabled (enable in config/settings.yaml)")
    
    # Show vision status
    if vision_available():
        print(f"  📸 Vision: Ready ({vision_strategy()})")
    else:
        print("  📸 Vision: Not available (install: sudo apt install gnome-screenshot)")
    
    if is_webcam_available():
        print("  📷 Webcam: Ready")
    else:
        print("  📷 Webcam: Not available (install: pip install opencv-python)")
    
    # Show available tools
    tools_count = len(jarvis_actions.get_all_tools())
    print(f"  🔧 Tools: {tools_count} available ({', '.join(jarvis_actions._MODULES.keys())})")

    print()
    print("  Commands:")
    print("    <ask anything>    — JARVIS thinks and responds")
    print("    remember that ... — JARVIS remembers a fact")
    print("    /recall <query>   — Search JARVIS's memories")
    print("    /listen           — Record microphone")
    print("    /see              — Take a screenshot (JARVIS describes it)")
    print("    /cam              — Take a webcam photo (JARVIS describes it)")
    print("    /do <name> <args> — Run an action/tool")
    print("    /tools            — List all available tools")
    print("    /face             — Show face demo")
    print("    /wake             — Toggle wake word on/off")
    print("    /deps             — Check/install dependencies")
    print("    /memory           — Show memory stats")
    print("    /status           — Show feature status")
    print("    /exit             — Quit")
    print()
    
    memory.log_event("milestone", "JARVIS started", success=True)

    # ── Wake word handler (closure over modules in main scope) ─────
    # Must be defined BEFORE it's referenced by wake.start() below.
    def _handle_wake_command():
        """Full voice interaction cycle: listen → think → speak.

        Runs in the wake word listener thread.  All JARVIS modules are
        designed for single-thread access; the face uses terminal writes
        which are safe under CPython's GIL for short bursts.
        """
        memory.log_event("wake_word", "Wake word detected", success=True)
        face.listen_start()

        print("\n  🎤 Listening for command...")
        text = stt.listen(timeout=10)

        if text:
            print(f"  🎤 You said: {text}")
            face.think()
            memory.add_conversation("user", text)

            # Non-streaming for voice — full response before speaking
            response = brain.think(text, stream=False)

            if response:
                print(f"\n  JARVIS: {response}")
                face.speak_start()
                tts.speak_and_wait(response)
                memory.add_conversation("assistant", response)
                memory.log_event("interaction", f"Spoken command: {text[:50]}...",
                                 success=True)
        else:
            print("  No command detected.")
            tts.speak("I didn't catch that. Try again.")

        # Return to idle
        face.show_emotion("sleeping")

    # ── Start wake word listener ────────────────────────────────────
    # WakeWordEngine uses its own arecord pipe (not sounddevice),
    # so it can work even when STT's PortAudio-based capture is unavailable.
    if wake.enabled:
        face.show_emotion("sleeping")
        if stt.is_available():
            print("  🎤 Microphone: Ready (via sounddevice)")
        else:
            print("  🎤 Microphone: arecord fallback active")
        print("  😴 JARVIS sleeping — say 'Hey JARVIS' to wake me!")
        memory.log_event("milestone", "Wake word listening started", success=True)
        wake.start(on_wake=_handle_wake_command)
    else:
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
            
            elif lower == "/tools":
                print(f"\n  {jarvis_actions.list_tools()}")

            elif lower.startswith("/do "):
                # Parse /do <name> [pos_arg1 pos_arg2] [key=value ...]
                parts = cmd[4:].split()
                if not parts:
                    print("  Usage: /do <tool_name> [args...] [key=value ...]")
                    print("  Example: /do open_app firefox")
                else:
                    tool_name = parts[0]
                    kwargs = {}
                    pos_args = []
                    for p in parts[1:]:
                        if "=" in p:
                            k, v = p.split("=", 1)
                            kwargs[k] = v
                        else:
                            pos_args.append(p)
                    # Auto-assign positional args to tool parameters
                    if pos_args:
                        for tool in jarvis_actions.get_all_tools():
                            if tool["name"] == tool_name:
                                param_names = list(tool.get("parameters", {}).keys())
                                for i, val in enumerate(pos_args):
                                    if i < len(param_names):
                                        kwargs[param_names[i]] = val
                                break
                    print(f"  🔧 Running: {tool_name}({kwargs})")
                    result = jarvis_actions.execute(tool_name, **kwargs)
                    print(f"  Result: {result}")

            elif lower == "/face":
                face.animate_demo()
            
            elif lower == "/wake":
                if wake.enabled:
                    if wake.is_active:
                        wake.stop()
                        print("  🔇 Wake word: OFF")
                        face.show_emotion("neutral")
                    else:
                        face.show_emotion("sleeping")
                        wake.start(on_wake=lambda: _handle_wake_command(
                            face, stt, brain, tts, memory))
                        print("  🔊 Wake word: ON — say 'Hey JARVIS'")
                else:
                    print("  ⚠️ Wake word is disabled in config/settings.yaml")
            
            elif lower == "/see":
                from core.vision import capture_screen, is_available as vis_ok
                if not vis_ok():
                    print("  📸 Screen capture not available.")
                    print("     Install: sudo apt install gnome-screenshot")
                else:
                    face.think()
                    print("  📸 Capturing screen...")
                    
                    img = capture_screen()
                    if img is None:
                        print("  ❌ Screenshot failed.")
                        face.show_emotion("neutral")
                    else:
                        from datetime import datetime
                        pics_dir = os.path.expanduser("~/Pictures/jarvis")
                        os.makedirs(pics_dir, exist_ok=True)
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        save_path = os.path.join(pics_dir, f"screenshot_{ts}.png")
                        
                        from PIL import Image
                        save_img = img.copy()
                        save_img.thumbnail((1920, 1080), Image.LANCZOS)
                        save_img.save(save_path, format="PNG")
                        print(f"  💾 Saved: {save_path}")
                        
                        print("  🧠 Analyzing screen with vision model...")
                        from io import BytesIO
                        import base64
                        thumb = img.copy()
                        thumb.thumbnail((1280, 720), Image.LANCZOS)
                        buf = BytesIO()
                        thumb.save(buf, format="JPEG", quality=75)
                        image_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
                        
                        response = brain.think_with_image(
                            "Describe what you see on this screen in detail. "
                            "What applications are open? What is the user looking at?",
                            image_b64
                        )
                        if response:
                            print(f"\n  JARVIS: {response}")
                            tts.speak(response)
                        else:
                            print("  ⚠️ Vision model didn't respond — your LLM may not support images.")
                            face.show_emotion("neutral")

            elif lower == "/cam":
                from core.vision import capture_webcam, is_webcam_available as cam_ok
                from PIL import Image
                if not cam_ok():
                    print("  📷 Webcam not available.")
                    print("     Install: pip install opencv-python")
                else:
                    face.think()
                    print("  📷 Capturing webcam...")
                    
                    img = capture_webcam()
                    if img is None:
                        print("  ❌ Webcam capture failed — check camera connection.")
                        face.show_emotion("neutral")
                    else:
                        from datetime import datetime
                        pics_dir = os.path.expanduser("~/Pictures/jarvis")
                        os.makedirs(pics_dir, exist_ok=True)
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        save_path = os.path.join(pics_dir, f"webcam_{ts}.png")
                        img.save(save_path, format="PNG")
                        print(f"  💾 Saved: {save_path}")
                        
                        print("  🧠 Analyzing webcam with vision model...")
                        from io import BytesIO
                        import base64
                        thumb = img.copy()
                        thumb.thumbnail((640, 480), Image.LANCZOS)
                        buf = BytesIO()
                        thumb.save(buf, format="JPEG", quality=75)
                        image_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
                        
                        response = brain.think_with_image(
                            "Describe what you see in this webcam image. "
                            "Is there a person? What are they doing? What's the setting?",
                            image_b64
                        )
                        if response:
                            print(f"\n  JARVIS: {response}")
                            tts.speak(response)
                        else:
                            print("  ⚠️ Vision model didn't respond — your LLM may not support images.")
                            face.show_emotion("neutral")
            
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
                print("    /see              — Take a screenshot")
                print("    /cam              — Take a webcam photo")
                print("    /do <name> <args> — Run an action/tool")
                print("    /tools            — List all available tools")
                print("    /face             — Show face demo")
                print("    /wake             — Toggle wake word on/off")
                print("    /deps             — Auto-install missing dependencies")
                print("    /status           — Show feature availability")
                print("    /memory           — Show memory stats")
                print("    /exit             — Quit")
            
            elif lower == "/deps":
                print("\n  🔧 Checking dependencies...")
                features = bootstrap.feature_status()
                for name, status in features.items():
                    icon = "✅" if status["installed"] else "⬜"
                    req = "(required)" if status["required"] else "(optional)"
                    print(f"  {icon} {name}: {status['ok']}/{status['total']} {req}")
                print()
                if bootstrap.check_and_install():
                    print("  ✅ All dependencies satisfied!")
                else:
                    print("  ⚠ Some deps could not be installed. Check logs.")
            
            elif lower == "/status":
                print("\n  📊 JARVIS Feature Status:")
                features = bootstrap.feature_status()
                for name, status in features.items():
                    icon = "✅" if status["installed"] else "⬜"
                    req = "(required)" if status["required"] else "(optional)"
                    print(f"  {icon} {name}: {status['description']}")
                    print(f"     {status['ok']}/{status['total']} packages installed {req}")
            
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
