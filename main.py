# main.py
"""
Entry point for NIA.
Initializes logging, brain, and the selected user interface.
"""

import asyncio
import logging
import os

from core.config import settings

def setup_logging():
    os.makedirs(os.path.join("data", "logs"), exist_ok=True)
    logger = logging.getLogger("nia")
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s", "%Y-%m-%d %H:%M:%S")

    # console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    # file handler
    fh = logging.FileHandler(os.path.join("data", "logs", "system.log"), encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    eh = logging.FileHandler(os.path.join("data", "logs", "error.log"), encoding="utf-8")
    eh.setLevel(logging.ERROR)
    eh.setFormatter(fmt)

    if not logger.handlers:
        logger.addHandler(ch)
        logger.addHandler(fh)
        logger.addHandler(eh)

    return logger

async def main():
    """Asynchronous main entry point for NIA."""
    logger = setup_logging()
    logger.info("Starting NIA")

    # Imports are now here to ensure config is loaded first
    from core.brain import Brain
    from core.tts_manager import TTSManager
    from core.stt_manager import STTManager # Import the new manager
    from core.autonomy_agent import AutonomyAgent
    from interface.console_interface import ConsoleInterface
    from interface.voice_interface import VoiceInterface

    # Use settings from the new config system
    use_voice = os.getenv("NIA_USE_VOICE", "true").lower() in ("true", "1", "yes")
    
    brain = Brain(
        model=settings["brain"]["model"],
        timeout=settings["brain"]["timeout_s"],
    )
    logger.info("Brain health: %s", brain.health_check())
    
    loop = asyncio.get_event_loop()
    tts_manager = None
    stt_manager = None # Add stt_manager
    autonomy = None
    
    try:
        if use_voice:
            tts_manager = TTSManager(loop)
            stt_manager = STTManager(loop) # Initialize it
            autonomy = AutonomyAgent(loop)
            logger.info("Using voice interface.")
            voice_iface = VoiceInterface(brain, tts_manager, stt_manager, autonomy) # Pass it in
            await voice_iface.start()
        else:
            logger.info("Using console interface.")
            console = ConsoleInterface(brain)
            await loop.run_in_executor(None, console.run)
    finally:
        logger.info("NIA is shutting down...")
        if use_voice and voice_iface:
            await voice_iface.shutdown()
        if tts_manager:
            tts_manager.shutdown()
        if stt_manager:
            # The shutdown for stt_manager is blocking, run in executor
            if loop.is_running():
                await loop.run_in_executor(None, stt_manager.shutdown)
            else:
                stt_manager.shutdown()
        if brain:
            await brain.close()
        logger.info("NIA shutdown complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.getLogger("nia").info("NIA shutdown requested by user.")
