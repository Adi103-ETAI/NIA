# core/memory_manager.py
"""
Lightweight memory manager for Phase 0.
- Stores recent messages in RAM and also appends to disk for persistence.
- Simple JSON-lines append file stored under data/memory/messages.jsonl
"""

from __future__ import annotations
import os
import json
import datetime
from typing import List

DATA_DIR = os.path.join("data", "memory")
LOG_FILE = os.path.join(DATA_DIR, "messages.jsonl")

class MemoryManager:
    def __init__(self, persist: bool = True, max_items: int = 200):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.persist = persist
        self.max_items = max_items
        self._history: List[dict] = []

    def store(self, role: str, text: str) -> None:
        entry = {
            "ts": datetime.datetime.utcnow().isoformat() + "Z",
            "role": role,
            "text": text
        }
        self._history.append(entry)
        # trim
        if len(self._history) > self.max_items:
            self._history = self._history[-self.max_items:]
        if self.persist:
            with open(LOG_FILE, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def session_history(self) -> List[dict]:
        return list(self._history)
