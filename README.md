# NIA - Neural Intelligence Assistant

A voice-enabled AI assistant with real-time speech-to-text, text-to-speech, and language model integration.

## Features

- **Voice Interface**: Press SPACE to speak, with barge-in support
- **Speech-to-Text**: Vosk-based offline STT with optional Silero VAD and DeepFilterNet enhancement
- **Text-to-Speech**: Streaming TTS with multiple engine support
- **Language Model**: Ollama integration with streaming responses
- **Real-time Processing**: Low-latency voice interaction
- **Semantic Memory**: LanceDB-powered conversation memory with Ollama embeddings
- **Context-Aware Autonomy**: Intelligent suggestions based on conversation history and decision patterns
- **Knowledge Management**: Vector-based knowledge retrieval and storage

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

7. Install Ollama and pull required models:
```bash
# Install Ollama (visit https://ollama.ai for installation instructions)
# Pull the main language model
ollama pull qwen3:4b
# Pull the embedding model for semantic memory
ollama pull nomic-embed-text
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

# Memory and Knowledge Management
memory:
  enabled: true                      # Enable semantic memory
  db_path: "data/memory"            # LanceDB storage path
  collection: "conversations"       # Collection name
  embedding_model: "nomic-embed-text"  # Ollama embedding model
  enable_embeddings: true           # Enable vector embeddings
  max_recent_queries: 5             # Max recent messages to retrieve
  min_similarity_score: 0.7        # Minimum similarity threshold

knowledge:
  enabled: true                     # Enable knowledge management
  retriever_type: "vector"          # Vector-based retrieval
  top_k: 5                          # Number of results to return
  sources: []                       # Knowledge sources
  index_path: "data/knowledge"      # Knowledge index path
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

## Memory and Knowledge Management

NIA includes a sophisticated memory system that learns from your conversations and provides context-aware responses.

### Semantic Memory System

The memory system uses **LanceDB** for persistent storage and **Ollama embeddings** for semantic understanding:

- **Conversation Storage**: All interactions are automatically stored with timestamps
- **Semantic Search**: Find relevant past conversations using natural language queries
- **Vector Embeddings**: Messages are converted to embeddings using the `nomic-embed-text` model
- **Context Retrieval**: Recent and relevant conversations are retrieved for context-aware responses

### How Memory Works

1. **Automatic Storage**: Every user input and NIA response is stored in the memory database
2. **Semantic Indexing**: Messages are embedded into vector space for semantic similarity
3. **Context Retrieval**: When you ask questions, NIA searches for relevant past conversations
4. **Memory Integration**: Retrieved context is included in responses for more personalized interactions

### Memory Configuration

Configure memory settings in `config/settings.yaml`:

```yaml
memory:
  enabled: true                      # Enable/disable memory system
  db_path: "data/memory"            # LanceDB database path
  collection: "conversations"       # Collection name for conversations
  embedding_model: "nomic-embed-text"  # Ollama embedding model
  enable_embeddings: true           # Enable vector embeddings
  max_recent_queries: 5             # Maximum recent messages to retrieve
  min_similarity_score: 0.7        # Minimum similarity score for retrieval
```

### Knowledge Management

The knowledge system provides long-term information storage and retrieval:

- **Vector Storage**: Knowledge items are stored as embeddings for semantic search
- **Flexible Sources**: Support for various knowledge sources and formats
- **Top-K Retrieval**: Configurable number of most relevant results
- **Integration**: Knowledge is seamlessly integrated with conversation context

### Knowledge Configuration

```yaml
knowledge:
  enabled: true                     # Enable/disable knowledge system
  retriever_type: "vector"          # Vector-based retrieval method
  top_k: 5                          # Number of top results to return
  sources: []                       # Knowledge sources (expandable)
  index_path: "data/knowledge"      # Knowledge index storage path
```

## Context-Aware Autonomy Mode

NIA includes an intelligent autonomy system that uses conversation memory to provide context-aware suggestions. The system detects decision points and offers helpful suggestions based on your conversation history.

### How Context-Aware Autonomy Works

1. **Decision-Point Detection**: NIA analyzes your speech for decision indicators:
   - **Decision keywords**: "should I", "what if", "maybe", "I'm not sure", "help me decide"
   - **High-value topics**: work, project, meeting, deadline, plan, schedule, task, problem, issue
   - **Hesitation patterns**: "um", "uh", "well", "I mean", "you know"
   - **Repetition**: When you mention the same topic multiple times

2. **Memory-Enhanced Suggestions**: When NIA detects a decision point:
   - **Semantic Search**: Queries conversation memory for relevant past discussions
   - **Context Retrieval**: Finds similar situations or topics from your history
   - **Intelligent Suggestions**: Generates suggestions based on both current context and past conversations
   - **Confidence Scoring**: Uses confidence thresholds to determine suggestion quality

3. **Polite Confirmation Flow**: 
   - Waits for 2-3 seconds of silence (idle detection)
   - Asks politely: "I have a suggestion that might help—would you like to hear it?"
   - Only proceeds if you confirm with "yes", "sure", "okay", etc.
   - Cancels if you say "no", "not now", "later", or if there's no response

4. **Barge-in Priority**: Your active interactions always take priority:
   - Pressing SPACE or using wake words interrupts any autonomy suggestions
   - NIA pauses autonomy during active conversations
   - Resumes autonomy only when you're idle

5. **Memory Integration**: 
   - **Context-Aware Responses**: Suggestions include relevant past conversation snippets
   - **Learning from History**: NIA learns from your preferences and decision patterns
   - **Semantic Understanding**: Uses embeddings to find semantically similar past discussions

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
  # Memory integration for context-aware suggestions
  use_memory: true                       # Enable memory-based suggestions
  max_memory_snippets: 5                 # Maximum memory snippets to include
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
├── core/                           # Core functionality
│   ├── brain.py                   # LLM integration with streaming
│   ├── stt_manager.py             # Speech-to-text with VAD and enhancement
│   ├── tts_manager.py             # Text-to-speech with streaming
│   ├── autonomy_agent.py          # Context-aware autonomy system
│   ├── confirmation_manager.py    # Autonomy confirmation flow
│   ├── memory_manager.py          # Semantic memory with LanceDB
│   ├── knowledge_manager.py       # Knowledge retrieval and storage
│   ├── personality.py             # Personality configuration
│   └── config.py                  # Configuration loader
├── interface/                      # User interfaces
│   ├── voice_interface.py         # Voice interaction interface
│   └── console_interface.py       # Console interface
├── config/                         # Configuration files
│   ├── settings.yaml              # Main configuration
│   └── personality.yaml           # Personality settings
├── data/                          # Data storage
│   ├── memory/                    # LanceDB memory database
│   ├── knowledge/                 # Knowledge base storage
│   └── logs/                      # Application logs
├── model/                         # AI models
│   └── vosk-model-small-en-us-0.15/  # Vosk STT model
├── tests/                         # Test suite
│   ├── test_hybrid.py            # Autonomy system tests
│   ├── test_memory.py            # Memory system tests
│   └── test_knowledge.py         # Knowledge system tests
└── requirements.txt              # Python dependencies
```

### Adding New Features

1. Core functionality goes in `core/`
2. User interfaces go in `interface/`
3. Configuration goes in `config/`
4. Update `requirements.txt` for new dependencies

## License

[Add your license information here]
