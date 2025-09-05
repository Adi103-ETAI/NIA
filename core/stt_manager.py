# core/stt_manager.py
"""
Manages Speech-to-Text (STT) operations using a streaming audio model (Vosk),
with optional Silero VAD for voice activity detection and DeepFilterNet for
noise suppression. All enhancements are feature-flagged via config.
"""
import asyncio
import json
import logging
import queue
from typing import Optional

import sounddevice as sd
from vosk import Model, KaldiRecognizer
import numpy as np

from core.config import settings

logger = logging.getLogger("nia.core.stt_manager")


# --- Optional provider wrappers -------------------------------------------------

class _SileroVADProvider:
    """Wrapper around Silero VAD providing a simple frame-based API.

    Falls back to disabled state if dependencies or model loading fail.
    """

    def __init__(self, sample_rate: int):
        self.sample_rate = sample_rate
        self._enabled = False
        self._vad_iter = None
        try:
            import torch  # noqa: F401
            # Load the PyTorch model via torch.hub
            vad_model, _ = __import__("torch").hub.load('snakers4/silero-vad', 'silero_vad', onnx=False)
            from silero_vad import VADIterator  # type: ignore
            self._vad_iter = VADIterator(vad_model, sampling_rate=self.sample_rate)
            self._enabled = True
            logger.info("Silero VAD initialized (sample_rate=%s).", self.sample_rate)
        except Exception as e:
            logger.warning("Silero VAD unavailable, VAD disabled. Reason: %s", e)
            self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    def process_frame(self, audio_float_mono: np.ndarray) -> bool:
        """Return True if frame contains speech, False otherwise.

        If disabled, always returns True (no gating).
        """
        if not self._enabled:
            return True
        try:
            import torch
            frame_t = torch.from_numpy(audio_float_mono)
            # VADIterator returns True/False-like for speech frames
            result = self._vad_iter(frame_t)
            return bool(result)
        except Exception as e:
            logger.error("Silero VAD runtime error; disabling VAD. Reason: %s", e)
            self._enabled = False
            return True


class _DeepFilterNetProvider:
    """Wrapper for DeepFilterNet enhancement with graceful fallback."""

    def __init__(self, model_dir: Optional[str], sample_rate: int):
        self.sample_rate = sample_rate
        self._enabled = False
        self._enhancer = None
        if not model_dir:
            return
        try:
            from df.enhance import Enhancer  # type: ignore
            self._enhancer = Enhancer(model_dir=model_dir)
            self._enabled = True
            logger.info("DeepFilterNet enhancer initialized (model_dir=%s).", model_dir)
        except Exception as e:
            logger.warning("DeepFilterNet unavailable, enhancement disabled. Reason: %s", e)
            self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    def enhance_frame(self, audio_float_mono: np.ndarray) -> np.ndarray:
        if not self._enabled:
            return audio_float_mono
        try:
            # The Enhancer API supports streaming; use frame-wise enhancement.
            enhanced = self._enhancer.enhance_frame(audio_float_mono, sr=self.sample_rate)
            return enhanced
        except Exception as e:
            logger.error("DeepFilterNet runtime error; disabling enhancement. Reason: %s", e)
            self._enabled = False
            return audio_float_mono


class STTManager:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self.sample_rate = 16000
        self.blocksize = 8000
        self.model_path = settings["stt"]["vosk_model_path"]
        try:
            self.model = Model(self.model_path)
        except Exception as e:
            logger.error(
                "Failed to load Vosk model from '%s'. "
                "Please ensure you have downloaded and placed the model correctly.",
                self.model_path
            )
            raise e

        self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self._stop_event = asyncio.Event()
        self.stream = None

        # Feature flags and providers
        stt_cfg = settings.get("stt", {})
        self.use_vad = bool(stt_cfg.get("vad", False)) and (stt_cfg.get("vad_engine", "").lower() == "silero")
        self.vad_trigger_ms = int(stt_cfg.get("vad_trigger_ms", 250))
        self.vad_release_ms = int(stt_cfg.get("vad_release_ms", 300))
        self.use_dfn = bool(stt_cfg.get("deepfilternet", False))
        self.dfn_model_dir = stt_cfg.get("deepfilternet_model_dir", None)

        self.vad_provider: Optional[_SileroVADProvider] = None
        if self.use_vad:
            self.vad_provider = _SileroVADProvider(self.sample_rate)
            if not self.vad_provider.enabled:
                self.use_vad = False

        self.dfn_provider: Optional[_DeepFilterNetProvider] = None
        if self.use_dfn:
            self.dfn_provider = _DeepFilterNetProvider(self.dfn_model_dir, self.sample_rate)
            if not self.dfn_provider.enabled:
                self.use_dfn = False

    def _audio_callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            logger.warning("Audio callback status: %s", status)
        if self.is_listening:
            # Keep callback lightweight; push raw PCM to queue
            self.audio_queue.put(bytes(indata))

    async def listen_and_transcribe(self) -> str | None:
        """
        Listens for speech and returns the final transcript.
        This is an async method that handles the streaming audio loop.
        """
        self.is_listening = True
        self._stop_event.clear()
        logger.info("STTManager is now listening.")
        
        transcription_complete = self.loop.create_future()
        self.loop.run_in_executor(None, self._transcription_loop, transcription_complete)

        try:
            return await transcription_complete
        except asyncio.CancelledError:
            logger.info("STT transcription was cancelled.")
            self._stop_event.set()
            # The future might be cancelled before a result is set
            if not transcription_complete.done():
                # This ensures the transcription_loop can exit if it's waiting on the future
                transcription_complete.cancel()
            await asyncio.sleep(0.2) 
            return None
        finally:
            self.is_listening = False
            logger.info("STTManager stopped listening.")

    def _transcription_loop(self, future: asyncio.Future):
        """
        The core loop that processes audio from the queue with Vosk.
        This runs in a thread to not block the main event loop.
        """
        try:
            self.stream = sd.RawInputStream(samplerate=self.sample_rate, blocksize=self.blocksize, dtype='int16',
                                            channels=1, callback=self._audio_callback)
            with self.stream:
                full_transcript = ""
                in_speech = False
                speech_ms = 0
                silence_ms = 0
                
                while not self._stop_event.is_set():
                    try:
                        data = self.audio_queue.get(timeout=0.1)
                        # Compute frame duration in ms based on byte length
                        num_samples = len(data) // 2  # int16 mono
                        frame_ms = int(1000 * num_samples / self.sample_rate)

                        # Convert to float32 mono [-1, 1] for VAD/DFN
                        audio_float = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

                        is_speech_frame = True
                        if self.use_vad and self.vad_provider is not None:
                            is_speech_frame = self.vad_provider.process_frame(audio_float)

                        if is_speech_frame:
                            speech_ms += frame_ms
                            silence_ms = 0
                            if not in_speech and speech_ms >= self.vad_trigger_ms:
                                in_speech = True

                            # Enhance if enabled
                            if self.use_dfn and self.dfn_provider is not None:
                                audio_float = self.dfn_provider.enhance_frame(audio_float)
                            # Back to int16 bytes
                            data = (np.clip(audio_float, -1.0, 1.0) * 32767).astype(np.int16).tobytes()

                            # Feed recognizer only during speech windows
                            if self.recognizer.AcceptWaveform(data):
                                result = json.loads(self.recognizer.Result())
                                text = result.get("text", "")
                                if text:
                                    full_transcript += f" {text}"
                            else:
                                # Partial accepted; we do not accumulate partials here
                                _ = self.recognizer.PartialResult()
                        else:
                            # Non-speech frame
                            silence_ms += frame_ms
                            speech_ms = 0
                            if in_speech and silence_ms >= self.vad_release_ms:
                                # End-of-utterance detected
                                break
                    except queue.Empty:
                        # Timeout waiting for audio; use fallback idle detection if VAD off
                        if not self.use_vad:
                            silence_ms += 100
                            if silence_ms >= 2000 and full_transcript:
                                break
                
                final_result = json.loads(self.recognizer.FinalResult())
                full_transcript += f" {final_result.get('text', '')}"

                if not future.done():
                    self.loop.call_soon_threadsafe(future.set_result, full_transcript.strip())
        except Exception as e:
            logger.exception("Error in STT transcription loop.")
            if not future.done():
                self.loop.call_soon_threadsafe(future.set_exception, e)

    def shutdown(self):
        """Signals the transcription loop to stop and closes the audio stream."""
        logger.info("Shutting down STTManager.")
        self._stop_event.set()
        if self.stream and not self.stream.closed:
            # This is a blocking call, but it's necessary to ensure the stream is closed.
            # Since we're shutting down, a small block is acceptable.
            self.stream.stop()
            self.stream.close()
        logger.info("STTManager shutdown complete.")
