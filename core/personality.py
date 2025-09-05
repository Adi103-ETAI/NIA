# core/personality.py
"""
Personality configuration loader for NIA.
Loads personality settings from config/personality.yaml and provides system prompts.
"""

from __future__ import annotations
import os
import yaml
import logging

logger = logging.getLogger("nia.core.personality")

DEFAULT_PERSONA = {
    "name": "NIA",
    "tone": "concise, helpful, friendly",
    "instruction": "You are NIA, a helpful assistant. Keep answers concise unless asked for detail."
}

def load_personality() -> dict:
    """
    Loads personality configuration from config/personality.yaml.
    Falls back to default if file doesn't exist or has errors.
    """
    config_path = os.path.join("config", "personality.yaml")
    
    if not os.path.exists(config_path):
        logger.warning("Personality config not found at '%s'. Using defaults.", config_path)
        return DEFAULT_PERSONA
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            personality_config = yaml.safe_load(f)
            if personality_config:
                logger.info("Personality configuration loaded successfully.")
                return personality_config
            else:
                logger.warning("Personality config file is empty. Using defaults.")
                return DEFAULT_PERSONA
    except (yaml.YAMLError, IOError) as e:
        logger.error("Error loading personality config '%s': %s", config_path, e)
        return DEFAULT_PERSONA

def get_system_prompt(context: str = "default") -> str:
    """
    Gets the appropriate system prompt for the given context.
    """
    personality = load_personality()
    
    # Try to get context-specific prompt
    system_prompts = personality.get("system_prompts", {})
    if context in system_prompts:
        return system_prompts[context]
    
    # Fall back to default prompt
    if "default" in system_prompts:
        return system_prompts["default"]
    
    # Ultimate fallback
    return personality.get("instruction", DEFAULT_PERSONA["instruction"])
