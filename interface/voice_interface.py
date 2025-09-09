# interface/voice_interface.py
"""
The voice interface, acting as the central orchestrator for real-time interaction.

- Manages the application state (IDLE, LISTENING, THINKING, SPEAKING).
- Listens for a hotkey to trigger speech-to-text (STT).
- Handles barge-in: interrupts NIA's speech when the user speaks again.
- Coordinates the flow: STT -> Brain (streaming) -> TTS (streaming).
"""

import asyncio
import logging
from enum import Enum, auto

import keyboard

from core.brain import Brain
from core.config import settings
from core.tts_manager import TTSManager
from core.stt_manager import STTManager
from core.autonomy_agent import AutonomyAgent
from core.confirmation_manager import ConfirmationManager

logger = logging.getLogger("nia.interface.voice")

class VoiceState(Enum):
    IDLE = auto()
    LISTENING = auto()
    THINKING = auto()
    SPEAKING = auto()

class VoiceInterface:
    def __init__(self, brain: Brain, tts_manager: TTSManager, stt_manager: STTManager, autonomy: AutonomyAgent | None = None):
        self.brain = brain
        self.tts_manager = tts_manager
        self.stt_manager = stt_manager # Use the new manager
        self.hotkey = settings["voice"]["hotkey"]
        self.hybrid_cfg = settings.get("hybrid", {})
        self.passive_enabled = bool(self.hybrid_cfg.get("passive_enabled", True))
        self.autonomy_enabled = bool(settings.get("autonomy", {}).get("enabled", True))
        self.autonomy = autonomy
        self.autonomy_cfg = settings.get("autonomy", {})
        self.use_memory = bool(self.autonomy_cfg.get("use_memory", True))
        self.max_memory_snippets = int(self.autonomy_cfg.get("max_memory_snippets", 5))
        
        self.state = VoiceState.IDLE
        self.current_brain_task = None
        self.loop = asyncio.get_event_loop()
        self.confirmation_manager = ConfirmationManager(tts_manager, stt_manager, self.loop, brain)
        self.hotkey_listener_task = None
        self.autonomy_consumer_task = None

    async def start(self):
        """Starts the main voice interface loop and hotkey listener."""
        logger.info(f"VoiceInterface started. Press '{self.hotkey.upper()}' to speak.")
        print("=" * 60)
        print("🎙️  NIA Voice Assistant Ready!")
        print(f"📢 Press '{self.hotkey.upper()}' to speak")
        print("⏱️  Note: Responses may be slower on this system")
        print("=" * 60)
        # Start the hotkey listener as a managed asyncio task
        self.hotkey_listener_task = self.loop.run_in_executor(None, self._hotkey_listener)
        # Start passive wake-word listener
        if self.passive_enabled:
            self.stt_manager.start_wake_listener(self._on_wake_detected)
        # Start autonomy agent and consumer
        if self.autonomy and self.autonomy_enabled:
            self.autonomy.start()
            self.autonomy_consumer_task = asyncio.create_task(self._consume_autonomy_suggestions())
        
        try:
            # Keep the main task alive to allow the listener to run
            while True:
                await asyncio.sleep(1)
        finally:
            await self.shutdown()

    def _hotkey_listener(self):
        """
        A blocking listener that waits for the hotkey and triggers the async handler.
        This runs in a thread to avoid blocking the main asyncio loop.
        """
        # Use a try-finally block to ensure the handler is set up again
        try:
            keyboard.wait(self.hotkey)
            if self.loop.is_running():
                # Schedule the async handler to run in the main event loop
                future = asyncio.run_coroutine_threadsafe(self.handle_hotkey_press(), self.loop)
                # Wait for the coroutine to complete to avoid the warning
                try:
                    future.result(timeout=1.0)
                except Exception:
                    pass  # Ignore errors during shutdown
        except (KeyboardInterrupt, EOFError):
            logger.info("Hotkey listener thread shutting down.")
            return # Exit thread
        
        # Relaunch the listener unless the loop is closing
        if self.loop.is_running():
            self.loop.run_in_executor(None, self._hotkey_listener)

    async def handle_hotkey_press(self):
        """Asynchronous handler for when the hotkey is pressed."""
        # If we are speaking or thinking, this is a barge-in.
        if self.state == VoiceState.SPEAKING or self.state == VoiceState.THINKING:
            logger.info("Barge-in detected. Interrupting current response.")
            self.tts_manager.stop()
            if self.current_brain_task:
                self.current_brain_task.cancel()
            # Clear any pending autonomy confirmations on barge-in
            self.confirmation_manager.clear_pending()
            # The existing listen_and_respond task will catch the cancellation
            # and transition to IDLE. The new listening session will start from there.
            return # Stop here, let the existing flow handle the state change.

        # If we are idle, start a new listening session.
        if self.state == VoiceState.IDLE:
            # Pause autonomy while actively interacting
            if self.autonomy:
                self.autonomy.pause()
            # Clear any pending autonomy confirmations when starting new interaction
            self.confirmation_manager.clear_pending()
            await self.listen_and_respond()
        elif self.state == VoiceState.LISTENING:
            # If already listening, ignore the hotkey press to avoid interrupting ongoing transcription
            logger.debug("Hotkey pressed while already listening, ignoring.")
        else:
            logger.warning("Hotkey pressed in an unexpected state: %s", self.state)

    def _on_wake_detected(self):
        """Callback invoked by STTManager when a wake word is detected."""
        logger.info("Wake-word callback fired.")
        # Forward to the same handler as hotkey
        asyncio.run_coroutine_threadsafe(self.handle_hotkey_press(), self.loop)

    async def listen_and_respond(self):
        """Listens for user input, processes it, and generates a response."""
        self.state = VoiceState.LISTENING
        logger.info("State changed to LISTENING")
        
        user_text = await self._recognize_speech()
        if not user_text:
            self.state = VoiceState.IDLE
            logger.info("State changed to IDLE (no speech recognized)")
            # Resume autonomy when done
            if self.autonomy:
                self.autonomy.resume()
            return
        
        # Feed user input to autonomy agent for context analysis
        if self.autonomy:
            self.autonomy.update_user_input(user_text)
        
        # Update confirmation manager activity
        self.confirmation_manager.update_activity()

        self.state = VoiceState.THINKING
        logger.info("State changed to THINKING")
        print("🤔 Thinking... (this may take a moment on slower systems)")
        
        # Create and run the brain streaming task
        self.current_brain_task = asyncio.create_task(self._stream_brain_to_tts(user_text))
        
        try:
            await self.current_brain_task
        except asyncio.CancelledError:
            logger.info("Brain stream was cancelled due to barge-in.")
        
        self.state = VoiceState.IDLE
        logger.info("State changed to IDLE (response finished)")
        # Resume autonomy when interaction finishes
        if self.autonomy:
            self.autonomy.resume()

    async def _recognize_speech(self) -> str | None:
        """
        Recognizes speech using the streaming STTManager.
        """
        print("🎤 Listening... (speak clearly, I'll wait up to 5 seconds)")
        try:
            # This single call now handles the entire streaming recognition process
            user_text = await self.stt_manager.listen_and_transcribe()
            
            if user_text:
                print(f"✅ You said: {user_text}")
                logger.info("USER (voice): %s", user_text)
                return user_text
            else:
                print("❌ Sorry, I didn't catch that. Please try again.")
                return None
        except Exception as e:
            logger.exception("An error occurred during speech recognition.")
            print("❌ Speech recognition error. Please try again.")
            return None

    async def _stream_brain_to_tts(self, prompt: str):
        """
        Streams the brain's response to the TTS manager.
        """
        full_response = ""
        try:
            async for chunk in self.brain.generate_stream(prompt):
                if "response" in chunk:
                    token = chunk["response"]
                    full_response += token
                    
                    if self.state != VoiceState.SPEAKING:
                        self.state = VoiceState.SPEAKING
                        logger.info("State changed to SPEAKING")
                        print("🔊 Speaking...")

                    self.tts_manager.add_to_buffer(token)
                
                if chunk.get("done"):
                    break
        except Exception as e:
            logger.exception("Error while streaming from brain.")
            self.tts_manager.add_to_buffer("I'm sorry, I encountered an error while processing your request.")
        
        # Flush any remaining text in the TTS buffer
        self.tts_manager.flush_buffer()
        
        # Wait for TTS to finish speaking (no need to speak buffer again)
        # The flush_buffer() already handles the remaining text
        
        logger.info("NIA (voice): %s", full_response)

    async def shutdown(self):
        """Cleanly shuts down the voice interface."""
        logger.info("Shutting down VoiceInterface.")
        if self.hotkey_listener_task:
            # This won't directly stop keyboard.wait, but it's good practice
            self.hotkey_listener_task.cancel()
        if self.current_brain_task:
            self.current_brain_task.cancel()
        if self.autonomy_consumer_task:
            self.autonomy_consumer_task.cancel()
        # Stop passive listener
        self.stt_manager.stop_wake_listener()
        if self.autonomy:
            self.autonomy.stop()

    async def _consume_autonomy_suggestions(self):
        """Continuously consumes autonomous suggestions with context-aware confirmation."""
        while True:
            await asyncio.sleep(0.1)
            if self.state != VoiceState.IDLE:
                continue
            if not self.autonomy:
                await asyncio.sleep(1)
                continue
            suggestion = await self.autonomy.get_next_suggestion_async(timeout_s=0.1)
            if not suggestion:
                continue
            # Double-check idle before processing
            if self.state == VoiceState.IDLE:
                # Use confirmation manager for context-aware confirmation
                await self.confirmation_manager.add_suggestion(suggestion)

    async def _confirm_autonomy(self) -> bool:
        """
        Ask the user if they want to hear an autonomous suggestion.
        Returns True if user confirms, False otherwise.
        """
        prompt = self.autonomy_cfg.get("confirm_prompt", "I have a suggestion. Would you like to hear it?")
        yes_words = [w.lower() for w in self.autonomy_cfg.get("confirm_yes_keywords", ["yes", "sure", "go ahead", "okay"]) ]
        no_words = [w.lower() for w in self.autonomy_cfg.get("confirm_no_keywords", ["no", "not now", "later"]) ]
        timeout_s = int(self.autonomy_cfg.get("confirm_timeout_s", 4))

        # Speak the confirmation prompt
        self.state = VoiceState.SPEAKING
        await self.tts_manager.speak_async(prompt)
        # Listen briefly for a response
        self.state = VoiceState.LISTENING
        try:
            resp = await asyncio.wait_for(self.stt_manager.listen_and_transcribe(), timeout=timeout_s)
        except asyncio.TimeoutError:
            resp = None
        except Exception:
            logger.exception("Error during autonomy confirmation listening.")
            resp = None
        finally:
            # If we were interrupted by barge-in elsewhere, state might have changed.
            if self.state == VoiceState.LISTENING:
                self.state = VoiceState.IDLE

        if not resp:
            return False
        r = resp.strip().lower()
        if any(word in r for word in yes_words):
            return True
        if any(word in r for word in no_words):
            return False
        # Default to not speaking if unclear
        return False
