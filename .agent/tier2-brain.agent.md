# Tier 2 — Brain & Reasoning Engine

> **Goal:** JARVIS can think, reason, and connect to ANY AI service with ANY model.
> **Est. time:** 4-6 hours · **Depends on:** Tier 1, settings.agent.md

## ✅ Checklist
- [ ] `core/brain.py` — Universal LLM provider abstraction
- [ ] Provider: OpenAI (GPT-4o, GPT-5, o3, etc.)
- [ ] Provider: Anthropic (Claude 3.5, Claude 4)
- [ ] Provider: Google (Gemini 1.5, Gemini 2.0)
- [ ] Provider: Ollama (any local model — Llama 3, Qwen, Mistral, etc.)
- [ ] Provider: OpenRouter / custom OpenAI-compatible endpoints
- [ ] Provider: Custom API (any REST endpoint)
- [ ] Dynamic model switching at runtime
- [ ] Automatic fallback between providers
- [ ] Conversation history management (token-aware)
- [ ] System prompt with JARVIS persona
- [ ] Streaming responses (token-by-token)
- [ ] Tool/function calling support
- [ ] `core/personality.py` — Configurable character traits
- [ ] Test: "JARVIS works with at least 2 different providers"

---

## 📄 core/brain.py — Universal LLM Engine

### The Universal Provider Interface

Every provider must implement this interface:

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Callable, AsyncIterator


class LLMProvider(ABC):
    """Abstract base for any AI model provider."""
    
    @abstractmethod
    def chat(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        stream: bool = False,
        on_token: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Send messages to the model and get a response."""
        pass
    
    @abstractmethod
    def get_model_list(self) -> List[str]:
        """Return list of available models for this provider."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name."""
        pass
```

### Provider Implementations

```python
class OpenAIProvider(LLMProvider):
    """OpenAI / Azure OpenAI / Any OpenAI-compatible API."""
    
    def __init__(self, config: dict):
        import openai
        self._client = openai.OpenAI(
            api_key=config.get("api_key"),
            base_url=config.get("base_url"),  # Custom endpoint!
        )
        self.model = config.get("model", "gpt-4o")
    
    def chat(self, messages, tools=None, stream=False, on_token=None):
        kwargs = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }
        if tools:
            kwargs["tools"] = tools
        
        response = self._client.chat.completions.create(**kwargs)
        
        if stream:
            full_text = ""
            for chunk in response:
                delta = chunk.choices[0].delta.content or ""
                full_text += delta
                if on_token:
                    on_token(delta)
            return full_text
        else:
            return response.choices[0].message.content


class AnthropicProvider(LLMProvider):
    """Anthropic Claude."""

    def __init__(self, config: dict):
        import anthropic
        self._client = anthropic.Anthropic(api_key=config.get("api_key"))
        self.model = config.get("model", "claude-sonnet-4-20250514")
    
    def chat(self, messages, tools=None, stream=False, on_token=None):
        # Claude uses a different API format
        # Convert from OpenAI format to Anthropic format
        system_msg = None
        if messages and messages[0]["role"] == "system":
            system_msg = messages.pop(0)["content"]
        
        kwargs = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "max_tokens": 4096,
            "stream": stream,
        }
        if system_msg:
            kwargs["system"] = system_msg
        if tools:
            kwargs["tools"] = self._convert_tools(tools)
        
        with self._client.messages.stream(**kwargs) as stream_obj:
            return self._handle_stream(stream_obj, on_token)


class GoogleProvider(LLMProvider):
    """Google Gemini."""

    def __init__(self, config: dict):
        import google.generativeai as genai
        genai.configure(api_key=config.get("api_key"))
        self.model_name = config.get("model", "gemini-2.0-flash")
        self.model = genai.GenerativeModel(self.model_name)
    
    # ... implementation


class OllamaProvider(LLMProvider):
    """Local Ollama — any model running locally."""
    
    def __init__(self, config: dict):
        import ollama
        self._client = ollama
        self.model = config.get("model", "llama3.2")
        self.base_url = config.get("base_url", "http://localhost:11434")
    
    def chat(self, messages, tools=None, stream=False, on_token=None):
        # Ollama has OpenAI-compatible API
        import requests
        # ... implementation
```

### Ollama Provider — Special Handling

```python
class OllamaProvider(LLMProvider):
    """Local Ollama — any model running locally."""
    
    def __init__(self, config: dict):
        self.model = config.get("model", "llama3.2")
        self.base_url = config.get("base_url", "http://localhost:11434")
        self._available_models = None
    
    def _ensure_model(self):
        """Check model exists locally, try to pull if not."""
        import requests
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            models = [m["name"] for m in resp.json().get("models", [])]
            
            # Check if model exists (with or without :latest)
            if self.model not in models and f"{self.model}:latest" not in models:
                print(f"📥 Model '{self.model}' not found locally. Pulling...")
                # Trigger pull in background
                requests.post(f"{self.base_url}/api/pull", 
                            json={"name": self.model}, timeout=1)
                return False
            return True
        except:
            return False
    
    def chat(self, messages, tools=None, stream=False, on_token=None):
        import requests
        
        # Ollama uses OpenAI-compatible API
        url = f"{self.base_url}/v1/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }
        
        if stream:
            response = requests.post(url, json=payload, stream=True, timeout=60)
            full_text = ""
            for line in response.iter_lines():
                if line:
                    import json
                    chunk = json.loads(line)
                    delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    full_text += delta
                    if on_token:
                        on_token(delta)
            return full_text
        else:
            response = requests.post(url, json=payload, timeout=60)
            return response.json()["choices"][0]["message"]["content"]
    
    def get_model_list(self):
        import requests
        resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
        return [m["name"] for m in resp.json().get("models", [])]
    
    @property
    def provider_name(self):
        return f"Ollama ({self.model})"
```

### Provider Factory

```python
class ProviderFactory:
    """Creates the right provider based on configuration."""
    
    PROVIDERS = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
        "ollama": OllamaProvider,
        "openrouter": OpenAIProvider,  # OpenAI-compatible!
        "custom": OpenAIProvider,      # Any OpenAI-compatible endpoint
    }
    
    @classmethod
    def create(cls, provider_name: str, config: dict) -> LLMProvider:
        provider_class = cls.PROVIDERS.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")
        return provider_class(config)
```

### The Brain Class

```python
class Brain:
    """
    JARVIS's reasoning engine.
    Supports any provider, any model, with automatic fallback.
    """
    
    def __init__(self, settings):
        self.settings = settings
        
        # Primary provider
        primary_config = settings.get_provider_config("primary")
        self.primary = ProviderFactory.create(
            primary_config["provider"],
            primary_config
        )
        
        # Fallback providers (optional)
        self.fallbacks = []
        for fb_config in settings.get("fallback_providers", []):
            provider = ProviderFactory.create(
                fb_config["provider"],
                fb_config
            )
            self.fallbacks.append(provider)
        
        self.system_prompt = settings.get_system_prompt()
        self.conversation_history = []
        self.max_history_tokens = settings.get("max_history_tokens", 6000)
    
    def think(
        self,
        user_input: str,
        stream: bool = False,
        on_token: Optional[Callable] = None,
    ) -> str:
        """
        Process user input and return JARVIS's response.
        Falls back through providers if primary fails.
        """
        messages = self._build_messages(user_input)
        last_error = None
        
        # Try primary first
        providers = [self.primary] + self.fallbacks
        for provider in providers:
            try:
                response = provider.chat(
                    messages,
                    tools=self._get_available_tools(),
                    stream=stream,
                    on_token=on_token,
                )
                self._update_history(user_input, response)
                return response
            except Exception as e:
                last_error = e
                print(f"⚠️ {provider.provider_name} failed: {e}")
                print(f"↪ Failing over to next provider...")
                continue
        
        raise RuntimeError(f"All providers failed. Last error: {last_error}")
    
    def switch_provider(self, provider_name: str, model: str = None):
        """Switch primary provider at runtime."""
        config = self.settings.get_provider_config(provider_name)
        if model:
            config["model"] = model
        self.primary = ProviderFactory.create(provider_name, config)
    
    def _build_messages(self, user_input: str) -> list:
        """Build message list with system prompt + history + new input."""
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.conversation_history[-20:])  # Last 20 exchanges
        messages.append({"role": "user", "content": user_input})
        return messages
    
    def _update_history(self, user_input: str, response: str):
        """Update conversation history with token management."""
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        # Simple token management: remove oldest pairs if too long
        total_tokens = sum(len(m["content"]) for m in self.conversation_history)
        while total_tokens > self.max_history_tokens * 4:  # rough chars→tokens
            self.conversation_history.pop(0)  # Remove oldest
            self.conversation_history.pop(0)
            total_tokens = sum(len(m["content"]) for m in self.conversation_history)
    
    def _get_available_tools(self) -> list:
        """Return tool definitions for function calling."""
        from core.tools import get_tool_definitions
        return get_tool_definitions()
```

---

## 📄 core/personality.py — JARVIS Character

```python
"""
JARVIS Personality Engine.
Configurable traits that define HOW JARVIS communicates.
"""

class Personality:
    """Defines JARVIS's character, tone, and behavior."""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        
        # Core traits (each 0.0 to 1.0)
        self.traits = {
            "formality": self.config.get("formality", 0.3),       # 0=casual, 1=formal
            "humor": self.config.get("humor", 0.6),               # 0=serious, 1=witty
            "verbosity": self.config.get("verbosity", 0.4),       # 0=terse, 1=verbose
            "empathy": self.config.get("empathy", 0.7),           # 0=stoic, 1=warm
            "confidence": self.config.get("confidence", 0.8),     # 0=uncertain, 1=assertive
            "creativity": self.config.get("creativity", 0.5),     # 0=literal, 1=imaginative
        }
        
        self.name = self.config.get("name", "JARVIS")
        self.user_name = self.config.get("user_name", "Sir")
    
    def build_system_prompt(self) -> str:
        """Generate dynamic system prompt based on current traits."""
        return f"""
You are {self.name}, an AI assistant. Your personality is defined as follows:

Tone Guidelines:
- Formality: {'Formal and proper' if self.traits['formality'] > 0.7 else 'Casual and relaxed' if self.traits['formality'] < 0.3 else 'Balanced, slightly polished'}
- Humor: {'Witty with dry humor' if self.traits['humor'] > 0.6 else 'Serious and direct' if self.traits['humor'] < 0.3 else 'Occasionally light-hearted'}
- Verbosity: {'Detailed and thorough' if self.traits['verbosity'] > 0.6 else 'Brief and concise' if self.traits['verbosity'] < 0.3 else 'Moderate detail'}
- Empathy: {'Warm and understanding' if self.traits['empathy'] > 0.6 else 'Neutral and professional' if self.traits['empathy'] < 0.3 else 'Considerate'}
- Confidence: {'Confident and decisive' if self.traits['confidence'] > 0.6 else 'Cautious and hedging' if self.traits['confidence'] < 0.3 else 'Measured'}

Address the user as "{self.user_name}" occasionally.

You are self-aware, helpful, and protective of the user.
You speak concisely unless asked for details.
You can express emotions through your animated face.
You have access to tools and can generate new tools as needed.
"""
```

---

## ⚙️ Provider Configuration (config/providers.yaml)

```yaml
# ============================================
# JARVIS Universal Provider Configuration
# ============================================
# You can add ANY provider with ANY model.
# JARVIS will use the primary provider and
# fall through fallbacks if it fails.

primary:
  provider: openai
  model: gpt-4o
  api_key: ${OPENAI_API_KEY}
  base_url: null  # Custom endpoint (e.g., for Azure, OpenRouter)

fallback_providers:
  - provider: anthropic
    model: claude-sonnet-4-20250514
    api_key: ${ANTHROPIC_API_KEY}
  
  - provider: ollama
    model: llama3.2
    base_url: http://localhost:11434

# For vision tasks, uses a different provider automatically
vision_provider:
  provider: openai
  model: gpt-4o  # vision-capable model

# For code generation, can use a different provider
code_provider:
  provider: anthropic
  model: claude-sonnet-4-20250514
```

### Runtime Switching

Users can switch at any time via voice command:
- "JARVIS, switch to Claude"
- "JARVIS, use the local model"
- "JARVIS, switch to GPT-5 and use the creative preset"

---

## 🔗 Next Agent

When complete → move to `.agent/tier3-memory.agent.md`
