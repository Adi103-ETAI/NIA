# NIA Enhanced - Multi-Provider LLM & Database Integration

This document outlines the enhanced features added to NIA, including multi-provider LLM support and comprehensive database integration.

## 🚀 New Features Overview

### 1. **Multi-Provider LLM Support**
- Support for **OpenAI GPT models** (GPT-4, GPT-3.5-turbo, etc.)
- Support for **Anthropic Claude models** (Claude-3.5-Sonnet, Claude-3-Haiku, etc.)
- **Ollama integration** (existing local models)
- **Automatic fallback** between providers
- **Streaming support** for all providers
- **Cost optimization** through provider selection

### 2. **Enhanced Database Integration**
- **SQLite, PostgreSQL, MySQL** support
- **Structured conversation storage** with metadata
- **Advanced analytics** and usage tracking
- **User management** and personalization
- **System health monitoring**
- **Redis caching** for performance
- **Automatic backups** and recovery

### 3. **Improved Memory System**
- **Hybrid storage** (vector + structured database)
- **Session-based conversations** with user context
- **Enhanced semantic search** with filtering
- **Conversation summaries** and analytics
- **Multi-user support** with privacy controls

### 4. **API and Integration Features**
- **REST API** for external integrations
- **Rate limiting** and authentication
- **WebSocket support** for real-time interactions
- **Plugin system enhancements**
- **Monitoring and observability**

---

## 📁 New File Structure

```
NIA/
├── core/
│   ├── llm_providers/              # Multi-provider LLM support
│   │   ├── __init__.py
│   │   ├── base.py                 # Abstract provider interface
│   │   ├── openai_provider.py      # OpenAI API integration
│   │   ├── anthropic_provider.py   # Anthropic Claude integration
│   │   ├── ollama_provider.py      # Enhanced Ollama provider
│   │   └── factory.py              # Provider factory and manager
│   ├── database/                   # Database integration
│   │   ├── __init__.py
│   │   ├── models.py               # SQLAlchemy models
│   │   └── manager.py              # Database manager
│   ├── brain.py                    # Enhanced with multi-provider support
│   ├── memory_manager_enhanced.py  # Hybrid memory system
│   └── ... (existing files)
├── config/
│   ├── settings_enhanced.yaml      # Enhanced configuration
│   └── ... (existing files)
├── requirements_enhanced.txt        # Enhanced dependencies
├── migrate_to_enhanced.py          # Migration script
├── README_Enhanced.md              # This file
└── ... (existing files)
```

---

## 🔧 Installation & Setup

### 1. **Backup Existing Installation**
```bash
# The migration script will create backups automatically
python migrate_to_enhanced.py --nia-root /path/to/nia
```

### 2. **Install Enhanced Dependencies**
```bash
# Install all enhanced features
pip install -r requirements_enhanced.txt

# Or install specific provider dependencies
pip install openai>=1.12.0          # For OpenAI support
pip install anthropic>=0.18.0        # For Anthropic support
pip install sqlalchemy>=2.0.0        # For database support
pip install fastapi>=0.104.0         # For API features
```

### 3. **Configure API Keys**
Create a `.env` file with your API keys:
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Database Configuration (optional)
DB_USER=your_database_username
DB_PASSWORD=your_database_password
```

### 4. **Update Configuration**
Copy and customize the enhanced configuration:
```bash
cp config/settings_enhanced.yaml config/settings.yaml
# Edit config/settings.yaml with your preferences
```

---

## 🤖 Multi-Provider LLM Configuration

### Basic Configuration
```yaml
brain:
  # Primary provider
  provider: "openai"  # Options: "openai", "anthropic", "ollama"
  model: "gpt-4o-mini"
  
  # Provider-specific settings
  provider_config:
    api_key: "${OPENAI_API_KEY}"
    # base_url: "https://api.openai.com/v1"  # Custom endpoint
  
  # Fallback providers (optional)
  fallback_providers:
    - provider: "anthropic"
      model: "claude-3-5-haiku-20241022"
      config:
        api_key: "${ANTHROPIC_API_KEY}"
    - provider: "ollama"
      model: "qwen3:4b"
      config:
        base_url: "http://localhost:11434"
```

### Provider-Specific Examples

#### OpenAI Configuration
```yaml
brain:
  provider: "openai"
  model: "gpt-4o"  # or "gpt-4o-mini", "gpt-3.5-turbo"
  provider_config:
    api_key: "${OPENAI_API_KEY}"
    # organization: "${OPENAI_ORG_ID}"  # Optional
    # base_url: "https://your-custom-endpoint.com/v1"  # For custom deployments
```

#### Anthropic Configuration
```yaml
brain:
  provider: "anthropic"
  model: "claude-3-5-sonnet-20241022"  # or "claude-3-5-haiku-20241022"
  provider_config:
    api_key: "${ANTHROPIC_API_KEY}"
```

#### Ollama Configuration (Enhanced)
```yaml
brain:
  provider: "ollama"
  model: "qwen3:4b"  # or any installed Ollama model
  provider_config:
    base_url: "http://localhost:11434"  # Custom Ollama server
```

---

## 🗄️ Database Integration

### SQLite Configuration (Default)
```yaml
database:
  primary:
    type: "sqlite"
    connection:
      path: "data/nia.db"
```

### PostgreSQL Configuration
```yaml
database:
  primary:
    type: "postgresql"
    connection:
      host: "localhost"
      port: 5432
      database: "nia"
      username: "${DB_USER}"
      password: "${DB_PASSWORD}"
    pool:
      min_connections: 2
      max_connections: 20
      timeout: 30
```

### Redis Caching (Optional)
```yaml
database:
  cache:
    enabled: true
    type: "redis"
    connection:
      host: "localhost"
      port: 6379
      password: "${REDIS_PASSWORD}"
    default_ttl: 3600
```

---

## 🧠 Enhanced Memory System

The new memory system combines vector-based semantic search with structured database storage:

### Features
- **Hybrid Storage**: Vector embeddings + structured database
- **Session Management**: Organize conversations by session and user
- **Advanced Search**: Semantic similarity + metadata filtering
- **Analytics**: Conversation summaries and usage statistics
- **Multi-User**: Support for multiple users with privacy controls

### Usage Examples

#### Python API
```python
from core.memory_manager_enhanced import EnhancedMemoryManager

# Initialize enhanced memory manager
memory = EnhancedMemoryManager()

# Store a message with metadata
await memory.store_message(
    user="user",
    text="Hello, how can you help me?",
    session_id="user123_session1",
    user_id="user123",
    metadata={
        "response_time": 0.5,
        "model_used": "gpt-4o-mini",
        "provider_used": "openai"
    }
)

# Query memory with filters
results = await memory.query_memory(
    topic="help with coding",
    recent_n=10,
    session_id="user123_session1",
    user_id="user123"
)

# Get conversation summary
summary = await memory.get_conversation_summary(
    session_id="user123_session1",
    user_id="user123"
)
```

---

## 📊 Analytics and Monitoring

### System Health Monitoring
- **Resource Usage**: CPU, memory, disk monitoring
- **Provider Status**: Health checks for all LLM providers
- **Performance Metrics**: Response times, error rates
- **Usage Analytics**: Conversation statistics, user patterns

### Database Models
- **Users**: User profiles and preferences
- **Conversations**: Detailed conversation logs with metadata
- **Analytics Events**: System usage and performance tracking
- **System Health**: Resource and component health monitoring
- **Configuration**: Dynamic configuration management

---

## 🌐 API Features

### REST API Endpoints
```bash
# Health check
GET /health

# Conversation endpoints
POST /api/v1/chat
GET /api/v1/conversations/{session_id}
DELETE /api/v1/conversations/{session_id}

# Memory endpoints
GET /api/v1/memory/search?q={query}
POST /api/v1/memory/store

# System endpoints
GET /api/v1/system/health
GET /api/v1/system/analytics
```

### WebSocket Support
```javascript
// Real-time chat via WebSocket
const ws = new WebSocket('ws://localhost:8080/ws/chat');

ws.send(JSON.stringify({
    type: 'message',
    content: 'Hello NIA!',
    session_id: 'session123'
}));
```

---

## 🔄 Migration Guide

### Automatic Migration
Use the provided migration script:
```bash
# Run migration with backup
python migrate_to_enhanced.py

# Migration options
python migrate_to_enhanced.py --no-backup    # Skip backup (not recommended)
python migrate_to_enhanced.py --no-database  # Skip database setup
```

### Manual Migration Steps

1. **Backup Current Installation**
   ```bash
   cp -r config config_backup
   cp -r data data_backup
   ```

2. **Install New Dependencies**
   ```bash
   pip install -r requirements_enhanced.txt
   ```

3. **Update Configuration**
   - Copy `config/settings_enhanced.yaml` to `config/settings.yaml`
   - Update with your API keys and preferences
   - Create `.env` file with sensitive configuration

4. **Initialize Database**
   ```python
   from core.database.manager import DatabaseManager
   db = DatabaseManager()  # Will create tables automatically
   ```

5. **Test Enhanced Features**
   ```bash
   python main.py  # Should work with new multi-provider system
   ```

---

## 💡 Usage Examples

### Multi-Provider Fallback
```python
# Automatic fallback: OpenAI -> Anthropic -> Ollama
brain = Brain(model="gpt-4o-mini", timeout=180)
response = brain.generate("What's the weather like?")
# Will try OpenAI first, fall back to Anthropic if it fails, then Ollama
```

### Enhanced Memory Queries
```python
# Search across all sessions for a user
results = await memory.query_memory(
    topic="machine learning projects",
    user_id="user123",
    recent_n=20
)

# Get conversation analytics
summary = await memory.get_conversation_summary("session123", "user123")
print(f"Total messages: {summary['total_messages']}")
print(f"Average response time: {summary['avg_response_time']}s")
```

### Database Analytics
```python
from core.database.manager import get_db_manager

db = get_db_manager()

# Log system event
await db.log_analytics_event(
    event_type="interaction",
    event_name="voice_command",
    session_id="session123",
    duration=2.5
)

# Get analytics summary
summary = await db.get_analytics_summary()
print(f"Total events: {summary['total_events']}")
```

---

## 🔒 Security Features

### API Authentication
- **API Key Management**: Secure API key storage and validation
- **Rate Limiting**: Configurable request rate limits
- **Session Management**: Secure session handling

### Data Privacy
- **User Isolation**: Separate data by user ID
- **Data Encryption**: Optional encryption for sensitive data
- **Audit Logging**: Track all system access and changes

### Configuration Security
- **Environment Variables**: Sensitive config via `.env` files
- **Secret Management**: Secure storage of API keys and passwords

---

## 📈 Performance Optimizations

### Caching
- **Redis Integration**: Fast caching for frequent queries
- **Memory Optimization**: Efficient in-memory data structures
- **Database Indexing**: Optimized database queries

### Async Operations
- **Async Database**: Non-blocking database operations
- **Concurrent Processing**: Parallel LLM provider requests
- **Background Tasks**: Non-blocking analytics and logging

### Resource Management
- **Connection Pooling**: Efficient database connection reuse
- **Memory Monitoring**: Automatic memory usage tracking
- **Cleanup Tasks**: Automatic cleanup of old data

---

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
pytest tests/

# Test specific components
pytest tests/test_llm_providers.py
pytest tests/test_database.py
pytest tests/test_memory_enhanced.py
```

### Integration Tests
```bash
# Test end-to-end workflows
pytest tests/integration/

# Test with different providers
PROVIDER=openai pytest tests/integration/test_conversation.py
PROVIDER=anthropic pytest tests/integration/test_conversation.py
```

---

## 🚨 Troubleshooting

### Common Issues

#### Provider Authentication Errors
```bash
# Check API key configuration
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Test API connectivity
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

#### Database Connection Issues
```bash
# Check database health
python -c "from core.database.manager import get_db_manager; print(get_db_manager().health_check())"

# Reset database
rm data/nia.db  # For SQLite
python -c "from core.database.manager import DatabaseManager; DatabaseManager()"
```

#### Memory System Issues
```bash
# Check LanceDB installation
python -c "import lancedb; print('LanceDB OK')"

# Check embedding model
ollama pull nomic-embed-text
```

### Debug Mode
Enable debug logging in configuration:
```yaml
logging:
  level: "DEBUG"
  detailed_errors: true
```

---

## 🗺️ Roadmap

### Planned Features
- **Google Gemini Integration**
- **Azure OpenAI Support**
- **Advanced Analytics Dashboard**
- **Multi-modal Support** (images, audio)
- **Plugin Marketplace**
- **Cloud Deployment Tools**
- **Advanced Security Features**

### Performance Improvements
- **Model Caching**
- **Response Streaming Optimization**
- **Database Sharding**
- **Distributed Processing**

---

## 🤝 Contributing

### Development Setup
```bash
# Install development dependencies
pip install -r requirements_enhanced.txt
pip install -e .

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

### Code Quality
- **Type Hints**: Full type annotation support
- **Code Formatting**: Black + isort
- **Linting**: flake8 + mypy
- **Testing**: pytest + coverage

---

## 📜 License

This enhanced version maintains the same license as the original NIA project.

---

## 📞 Support

For issues with the enhanced features:

1. **Check the troubleshooting section** above
2. **Review configuration** files for correct API keys and settings
3. **Check logs** in `data/logs/` for detailed error information
4. **Test with fallback providers** to isolate provider-specific issues

---

## 🎉 Conclusion

The enhanced NIA system provides enterprise-grade capabilities while maintaining the simplicity and ease of use of the original system. The multi-provider LLM support ensures reliability and cost optimization, while the database integration provides comprehensive analytics and user management capabilities.

**Key Benefits:**
- ✅ **Reliability**: Multi-provider fallback system
- ✅ **Scalability**: Database integration with caching
- ✅ **Analytics**: Comprehensive usage and performance tracking  
- ✅ **Security**: Authentication, rate limiting, and data privacy
- ✅ **Extensibility**: Plugin system and API integration
- ✅ **Cost Optimization**: Smart provider selection and caching

Start with the migration script and gradually enable enhanced features based on your needs!