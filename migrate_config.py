#!/usr/bin/env python3
"""
Migration script to update config.yaml from old format to new consolidated format.
This script will:
1. Backup existing config.yaml
2. Consolidate logging, debug, and development sections into unified logging
3. Save the updated config
"""

import yaml
import sys
import os
from pathlib import Path
from datetime import datetime
import shutil


def migrate_config(config_path: str) -> bool:
    """
    Migrate configuration to new consolidated format.
    
    Args:
        config_path: Path to config.yaml file
        
    Returns:
        True if migration successful, False otherwise
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        print(f"❌ Config file not found: {config_path}")
        return False
    
    # Load existing config
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return False
    
    # Check if already migrated
    if 'logging' in config and 'debug' in config.get('logging', {}):
        print("✅ Config already in new format, no migration needed")
        return True
    
    # Create backup
    backup_path = config_file.parent / f"config.yaml.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(config_file, backup_path)
    print(f"📁 Created backup: {backup_path}")
    
    # Migrate configuration
    print("🔄 Migrating configuration...")
    
    # Get old sections
    old_logging = config.get('logging', {})
    old_debug = config.get('debug', {})
    old_development = config.get('development', {})
    
    # Build new consolidated logging section
    new_logging = {
        'level': old_logging.get('level', old_debug.get('log_level', 'INFO')),
        'console': {
            'enabled': old_logging.get('console', True),
            'format': old_logging.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            'colored': True
        },
        'file': {
            'enabled': old_logging.get('file', None) is not None or old_debug.get('enabled', False),
            'path': old_debug.get('log_path', './logs'),
            'filename': 'chat_with_tools.log' if old_logging.get('file') else old_logging.get('file', 'chat_with_tools.log'),
            'format': '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s | %(message)s',
            'max_size_mb': old_debug.get('max_log_size_mb', 10),
            'max_files': old_debug.get('max_log_files', 5)
        },
        'debug': {
            'enabled': old_debug.get('enabled', False) or old_development.get('debug', False),
            'verbose': old_development.get('trace_tools', False),
            'log_tool_calls': old_debug.get('log_tool_calls', True),
            'log_llm_calls': old_debug.get('log_llm_calls', True),
            'log_agent_thoughts': old_debug.get('log_agent_thoughts', True),
            'log_orchestrator': True,
            'debug_file': {
                'enabled': old_debug.get('enabled', False),
                'path': './logs/debug',
                'max_size_mb': old_debug.get('max_log_size_mb', 10) * 2,
                'max_files': old_debug.get('max_log_files', 5) * 2
            }
        },
        'development': {
            'save_responses': old_development.get('save_responses', False),
            'response_dir': old_development.get('response_dir', './debug/responses'),
            'save_history': old_development.get('save_history', False),
            'history_dir': old_development.get('history_dir', './chat_history'),
            'profile': old_development.get('profile', False),
            'profile_dir': './debug/profiles',
            'trace_tools': old_development.get('trace_tools', False),
            'mock_api': old_development.get('mock_api', False)
        }
    }
    
    # Update config with new logging section
    config['logging'] = new_logging
    
    # Remove old sections
    if 'debug' in config:
        del config['debug']
        print("  ✓ Migrated 'debug' section")
    
    if 'development' in config:
        del config['development']
        print("  ✓ Migrated 'development' section")
    
    # Update agent section if it has verbose/silent settings
    if 'agent' in config:
        if 'verbose' in config['agent']:
            del config['agent']['verbose']
            print("  ✓ Removed 'agent.verbose' (now controlled by logging.debug)")
        if 'silent' in config['agent']:
            del config['agent']['silent']
            print("  ✓ Removed 'agent.silent' (now controlled by logging.level)")
    
    # Update orchestrator section
    if 'orchestrator' in config:
        if 'verbose' in config['orchestrator']:
            del config['orchestrator']['verbose']
            print("  ✓ Removed 'orchestrator.verbose' (now controlled by logging.debug)")
    
    # Save updated config
    try:
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False, width=100)
        print(f"✅ Successfully migrated config to new format")
        print(f"   Old config backed up to: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving migrated config: {e}")
        print(f"   Restoring from backup...")
        shutil.copy2(backup_path, config_file)
        return False


def main():
    """Main entry point for migration script."""
    print("=" * 60)
    print("   CONFIG MIGRATION TOOL")
    print("=" * 60)
    print("\nThis tool will migrate your config.yaml to the new")
    print("consolidated format that combines logging, debug, and")
    print("development sections into a unified structure.\n")
    
    # Find config file
    search_paths = [
        Path.cwd() / "config" / "config.yaml",
        Path.cwd() / "config.yaml",
        Path(__file__).parent.parent / "config" / "config.yaml",
    ]
    
    config_path = None
    for path in search_paths:
        if path.exists():
            config_path = path
            break
    
    if not config_path:
        print("❌ No config.yaml found in standard locations:")
        for path in search_paths:
            print(f"   - {path}")
        print("\nYou can specify a path manually:")
        manual_path = input("Config path (or press Enter to exit): ").strip()
        if manual_path:
            config_path = Path(manual_path)
        else:
            return
    
    print(f"\n📄 Found config at: {config_path}")
    
    # Confirm migration
    response = input("\nProceed with migration? (y/N): ").strip().lower()
    if response != 'y':
        print("Migration cancelled.")
        return
    
    # Run migration
    if migrate_config(str(config_path)):
        print("\n✨ Migration completed successfully!")
        print("\nYour configuration has been updated to the new format.")
        print("The old config has been backed up for safety.")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
