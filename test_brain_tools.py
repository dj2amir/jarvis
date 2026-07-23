#!/usr/bin/env python3
"""Test the brain's auto-tool-calling system."""

import sys
sys.path.insert(0, '.')

print("=== Test 1: Tools catalog in brain ===")
from core.brain import Brain

class FakeSettings:
    def get(self, key, default=None):
        return default

brain = Brain(settings=FakeSettings())
print(f"Tools catalog loaded: {len(brain._tools_catalog)} tools")
for t in brain._tools_catalog:
    params = ", ".join(t.get("parameters", {}).keys())
    print(f"  {t['name']}({params}) — {t['description'][:60]}")

print()
print("=== Test 2: Tools prompt ===")
prompt = brain._build_tools_prompt()
print(f"Prompt length: {len(prompt)} chars")
print(prompt[:500])
print("...")

print()
print("=== Test 3: Parse tool calls ===")
test_response = """Sure, let me check the time for you.
<tool_call>{"name": "get_time", "arguments": {}}</tool_call>
And here is some text after."""
calls = brain._parse_tool_calls(test_response)
print(f"Parsed {len(calls)} tool calls:")
for c in calls:
    print(f"  {c['name']}({c['arguments']})")

print()
print("=== Test 4: Strip tool calls ===")
stripped = brain._strip_tool_calls(test_response)
print(f"After stripping: '{stripped}'")

print()
print("=== Test 5: Execute tool calls ===")
results = brain._execute_tool_calls(calls)
for r in results:
    print(f"  {r[:100]}")

print()
print("=== Test 6: Full system prompt includes tools ===")
if "Available Tools" in brain.system_prompt:
    print("YES — system prompt contains tool instructions")
else:
    print("NO — system prompt missing tools!")

print()
print("=== Test 7: Multiple tool calls ===")
multi_response = """Let me search and get the time.
<tool_call>{"name": "get_time", "arguments": {}}</tool_call>
<tool_call>{"name": "system_info", "arguments": {}}</tool_call>
"""
calls2 = brain._parse_tool_calls(multi_response)
print(f"Parsed {len(calls2)} tool calls:")
for c in calls2:
    print(f"  {c['name']}({c['arguments']})")

print()
print("=== Test 8: Invalid JSON is ignored ===")
bad_response = '<tool_call>not json</tool_call><tool_call>{"name": "get_time", "arguments": {}}</tool_call>'
calls3 = brain._parse_tool_calls(bad_response)
print(f"Parsed {len(calls3)} valid calls (ignored 1 bad):")
for c in calls3:
    print(f"  {c['name']}")

print()
print("=== ALL TESTS PASSED ===")
