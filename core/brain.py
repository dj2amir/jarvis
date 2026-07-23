"""
Brain Module — JARVIS's Reasoning Engine.

Connects to ANY AI provider using the OpenAI SDK:
  - LM Studio (local):  http://localhost:1234/v1
  - Ollama (local):     http://localhost:11434/v1
  - OpenAI API:         https://api.openai.com/v1
  - Anthropic:          https://api.anthropic.com/v1
  - Any OpenAI-compatible endpoint

Features:
  - Multi-provider with automatic fallback
  - Conversation history management
  - Streaming responses
  - JARVIS personality integration
"""

import json
import os
import re
import time
import threading
from typing import Optional, Callable, List, Dict
from pathlib import Path


class Brain:
    """JARVIS's reasoning engine."""

    def __init__(self, settings=None, face=None, memory=None):
        self.settings = settings or {}
        self.face = face
        self.memory = memory  # Memory system (optional)
        
        # Check openai package availability once
        self._openai_available = self._check_openai()
        
        # Load provider configuration
        self._providers = self._load_providers()
        self._primary_config = self._providers.get("primary", {})
        self._has_config = bool(self._primary_config.get("base_url") or self._primary_config.get("api_key"))
        
        # Conversation state
        self.conversation_history: List[Dict] = []
        self.max_history_tokens = self.settings.get("brain.max_history_tokens", 6000)
        
        # ── Tool-calling setup (must happen BEFORE _build_system_prompt) ──
        self._tools_catalog = self._build_tools_catalog()
        self._max_tool_rounds = 3
        
        self.system_prompt = self._build_system_prompt()
        self._is_thinking = False
        
        if self._openai_available and self._has_config:
            model = self._primary_config.get("model", "unknown")
            print(f"🧠 Brain ready | Model: {model}")
        elif not self._openai_available:
            print("⚠️ Brain: openai package not installed (pip install openai)")
        else:
            print("⚠️ Brain: No provider configured in config/providers.yaml")
    
    def _check_openai(self) -> bool:
        try:
            import openai
            return True
        except ImportError:
            return False
    
    def _load_providers(self):
        path = Path(__file__).parent.parent / "config" / "providers.yaml"
        if not path.exists():
            return {}
        import yaml
        with open(path) as f:
            config = yaml.safe_load(f) or {}
        self._interpolate_env(config)
        return config
    
    def _interpolate_env(self, obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    self._interpolate_env(value)
                elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    obj[key] = os.environ.get(env_var, "")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, (dict, list)):
                    self._interpolate_env(item)
                elif isinstance(item, str) and item.startswith("${") and item.endswith("}"):
                    env_var = item[2:-1]
                    obj[i] = os.environ.get(env_var, "")
    
    def _build_system_prompt(self) -> str:
        try:
            from core.personality import Personality
            base = Personality().build_system_prompt()
        except Exception:
            base = "You are JARVIS, a helpful AI assistant. Be concise, witty, and helpful."
        
        # Append tool-calling instructions
        tools_prompt = self._build_tools_prompt()
        if tools_prompt:
            base += tools_prompt
        
        return base
    
    # ────────────────────────────────────────────────────────────
    # Tool-calling system
    # ────────────────────────────────────────────────────────────

    def _build_tools_catalog(self) -> List[Dict]:
        """Build a flat list of tool definitions for the LLM."""
        try:
            import actions as jarvis_actions
            return jarvis_actions.get_all_tools()
        except Exception:
            return []

    def _build_tools_prompt(self) -> str:
        """Generate the tools section of the system prompt."""
        catalog = self._tools_catalog
        if not catalog:
            return ""

        lines = [
            "\n\n## Available Tools",
            "You have access to tools that let you take real actions. When you need",
            "to open an app, search the web, get the time, read/write files, or run",
            "a shell command, you MUST call the appropriate tool instead of saying",
            "you can't do it.",
            "",
            "To call a tool, output exactly this format:",
            '<tool_call>{"name": "tool_name", "arguments": {"arg1": "value"}}</tool_call>',
            "",
            "You can call multiple tools with multiple <tool_call> blocks.",
            "You may write natural language before or after the tool calls.",
            "After calling a tool, the result will be fed back to you so you can",
            "weave it into a natural response.",
            "",
            "Tool list:",
        ]

        for tool in catalog:
            params = ", ".join(tool.get("parameters", {}).keys())
            desc = tool.get("description", "")
            lines.append(f"- {tool['name']}({params}): {desc}")

        return "\n".join(lines)

    def _parse_tool_calls(self, text: str) -> List[Dict]:
        """Extract <tool_call> JSON blocks from LLM output.

        Returns list of {name, arguments} dicts.
        """
        pattern = r'<tool_call>(.*?)</tool_call>'
        calls = []
        for match in re.finditer(pattern, text, re.DOTALL):
            try:
                parsed = json.loads(match.group(1).strip())
                if "name" in parsed:
                    calls.append({
                        "name": parsed["name"],
                        "arguments": parsed.get("arguments", {}),
                    })
            except json.JSONDecodeError:
                continue
        return calls

    def _execute_tool_calls(self, calls: List[Dict]) -> List[str]:
        """Execute parsed tool calls and return results."""
        import actions as jarvis_actions

        results = []
        for call in calls:
            name = call["name"]
            args = call["arguments"]
            try:
                result = jarvis_actions.execute(name, **args)
                results.append(f"[{name}] {result}")
            except Exception as e:
                results.append(f"[{name}] Error: {e}")
        return results

    def _strip_tool_calls(self, text: str) -> str:
        """Remove <tool_call> blocks from text, leaving natural-language portion."""
        return re.sub(r'<tool_call>.*?</tool_call>', '', text, flags=re.DOTALL).strip()

    def _tool_loop(self, user_input: str, stream: bool, on_token) -> Optional[str]:
        """Run the think → tool-call → feedback loop (up to _max_tool_rounds)."""
        current_input = user_input
        all_tool_results = []
        last_natural = ""

        for round_num in range(self._max_tool_rounds):
            try:
                response = self._call_llm(self._primary_config, current_input, stream, on_token)
            except Exception as e:
                if all_tool_results:
                    return "\n".join(all_tool_results) + f"\n\n⚠️ Follow-up failed: {e}"
                return f"⚠️ LLM call failed: {e}"

            if not response:
                return None

            tool_calls = self._parse_tool_calls(response)

            if not tool_calls:
                return response

            # Execute discovered tool calls
            tool_results = self._execute_tool_calls(tool_calls)
            all_tool_results.extend(tool_results)
            last_natural = self._strip_tool_calls(response)

            print(f"  🔧 Tool: {', '.join(t['name'] for t in tool_calls)}")

            # Build feedback for next LLM round
            feedback_lines = [
                "Tool results:",
                *[f"  {r}" for r in tool_results],
                "",
                "Now respond naturally, weaving these results into your answer.",
            ]
            if last_natural:
                feedback_lines.insert(0, f"(Your previous partial response: {last_natural})")

            current_input = "\n".join(feedback_lines)

        # Max rounds exhausted — return results + last natural-language text
        if last_natural:
            return last_natural + "\n\n" + "\n".join(all_tool_results)
        return "\n".join(all_tool_results)

    def is_available(self) -> bool:
        return self._openai_available and self._has_config
    
    def think(self, user_input: str, stream: bool = False,
              on_token: Optional[Callable[[str], None]] = None) -> Optional[str]:
        """Process user input and return JARVIS's response.

        Automatically detects tool calls (<tool_call>) in the LLM response,
        executes them, and feeds results back for a natural summary.
        """
        if not self._openai_available:
            return "I need the openai package. Run: pip install openai"
        if not self._has_config:
            return "I'm not connected to any AI model. Configure config/providers.yaml"
        
        self._is_thinking = True
        if self.face:
            self.face.think()
        
        self._extract_memory(user_input)

        # Run the tool-calling loop (handles both tool calls and plain chat)
        response = self._tool_loop(user_input, stream, on_token)

        if response:
            self._update_history(user_input, response)
            self._store_memory_from_response(user_input, response)

        self._is_thinking = False
        return response
    
    def _call_llm(self, config: dict, user_input: str,
                  stream: bool = False,
                  on_token: Optional[Callable] = None) -> Optional[str]:
        """Call an LLM provider, temporarily clearing proxies."""
        api_key = config.get("api_key", "not-needed")
        base_url = config.get("base_url")
        model = config.get("model", "gpt-4o")
        
        # Build messages with memory context
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Inject memory context between system prompt and conversation
        memory_context = self._get_memory_context(user_input)
        if memory_context:
            messages.append({"role": "system", "content": memory_context})
        
        messages.extend(self.conversation_history[-10:])
        messages.append({"role": "user", "content": user_input})
        
        # Save and clear proxy env vars
        saved_proxies = {
            k: os.environ.pop(k, None)
            for k in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"]
        }
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=stream,
                max_tokens=config.get("max_tokens", 2048),
                temperature=config.get("temperature", 0.7),
            )
            
            if stream:
                full_text = ""
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        token = chunk.choices[0].delta.content
                        full_text += token
                        if on_token:
                            on_token(token)
                return full_text
            else:
                return response.choices[0].message.content
        finally:
            for k, v in saved_proxies.items():
                if v is not None:
                    os.environ[k] = v
    
    def _get_memory_context(self, user_input: str) -> str:
        """Build memory context for LLM injection."""
        if not self.memory or not self.memory.is_enabled:
            return ""
        return self.memory.build_context(user_input)
    
    def _extract_memory(self, user_input: str):
        """Extract and store important information from user input."""
        if not self.memory or not self.memory.is_enabled:
            return
        
        self.memory.add_conversation("user", user_input)
        
        # Store explicit remember commands (flexible matching)
        import re
        lower = user_input.lower().strip()
        
        # Match patterns like:
        #   "remember that I like coffee"
        #   "JARVIS, remember I like coffee"
        #   "don't forget my name is Alex"
        #   "remember: coffee is good"
        patterns = [
            r'remember\s+that\s+(.+)',
            r'(?:please\s+)?remember\s+(?:that\s+)?(.+)',
            r"don't\s+forget\s+(?:that\s+)?(.+)",
            r'remember:\s*(.+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, lower)
            if match:
                fact = match.group(1).strip().strip('.,!?')
                if fact and len(fact) > 3:
                    self.memory.remember(fact, "fact", 0.7)
                    print(f"💾 Remembered: {fact[:80]}...")
                break
    
    def _store_memory_from_response(self, user_input: str, response: str):
        """Store conversation in memory."""
        if not self.memory or not self.memory.is_enabled:
            return
        
        self.memory.add_conversation("assistant", response)
        self.memory.log_event("interaction", f"User asked: {user_input[:50]}...", success=True)
    
    def _update_history(self, user_input: str, response: str):
        """Update conversation history with token management."""
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        total_chars = sum(len(m["content"]) for m in self.conversation_history)
        max_chars = self.max_history_tokens * 4
        while total_chars > max_chars and len(self.conversation_history) > 4:
            self.conversation_history.pop(0)
            self.conversation_history.pop(0)
            total_chars = sum(len(m["content"]) for m in self.conversation_history)
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history.clear()
    
    def switch_model(self, model_name: str):
        if self._primary_config:
            self._primary_config["model"] = model_name
            print(f"🔄 Switched to model: {model_name}")
    
    @property
    def is_thinking(self) -> bool:
        return self._is_thinking
