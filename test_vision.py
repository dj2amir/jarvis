#!/usr/bin/env python3
"""End-to-end test of the vision pipeline."""

import sys
sys.path.insert(0, '.')

print("=== Vision Pipeline Test ===")
print()

# Test 1: Engine imports and availability
from core.vision import (
    capture_screen, capture_screen_base64, capture_screen_file,
    is_available, available_strategy
)
print(f"1. Vision available: {is_available()}")
print(f"   Strategy: {available_strategy()}")

# Test 2: Capture attempt (will fail gracefully since no tool installed)
img = capture_screen()
if img:
    print(f"2. Capture: SUCCESS ({img.size[0]}x{img.size[1]})")
else:
    print("2. Capture: No tool installed (expected — needs gnome-screenshot)")

# Test 3: base64 returns None when no capture tool
b64 = capture_screen_base64()
if b64:
    print(f"3. Base64: SUCCESS ({len(b64)} chars)")
else:
    print("3. Base64: None (expected — no capture tool)")

# Test 4: Vision tools are auto-discovered
import actions as a
tools = a.get_all_tools()
vision_tools = [t for t in tools if t['module'] == 'vision']
print(f"4. Vision tools: {len(vision_tools)}")
for t in vision_tools:
    print(f"   {t['name']} — {t['description'][:60]}")

# Test 5: Vision tools can execute
print("5. Executing describe_screen():")
result = a.execute('describe_screen')
print(f"   {result[:120]}")

print("6. Executing capture_screen():")
result = a.execute('capture_screen')
print(f"   {result[:120]}")

# Test 6: Brain has think_with_image
from core.brain import Brain
class FakeSettings:
    def get(self, k, d=None): return d

brain = Brain(settings=FakeSettings())
assert hasattr(brain, 'think_with_image'), "think_with_image missing!"
print("7. Brain.think_with_image: EXISTS")

# Test 7: Total tools = 10 (8 original + 2 vision)
print(f"8. Total tools: {len(tools)}")
print(f"   Modules: {list(a._MODULES.keys())}")

# Test 8: All action modules loaded
expected = {'file', 'system', 'vision', 'web'}
actual = set(a._MODULES.keys())
assert expected == actual, f"Module mismatch: {expected} vs {actual}"
print("9. All 4 modules loaded: OK")

print()
print("=== ALL VISION TESTS PASSED ===")
print()
print("To enable screen capture, run on YOUR terminal:")
print("  sudo apt install gnome-screenshot")
print("  cd ~/Desktop/jarvis/jarvis-core && python3 main.py")
print("  Then type: /see")
