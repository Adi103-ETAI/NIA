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

import speech_recognition as sr
import keyboard

from core.brain import Brain
from core.config import settings
import asyncio
import logging
from enum import Enum, auto

import keyboard

from core.brain import Brain
from core.config import settings
from core.tts_manager import TTSManager
from core.stt_manager import STTManager # Import the new manager

logger = logging.getLogger("nia.interface.voice")

class VoiceState(Enum):
    IDLE = auto()
    LISTENING = auto()
    THINKING = auto()
    SPEAKING = auto()

class VoiceInterface:
    def __init__(self, brain: Brain, tts_manager: TTSManager, stt_manager: STTManager):
        self.brain = brain
        self.tts_manager = tts_manager
        self.stt_manager = stt_manager # Use the new manager
        self.hotkey = settings["voice"]["hotkey"]
        
        self.state = VoiceState.IDLE
        self.current_brain_task = None
        self.loop = asyncio.get_event_loop()
        self.hotkey_listener_task = None

    async def start(self):
        """Starts the main voice interface loop and hotkey listener."""
        logger.info(f"VoiceInterface started. Press '{self.hotkey.upper()}' to speak.")
        # Start the hotkey listener as a managed asyncio task
        self.hotkey_listener_task = self.loop.run_in_executor(None, self._hotkey_listener)
        
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
                asyncio.run_coroutine_threadsafe(self.handle_hotkey_press(), self.loop)
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
            # The existing listen_and_respond task will catch the cancellation
            # and transition to IDLE. The new listening session will start from there.
            return # Stop here, let the existing flow handle the state change.

        # If we are idle, start a new listening session.
        if self.state == VoiceState.IDLE:
            await self.listen_and_respond()
        else:
            logger.warning("Hotkey pressed in an unexpected state: %s", self.state)

    async def listen_and_respond(self):
        """Listens for user input, processes it, and generates a response."""
        self.state = VoiceState.LISTENING
        logger.info("State changed to LISTENING")
        
        user_text = await self._recognize_speech()
        if not user_text:
            self.state = VoiceState.IDLE
            logger.info("State changed to IDLE (no speech recognized)")
            return

        self.state = VoiceState.THINKING
        logger.info("State changed to THINKING")
        
        # Create and run the brain streaming task
        self.current_brain_task = asyncio.create_task(self._stream_brain_to_tts(user_text))
        
        try:
            await self.current_brain_task
        except asyncio.CancelledError:
            logger.info("Brain stream was cancelled due to barge-in.")
        
        self.state = VoiceState.IDLE
        logger.info("State changed to IDLE (response finished)")

    async def _recognize_speech(self) -> str | None:
        """
        Recognizes speech using the streaming STTManager.
        """
        print("Listening...")
        try:
            # This single call now handles the entire streaming recognition process
            user_text = await self.stt_manager.listen_and_transcribe()
            
            if user_text:
                print(f"You said: {user_text}")
                logger.info("USER (voice): %s", user_text)
                return user_text
            else:
                print("Sorry, I didn't catch that.")
                return None
        except Exception as e:
            logger.exception("An error occurred during speech recognition.")
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
