@echo off
REM NIA Enhanced Installation Script for Windows
REM Quick setup script for Windows systems

setlocal enabledelayedexpansion

REM Colors for output (using echo escape sequences)
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

echo.
echo %GREEN%🚀 NIA Enhanced Installation Script for Windows%NC%
echo ══════════════════════════════════════════════════════════════
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%❌ Python is not installed or not in PATH%NC%
    echo %BLUE%📋 Please install Python 3.8 or higher from https://python.org%NC%
    pause
    exit /b 1
)

echo %GREEN%✅ Python detected%NC%

REM Check if pip is available
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%❌ pip is not available%NC%
    echo %BLUE%📋 Please reinstall Python with pip included%NC%
    pause
    exit /b 1
)

echo %GREEN%✅ pip is available%NC%

REM Check for virtual environment
if not defined VIRTUAL_ENV (
    echo %YELLOW%⚠️  Warning: Not running in a virtual environment%NC%
    echo %BLUE%📋 It's recommended to use a virtual environment:%NC%
    echo    python -m venv venvNIA
    echo    venvNIA\Scripts\activate
    echo.
    set /p continue="Continue anyway? [y/N]: "
    if /i not "!continue!"=="y" (
        echo %BLUE%📋 Setup cancelled. Please create a virtual environment first.%NC%
        pause
        exit /b 0
    )
) else (
    echo %GREEN%✅ Running in virtual environment%NC%
)

echo.
echo %BLUE%🚀 NIA Enhanced Installation Options:%NC%
echo ════════════════════════════════════════════════════════════════
echo.
echo 1️⃣  MINIMAL     - Essential features only (OpenAI + SQLite)
echo                Best for: Testing, simple deployments
echo                Size: ~50 packages, ~500 MB
echo.
echo 2️⃣  STANDARD    - Full enhanced features (Recommended)
echo                Best for: Most users who want all features
echo                Size: ~120 packages, ~1.2 GB
echo.
echo 3️⃣  PRODUCTION  - Production-ready with version pinning
echo                Best for: Production deployments
echo                Size: ~180 packages, ~2 GB
echo.
echo 4️⃣  DOCKER      - Container optimized
echo                Best for: Docker, Kubernetes deployments
echo                Size: ~80 packages, ~800 MB
echo.
echo 5️⃣  DEVELOPMENT - Development tools and testing
echo                Best for: Contributors and developers
echo                Size: ~250 packages, ~3 GB
echo.
echo ════════════════════════════════════════════════════════════════

:choice
set /p choice="Choose installation type [1-5] or 'q' to quit: "

if "%choice%"=="1" (
    set "REQUIREMENTS_FILE=requirements-minimal.txt"
    set "INSTALL_TYPE=minimal"
    goto install
)
if "%choice%"=="2" (
    set "REQUIREMENTS_FILE=requirements.txt"
    set "INSTALL_TYPE=standard"
    goto install
)
if "%choice%"=="3" (
    set "REQUIREMENTS_FILE=requirements-production.txt"
    set "INSTALL_TYPE=production"
    goto install
)
if "%choice%"=="4" (
    set "REQUIREMENTS_FILE=requirements-docker.txt"
    set "INSTALL_TYPE=docker"
    goto install
)
if "%choice%"=="5" (
    set "REQUIREMENTS_FILE=requirements-dev.txt"
    set "INSTALL_TYPE=development"
    goto install
)
if /i "%choice%"=="q" (
    echo %BLUE%📋 Installation cancelled.%NC%
    pause
    exit /b 0
)
if /i "%choice%"=="quit" (
    echo %BLUE%📋 Installation cancelled.%NC%
    pause
    exit /b 0
)

echo %RED%❌ Invalid choice. Please enter 1-5 or 'q' to quit.%NC%
goto choice

:install
echo.
echo %BLUE%📋 Selected: %INSTALL_TYPE% (%REQUIREMENTS_FILE%)%NC%
set /p confirm="Proceed with installation? [Y/n]: "
if /i "!confirm!"=="n" (
    echo %BLUE%📋 Installation cancelled.%NC%
    pause
    exit /b 0
)

if not exist "%REQUIREMENTS_FILE%" (
    echo %RED%❌ Requirements file not found: %REQUIREMENTS_FILE%%NC%
    pause
    exit /b 1
)

echo.
echo %BLUE%📋 Installing %INSTALL_TYPE% requirements...%NC%
echo %BLUE%📋 This may take several minutes depending on your internet connection...%NC%
echo.
echo %BLUE%📋 Upgrading pip first...%NC%
python -m pip install --upgrade pip

echo %BLUE%📋 Installing packages...%NC%
echo ════════════════════════════════════════════════════════════════

python -m pip install -r "%REQUIREMENTS_FILE%"
if %errorlevel% neq 0 (
    echo ════════════════════════════════════════════════════════════════
    echo %RED%❌ Installation failed!%NC%
    echo %BLUE%📋 Troubleshooting tips:%NC%
    echo 1. Check your internet connection
    echo 2. Install Visual Studio Build Tools
    echo 3. Try: python -m pip install --upgrade pip
    echo 4. For PyTorch issues: pip install torch --index-url https://download.pytorch.org/whl/cpu
    pause
    exit /b 1
)

echo ════════════════════════════════════════════════════════════════
echo %GREEN%✅ Installation completed successfully!%NC%
echo.

echo %GREEN%🎉 Setup Complete!%NC%
echo ════════════════════════════════════════════════════════════════

if "%INSTALL_TYPE%"=="minimal" (
    echo %BLUE%📝 Next steps for minimal setup:%NC%
    echo 1. Create .env file with your API key:
    echo    echo OPENAI_API_KEY=your_key_here ^> .env
    echo 2. Update config\settings.yaml to use OpenAI provider
    echo 3. Test with: python main.py
) else if "%INSTALL_TYPE%"=="standard" (
    echo %BLUE%📝 Next steps for standard setup:%NC%
    echo 1. Create .env file with your API keys:
    echo    copy .env.template .env
    echo    # Edit .env with your API keys
    echo 2. Run migration script: python migrate_to_enhanced.py
    echo 3. Update config\settings.yaml with your preferences
) else if "%INSTALL_TYPE%"=="production" (
    echo %BLUE%📝 Next steps for production setup:%NC%
    echo 1. Configure environment variables (database, API keys)
    echo 2. Set up PostgreSQL database
    echo 3. Configure Redis for caching
    echo 4. Set up monitoring and logging
    echo 5. Run database migrations: python -m alembic upgrade head
) else if "%INSTALL_TYPE%"=="docker" (
    echo %BLUE%📝 Next steps for Docker setup:%NC%
    echo 1. Build Docker image: docker build -t nia-enhanced .
    echo 2. Set up environment variables
    echo 3. Configure external database and Redis
    echo 4. Deploy with docker-compose
) else if "%INSTALL_TYPE%"=="development" (
    echo %BLUE%📝 Next steps for development setup:%NC%
    echo 1. Install pre-commit hooks: pre-commit install
    echo 2. Run tests: python -m pytest
    echo 3. Check code quality: black . ^&^& flake8
    echo 4. Set up your IDE with Python extensions
)

echo.
echo %BLUE%📚 Documentation: README_Enhanced.md%NC%
echo %BLUE%🐛 Issues: Check logs in data\logs\%NC%
echo %BLUE%💡 Configuration: config\settings_enhanced.yaml%NC%
echo.
echo %GREEN%✅ Installation completed successfully!%NC%

pause