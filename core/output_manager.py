# core/output_manager.py
"""
Output manager for NIA core.
Phase 0: console print + logging. Later: TTS integration.
"""

from __future__ import annotations
import logging

logger = logging.getLogger("nia.core.output")

class OutputManager:
    def __init__(self):
        pass

    def say(self, text: str) -> None:
        text = (text or "").strip()
        if not text:
            return
        # Console
        print(f"NIA: {text}\n")
        # Log
        logger.info("NIA_RESPONSE: %s", text)
