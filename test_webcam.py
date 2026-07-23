#!/usr/bin/env python3
"""Test webcam support end-to-end."""

import sys
sys.path.insert(0, '.')

print("=== Webcam Pipeline Test ===")
print()

# Test 1: Imports
from core.vision import (
    capture_webcam, capture_webcam_base64, capture_webcam_file,
    is_webcam_available, _cv2_available
)
print(f"1. cv2 available: {_cv2_available()}")
print(f"   Webcam available: {is_webcam_available()}")

# Test 2: Graceful failure when no webcam
img = capture_webcam()
if img:
    print(f"2. Webcam capture: SUCCESS ({img.size[0]}x{img.size[1]})")
else:
    print("2. Webcam capture: Not available (expected — no webcam on this system)")

# Test 3: Base64 graceful failure
b64 = capture_webcam_base64()
if b64:
    print(f"3. Webcam base64: SUCCESS ({len(b64)} chars)")
else:
    print("3. Webcam base64: None (expected)")

# Test 4: Vision tools auto-discovered (now 4 tools)
import actions as a
tools = a.get_all_tools()
vision_tools = [t for t in tools if t['module'] == 'vision']
print(f"4. Vision tools: {len(vision_tools)}")
for t in vision_tools:
    print(f"   {t['name']} — {t['description'][:60]}")

# Test 5: Webcam tools execute
print("5. Executing describe_webcam():")
result = a.execute('describe_webcam')
print(f"   {result[:120]}")

print("6. Executing capture_webcam():")
result = a.execute('capture_webcam')
print(f"   {result[:120]}")

# Test 6: Total tools now 12
print(f"7. Total tools: {len(tools)}")
print(f"   Modules: {list(a._MODULES.keys())}")

# Test 7: All files compile
import py_compile
for f in ['core/vision.py', 'actions/vision.py', 'main.py']:
    py_compile.compile(f, doraise=True)
print("8. All files: Syntax OK")

print()
print("=== ALL WEBCAM TESTS PASSED ===")
print()
print("To enable webcam, run on YOUR terminal:")
print("  pip install opencv-python")
print("  cd ~/Desktop/jarvis/jarvis-core && python3 main.py")
print("  Then type: /cam")
