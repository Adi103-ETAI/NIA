# core/tts_engine.py
"""
TTS Engine with Coqui TTS (VITS/Glow-TTS) as primary and pyttsx3 as fallback.
Provides seamless TTS functionality with automatic fallback to pyttsx3 on errors.
"""

import logging
import os
import tempfile
import threading
from typing import Optional

logger = logging.getLogger("nia.core.tts_engine")

# Global variables for TTS engines
_coqui_tts = None
_pyttsx3_engine = None
_tts_lock = threading.Lock()

def _init_coqui_tts():
    """Initialize Coqui TTS model (CPU-only)."""
    global _coqui_tts
    
    if _coqui_tts is not None:
        return _coqui_tts
    
    try:
        from TTS.api import TTS
        
        # Use CPU-only mode to avoid CUDA issues
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        
        # Load a lightweight VITS model
        model_name = "tts_models/en/ljspeech/vits"
        logger.info(f"Loading Coqui TTS model: {model_name}")
        
        _coqui_tts = TTS(model_name=model_name, progress_bar=False)
        logger.info("Coqui TTS model loaded successfully")
        return _coqui_tts
        
    except Exception as e:
        logger.warning(f"Failed to initialize Coqui TTS: {e}")
        _coqui_tts = None
        return None

def _init_pyttsx3():
    """Initialize pyttsx3 engine as fallback."""
    global _pyttsx3_engine
    
    if _pyttsx3_engine is not None:
        return _pyttsx3_engine
    
    try:
        import pyttsx3
        _pyttsx3_engine = pyttsx3.init()
        
        # Configure pyttsx3 with reasonable defaults
        _pyttsx3_engine.setProperty("rate", 150)  # Speech rate
        
        # Try to set a good voice
        voices = _pyttsx3_engine.getProperty("voices")
        if voices:
            # Prefer female voices if available
            for voice in voices:
                if "female" in voice.name.lower() or "zira" in voice.name.lower():
                    _pyttsx3_engine.setProperty("voice", voice.id)
                    break
            else:
                # Use first available voice
                _pyttsx3_engine.setProperty("voice", voices[0].id)
        
        logger.info("pyttsx3 engine initialized successfully")
        return _pyttsx3_engine
        
    except Exception as e:
        logger.error(f"Failed to initialize pyttsx3: {e}")
        _pyttsx3_engine = None
        return None

def _play_audio_file(file_path: str) -> bool:
    """Play audio file using sounddevice or pygame."""
    try:
        import sounddevice as sd
        import soundfile as sf
        
        # Load and play audio
        data, sample_rate = sf.read(file_path)
        sd.play(data, sample_rate)
        sd.wait()  # Wait until playback is finished
        return True
        
    except ImportError:
        # Fallback to pygame if sounddevice is not available
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
            return True
        except Exception as e:
            logger.error(f"Failed to play audio with pygame: {e}")
            return False
    except Exception as e:
        logger.error(f"Failed to play audio with sounddevice: {e}")
        return False

def speak(text: str, use_coqui: bool = True) -> bool:
    """
    Speak text using Coqui TTS (primary) or pyttsx3 (fallback).
    
    Args:
        text: Text to speak
        use_coqui: Whether to try Coqui TTS first (default: True)
    
    Returns:
        bool: True if speech was successful, False otherwise
    """
    if not text or not text.strip():
        return True
    
    text = text.strip()
    logger.debug(f"Speaking text: '{text[:50]}{'...' if len(text) > 50 else ''}'")
    
    with _tts_lock:
        # Try Coqui TTS first if requested and available
        if use_coqui:
            coqui_engine = _init_coqui_tts()
            if coqui_engine is not None:
                try:
                    logger.info("Using Coqui TTS engine")
                    
                    # Create temporary file for audio output
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                        temp_path = temp_file.name
                    
                    # Generate speech
                    coqui_engine.tts_to_file(text=text, file_path=temp_path)
                    
                    # Play the generated audio
                    if _play_audio_file(temp_path):
                        # Clean up temporary file
                        try:
                            os.unlink(temp_path)
                        except OSError:
                            pass
                        return True
                    else:
                        logger.warning("Failed to play Coqui TTS audio, falling back to pyttsx3")
                except Exception as e:
                    logger.warning(f"Coqui TTS failed: {e}, falling back to pyttsx3")
                finally:
                    # Clean up temporary file if it exists
                    try:
                        if 'temp_path' in locals():
                            os.unlink(temp_path)
                    except OSError:
                        pass
        
        # Fallback to pyttsx3
        pyttsx3_engine = _init_pyttsx3()
        if pyttsx3_engine is not None:
            try:
                logger.info("Using pyttsx3 engine (fallback)")
                pyttsx3_engine.say(text)
                pyttsx3_engine.runAndWait()
                return True
            except Exception as e:
                logger.error(f"pyttsx3 failed: {e}")
                return False
        else:
            logger.error("Both TTS engines failed to initialize")
            return False

def is_coqui_available() -> bool:
    """Check if Coqui TTS is available."""
    return _init_coqui_tts() is not None

def is_pyttsx3_available() -> bool:
    """Check if pyttsx3 is available."""
    return _init_pyttsx3() is not None

def get_available_engines() -> list:
    """Get list of available TTS engines."""
    engines = []
    if is_coqui_available():
        engines.append("coqui")
    if is_pyttsx3_available():
        engines.append("pyttsx3")
    return engines

def shutdown():
    """Shutdown TTS engines."""
    global _coqui_tts, _pyttsx3_engine
    
    with _tts_lock:
        if _pyttsx3_engine is not None:
            try:
                _pyttsx3_engine.stop()
            except Exception as e:
                logger.warning(f"Error stopping pyttsx3: {e}")
            _pyttsx3_engine = None
        
        _coqui_tts = None
        logger.info("TTS engines shutdown complete")

if __name__ == "__main__":
    # Test the TTS engine
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testing TTS Engine...")
    print(f"Available engines: {get_available_engines()}")
    
    test_text = "Hello from NIA! This is a test of the TTS engine integration."
    
    print(f"\nSpeaking: '{test_text}'")
    success = speak(test_text)
    
    if success:
        print("✓ TTS test completed successfully")
    else:
        print("✗ TTS test failed")
    
    print(f"Engine used: {'Coqui TTS' if is_coqui_available() else 'pyttsx3'}")
