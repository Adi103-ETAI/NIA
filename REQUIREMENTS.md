# NIA Enhanced Requirements Guide

This document explains the different requirements files available for NIA Enhanced and helps you choose the right one for your use case.

## 📋 Available Requirements Files

### 🟢 `requirements-minimal.txt` - Essential Features Only
**Best for:** Quick testing, simple deployments, or resource-constrained environments

**Includes:**
- Core NIA functionality (voice, STT/TTS)
- OpenAI API integration
- SQLite database support
- Basic HTTP client
- Environment management

**Size:** ~50 packages  
**Install time:** 2-3 minutes  
**Disk space:** ~500 MB

```bash
pip install -r requirements-minimal.txt
```

### 🟡 `requirements.txt` - Standard Enhanced Features
**Best for:** Most users who want full functionality with flexibility

**Includes:**
- All minimal features
- Multiple LLM providers (OpenAI, Anthropic, Google AI)
- Multi-database support (SQLite, PostgreSQL, MySQL)
- Redis caching
- FastAPI web framework
- Security features
- Monitoring tools
- Optional cloud storage

**Size:** ~120 packages  
**Install time:** 5-8 minutes  
**Disk space:** ~1.2 GB

```bash
pip install -r requirements.txt
```

### 🔴 `requirements-production.txt` - Production Ready
**Best for:** Production deployments requiring stability and full features

**Includes:**
- All standard features
- Version-pinned dependencies for stability
- Comprehensive monitoring (Prometheus, Sentry)
- Multi-cloud storage support
- Background task processing (Celery)
- Advanced security features
- Distributed tracing

**Size:** ~180 packages  
**Install time:** 10-15 minutes  
**Disk space:** ~2 GB

```bash
pip install -r requirements-production.txt
```

### 🐳 `requirements-docker.txt` - Container Optimized
**Best for:** Docker containers, Kubernetes, and cloud deployments

**Includes:**
- Container-optimized packages
- CPU-only PyTorch for smaller images
- Essential monitoring tools
- PostgreSQL focus (better for containers)
- Lightweight alternatives where possible
- Container-specific utilities

**Size:** ~80 packages  
**Install time:** 4-6 minutes  
**Disk space:** ~800 MB

```bash
pip install -r requirements-docker.txt
```

### 🛠️ `requirements-dev.txt` - Development Environment
**Best for:** Contributors, developers, and code quality enthusiasts

**Includes:**
- All standard requirements
- Testing frameworks (pytest, coverage)
- Code quality tools (black, flake8, mypy)
- Debugging tools (ipdb, profilers)
- Documentation tools (Sphinx, MkDocs)
- Pre-commit hooks
- Jupyter environment

**Size:** ~250 packages  
**Install time:** 15-20 minutes  
**Disk space:** ~3 GB

```bash
pip install -r requirements-dev.txt
```

## 🚀 Quick Setup Script

Use our interactive setup script to choose automatically:

```bash
python setup_requirements.py
```

Or install specific type directly:

```bash
python setup_requirements.py --type minimal
python setup_requirements.py --type production
python setup_requirements.py --type docker
```

## 🤔 Which Requirements Should I Choose?

### For Getting Started (First Time Users)
```bash
pip install -r requirements-minimal.txt
```
- Quick to install and test
- Includes OpenAI integration
- SQLite database (no setup required)

### For Most Users (Recommended)
```bash
pip install -r requirements.txt
```
- Full feature set
- Flexibility to enable/disable features
- Good balance of functionality and complexity

### For Production Deployment
```bash
pip install -r requirements-production.txt
```
- Stable, version-pinned dependencies
- Comprehensive monitoring and observability
- Enterprise-grade security features

### For Docker/Cloud Deployment
```bash
pip install -r requirements-docker.txt
```
- Optimized for containers
- Smaller image sizes
- Container-aware monitoring

### For Development/Contributing
```bash
pip install -r requirements-dev.txt
```
- All development tools included
- Code quality enforcement
- Testing and debugging capabilities

## 📊 Feature Comparison Matrix

| Feature | Minimal | Standard | Production | Docker | Dev |
|---------|---------|----------|------------|--------|-----|
| **Core NIA** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **OpenAI API** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Anthropic API** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Google AI API** | ❌ | ✅ | ✅ | ❌ | ✅ |
| **SQLite Support** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **PostgreSQL Support** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **MySQL Support** | ❌ | ✅ | ✅ | ❌ | ✅ |
| **Redis Caching** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **FastAPI Web** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Authentication** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Monitoring** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Cloud Storage** | ❌ | ❌ | ✅ | ❌ | ✅ |
| **Background Tasks** | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Testing Tools** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Code Quality** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Documentation** | ❌ | ❌ | ❌ | ❌ | ✅ |

## 🔧 Installation Tips

### Before Installing

1. **Use Virtual Environment** (Recommended):
   ```bash
   python -m venv venvNIA
   source venvNIA/bin/activate  # Linux/Mac
   venvNIA\Scripts\activate     # Windows
   ```

2. **Upgrade pip**:
   ```bash
   python -m pip install --upgrade pip
   ```

3. **Check Python Version**:
   ```bash
   python --version  # Should be 3.8 or higher
   ```

### Common Installation Issues

#### PyTorch Installation
If you encounter issues with PyTorch, install CPU version explicitly:
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

#### Windows Build Tools
For Windows users, you may need Visual Studio Build Tools:
```bash
# Install Microsoft C++ Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

#### macOS Dependencies
For macOS users with M1/M2 chips:
```bash
# Install system dependencies first
brew install portaudio
```

#### Linux Dependencies
For Ubuntu/Debian users:
```bash
sudo apt-get update
sudo apt-get install -y build-essential portaudio19-dev python3-dev
```

### Performance Optimization

#### Faster Installation
Use pip's parallel downloads:
```bash
pip install --upgrade pip
pip install -r requirements.txt --use-pep517
```

#### Reduce Install Size
For production deployments, consider:
```bash
# Install without dev dependencies
pip install --no-dev -r requirements-production.txt

# Use slim Docker base images
FROM python:3.11-slim
```

## 🔄 Upgrading Requirements

### From Original NIA
1. Backup current installation
2. Run migration script: `python migrate_to_enhanced.py`
3. Install enhanced requirements
4. Update configuration

### Between Requirements Types
```bash
# Upgrade from minimal to standard
pip install -r requirements.txt

# Downgrade from standard to minimal
pip uninstall -y -r requirements.txt
pip install -r requirements-minimal.txt
```

## 🐛 Troubleshooting

### Installation Fails
1. Check Python version (3.8+ required)
2. Update pip: `python -m pip install --upgrade pip`
3. Install build tools (see platform-specific instructions above)
4. Try installing in clean virtual environment

### Package Conflicts
```bash
# Reset environment
pip freeze | xargs pip uninstall -y
pip install -r requirements-minimal.txt
```

### Memory Issues During Installation
```bash
# Install with no cache
pip install --no-cache-dir -r requirements.txt

# Or install packages one by one
cat requirements.txt | xargs -n 1 pip install
```

### Specific Package Issues

#### LanceDB Installation
```bash
# Install from conda-forge if pip fails
conda install -c conda-forge lancedb
```

#### DeepFilterNet Issues
```bash
# Skip if having issues (it's optional)
pip install -r requirements.txt --ignore-installed deepfilternet
```

## 📚 Additional Resources

- **Main Documentation**: `README_Enhanced.md`
- **Migration Guide**: `migrate_to_enhanced.py`
- **Configuration**: `config/settings_enhanced.yaml`
- **Environment Variables**: `.env.template`

## 🆘 Getting Help

If you encounter issues:

1. **Check this troubleshooting section** first
2. **Search existing issues** in the repository
3. **Create detailed issue** with:
   - Python version
   - Operating system
   - Requirements file used
   - Full error message
   - Steps to reproduce

## 📝 Contributing Requirements

When adding new dependencies:

1. Add to appropriate requirements file(s)
2. Pin versions for stability
3. Add comments explaining the purpose
4. Update this documentation
5. Test installation on multiple platforms

---

**Quick Links:**
- [Setup Script](setup_requirements.py) - Interactive installation
- [Migration Guide](migrate_to_enhanced.py) - Upgrade from original NIA
- [Enhanced Documentation](README_Enhanced.md) - Complete feature guide