"""
Settings System — Central configuration for all JARVIS modules.
Loads from config/settings.yaml + .env + environment variables.
"""

import os
import yaml
from pathlib import Path
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
        
        load_dotenv()
        
        self.config_dir = Path(__file__).parent.parent / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self._settings = self._load_yaml("settings.yaml")
        self._initialized = True
    
    def _load_yaml(self, filename):
        path = self.config_dir / filename
        if path.exists():
            with open(path) as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def get(self, key, default=None):
        """Get a setting by dot-notation (e.g., 'face.mode')."""
        keys = key.split(".")
        value = self._settings
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    def set(self, key, value):
        """Set a setting by dot-notation."""
        keys = key.split(".")
        target = self._settings
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
    
    def save(self):
        """Save settings to disk."""
        path = self.config_dir / "settings.yaml"
        with open(path, "w") as f:
            yaml.dump(self._settings, f, default_flow_style=False)
    
    def get_system_prompt(self):
        """Get JARVIS system prompt."""
        from core.personality import Personality
        return Personality().build_system_prompt()
