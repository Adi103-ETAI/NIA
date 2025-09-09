"""
Background autonomy agent for NIA.

- Periodically generates suggestions/actions based on simple heuristics (placeholder).
- Provides a thread-safe queue to deliver suggestions to the TTS pipeline.
- Supports pause/resume to allow active user interactions to override autonomy.
"""

import asyncio
import logging
import re
import threading
import time
from dataclasses import dataclass
from queue import Queue, Empty
from typing import Optional, List

from core.config import settings
from core.memory_manager import MemoryManager

logger = logging.getLogger("nia.core.autonomy")


@dataclass
class AutonomousSuggestion:
    text: str
    confidence: float
    trigger_type: str
    timestamp: float
    topic: Optional[str] = None
    metadata: Optional[dict] = None


class AutonomyAgent:
    def __init__(self, loop: asyncio.AbstractEventLoop, memory: MemoryManager | None = None):
        self.loop = loop
        self._stop_event = threading.Event()
        self._paused_event = threading.Event()
        self._paused_event.set()  # start paused until explicitly started
        self.suggestion_queue: Queue[AutonomousSuggestion] = Queue()
        self.worker_thread: Optional[threading.Thread] = None
        self._last_user_input = ""
        self._input_history: List[str] = []
        self._last_activity_time = 0.0

        cfg = settings.get("autonomy", {})
        self.interval_seconds = int(cfg.get("suggestion_interval_s", 45))
        self.enabled = bool(cfg.get("enabled", True))
        self.use_memory = bool(cfg.get("use_memory", True))
        self.max_memory_snippets = int(cfg.get("max_memory_snippets", 5))
        self.memory = memory or MemoryManager()
        
        # Context-aware configuration
        self.confidence_threshold = float(cfg.get("confidence_threshold", 0.6))
        self.decision_keywords = cfg.get("decision_keywords", [
            "should i", "what if", "maybe", "i think", "i'm not sure", "help me decide",
            "i need to", "i want to", "i have to", "i should", "i could", "i might",
            "what do you think", "any suggestions", "any ideas", "what would you do"
        ])
        self.high_value_topics = cfg.get("high_value_topics", [
            "work", "project", "meeting", "deadline", "plan", "schedule", "task",
            "problem", "issue", "decision", "choice", "option", "strategy"
        ])
        self.hesitation_patterns = cfg.get("hesitation_patterns", [
            r"\b(um|uh|er|ah|hmm|well|so|like|you know)\b",
            r"\b(i mean|i guess|i suppose|sort of|kind of)\b"
        ])
        self.repetition_threshold = int(cfg.get("repetition_threshold", 2))

    def start(self):
        if not self.enabled:
            logger.info("Autonomy disabled by configuration.")
            return
        if self.worker_thread and self.worker_thread.is_alive():
            return
        self._stop_event.clear()
        # default to running but paused; resume controlled by orchestrator
        self.worker_thread = threading.Thread(target=self._run_loop, daemon=True)
        self.worker_thread.start()
        logger.info("Autonomy agent started (interval=%ss).", self.interval_seconds)

    def stop(self):
        self._stop_event.set()
        if self.worker_thread:
            self.worker_thread.join(timeout=2)
        logger.info("Autonomy agent stopped.")

    def pause(self):
        """Pause generating and emitting suggestions."""
        if not self._paused_event.is_set():
            self._paused_event.set()
            logger.info("Autonomy paused by override.")

    def resume(self):
        """Resume generating suggestions."""
        if self._paused_event.is_set():
            self._paused_event.clear()
            logger.info("Autonomy resumed.")

    def _run_loop(self):
        """Blocking thread loop generating periodic suggestions."""
        last_emit = 0.0
        while not self._stop_event.is_set():
            # sleep small to be responsive to pause/stop
            time.sleep(0.2)
            if self._paused_event.is_set():
                continue
            now = time.time()
            if now - last_emit >= self.interval_seconds:
                suggestion = self._generate_context_aware_suggestion()
                if suggestion:
                    self.suggestion_queue.put(suggestion)
                    logger.info("Autonomous suggestion enqueued: %s (confidence=%.2f, trigger=%s)", 
                               suggestion.text, suggestion.confidence, suggestion.trigger_type)
                last_emit = now

    def update_user_input(self, text: str):
        """Update the agent with recent user input for context analysis."""
        if not text or not text.strip():
            return
        self._last_user_input = text.strip()
        self._input_history.append(self._last_user_input)
        self._last_activity_time = time.time()
        # Keep only last 10 inputs for context
        if len(self._input_history) > 10:
            self._input_history = self._input_history[-10:]

    def _generate_context_aware_suggestion(self) -> Optional[AutonomousSuggestion]:
        """Generate suggestions based on context analysis rather than random prompts."""
        if not self._last_user_input:
            return None
        
        confidence, trigger_type, topic = self._analyze_context()
        if confidence < self.confidence_threshold:
            return None
        
        # Only generate suggestions for decision points, not periodic ones
        if trigger_type == "periodic":
            return None
        
        # Build context snippets from memory using async query if enabled
        memory_context = []
        if self.use_memory and self.memory and self._last_user_input:
            try:
                if self.loop.is_running():
                    fut = asyncio.run_coroutine_threadsafe(
                        self.memory.query_memory(topic=self._last_user_input, recent_n=self.max_memory_snippets, min_score=0.0),
                        self.loop,
                    )
                    sims = fut.result(timeout=2.0)
                else:
                    sims = self.loop.run_until_complete(
                        self.memory.query_memory(topic=self._last_user_input, recent_n=self.max_memory_snippets, min_score=0.0)
                    )
                # Fallback to recent messages if no semantic hits
                if not sims:
                    sims = self.memory.get_recent_messages(n=self.max_memory_snippets)
                sims_sorted = sorted(
                    sims,
                    key=lambda r: (0 if (r.get("user") == "user" or r.get("role") == "user") else 1, r.get("ts", "")),
                )
                memory_context = [f"[{r.get('ts','')}] {r.get('user', r.get('role',''))}: {r.get('text','')}" for r in sims_sorted if r.get('text')]
            except Exception:
                memory_context = []

        suggestion_text = self._generate_suggestion_for_context(topic, trigger_type, memory_context)
        if not suggestion_text:
            return None
            
        meta = {"source": "context_aware_autonomy", "memory_context": memory_context}
        return AutonomousSuggestion(
            text=suggestion_text,
            confidence=confidence,
            trigger_type=trigger_type,
            topic=topic,
            timestamp=time.time(),
            metadata=meta
        )

    def _analyze_context(self) -> tuple[float, str, Optional[str]]:
        """Analyze user input for decision points and return confidence, trigger type, and topic."""
        text = self._last_user_input.lower()
        confidence = 0.0
        trigger_type = "periodic"
        topic = None
        
        # Check for decision keywords
        decision_score = 0.0
        for keyword in self.decision_keywords:
            if keyword in text:
                decision_score += 0.3
        if decision_score > 0:
            confidence += min(decision_score, 0.8)
            trigger_type = "decision_keyword"
        
        # Check for high-value topics
        topic_score = 0.0
        for topic_word in self.high_value_topics:
            if topic_word in text:
                topic_score += 0.2
                topic = topic_word
        if topic_score > 0:
            confidence += min(topic_score, 0.6)
            if trigger_type == "periodic":
                trigger_type = "high_value_topic"
        
        # Check for hesitation patterns
        hesitation_count = 0
        for pattern in self.hesitation_patterns:
            hesitation_count += len(re.findall(pattern, text, re.IGNORECASE))
        if hesitation_count > 0:
            confidence += min(hesitation_count * 0.1, 0.4)
            if trigger_type == "periodic":
                trigger_type = "hesitation"
        
        # Check for repetition in recent history
        if len(self._input_history) >= 3:
            recent_texts = [t.lower() for t in self._input_history[-3:]]
            if len(set(recent_texts)) < len(recent_texts):
                confidence += 0.3
                if trigger_type == "periodic":
                    trigger_type = "repetition"
        
        # Time-based decay (recent input gets higher confidence)
        time_since_activity = time.time() - self._last_activity_time
        if time_since_activity < 30:  # Within 30 seconds
            confidence += 0.2
        
        return min(confidence, 1.0), trigger_type, topic

    def _generate_suggestion_for_context(self, topic: Optional[str], trigger_type: str, memory_context: List[str]) -> Optional[str]:
        """Generate a suggestion using memory snippets when available."""
        if memory_context:
            preview = " \n".join(memory_context[:3])
            if trigger_type == "high_value_topic" and topic:
                return f"On {topic}, here's what we've discussed before: \n{preview}\nWould you like me to summarize options or next steps?"
            if trigger_type == "decision_keyword":
                return f"Based on similar past moments: \n{preview}\nWant me to help weigh pros and cons now?"
            if trigger_type == "hesitation":
                return f"I remember you sounded unsure previously: \n{preview}\nWant a quick path forward?"
            if trigger_type == "repetition":
                return f"This keeps coming up: \n{preview}\nShould we make a plan together?"
            # periodic or fallback
            return f"Here's some context that might help: \n{preview}\nWant suggestions?"

        # Fallback to lightweight templates
        if trigger_type == "high_value_topic" and topic:
            return f"I noticed you mentioned {topic}. Would you like some help with that?"
        if trigger_type == "decision_keyword":
            return "I can help you think through that decision. What factors are you considering?"
        if trigger_type == "hesitation":
            return "It sounds like you're thinking through something. Want to talk it out?"
        if trigger_type == "repetition":
            return "I notice you've mentioned this before. Would you like some help with it?"
        return "Is there anything I can help you with right now?"

    def _generate_suggestion(self) -> Optional[AutonomousSuggestion]:
        """
        Placeholder heuristic. In next phase, integrate memory/context signals.
        """
        prompts = settings.get("autonomy", {}).get("prompts", [
            "Would you like a summary of recent updates?",
            "Need me to set a reminder for anything?",
            "I can check your schedule if you want.",
        ])
        # rotate by time
        idx = int(time.time() // self.interval_seconds) % len(prompts)
        text = prompts[idx]
        return AutonomousSuggestion(
            text=text, 
            confidence=0.5,
            trigger_type="periodic",
            topic=None,
            timestamp=time.time(),
            metadata={"source": "autonomy", "idx": idx}
        )

    async def get_next_suggestion_async(self, timeout_s: float = 0.1) -> Optional[AutonomousSuggestion]:
        try:
            return await asyncio.get_event_loop().run_in_executor(None, self._get_next_blocking, timeout_s)
        except Exception:
            return None

    def _get_next_blocking(self, timeout_s: float) -> Optional[AutonomousSuggestion]:
        try:
            return self.suggestion_queue.get(timeout=timeout_s)
        except Empty:
            return None

