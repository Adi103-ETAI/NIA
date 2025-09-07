# core/plugin_manager.py
"""
Plugin manager skeleton.
- Discovers python modules in ../plugins/ that follow the plugin contract.
- For Phase 0 the manager exposes a minimal registry; plugins are optional.
"""

from __future__ import annotations
import importlib
import logging
import pkgutil

logger = logging.getLogger("nia.core.plugin_manager")

PLUGIN_PACKAGE = "plugins"

class PluginManager:
    def __init__(self):
        self.plugins: dict[str, object] = {}
        self.discover_plugins()

    def discover_plugins(self) -> None:
        """
        Import any module in plugins package and register if it exposes PLUGIN metadata.
        Non-fatal: errors are logged but do not stop execution.
        """
        try:
            package = importlib.import_module(PLUGIN_PACKAGE)
        except Exception:
            logger.debug("No plugins package available.")
            return

        for finder, name, ispkg in pkgutil.iter_modules(package.__path__):
            full = f"{PLUGIN_PACKAGE}.{name}"
            try:
                mod = importlib.import_module(full)
                meta = getattr(mod, "PLUGIN", None)
                if meta:
                    self.plugins[meta.get("name", name)] = mod
                    logger.info("Registered plugin: %s", meta.get("name", name))
                else:
                    # allow modules that expose a register() function later
                    logger.debug("Plugin module %s loaded (no PLUGIN metadata).", full)
            except Exception as exc:
                logger.exception("Failed to load plugin %s: %s", full, exc)

    def list_plugins(self) -> list[str]:
        return list(self.plugins.keys())

    # Example call interface: plugins should expose functions you call explicitly
    def call_plugin(self, name: str, action: str, *args, **kwargs):
        plugin = self.plugins.get(name)
        if not plugin:
            raise ValueError(f"Plugin '{name}' not found.")
        fn = getattr(plugin, action, None)
        if not fn:
            raise ValueError(f"Plugin '{name}' has no action '{action}'.")
        return fn(*args, **kwargs)
