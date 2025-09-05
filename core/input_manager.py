# core/input_manager.py
"""
Input manager for NIA core.
Phase 0: provides blocking text input from console.
Later: voice input integration will be added here.
"""

from __future__ import annotations
from typing import Optional

class InputManager:
    def __init__(self):
        pass

    def get_text(self, prompt: str = "You: ") -> Optional[str]:
        """
        Blocking read from stdin; returns None on EOF or KeyboardInterrupt.
        """
        try:
            raw = input(prompt)
            if raw is None:
                return None
            s = raw.strip()
            return s or None
        except (EOFError, KeyboardInterrupt):
            return None
