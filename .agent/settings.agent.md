# Settings — Universal Configuration System

> **Goal:** A unified settings system that JARVIS and all its modules use. Loaded at startup, accessible everywhere, supports any AI provider with any model.
> **Est. time:** 2-3 hours · **Cross-cutting:** All tiers

## ✅ Checklist
- [ ] `core/settings.py` — Central settings loader
- [ ] `config/settings.yaml` — Default user configuration
- [ ] `config/providers.yaml` — AI provider definitions
- [ ] `.env` — Secret keys (API keys, passwords)
- [ ] YAML-based configuration with env var interpolation (`${VAR_NAME}`)
- [ ] Runtime configuration overrides (JARVIS can change settings as needed)
- [ ] Settings validation (required keys, type checking)
- [ ] Provider configuration: ANY provider, ANY model
- [ ] Auto-generated documentation for available settings
- [ ] Settings persistence (changes saved to disk)
- [ ] Profile system (multiple config profiles)

---

## 📄 core/settings.py

```python
"""
Settings System — Central configuration for all JARVIS modules.

Loads from:
1. config/settings.yaml — Main configuration
2. config/providers.yaml — Provider definitions
3. .env — Secret keys (never committed)
4. Environment variables (overrides everything)

Supports ANY AI provider by using a generic provider config model.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv


class Settings:
    """Universal settings manager."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Load .env file
        load_dotenv()
        
        self.config_dir = Path("./config")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration files
        self._settings = self._load_yaml("settings.yaml") or {}
        self._providers = self._load_yaml("providers.yaml") or {}
        
        # Interpolate env vars (${VAR_NAME} → os.environ)
        self._interpolate_env_vars(self._settings)
        self._interpolate_env_vars(self._providers)
        
        self._initialized = True
    
    def _load_yaml(self, filename: str) -> Dict:
        """Load a YAML config file."""
        path = self.config_dir / filename
        if path.exists():
            with open(path, "r") as f:
                return yaml.safe_load(f) or {}
        print(f"⚠️ Config file not found: {path}, using defaults")
        return self._get_defaults(filename)
    
    def _get_defaults(self, filename: str) -> Dict:
        """Return default configuration if file doesn't exist."""
        defaults = {
            "settings.yaml": {
                "general": {
                    "name": "JARVIS",
                    "user_name": "Sir",
                    "language": "en",
                    "timezone": "auto",
                    "log_level": "INFO",
                },
                "voice": {
                    "stt_provider": "openai",
                    "tts_provider": "edge-tts",
                    "wake_word_enabled": True,
                    "wake_word": "jarvis",
                    "silence_timeout": 1.5,
                },
                "brain": {
                    "primary_provider": "primary",
                    "max_history_tokens": 6000,
                    "streaming": True,
                    "enable_tools": True,
                },
                "memory": {
                    "storage_path": "./memory_store",
                    "max_history_messages": 20,
                },
                "vision": {
                    "enabled": False,
                    "camera_id": 0,
                },
                "system_control": {
                    "enabled": True,
                },
                "hardware": {
                    "enabled": False,
                    "mode": "simulation",
                },
                "face": {
                    "mode": "terminal",  # terminal | pygame | hardware
                    "width": 480,
                    "height": 320,
                    "framerate": 30,
                    "style": "anonymous",  # robot | anonymous | minimal
                },
            },
            "providers.yaml": {
                "primary": {
                    "provider": "openai",
                    "model": "gpt-4o",
                    "api_key": "${OPENAI_API_KEY}",
                },
                "vision_provider": {
                    "provider": "openai",
                    "model": "gpt-4o",
                },
                "fallback_providers": [],
            },
        }
        return defaults.get(filename, {})
    
    def _interpolate_env_vars(self, obj: Any):
        """Recursively replace ${VAR_NAME} with environment variables."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    self._interpolate_env_vars(value)
                elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    obj[key] = os.environ.get(env_var, "")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, (dict, list)):
                    self._interpolate_env_vars(item)
                elif isinstance(item, str) and item.startswith("${") and item.endswith("}"):
                    env_var = item[2:-1]
                    obj[i] = os.environ.get(env_var, "")
    
    # =========== GETTERS ===========
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting by dot-notation key (e.g., 'voice.stt_provider')."""
        keys = key.split(".")
        value = self._settings
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    def get_provider_config(self, provider_key: str = "primary") -> Dict:
        """
        Get a provider configuration by key.
        Returns a dict with: provider, model, api_key, base_url, etc.
        """
        providers = self._providers.get(provider_key, {})
        
        # If the key refers to another provider name, resolve it
        if isinstance(providers, str):
            providers = self._providers.get(providers, {})
        
        # Ensure api_key is loaded (might be in env)
        if not providers.get("api_key"):
            env_key = f"{providers.get('provider', '').upper()}_API_KEY"
            providers["api_key"] = os.environ.get(env_key, "")
        
        return providers
    
    def get_all_providers(self) -> Dict[str, Dict]:
        """Get all configured providers."""
        result = {}
        for key in self._providers:
            if key != "fallback_providers":
                result[key] = self.get_provider_config(key)
        
        # Add fallbacks
        result["fallbacks"] = [
            self.get_provider_config(fb) 
            for fb in self._providers.get("fallback_providers", [])
        ]
        
        return result
    
    def get_system_prompt(self) -> str:
        """Get the JARVIS system prompt with dynamic personality injection."""
        from core.personality import Personality
        personality = Personality(self.get("personality", {}))
        return personality.build_system_prompt()
    
    # =========== SETTERS ===========
    
    def set(self, key: str, value: Any):
        """Set a setting by dot-notation key."""
        keys = key.split(".")
        target = self._settings
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
    
    def save(self):
        """Save current settings to disk."""
        path = self.config_dir / "settings.yaml"
        with open(path, "w") as f:
            yaml.dump(self._settings, f, default_flow_style=False)
        print("💾 Settings saved")
    
    # =========== PROVIDER MANAGEMENT ===========
    
    def add_provider(self, name: str, provider_type: str, 
                     model: str, api_key: str = None, 
                     base_url: str = None):
        """Add or update an AI provider at runtime."""
        config = {
            "provider": provider_type,
            "model": model,
        }
        if api_key:
            config["api_key"] = api_key
        if base_url:
            config["base_url"] = base_url
        
        self._providers[name] = config
        
        # Save providers
        provider_path = self.config_dir / "providers.yaml"
        with open(provider_path, "w") as f:
            yaml.dump(self._providers, f, default_flow_style=False)
    
    def switch_provider(self, provider_name: str, model: str = None):
        """Switch the primary provider at runtime."""
        config = self.get_provider_config(provider_name)
        if model:
            config["model"] = model
        self._providers["primary"] = config
        print(f"🔄 Switched to provider: {provider_name} ({config.get('model')})")
    
    # =========== PROFILE MANAGEMENT ===========
    
    def load_profile(self, profile_name: str):
        """Load a settings profile."""
        profile_path = self.config_dir / f"profile_{profile_name}.yaml"
        if profile_path.exists():
            with open(profile_path) as f:
                self._settings = yaml.safe_load(f)
            print(f"📋 Loaded profile: {profile_name}")
    
    def save_profile(self, profile_name: str):
        """Save current settings as a named profile."""
        profile_path = self.config_dir / f"profile_{profile_name}.yaml"
        with open(profile_path, "w") as f:
            yaml.dump(self._settings, f)
        print(f"📋 Saved profile: {profile_name}")
```
