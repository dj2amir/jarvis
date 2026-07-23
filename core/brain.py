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
            return Personality().build_system_prompt()
        except Exception:
            return "You are JARVIS, a helpful AI assistant. Be concise, witty, and helpful."
    
    def is_available(self) -> bool:
        return self._openai_available and self._has_config
    
    def think(self, user_input: str, stream: bool = False,
              on_token: Optional[Callable[[str], None]] = None) -> Optional[str]:
        """Process user input and return JARVIS's response."""
        if not self._openai_available:
            return "I need the openai package. Run: pip install openai"
        if not self._has_config:
            return "I'm not connected to any AI model. Configure config/providers.yaml"
        
        self._is_thinking = True
        if self.face:
            self.face.think()
        
        self._extract_memory(user_input)
        
        # Try primary, then fallbacks
        providers_to_try = [self._primary_config]
        for fb in self._providers.get("fallback_providers", []):
            providers_to_try.append(fb)
        
        last_error = None
        for config in providers_to_try:
            try:
                response = self._call_llm(config, user_input, stream, on_token)
                if response:
                    self._update_history(user_input, response)
                    self._store_memory_from_response(user_input, response)
                    self._is_thinking = False
                    return response
            except Exception as e:
                last_error = e
                print(f"⚠️ Provider '{config.get('model')}' failed: {e}")
                continue
        
        self._is_thinking = False
        return f"All providers failed. Error: {last_error}"
    
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
