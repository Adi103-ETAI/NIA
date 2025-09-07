# NIA - Neural Intelligence Assistant

A voice-enabled AI assistant with real-time speech-to-text, text-to-speech, and language model integration.

## Features

- **Voice Interface**: Press SPACE to speak, with barge-in support
- **Speech-to-Text**: Vosk-based offline STT with optional Silero VAD and DeepFilterNet enhancement
- **Text-to-Speech**: Streaming TTS with multiple engine support
- **Language Model**: Ollama integration with streaming responses
- **Real-time Processing**: Low-latency voice interaction

## Installation

### Basic Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd NIA
```

2. Create and activate a virtual environment:
```bash
python -m venv venvNIA
# On Windows:
venvNIA\Scripts\activate
# On Linux/Mac:
source venvNIA/bin/activate
```

3. Install basic dependencies:
```bash
pip install -r requirements.txt
```

4. Install enhanced STT dependencies (recommended):
```bash
# Install PyTorch (CPU version for better compatibility)
pip install torch torchaudio -f https://download.pytorch.org/whl/cpu/torch_stable.html

# Install Silero VAD
pip install silero-vad

# Install DeepFilterNet from GitHub
pip install git+https://github.com/Rikorose/DeepFilterNet.git
```

5. Download the Vosk model:
```bash
# Download the small English model (39MB)
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
mv vosk-model-small-en-us-0.15 model/
```

6. Download DeepFilterNet models (optional, for noise suppression):
```bash
# Clone the DeepFilterNet models repository
git clone https://github.com/Rikorose/DeepFilterNet-models.git models/DeepFilterNet
```

### Enhanced STT Features (Optional)

For improved speech recognition accuracy, install additional dependencies:

#### Silero VAD (Voice Activity Detection)
```bash
# Install PyTorch (CPU version for better compatibility)
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Install Silero VAD
pip install silero-vad
```

#### DeepFilterNet (Noise Suppression)
```bash
# Install DeepFilterNet from GitHub
pip install git+https://github.com/Rikorose/DeepFilterNet.git

# Download DeepFilterNet models
git clone https://github.com/Rikorose/DeepFilterNet-models.git models/DeepFilterNet
```

### Configuration

Edit `config/settings.yaml` to enable enhanced features:

```yaml
stt:
  vad: true                    # Enable VAD
  vad_engine: "silero"         # Use Silero VAD
  deepfilternet: true          # Enable noise suppression
  deepfilternet_model_dir: "deepfilternet2"  # Model directory

stt_enhancement:
  model_dir: "models/DeepFilterNet"  # DeepFilterNet model directory
  enable: true                       # Enable audio enhancement
```

## Usage

1. Start the application:
```bash
python main.py
```

2. Press **SPACE** to start speaking
3. Release SPACE when finished speaking
4. NIA will process your speech and respond

### Voice Commands

- **Press SPACE**: Start/stop speaking
- **Press SPACE while NIA is speaking**: Barge-in (interrupt and speak)

## Troubleshooting

### STT Issues

- **"Silero VAD unavailable"**: Install torch and silero-vad as shown above
- **"DeepFilterNet unavailable"**: Install deepfilternet as shown above
- **Poor transcription quality**: Ensure VAD and DeepFilterNet are properly installed

### Audio Issues

- **No audio input**: Check microphone permissions and audio device settings
- **Audio feedback**: Adjust microphone sensitivity or use headphones

### Model Issues

- **"Failed to load Vosk model"**: Ensure the model is downloaded and placed in the `model/` directory
- **"Ollama model not found"**: Install and start Ollama, then pull the required model:
  ```bash
  ollama pull qwen3:4b
  ```

## Development

### Project Structure

```
NIA/
├── core/                 # Core functionality
│   ├── brain.py         # LLM integration
│   ├── stt_manager.py   # Speech-to-text
│   ├── tts_manager.py   # Text-to-speech
│   └── config.py        # Configuration
├── interface/           # User interfaces
│   └── voice_interface.py
├── config/              # Configuration files
│   └── settings.yaml
├── model/               # AI models
└── data/logs/          # Log files
```

### Adding New Features

1. Core functionality goes in `core/`
2. User interfaces go in `interface/`
3. Configuration goes in `config/`
4. Update `requirements.txt` for new dependencies

## License

[Add your license information here]
