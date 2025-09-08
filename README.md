# NIA - Neural Intelligence Assistant

A voice-enabled AI assistant with real-time speech-to-text, text-to-speech, and language model integration.

## Features

- **Voice Interface**: Press SPACE to speak, with barge-in support
- **Speech-to-Text**: Vosk-based offline STT with optional Silero VAD and DeepFilterNet enhancement
- **Text-to-Speech**: Streaming TTS with multiple engine support
- **Language Model**: Ollama integration with streaming responses
- **Real-time Processing**: Low-latency voice interaction
- **Hybrid Autonomy**: Intelligent decision-point detection with polite confirmation flow

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

2. Activate NIA in one of these ways:
   - **Press SPACE**: Start/stop speaking (push-to-talk)
   - **Say wake words**: "NIA", "Hey NIA", "Okay NIA", "Buddy", "Hey Buddy" (hands-free)
   - **Wait for autonomy**: NIA may offer suggestions when it detects decision points

3. NIA will process your speech and respond

### Voice Commands

- **Press SPACE**: Start/stop speaking (push-to-talk mode)
- **Say wake words**: "NIA", "Hey NIA", "Okay NIA", "Buddy", "Hey Buddy" (hands-free mode)
- **Press SPACE while NIA is speaking**: Barge-in (interrupt and speak)
- **Respond to autonomy prompts**: "Yes" to hear suggestions, "No" to decline

## Hybrid Autonomy Mode (Optional)

NIA includes an intelligent autonomy system that can detect when you're facing decisions or need help, and politely offer suggestions. This feature is designed to be helpful without being intrusive.

### How It Works

1. **Decision-Point Detection**: NIA analyzes your speech for decision indicators like:
   - Decision keywords: "should I", "what if", "maybe", "I'm not sure", "help me decide"
   - High-value topics: work, project, meeting, deadline, plan, schedule, task, problem, issue
   - Hesitation patterns: "um", "uh", "well", "I mean", "you know"
   - Repetition: When you mention the same topic multiple times

2. **Polite Confirmation Flow**: When NIA detects a decision point:
   - Waits for 2-3 seconds of silence (idle detection)
   - Asks politely: "I have a suggestion that might help—would you like to hear it?"
   - Only proceeds if you confirm with "yes", "sure", "okay", etc.
   - Cancels if you say "no", "not now", "later", or if there's no response

3. **Barge-in Priority**: Your active interactions always take priority:
   - Pressing SPACE or using wake words interrupts any autonomy suggestions
   - NIA pauses autonomy during active conversations
   - Resumes autonomy only when you're idle

4. **Configurable Behavior**: All autonomy settings can be customized in `config/settings.yaml`

### Configuration

Add or modify the autonomy section in `config/settings.yaml`:

```yaml
autonomy:
  enabled: true                           # Enable/disable autonomy
  confirm_before_speaking: true          # Always ask before speaking suggestions
  confirm_prompt: "I have a suggestion that might help—would you like to hear it?"
  confirm_yes_keywords:                  # Keywords that confirm suggestions
    - "yes"
    - "sure" 
    - "okay"
    - "go ahead"
    - "please"
    - "sounds good"
  confirm_no_keywords:                   # Keywords that decline suggestions
    - "no"
    - "not now"
    - "later"
    - "skip"
    - "dismiss"
  confirm_timeout_s: 4                   # Seconds to wait for confirmation
  suggestion_interval_s: 90              # Minimum seconds between suggestions
  confidence_threshold: 0.6              # Minimum confidence to suggest (0.0-1.0)
  decision_keywords:                     # Customize decision detection keywords
    - "should i"
    - "what if"
    - "maybe"
    - "i think"
    - "i'm not sure"
    - "help me decide"
  high_value_topics:                     # Topics that trigger suggestions
    - "work"
    - "project"
    - "meeting"
    - "deadline"
    - "plan"
    - "schedule"
    - "task"
    - "problem"
    - "issue"
    - "decision"
    - "choice"
    - "option"
    - "strategy"
```

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

### Autonomy Issues

- **Autonomy suggestions too frequent**: Adjust `autonomy.suggestion_interval_s` or `autonomy.confidence_threshold` in `config/settings.yaml`
- **Autonomy not working**: Check that `autonomy.enabled` is set to `true` in `config/settings.yaml`
- **Suggestions too intrusive**: Increase `autonomy.confidence_threshold` or disable `autonomy.confirm_before_speaking`

## Development

### Project Structure

```
NIA/
├── core/                    # Core functionality
│   ├── brain.py            # LLM integration
│   ├── stt_manager.py      # Speech-to-text
│   ├── tts_manager.py      # Text-to-speech
│   ├── autonomy_agent.py   # Hybrid autonomy system
│   ├── confirmation_manager.py  # Autonomy confirmation flow
│   └── config.py           # Configuration
├── interface/              # User interfaces
│   └── voice_interface.py
├── config/                 # Configuration files
│   └── settings.yaml
├── model/                  # AI models
├── tests/                  # Test suite
│   └── test_hybrid.py     # Hybrid autonomy tests
└── data/logs/             # Log files
```

### Adding New Features

1. Core functionality goes in `core/`
2. User interfaces go in `interface/`
3. Configuration goes in `config/`
4. Update `requirements.txt` for new dependencies

## License

[Add your license information here]
