# core/config.py
"""
Configuration loader for NIA.

Loads settings from config/settings.yaml and allows overrides from environment variables.
"""
import os
import yaml
import logging

logger = logging.getLogger("nia.core.config")

def _load_config():
    """
    Loads configuration from a YAML file and merges it with environment variables.
    Environment variables should be prefixed with 'NIA_'.
    For nested keys, use double underscores, e.g., NIA_VOICE__HOTKEY.
    """
    config_path = os.path.join("config", "settings.yaml")
    
    # Default configuration structure
    config = {
        "voice": {},
        "stt": {},
        "brain": {}
    }

    if not os.path.exists(config_path):
        logger.warning("Config file not found at '%s'. Using defaults and environment variables.", config_path)
    else:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config:
                    config.update(yaml_config)
        except (yaml.YAMLError, IOError) as e:
            logger.error("Error loading or parsing config file '%s': %s", config_path, e)
            # Continue with defaults so the app can attempt to run

    # Override with environment variables
    for section, settings in config.items():
        for key, value in settings.items():
            env_var_name = f"NIA_{section.upper()}__{key.upper()}"
            if env_var_name in os.environ:
                env_value = os.environ[env_var_name]
                # Attempt to cast to the original type (int, bool, float)
                original_type = type(value)
                try:
                    if original_type is bool:
                        config[section][key] = env_value.lower() in ('true', '1', 'yes')
                    elif original_type is not None:
                        config[section][key] = original_type(env_value)
                    else:
                        config[section][key] = env_value
                except (ValueError, TypeError):
                    logger.warning("Could not cast env var %s value '%s' to type %s. Using as string.", env_var_name, env_value, original_type)
                    config[section][key] = env_value
    
    return config

# Load the configuration once on import
settings = _load_config()
logger.info("Configuration loaded successfully.")
