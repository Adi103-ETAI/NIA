# interface/console_interface.py
"""
Console interface: orchestrates InputManager -> Brain -> MemoryManager -> OutputManager
"""

from __future__ import annotations
import logging

from core.input_manager import InputManager
from core.output_manager import OutputManager
from core.brain import Brain
from core.memory_manager import MemoryManager

logger = logging.getLogger("nia.console")

class ConsoleInterface:
    def __init__(self, brain: Brain):
        self.input = InputManager()
        self.output = OutputManager()
        self.brain = brain
        self.memory = MemoryManager()

    def run(self) -> None:
        logger.info("Console interface started.")
        print("NIA (console). Type 'exit' or 'quit' to stop.\n")
        while True:
            text = self.input.get_text("You: ")
            if text is None:
                logger.info("Input ended. Exiting.")
                print("Exiting.")
                break

            if text.lower() in ("exit", "quit"):
                logger.info("User requested exit.")
                print("Goodbye.")
                break

            logger.info("USER: %s", text)
            self.memory.store("user", text)

            resp = self.brain.generate(text)
            self.memory.store("nia", resp)

            self.output.say(resp)
