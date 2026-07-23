#!/usr/bin/env python3
"""Quick test — just run it."""
import sys
sys.path.insert(0, ".")
from core.face import Face

face = Face()
print("\n=== TESTING FACE ENGINE ===")
face.animate_demo()
print("\n=== ALL GOOD ===")
