"""
Confirmation manager for NIA autonomous suggestions.

- Handles idle detection before prompting for confirmation
- Batches multiple suggestions into single prompts
- Manages confirmation flow with configurable timeouts
- Provides polite confirmation messages based on suggestion context
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import List, Optional

from core.autonomy_agent import AutonomousSuggestion
from typing import Any

logger = logging.getLogger("nia.core.confirmation")


@dataclass
class BatchedSuggestion:
    suggestions: List[AutonomousSuggestion]
    combined_text: str
    highest_confidence: float
    primary_trigger: str


class ConfirmationManager:
    def __init__(self, tts_manager, stt_manager, loop: asyncio.AbstractEventLoop, brain: Any | None = None):
        self.tts_manager = tts_manager
        self.stt_manager = stt_manager
        self.loop = loop
        self.brain = brain
        self._idle_detection_time = 3.0  # seconds of silence before prompting
        self._batching_window = 2.0  # seconds to collect multiple suggestions
        self._last_activity_time = 0.0
        self._pending_suggestions: List[AutonomousSuggestion] = []
        self._batching_task: Optional[asyncio.Task] = None

    def update_activity(self):
        """Call this when user is actively speaking or interacting."""
        self._last_activity_time = time.time()

    def is_idle(self) -> bool:
        """Check if user has been idle long enough for confirmation."""
        return time.time() - self._last_activity_time >= self._idle_detection_time

    async def add_suggestion(self, suggestion: AutonomousSuggestion) -> bool:
        """
        Add a suggestion to the batch. Returns True if confirmation should be triggered.
        """
        self._pending_suggestions.append(suggestion)
        
        # If this is the first suggestion, start batching timer
        if len(self._pending_suggestions) == 1:
            self._batching_task = asyncio.create_task(self._batching_timer())
            return False
        
        # If we already have suggestions, just add to batch
        return False

    async def _batching_timer(self):
        """Wait for batching window, then trigger confirmation if idle."""
        await asyncio.sleep(self._batching_window)
        
        if not self._pending_suggestions:
            return
            
        # Only proceed if user is idle
        if not self.is_idle():
            logger.info("User not idle, skipping confirmation")
            self._pending_suggestions.clear()
            return
            
        # Process the batched suggestions
        await self._confirm_batched_suggestions()

    async def _confirm_batched_suggestions(self):
        """Present batched suggestions to user for confirmation."""
        if not self._pending_suggestions:
            return
            
        batched = self._create_batched_suggestion()
        self._pending_suggestions.clear()
        
        if not batched:
            return
            
        # Present confirmation
        confirmed = await self._present_confirmation(batched)
        if confirmed:
            logger.info("User confirmed autonomous suggestions")
            await self._speak_suggestions(batched)
        else:
            logger.info("User dismissed autonomous suggestions")

    def _create_batched_suggestion(self) -> Optional[BatchedSuggestion]:
        """Combine multiple suggestions into a single batched suggestion."""
        if not self._pending_suggestions:
            return None
            
        # Sort by confidence (highest first)
        sorted_suggestions = sorted(self._pending_suggestions, 
                                  key=lambda s: s.confidence, reverse=True)
        
        # Take top 3 suggestions max
        top_suggestions = sorted_suggestions[:3]
        
        # Create combined text
        if len(top_suggestions) == 1:
            combined_text = top_suggestions[0].text
        elif len(top_suggestions) == 2:
            combined_text = f"I have a couple of thoughts: {top_suggestions[0].text} Also, {top_suggestions[1].text}"
        else:
            combined_text = f"I have a few thoughts: {top_suggestions[0].text} Also, {top_suggestions[1].text} And {top_suggestions[2].text}"
        
        return BatchedSuggestion(
            suggestions=top_suggestions,
            combined_text=combined_text,
            highest_confidence=top_suggestions[0].confidence,
            primary_trigger=top_suggestions[0].trigger_type
        )

    async def _present_confirmation(self, batched: BatchedSuggestion) -> bool:
        """Present confirmation prompt to user and get response."""
        # Generate context-aware confirmation prompt
        prompt = self._generate_confirmation_prompt(batched)
        
        # Speak the confirmation prompt
        await self.tts_manager.speak_async(prompt)
        
        # Listen for response
        try:
            response = await asyncio.wait_for(
                self.stt_manager.listen_and_transcribe(), 
                timeout=4.0
            )
        except asyncio.TimeoutError:
            response = None
        except Exception as e:
            logger.exception("Error during confirmation listening")
            response = None
            
        if not response:
            return False
            
        # Check for positive/negative responses
        response_lower = response.lower().strip()
        yes_words = ["yes", "sure", "okay", "go ahead", "please", "sounds good"]
        no_words = ["no", "not now", "later", "skip", "dismiss"]
        
        if any(word in response_lower for word in yes_words):
            return True
        if any(word in response_lower for word in no_words):
            return False
            
        # Default to no for unclear responses
        return False

    def _generate_confirmation_prompt(self, batched: BatchedSuggestion) -> str:
        """Generate appropriate confirmation prompt based on suggestion context."""
        trigger = batched.primary_trigger
        confidence = batched.highest_confidence
        
        if trigger == "decision_keyword":
            return "I noticed you're working through a decision. I have some thoughts that might help. Would you like to hear them?"
        elif trigger == "high_value_topic":
            return "I picked up on something important you mentioned. I might have some useful insights. Interested?"
        elif trigger == "hesitation":
            return "It sounds like you're thinking through something. I have some ideas that might help. Want to hear them?"
        elif trigger == "repetition":
            return "I notice this topic has come up before. I have some thoughts that might be helpful. Would you like to hear them?"
        else:
            if confidence > 0.8:
                return "I have a suggestion that might be helpful. Would you like to hear it?"
            else:
                return "I have a thought. Would you like to hear it?"

    async def _speak_suggestions(self, batched: BatchedSuggestion):
        """Speak the confirmed suggestions using Brain with memory context if available."""
        context_snippets: list[str] = []
        for s in batched.suggestions:
            if s.metadata and isinstance(s.metadata, dict):
                ctx = s.metadata.get("memory_context")
                if isinstance(ctx, list):
                    context_snippets.extend(ctx)
        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for c in context_snippets:
            if c not in seen:
                deduped.append(c)
                seen.add(c)

        if self.brain:
            # Ask Brain to generate a concise suggestion based on the combined text
            prompt = f"Provide a concise, helpful suggestion given this context and user signals: {batched.combined_text}"
            full = ""
            try:
                async for chunk in self.brain.generate_stream(prompt, context_snippets=deduped[:8]):
                    if chunk.get("response"):
                        full += chunk["response"]
                text_to_speak = full.strip() or batched.combined_text
            except Exception:
                text_to_speak = batched.combined_text
        else:
            text_to_speak = batched.combined_text

        await self.tts_manager.speak_async(text_to_speak)

    def clear_pending(self):
        """Clear any pending suggestions (e.g., on barge-in)."""
        self._pending_suggestions.clear()
        if self._batching_task and not self._batching_task.done():
            self._batching_task.cancel()
        self._batching_task = None
