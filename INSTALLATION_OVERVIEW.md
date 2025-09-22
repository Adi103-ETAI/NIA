# 🚀 NIA Enhanced - Complete Installation Overview

This document provides a comprehensive overview of all the requirements files and installation options available for NIA Enhanced.

## 📦 Requirements Files Created

I've created **5 different requirements files** to match different use cases and environments:

### 1. **`requirements-minimal.txt`** 🟢
**Perfect for beginners and quick testing**
- ✅ Core NIA functionality
- ✅ OpenAI API integration only
- ✅ SQLite database (no setup required)
- ✅ Basic dependencies only
- **Size:** ~50 packages (~500 MB)
- **Install time:** 2-3 minutes

### 2. **`requirements.txt`** 🟡 ⭐ **RECOMMENDED**
**Best for most users who want full functionality**
- ✅ All minimal features +
- ✅ Multiple LLM providers (OpenAI, Anthropic, Google AI)
- ✅ Multi-database support (SQLite, PostgreSQL, MySQL)  
- ✅ Redis caching and FastAPI web framework
- ✅ Security and monitoring features
- **Size:** ~120 packages (~1.2 GB)
- **Install time:** 5-8 minutes

### 3. **`requirements-production.txt`** 🔴
**Enterprise-grade with version pinning for stability**
- ✅ All standard features +
- ✅ Version-pinned dependencies for stability
- ✅ Comprehensive monitoring (Prometheus, Sentry)
- ✅ Multi-cloud storage support
- ✅ Background task processing (Celery)
- ✅ Advanced security and distributed tracing
- **Size:** ~180 packages (~2 GB)
- **Install time:** 10-15 minutes

### 4. **`requirements-docker.txt`** 🐳
**Optimized for containerized deployments**
- ✅ Container-optimized packages
- ✅ CPU-only PyTorch for smaller images
- ✅ PostgreSQL focus (better for containers)
- ✅ Essential monitoring tools
- ✅ Lightweight alternatives where possible
- **Size:** ~80 packages (~800 MB)
- **Install time:** 4-6 minutes

### 5. **`requirements-dev.txt`** 🛠️
**Complete development environment**
- ✅ All standard requirements +
- ✅ Testing frameworks (pytest, coverage)
- ✅ Code quality tools (black, flake8, mypy)
- ✅ Debugging tools (ipdb, profilers)
- ✅ Documentation tools (Sphinx, MkDocs)
- ✅ Jupyter environment
- **Size:** ~250 packages (~3 GB)
- **Install time:** 15-20 minutes

---

## 🛠️ Installation Methods

I've created **3 different installation methods** to suit different preferences and platforms:

### 1. **Interactive Python Script** 🐍
**Cross-platform Python script with interactive prompts**

```bash
python setup_requirements.py
# or
python setup_requirements.py --type minimal
python setup_requirements.py --type production
```

**Features:**
- ✅ Interactive menu system
- ✅ Automatic system checks (Python version, virtual environment)
- ✅ Detailed installation progress
- ✅ Post-installation instructions
- ✅ Cross-platform (Windows, macOS, Linux)

### 2. **Unix Shell Script** 🐧🍎
**Native shell script for Linux and macOS**

```bash
./install.sh
# or
./install.sh minimal
./install.sh production
```

**Features:**
- ✅ Colorized output
- ✅ Native shell experience
- ✅ Non-interactive mode support
- ✅ Built-in error handling
- ✅ System dependency checks

### 3. **Windows Batch File** 🪟
**Native batch script for Windows**

```cmd
install.bat
```

**Features:**
- ✅ Windows-native experience
- ✅ Colorized output support
- ✅ Automatic Python detection
- ✅ Virtual environment checks
- ✅ Windows-specific troubleshooting tips

---

## 🎯 Quick Start Guide

### For First-Time Users (Easiest)
```bash
# 1. Use interactive installer
python setup_requirements.py

# 2. Choose "minimal" when prompted
# 3. Follow post-installation instructions
```

### For Experienced Users (Recommended)
```bash
# Direct installation of standard requirements
pip install -r requirements.txt

# Or use shell script
./install.sh standard
```

### For Production Deployment
```bash
# Install production requirements
pip install -r requirements-production.txt

# Or
python setup_requirements.py --type production
```

### For Docker/Container Deployment
```bash
# Install container-optimized requirements
pip install -r requirements-docker.txt

# Build Docker image
docker build -t nia-enhanced .
```

---

## 📊 Feature Comparison at a Glance

| Feature | Minimal | Standard | Production | Docker | Dev |
|---------|---------|----------|------------|--------|-----|
| **🤖 OpenAI API** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **🧠 Anthropic API** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **🌐 Google AI API** | ❌ | ✅ | ✅ | ❌ | ✅ |
| **🗄️ PostgreSQL** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **📊 Redis Caching** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **🌐 Web API** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **🔒 Security** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **📈 Monitoring** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **☁️ Cloud Storage** | ❌ | ❌ | ✅ | ❌ | ✅ |
| **⚙️ Background Tasks** | ❌ | ❌ | ✅ | ❌ | ❌ |
| **🧪 Testing Tools** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **📝 Code Quality** | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 💡 Which Requirements Should You Choose?

### 🟢 **Choose MINIMAL if you:**
- Want to quickly test NIA Enhanced features
- Have limited disk space or bandwidth
- Only need OpenAI integration
- Are doing initial development/testing
- Want the fastest installation

### 🟡 **Choose STANDARD if you:** ⭐ **RECOMMENDED**
- Want access to all LLM providers (OpenAI, Anthropic, Google AI)
- Need multiple database options (PostgreSQL, MySQL, SQLite)
- Want web API functionality
- Need caching and authentication features
- Are building a complete NIA application

### 🔴 **Choose PRODUCTION if you:**
- Are deploying to production environment
- Need stability with version-pinned dependencies
- Require comprehensive monitoring and observability
- Need multi-cloud storage integration
- Want enterprise-grade security features
- Are building a scalable, production-ready system

### 🐳 **Choose DOCKER if you:**
- Are deploying with Docker or Kubernetes
- Want container-optimized packages
- Need smaller container images
- Are using cloud container services (ECS, GKE, AKS)
- Want production features in a containerized environment

### 🛠️ **Choose DEV if you:**
- Are contributing to NIA development
- Want comprehensive testing tools
- Need code quality enforcement
- Are doing active development and debugging
- Want documentation generation tools

---

## 🚨 System Requirements

### **Minimum Requirements**
- **Python:** 3.8 or higher
- **RAM:** 4 GB (8 GB recommended)
- **Disk Space:** 1-4 GB (depending on requirements type)
- **Internet:** Broadband connection for installation

### **Recommended Requirements**  
- **Python:** 3.10 or higher
- **RAM:** 8 GB or higher
- **Disk Space:** 5 GB free space
- **OS:** Linux, macOS, or Windows 10/11

### **For Production Deployment**
- **Python:** 3.10 or higher
- **RAM:** 16 GB or higher
- **Disk Space:** 10 GB free space
- **Database:** PostgreSQL 12+ (recommended)
- **Cache:** Redis 6+ (recommended)

---

## 🔧 Pre-Installation Setup

### 1. **Create Virtual Environment** (Highly Recommended)
```bash
# Create virtual environment
python -m venv venvNIA

# Activate virtual environment
source venvNIA/bin/activate  # Linux/macOS
venvNIA\Scripts\activate     # Windows
```

### 2. **Upgrade pip**
```bash
python -m pip install --upgrade pip
```

### 3. **Install System Dependencies**

#### **Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y build-essential portaudio19-dev python3-dev
```

#### **macOS:**
```bash
brew install portaudio
```

#### **Windows:**
- Install Visual Studio Build Tools
- Or install Visual Studio Community with C++ build tools

---

## 📋 Installation Commands Summary

### **Interactive Installation (Recommended for beginners)**
```bash
python setup_requirements.py
```

### **Direct pip Installation**
```bash
# Minimal
pip install -r requirements-minimal.txt

# Standard (recommended)
pip install -r requirements.txt

# Production
pip install -r requirements-production.txt

# Docker
pip install -r requirements-docker.txt

# Development
pip install -r requirements-dev.txt
```

### **Shell Script Installation (Unix)**
```bash
# Interactive
./install.sh

# Direct
./install.sh minimal
./install.sh standard  
./install.sh production
./install.sh docker
./install.sh dev
```

### **Batch Script Installation (Windows)**
```cmd
install.bat
```

---

## 🔄 Migration from Original NIA

If you have an existing NIA installation:

### **1. Backup First**
```bash
cp -r config config_backup
cp -r data data_backup
```

### **2. Run Migration Script**
```bash
python migrate_to_enhanced.py
```

### **3. Install Enhanced Requirements**
```bash
python setup_requirements.py
```

### **4. Configure API Keys**
```bash
cp .env.template .env
# Edit .env with your API keys
```

---

## 🐛 Troubleshooting

### **Installation Fails**
1. Ensure Python 3.8+ is installed
2. Upgrade pip: `python -m pip install --upgrade pip`
3. Install system build tools (see system requirements)
4. Use virtual environment

### **PyTorch Installation Issues**
```bash
# Install CPU version explicitly
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### **Permission Errors**
```bash
# Install for current user only
pip install --user -r requirements.txt
```

### **Memory Errors During Installation**
```bash
# Install without cache
pip install --no-cache-dir -r requirements.txt
```

---

## 📚 Additional Resources

- **📖 Main Documentation:** [README_Enhanced.md](README_Enhanced.md)
- **🔧 Requirements Guide:** [REQUIREMENTS.md](REQUIREMENTS.md)
- **🔄 Migration Script:** [migrate_to_enhanced.py](migrate_to_enhanced.py)
- **⚙️ Configuration:** [config/settings_enhanced.yaml](config/settings_enhanced.yaml)
- **🔐 Environment Template:** [.env.template](.env.template)

---

## 🎉 Quick Success Path

**For the fastest path to success with NIA Enhanced:**

1. **Create virtual environment:** `python -m venv venvNIA && source venvNIA/bin/activate`
2. **Run interactive installer:** `python setup_requirements.py`
3. **Choose "standard" option** when prompted
4. **Wait for installation to complete** (5-8 minutes)
5. **Create .env file:** `echo "OPENAI_API_KEY=your_key_here" > .env`
6. **Test installation:** `python main.py`

🎊 **You're now ready to use NIA Enhanced with multiple LLM providers and advanced features!**

---

*This installation system provides maximum flexibility while maintaining simplicity. Choose the requirements file that matches your needs, and use the installation method that feels most comfortable for your platform.*