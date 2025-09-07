# core/tts_manager.py
"""
Manages Text-to-Speech (TTS) operations in a non-blocking way.

- Runs the blocking pyttsx3 engine in a separate thread.
- Uses an asyncio.Queue to receive text phrases to be spoken.
- Implements a phrase chunker to stream audio smoothly.
- Provides methods to stop speech immediately for barge-in.
"""

import asyncio
import logging
import queue
import re
import threading
from core.config import settings
from core.tts_engine import speak as tts_speak

logger = logging.getLogger("nia.core.tts_manager")

class TTSManager:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        # No longer need to initialize pyttsx3 directly - tts_engine handles this

        self.phrase_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.is_speaking_event = threading.Event()
        self.speak_complete_event = asyncio.Event()

        self.buffer = ""
        self.boundary_regex = re.compile(settings["voice"]["sentence_boundary_regex"])

        self.worker_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.worker_thread.start()
        logger.info("TTSManager initialized and worker thread started.")

    def _clean_text_for_speech(self, text: str) -> str:
        """
        Cleans text for TTS by removing emojis and other non-speech characters.
        """
        if not text:
            return text
        
        # Remove emojis and other symbols
        # This regex matches most emojis and symbols
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"  # dingbats
            "\U000024C2-\U0001F251"  # enclosed characters
            "\U0001F900-\U0001F9FF"  # supplemental symbols
            "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A
            "]+", 
            flags=re.UNICODE
        )
        
        # Remove emojis
        cleaned = emoji_pattern.sub('', text)
        
        # Remove other problematic characters but keep common punctuation
        cleaned = re.sub(r'[^\w\s.,!?;:\'"()—-]', '', cleaned)
        
        # Clean up extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned


    def _tts_worker(self):
        """The main loop for the TTS worker thread."""
        while not self.stop_event.is_set():
            try:
                # Wait for a phrase to be added to the queue
                phrase = self.phrase_queue.get(timeout=1)
                if phrase is None:  # Sentinel for shutdown
                    break

                self.is_speaking_event.set()
                # Use the new tts_engine module
                success = tts_speak(phrase)
                if not success:
                    logger.warning("TTS engine failed to speak phrase")
                self.is_speaking_event.clear()

                self.phrase_queue.task_done()

                # If the queue is now empty, signal completion
                if self.phrase_queue.empty():
                    self.loop.call_soon_threadsafe(self.speak_complete_event.set)

            except queue.Empty:
                # This can happen during shutdown or if the queue is empty
                if self.phrase_queue.empty() and not self.is_speaking_event.is_set():
                    self.loop.call_soon_threadsafe(self.speak_complete_event.set)
                continue
        logger.info("TTS worker thread finished.")

    def add_to_buffer(self, text: str):
        """
        Adds text from the streaming Brain to a buffer and processes it into phrases.
        """
        self.buffer += text
        
        # Use regex to find sentence boundaries
        match = self.boundary_regex.search(self.buffer)
        while match:
            # Extract the phrase including the boundary
            phrase = self.buffer[:match.end()]

            # If the phrase is too short, keep it in the buffer and wait for more text
            if len(phrase.strip()) <= settings["voice"]["chunk_chars_min"]:
                # Do not consume from buffer yet to avoid truncation of short first sentences
                break

            # Consume the phrase from the buffer and speak it
            self.buffer = self.buffer[match.end():]
            self.speak(phrase.strip())

            # Find the next match in the remaining buffer
            match = self.boundary_regex.search(self.buffer)

    async def speak_async(self, phrase: str):
        """Asynchronously adds a phrase to the TTS queue and waits for completion."""
        if not self.stop_event.is_set():
            # Clean the text before adding to queue
            cleaned_phrase = self._clean_text_for_speech(phrase)
            if cleaned_phrase:  # Only add if there's content after cleaning
                self.speak_complete_event.clear()
                self.phrase_queue.put(cleaned_phrase)
                logger.debug("Queued for TTS: '%s'", cleaned_phrase)
                await self.speak_complete_event.wait()

    def speak(self, phrase: str):
        """Adds a phrase to the TTS queue."""
        if not self.stop_event.is_set():
            # Clean the text before adding to queue
            cleaned_phrase = self._clean_text_for_speech(phrase)
            if cleaned_phrase:  # Only add if there's content after cleaning
                self.phrase_queue.put(cleaned_phrase)
                logger.debug("Queued for TTS: '%s'", cleaned_phrase)

    def flush_buffer(self):
        """Speaks any remaining text in the buffer."""
        if self.buffer.strip():
            self.speak(self.buffer.strip())
            self.buffer = ""

    def stop(self):
        """Stops the current speech and clears the queue."""
        logger.info("TTS stop requested (barge-in).")
        # Clear any pending phrases
        with self.phrase_queue.mutex:
            self.phrase_queue.queue.clear()
        
        # Note: The tts_engine module doesn't support stopping mid-speech
        # This is a limitation of the current implementation
        # The stop will be effective for the next phrase in the queue
        
        self.buffer = "" # Clear the text buffer as well

    def is_speaking(self) -> bool:
        """Returns True if the TTS engine is currently speaking."""
        return self.is_speaking_event.is_set()

    def shutdown(self):
        """Shuts down the TTS worker thread gracefully."""
        logger.info("Shutting down TTSManager.")
        self.stop_event.set()
        self.phrase_queue.put(None)  # Sentinel to unblock the worker
        self.worker_thread.join(timeout=2)
        # No need to stop engine directly - tts_engine handles this
