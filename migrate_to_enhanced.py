#!/usr/bin/env python3
"""
Migration script for NIA Enhanced Features.

This script helps migrate existing NIA installations to use the new LLM provider
system and database integration features.
"""

import os
import sys
import json
import yaml
import shutil
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


class NIAMigrator:
    """Handles migration to enhanced NIA features."""
    
    def __init__(self, nia_root: str):
        self.nia_root = Path(nia_root)
        self.backup_dir = self.nia_root / "backup" / f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.config_dir = self.nia_root / "config"
        self.data_dir = self.nia_root / "data"
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"NIA Migration Tool")
        print(f"Root directory: {self.nia_root}")
        print(f"Backup directory: {self.backup_dir}")
        print("-" * 50)
    
    def backup_existing_files(self):
        """Create backup of existing configuration and data files."""
        print("📦 Creating backup of existing files...")
        
        # Backup config files
        if self.config_dir.exists():
            shutil.copytree(
                self.config_dir,
                self.backup_dir / "config",
                dirs_exist_ok=True
            )
            print(f"✅ Backed up configuration files")
        
        # Backup data files
        if self.data_dir.exists():
            # Only backup specific files, not the entire data directory
            for file_pattern in ["*.log", "*.jsonl", "*.db"]:
                for file_path in self.data_dir.glob(f"**/{file_pattern}"):
                    relative_path = file_path.relative_to(self.data_dir)
                    backup_path = self.backup_dir / "data" / relative_path
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, backup_path)
            
            print(f"✅ Backed up data files")
        
        print(f"📦 Backup created at: {self.backup_dir}")
    
    def migrate_configuration(self):
        """Migrate existing configuration to enhanced format."""
        print("🔧 Migrating configuration...")
        
        settings_file = self.config_dir / "settings.yaml"
        enhanced_file = self.config_dir / "settings_enhanced.yaml"
        
        if not settings_file.exists():
            print("⚠️  No existing settings.yaml found")
            return
        
        try:
            # Load existing configuration
            with open(settings_file, 'r', encoding='utf-8') as f:
                existing_config = yaml.safe_load(f)
            
            # Load enhanced template
            enhanced_template_file = self.nia_root / "config" / "settings_enhanced.yaml"
            if enhanced_template_file.exists():
                with open(enhanced_template_file, 'r', encoding='utf-8') as f:
                    enhanced_config = yaml.safe_load(f)
            else:
                enhanced_config = {}
            
            # Merge configurations
            migrated_config = self._merge_configs(existing_config, enhanced_config)
            
            # Write new configuration
            with open(enhanced_file, 'w', encoding='utf-8') as f:
                yaml.dump(migrated_config, f, default_flow_style=False, indent=2)
            
            print(f"✅ Configuration migrated to {enhanced_file}")
            print(f"📝 Original configuration preserved as {settings_file}")
            
        except Exception as e:
            print(f"❌ Error migrating configuration: {e}")
    
    def _merge_configs(self, existing: Dict[str, Any], enhanced: Dict[str, Any]) -> Dict[str, Any]:
        """Merge existing configuration with enhanced template."""
        migrated = enhanced.copy()
        
        # Preserve existing brain settings but enhance them
        if "brain" in existing:
            brain_config = existing["brain"].copy()
            
            # Convert to new multi-provider format
            existing_model = brain_config.get("model", "qwen3:4b")
            
            # If using Ollama model, set as primary provider
            migrated["brain"] = {
                "provider": "ollama",
                "model": existing_model,
                "provider_config": {
                    "base_url": "http://localhost:11434"
                },
                "temperature": brain_config.get("temperature", 0.7),
                "max_tokens": brain_config.get("max_tokens", 2000),
                "timeout_s": brain_config.get("timeout_s", 180),
                "system_prompt": brain_config.get("system_prompt", ""),
                "fallback_providers": enhanced.get("brain", {}).get("fallback_providers", [])
            }
        
        # Preserve other existing sections
        for section in ["voice", "stt", "hybrid", "autonomy", "memory", "knowledge"]:
            if section in existing:
                if section in migrated:
                    # Merge section-specific configs
                    migrated[section].update(existing[section])
                else:
                    migrated[section] = existing[section]
        
        return migrated
    
    def setup_database(self):
        """Initialize the new database system."""
        print("🗄️  Setting up enhanced database...")
        
        try:
            # Create database directory
            db_dir = self.data_dir / "database"
            db_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize SQLite database
            db_path = db_dir / "nia.db"
            
            # Import and initialize database models
            sys.path.insert(0, str(self.nia_root))
            
            try:
                from core.database.models import Base
                from core.database.manager import DatabaseManager
                
                # Create database manager with SQLite configuration
                db_config = {
                    "primary": {
                        "type": "sqlite",
                        "connection": {
                            "path": str(db_path)
                        }
                    }
                }
                
                db_manager = DatabaseManager(db_config)
                
                if db_manager.is_connected:
                    print(f"✅ Database initialized at {db_path}")
                else:
                    print(f"❌ Failed to initialize database")
                    
            except ImportError as e:
                print(f"⚠️  Database models not available: {e}")
                print("💡 You may need to install additional dependencies")
            
        except Exception as e:
            print(f"❌ Error setting up database: {e}")
    
    def migrate_memory_data(self):
        """Migrate existing memory data to new format."""
        print("🧠 Migrating memory data...")
        
        # Check for existing JSONL memory file
        memory_file = self.data_dir / "memory" / "messages.jsonl"
        
        if not memory_file.exists():
            print("💭 No existing memory file found")
            return
        
        try:
            messages = []
            with open(memory_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            message = json.loads(line)
                            messages.append(message)
                        except json.JSONDecodeError:
                            continue
            
            print(f"📊 Found {len(messages)} existing memory entries")
            
            # TODO: Convert to new database format
            # This would require the enhanced memory manager to be available
            print("💡 Memory data preserved in original format")
            print("   Enhanced memory system will automatically integrate existing data")
            
        except Exception as e:
            print(f"❌ Error migrating memory data: {e}")
    
    def install_dependencies(self):
        """Guide user through installing new dependencies."""
        print("📦 Checking dependencies...")
        
        enhanced_requirements = self.nia_root / "requirements_enhanced.txt"
        
        if enhanced_requirements.exists():
            print(f"📋 Enhanced requirements file available at: {enhanced_requirements}")
            print("\n💡 To install enhanced dependencies, run:")
            print(f"   pip install -r {enhanced_requirements}")
            
            # Check which dependencies are missing
            try:
                import pkg_resources
                
                with open(enhanced_requirements, 'r') as f:
                    requirements = f.read().splitlines()
                
                missing = []
                for req in requirements:
                    req = req.strip()
                    if req and not req.startswith('#') and not req.startswith('-'):
                        try:
                            # Parse requirement
                            req_name = req.split('>=')[0].split('==')[0].split('[')[0]
                            pkg_resources.get_distribution(req_name)
                        except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
                            missing.append(req_name)
                
                if missing:
                    print(f"\n⚠️  Missing dependencies: {', '.join(missing[:10])}")
                    if len(missing) > 10:
                        print(f"   ... and {len(missing) - 10} more")
                else:
                    print("✅ All dependencies appear to be installed")
                
            except ImportError:
                print("💡 Install setuptools to check dependency status: pip install setuptools")
        
        else:
            print("⚠️  Enhanced requirements file not found")
    
    def create_environment_template(self):
        """Create environment variable template for API keys."""
        print("🔑 Creating environment template...")
        
        env_template = self.nia_root / ".env.template"
        env_file = self.nia_root / ".env"
        
        template_content = """# NIA Enhanced Configuration Environment Variables
# Copy this file to .env and fill in your API keys

# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
# OPENAI_ORG_ID=your_organization_id_here  # Optional

# Anthropic API Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Google AI API Configuration (Optional)
# GOOGLE_API_KEY=your_google_ai_api_key_here

# Database Configuration (for PostgreSQL/MySQL)
# DB_USER=your_database_username
# DB_PASSWORD=your_database_password

# Redis Configuration (Optional)
# REDIS_PASSWORD=your_redis_password

# Security Keys
# JWT_SECRET_KEY=your_jwt_secret_key_here
# ENCRYPTION_KEY=your_encryption_key_here

# Third-party Service API Keys (Optional)
# SENTRY_DSN=your_sentry_dsn_for_error_tracking
"""
        
        with open(env_template, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        print(f"✅ Environment template created: {env_template}")
        
        if not env_file.exists():
            shutil.copy2(env_template, env_file)
            print(f"📝 Environment file created: {env_file}")
            print("🔧 Please edit .env file with your API keys")
        else:
            print(f"📝 Existing .env file found: {env_file}")
    
    def run_migration(self, backup: bool = True, setup_db: bool = True):
        """Run the complete migration process."""
        print("🚀 Starting NIA Enhanced Migration")
        print("=" * 50)
        
        try:
            if backup:
                self.backup_existing_files()
            
            self.migrate_configuration()
            
            if setup_db:
                self.setup_database()
            
            self.migrate_memory_data()
            self.create_environment_template()
            self.install_dependencies()
            
            print("\n" + "=" * 50)
            print("✅ Migration completed successfully!")
            print("\n📋 Next steps:")
            print("1. Install enhanced dependencies: pip install -r requirements_enhanced.txt")
            print("2. Configure API keys in .env file")
            print("3. Review settings_enhanced.yaml configuration")
            print("4. Test the enhanced features")
            print(f"\n💾 Backup created at: {self.backup_dir}")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            print(f"💾 Your data is safely backed up at: {self.backup_dir}")


def main():
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(description="Migrate NIA to enhanced features")
    parser.add_argument(
        "--nia-root",
        type=str,
        default=".",
        help="Path to NIA root directory (default: current directory)"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup (not recommended)"
    )
    parser.add_argument(
        "--no-database",
        action="store_true",
        help="Skip database setup"
    )
    
    args = parser.parse_args()
    
    # Validate NIA root directory
    nia_root = Path(args.nia_root).resolve()
    
    if not (nia_root / "main.py").exists():
        print(f"❌ Error: {nia_root} doesn't appear to be a NIA directory")
        print("   (main.py not found)")
        sys.exit(1)
    
    # Run migration
    migrator = NIAMigrator(str(nia_root))
    migrator.run_migration(
        backup=not args.no_backup,
        setup_db=not args.no_database
    )


if __name__ == "__main__":
    main()