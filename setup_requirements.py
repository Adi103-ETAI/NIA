#!/usr/bin/env python3
"""
NIA Enhanced Requirements Setup Script

This script helps you choose and install the appropriate requirements file
based on your use case and environment.
"""

import os
import sys
import subprocess
from pathlib import Path
import argparse


class RequirementsSetup:
    """Interactive setup for NIA Enhanced requirements."""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.available_requirements = {
            'minimal': {
                'file': 'requirements-minimal.txt',
                'description': 'Essential features only (OpenAI + SQLite)',
                'use_case': 'Testing, development, or simple deployments'
            },
            'standard': {
                'file': 'requirements.txt',
                'description': 'Full enhanced features with flexibility',
                'use_case': 'Most users who want all features'
            },
            'production': {
                'file': 'requirements-production.txt',
                'description': 'Production-ready with version pinning',
                'use_case': 'Production deployments requiring stability'
            },
            'docker': {
                'file': 'requirements-docker.txt',
                'description': 'Optimized for containerized deployments',
                'use_case': 'Docker containers, Kubernetes, cloud deployments'
            },
            'dev': {
                'file': 'requirements-dev.txt',
                'description': 'Development tools, testing, debugging',
                'use_case': 'Contributors and developers'
            }
        }
    
    def display_options(self):
        """Display available requirements options."""
        print("🚀 NIA Enhanced Requirements Setup")
        print("=" * 50)
        print("\nAvailable requirement configurations:\n")
        
        for key, info in self.available_requirements.items():
            print(f"📦 {key.upper()}")
            print(f"   File: {info['file']}")
            print(f"   Description: {info['description']}")
            print(f"   Best for: {info['use_case']}")
            print()
    
    def get_user_choice(self):
        """Get user's choice for requirements."""
        while True:
            choice = input("Choose a configuration [minimal/standard/production/docker/dev]: ").lower().strip()
            
            if choice in self.available_requirements:
                return choice
            elif choice in ['help', 'h', '?']:
                self.display_options()
            elif choice in ['quit', 'q', 'exit']:
                print("Setup cancelled.")
                sys.exit(0)
            else:
                print(f"❌ Invalid choice: {choice}")
                print("Valid options: " + ", ".join(self.available_requirements.keys()))
                print("Type 'help' for more information or 'quit' to exit.\n")
    
    def check_python_version(self):
        """Check if Python version is compatible."""
        if sys.version_info < (3, 8):
            print("❌ Python 3.8 or higher is required for NIA Enhanced")
            print(f"Current version: {sys.version}")
            sys.exit(1)
        
        print(f"✅ Python version: {sys.version.split()[0]} (compatible)")
    
    def check_virtual_environment(self):
        """Check if running in virtual environment."""
        in_venv = (
            hasattr(sys, 'real_prefix') or  # virtualenv
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)  # venv
        )
        
        if not in_venv:
            print("⚠️  Warning: Not running in a virtual environment")
            print("   It's recommended to use a virtual environment for NIA")
            print("   Create one with: python -m venv venvNIA")
            print("   Activate with: source venvNIA/bin/activate (Linux/Mac)")
            print("                 venvNIA\\Scripts\\activate (Windows)")
            
            continue_anyway = input("\nContinue anyway? [y/N]: ").lower().strip()
            if continue_anyway not in ['y', 'yes']:
                print("Setup cancelled. Please set up a virtual environment first.")
                sys.exit(0)
        else:
            print("✅ Running in virtual environment")
    
    def install_requirements(self, requirements_file):
        """Install the selected requirements file."""
        file_path = self.base_path / requirements_file
        
        if not file_path.exists():
            print(f"❌ Requirements file not found: {file_path}")
            return False
        
        print(f"\n📦 Installing packages from {requirements_file}...")
        print("This may take several minutes depending on your internet connection.")
        print("=" * 60)
        
        try:
            # Upgrade pip first
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'
            ], check=True)
            
            # Install requirements
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', str(file_path)
            ], check=True, capture_output=False)
            
            print("=" * 60)
            print("✅ Installation completed successfully!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Installation failed with exit code: {e.returncode}")
            print("\nTroubleshooting tips:")
            print("1. Check your internet connection")
            print("2. Try upgrading pip: python -m pip install --upgrade pip")
            print("3. Install Visual Studio Build Tools if on Windows")
            print("4. For PyTorch CPU version: pip install torch --index-url https://download.pytorch.org/whl/cpu")
            return False
        except KeyboardInterrupt:
            print("\n⚠️  Installation cancelled by user")
            return False
    
    def post_install_instructions(self, choice):
        """Display post-installation instructions."""
        print("\n🎉 Setup Complete!")
        print("=" * 50)
        
        if choice == 'minimal':
            print("📝 Next steps for minimal setup:")
            print("1. Create .env file with your API key:")
            print("   echo 'OPENAI_API_KEY=your_key_here' > .env")
            print("2. Update config/settings.yaml to use OpenAI provider")
            print("3. Test with: python main.py")
            
        elif choice == 'standard':
            print("📝 Next steps for standard setup:")
            print("1. Create .env file with your API keys:")
            print("   cp .env.template .env")
            print("   # Edit .env with your API keys")
            print("2. Choose your database (SQLite/PostgreSQL/MySQL)")
            print("3. Update config/settings.yaml with your preferences")
            print("4. Run migration script: python migrate_to_enhanced.py")
            
        elif choice == 'production':
            print("📝 Next steps for production setup:")
            print("1. Configure environment variables:")
            print("   - Database credentials")
            print("   - API keys")
            print("   - Redis configuration (if using)")
            print("2. Set up monitoring and logging")
            print("3. Configure reverse proxy (nginx)")
            print("4. Set up database (PostgreSQL recommended)")
            print("5. Run database migrations: alembic upgrade head")
            
        elif choice == 'docker':
            print("📝 Next steps for Docker setup:")
            print("1. Build Docker image: docker build -t nia-enhanced .")
            print("2. Set up environment variables in Docker")
            print("3. Configure database connection (external DB recommended)")
            print("4. Set up Redis for caching")
            print("5. Deploy with docker-compose or Kubernetes")
            
        elif choice == 'dev':
            print("📝 Next steps for development setup:")
            print("1. Install pre-commit hooks: pre-commit install")
            print("2. Run tests: pytest")
            print("3. Check code quality: black . && flake8")
            print("4. Set up IDE with Python extension")
            print("5. Create feature branch for development")
        
        print(f"\n📚 Documentation: README_Enhanced.md")
        print(f"🐛 Issues: Check logs in data/logs/")
        print(f"💡 Configuration: config/settings_enhanced.yaml")
    
    def run_interactive_setup(self):
        """Run the interactive setup process."""
        print("🔍 Checking system requirements...")
        self.check_python_version()
        self.check_virtual_environment()
        
        print("\n" + "=" * 50)
        self.display_options()
        
        choice = self.get_user_choice()
        requirements_file = self.available_requirements[choice]['file']
        
        print(f"\n📋 Selected: {choice.upper()}")
        print(f"📄 File: {requirements_file}")
        print(f"📝 Description: {self.available_requirements[choice]['description']}")
        
        confirm = input(f"\nProceed with installation? [Y/n]: ").lower().strip()
        if confirm in ['n', 'no']:
            print("Installation cancelled.")
            sys.exit(0)
        
        success = self.install_requirements(requirements_file)
        
        if success:
            self.post_install_instructions(choice)
        else:
            print("\n❌ Installation failed. Please check the errors above.")
            sys.exit(1)
    
    def install_specific(self, requirements_type):
        """Install specific requirements type without interactive prompts."""
        if requirements_type not in self.available_requirements:
            print(f"❌ Unknown requirements type: {requirements_type}")
            print(f"Available types: {', '.join(self.available_requirements.keys())}")
            sys.exit(1)
        
        print("🔍 Checking system requirements...")
        self.check_python_version()
        
        requirements_file = self.available_requirements[requirements_type]['file']
        print(f"📦 Installing {requirements_type} requirements...")
        
        success = self.install_requirements(requirements_file)
        
        if success:
            self.post_install_instructions(requirements_type)
        else:
            sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="NIA Enhanced Requirements Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup_requirements.py                    # Interactive setup
  python setup_requirements.py --type minimal    # Install minimal requirements
  python setup_requirements.py --type production # Install production requirements
  python setup_requirements.py --list            # List available types
        """
    )
    
    parser.add_argument(
        '--type',
        choices=['minimal', 'standard', 'production', 'docker', 'dev'],
        help='Requirements type to install'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available requirements types and exit'
    )
    
    args = parser.parse_args()
    
    setup = RequirementsSetup()
    
    if args.list:
        setup.display_options()
        sys.exit(0)
    
    if args.type:
        setup.install_specific(args.type)
    else:
        setup.run_interactive_setup()


if __name__ == '__main__':
    main()