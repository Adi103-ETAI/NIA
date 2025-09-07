# TTS Integration Documentation

## Overview

NIA now supports VITS/Glow-TTS via Coqui TTS library as the primary TTS engine, with pyttsx3 as automatic fallback. This provides high-quality neural text-to-speech while maintaining compatibility and reliability.

## Architecture

### Primary Engine: Coqui TTS
- **Model**: `tts_models/en/ljspeech/vits` (VITS architecture)
- **Quality**: High-quality neural TTS with natural-sounding speech
- **CPU-only**: Configured to run on CPU to avoid CUDA dependency issues
- **Format**: Generates WAV audio files for playback

### Fallback Engine: pyttsx3
- **Purpose**: Reliable fallback when Coqui TTS is unavailable
- **Compatibility**: Works on Windows, Linux, and macOS
- **Features**: System TTS integration with configurable voices

## Files Modified

### New Files
- `core/tts_engine.py` - Main TTS engine module with Coqui/pyttsx3 integration

### Modified Files
- `requirements.txt` - Added torch, torchaudio, TTS, soundfile, pygame
- `core/tts_manager.py` - Updated to use new tts_engine module

## Usage

### Basic Usage
```python
from core.tts_engine import speak

# Speak text (tries Coqui first, falls back to pyttsx3)
success = speak("Hello from NIA!")

# Force pyttsx3 usage
success = speak("Hello from NIA!", use_coqui=False)
```

### Engine Status
```python
from core.tts_engine import is_coqui_available, is_pyttsx3_available, get_available_engines

print(f"Coqui available: {is_coqui_available()}")
print(f"pyttsx3 available: {is_pyttsx3_available()}")
print(f"Available engines: {get_available_engines()}")
```

## Installation

### Dependencies
The following packages are required:
- `torch` - PyTorch for neural network inference
- `torchaudio` - Audio processing for PyTorch
- `TTS` - Coqui TTS library
- `soundfile` - Audio file I/O
- `pygame` - Alternative audio playback (fallback)
- `pyttsx3` - System TTS fallback (existing)

### Installation Commands
```bash
pip install torch torchaudio TTS soundfile pygame
```

**Note**: On Windows, TTS installation may require Microsoft Visual C++ Build Tools. If installation fails, the system will automatically fall back to pyttsx3.

## Configuration

### Environment Variables
- `CUDA_VISIBLE_DEVICES=""` - Forces CPU-only mode for Coqui TTS

### Model Selection
The default model is `tts_models/en/ljspeech/vits`. To use a different model, modify the `model_name` variable in `core/tts_engine.py`:

```python
model_name = "tts_models/en/ljspeech/vits"  # Default
# model_name = "tts_models/en/vctk/vits"    # Alternative
```

## Error Handling

The system includes comprehensive error handling:

1. **Coqui TTS Initialization Failure**: Automatically falls back to pyttsx3
2. **Audio Playback Failure**: Logs error and continues
3. **Model Loading Failure**: Falls back to pyttsx3
4. **File I/O Errors**: Graceful cleanup of temporary files

## Logging

The TTS engine provides detailed logging:
- `INFO`: Engine initialization and usage
- `WARNING`: Fallback activations and non-critical errors
- `ERROR`: Critical failures
- `DEBUG`: Detailed operation information

## Cross-Platform Compatibility

### Windows
- ✅ Coqui TTS (requires Visual C++ Build Tools)
- ✅ pyttsx3 (SAPI5 driver)
- ✅ sounddevice/soundfile for audio playback

### Linux
- ✅ Coqui TTS
- ✅ pyttsx3 (espeak driver)
- ✅ sounddevice/soundfile for audio playback

### macOS
- ✅ Coqui TTS
- ✅ pyttsx3 (NSSS driver)
- ✅ sounddevice/soundfile for audio playback

## Performance Considerations

### Coqui TTS
- **First Run**: Model loading takes 5-10 seconds
- **Subsequent Runs**: Fast synthesis (~1-2 seconds)
- **Memory Usage**: ~500MB-1GB RAM
- **CPU Usage**: Moderate during synthesis

### pyttsx3
- **Startup**: Instant
- **Synthesis**: Fast (~0.5-1 second)
- **Memory Usage**: Minimal (~50MB)
- **CPU Usage**: Low

## Troubleshooting

### Common Issues

1. **"No module named 'TTS'"**
   - Solution: Install TTS library or use pyttsx3 fallback

2. **"Microsoft Visual C++ 14.0 or greater is required"**
   - Solution: Install Visual C++ Build Tools or use pyttsx3 fallback

3. **Audio playback issues**
   - Solution: Check sounddevice/pygame installation

4. **Model download failures**
   - Solution: Check internet connection or use pyttsx3 fallback

### Testing
Run the test script to verify installation:
```bash
python core/tts_engine.py
```

This will test both engines and report which one is being used.

## Future Enhancements

- Support for additional Coqui TTS models
- Voice cloning capabilities
- Real-time streaming synthesis
- Custom voice training integration
- Multi-language support
