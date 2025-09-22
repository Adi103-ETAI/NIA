#!/bin/bash

# NIA Enhanced Installation Script
# Quick setup script for Unix-like systems (Linux, macOS)

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "${BLUE}📋 $1${NC}"; }

# Check if Python is installed and version is adequate
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        print_info "Please install Python 3.8 or higher"
        exit 1
    fi
    
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    required_version="3.8"
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
        print_error "Python $python_version is installed, but Python $required_version or higher is required"
        exit 1
    fi
    
    print_success "Python $python_version detected"
}

# Check if pip is installed
check_pip() {
    if ! python3 -m pip --version &> /dev/null; then
        print_error "pip is not installed"
        print_info "Install pip with: python3 -m ensurepip --upgrade"
        exit 1
    fi
    
    print_success "pip is available"
}

# Check virtual environment
check_venv() {
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        print_warning "Not running in a virtual environment"
        print_info "It's recommended to use a virtual environment:"
        print_info "  python3 -m venv venvNIA"
        print_info "  source venvNIA/bin/activate"
        
        read -p "Continue anyway? [y/N]: " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Setup cancelled. Please create a virtual environment first."
            exit 0
        fi
    else
        print_success "Running in virtual environment: $VIRTUAL_ENV"
    fi
}

# Display available options
show_options() {
    echo ""
    echo "🚀 NIA Enhanced Installation Options:"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "1️⃣  MINIMAL     - Essential features only (OpenAI + SQLite)"
    echo "                Best for: Testing, simple deployments"
    echo "                Size: ~50 packages, ~500 MB"
    echo ""
    echo "2️⃣  STANDARD    - Full enhanced features (Recommended)"
    echo "                Best for: Most users who want all features"
    echo "                Size: ~120 packages, ~1.2 GB"
    echo ""
    echo "3️⃣  PRODUCTION  - Production-ready with version pinning"
    echo "                Best for: Production deployments"
    echo "                Size: ~180 packages, ~2 GB"
    echo ""
    echo "4️⃣  DOCKER      - Container optimized"
    echo "                Best for: Docker, Kubernetes deployments"
    echo "                Size: ~80 packages, ~800 MB"
    echo ""
    echo "5️⃣  DEVELOPMENT - Development tools and testing"
    echo "                Best for: Contributors and developers"
    echo "                Size: ~250 packages, ~3 GB"
    echo ""
    echo "════════════════════════════════════════════════════════════════"
}

# Get user choice
get_choice() {
    while true; do
        echo ""
        read -p "Choose installation type [1-5] or 'q' to quit: " choice
        
        case $choice in
            1) 
                REQUIREMENTS_FILE="requirements-minimal.txt"
                INSTALL_TYPE="minimal"
                break
                ;;
            2) 
                REQUIREMENTS_FILE="requirements.txt"
                INSTALL_TYPE="standard"
                break
                ;;
            3) 
                REQUIREMENTS_FILE="requirements-production.txt"
                INSTALL_TYPE="production"
                break
                ;;
            4) 
                REQUIREMENTS_FILE="requirements-docker.txt"
                INSTALL_TYPE="docker"
                break
                ;;
            5) 
                REQUIREMENTS_FILE="requirements-dev.txt"
                INSTALL_TYPE="development"
                break
                ;;
            [Qq]|[Qq][Uu][Ii][Tt]) 
                print_info "Installation cancelled."
                exit 0
                ;;
            *) 
                print_error "Invalid choice. Please enter 1-5 or 'q' to quit."
                ;;
        esac
    done
}

# Install requirements
install_requirements() {
    print_info "Installing $INSTALL_TYPE requirements..."
    print_info "File: $REQUIREMENTS_FILE"
    
    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        print_error "Requirements file not found: $REQUIREMENTS_FILE"
        exit 1
    fi
    
    echo ""
    print_info "This may take several minutes depending on your internet connection..."
    print_info "Upgrading pip first..."
    
    # Upgrade pip
    python3 -m pip install --upgrade pip
    
    print_info "Installing packages..."
    echo "════════════════════════════════════════════════════════════════"
    
    # Install requirements
    if python3 -m pip install -r "$REQUIREMENTS_FILE"; then
        echo "════════════════════════════════════════════════════════════════"
        print_success "Installation completed successfully!"
    else
        echo "════════════════════════════════════════════════════════════════"
        print_error "Installation failed!"
        print_info "Troubleshooting tips:"
        print_info "1. Check your internet connection"
        print_info "2. Install system dependencies (see REQUIREMENTS.md)"
        print_info "3. Try: python3 -m pip install --upgrade pip"
        exit 1
    fi
}

# Show post-install instructions
show_next_steps() {
    echo ""
    echo "🎉 Setup Complete!"
    echo "════════════════════════════════════════════════════════════════"
    
    case $INSTALL_TYPE in
        "minimal")
            echo "📝 Next steps for minimal setup:"
            echo "1. Create .env file with your API key:"
            echo "   echo 'OPENAI_API_KEY=your_key_here' > .env"
            echo "2. Update config/settings.yaml to use OpenAI provider"
            echo "3. Test with: python3 main.py"
            ;;
        "standard")
            echo "📝 Next steps for standard setup:"
            echo "1. Create .env file with your API keys:"
            echo "   cp .env.template .env"
            echo "   # Edit .env with your API keys"
            echo "2. Run migration script: python3 migrate_to_enhanced.py"
            echo "3. Update config/settings.yaml with your preferences"
            ;;
        "production")
            echo "📝 Next steps for production setup:"
            echo "1. Configure environment variables (database, API keys)"
            echo "2. Set up PostgreSQL database"
            echo "3. Configure Redis for caching"
            echo "4. Set up monitoring and logging"
            echo "5. Run database migrations: python3 -m alembic upgrade head"
            ;;
        "docker")
            echo "📝 Next steps for Docker setup:"
            echo "1. Build Docker image: docker build -t nia-enhanced ."
            echo "2. Set up environment variables"
            echo "3. Configure external database and Redis"
            echo "4. Deploy with docker-compose"
            ;;
        "development")
            echo "📝 Next steps for development setup:"
            echo "1. Install pre-commit hooks: pre-commit install"
            echo "2. Run tests: python3 -m pytest"
            echo "3. Check code quality: black . && flake8"
            echo "4. Set up your IDE with Python extensions"
            ;;
    esac
    
    echo ""
    echo "📚 Documentation: README_Enhanced.md"
    echo "🐛 Issues: Check logs in data/logs/"
    echo "💡 Configuration: config/settings_enhanced.yaml"
    echo ""
    print_success "Installation completed successfully!"
}

# Main installation flow
main() {
    echo "🚀 NIA Enhanced Installation Script"
    echo "══════════════════════════════════════════════════════════════"
    
    # System checks
    print_info "Checking system requirements..."
    check_python
    check_pip
    check_venv
    
    # Show options and get choice
    show_options
    get_choice
    
    # Confirm installation
    echo ""
    print_info "Selected: $INSTALL_TYPE ($REQUIREMENTS_FILE)"
    read -p "Proceed with installation? [Y/n]: " -r
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        print_info "Installation cancelled."
        exit 0
    fi
    
    # Install
    install_requirements
    
    # Show next steps
    show_next_steps
}

# Handle command line arguments
if [[ $# -gt 0 ]]; then
    case $1 in
        "minimal"|"1")
            REQUIREMENTS_FILE="requirements-minimal.txt"
            INSTALL_TYPE="minimal"
            ;;
        "standard"|"2")
            REQUIREMENTS_FILE="requirements.txt"
            INSTALL_TYPE="standard"
            ;;
        "production"|"3")
            REQUIREMENTS_FILE="requirements-production.txt"
            INSTALL_TYPE="production"
            ;;
        "docker"|"4")
            REQUIREMENTS_FILE="requirements-docker.txt"
            INSTALL_TYPE="docker"
            ;;
        "dev"|"development"|"5")
            REQUIREMENTS_FILE="requirements-dev.txt"
            INSTALL_TYPE="development"
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [type]"
            echo ""
            echo "Types:"
            echo "  minimal     - Essential features only"
            echo "  standard    - Full enhanced features (default)"
            echo "  production  - Production-ready setup"
            echo "  docker      - Container optimized"
            echo "  dev         - Development environment"
            echo ""
            echo "Examples:"
            echo "  $0 minimal      # Install minimal requirements"
            echo "  $0 production   # Install production requirements"
            echo "  $0              # Interactive mode"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            print_info "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
    
    # Non-interactive installation
    check_python
    check_pip
    print_info "Installing $INSTALL_TYPE requirements non-interactively..."
    install_requirements
    show_next_steps
else
    # Interactive installation
    main
fi