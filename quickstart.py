#!/usr/bin/env python3
"""
Quick start script after applying fixes.
This helps users verify everything is working after the configuration update.
"""

import sys
import os
import subprocess
from pathlib import Path


def check_config():
    """Check if config.yaml exists."""
    config_path = Path("config/config.yaml")
    example_path = Path("config/config.example.yaml")
    
    if not config_path.exists():
        print("❌ config.yaml not found!")
        
        if example_path.exists():
            print("\n📝 Would you like to create config.yaml from the example?")
            response = input("Create config.yaml? (y/N): ").strip().lower()
            
            if response == 'y':
                import shutil
                shutil.copy2(example_path, config_path)
                print("✅ Created config/config.yaml")
                print("\n⚠️  Remember to add your OpenRouter API key to config.yaml")
                print("   Edit: config/config.yaml")
                print("   Replace: 'YOUR API KEY HERE' with your actual key")
                print("   Get key at: https://openrouter.ai/keys")
                return True
        else:
            print("❌ config.example.yaml also missing!")
            return False
    else:
        # Check if it's the new format
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check for new structure
        if 'logging' in config and 'debug' in config.get('logging', {}):
            print("✅ config.yaml exists (new format)")
            return True
        elif 'debug' in config or 'development' in config:
            print("⚠️  config.yaml exists but uses old format")
            print("\n📝 Would you like to migrate to the new format?")
            response = input("Run migration? (y/N): ").strip().lower()
            
            if response == 'y':
                result = subprocess.run([sys.executable, "migrate_config.py"], 
                                      capture_output=False, text=True)
                return result.returncode == 0
            return False
        else:
            print("✅ config.yaml exists")
            return True
    
    return False


def run_tests():
    """Run the test suite."""
    print("\n🧪 Running tests...")
    print("-" * 50)
    
    result = subprocess.run([sys.executable, "test_fixes.py"], 
                          capture_output=False, text=True)
    
    return result.returncode == 0


def main():
    """Main entry point."""
    print("=" * 60)
    print("   CHAT WITH TOOLS - QUICK START")
    print("=" * 60)
    print("\nChecking your setup after the fixes...\n")
    
    # Step 1: Check Python version
    print("1️⃣  Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
    else:
        print(f"   ❌ Python {version.major}.{version.minor} (need 3.9+)")
        return 1
    
    # Step 2: Check configuration
    print("\n2️⃣  Checking configuration...")
    if not check_config():
        print("\n❌ Configuration issues need to be resolved first.")
        return 1
    
    # Step 3: Run tests
    print("\n3️⃣  Running verification tests...")
    if not run_tests():
        print("\n⚠️  Some tests failed, but you may still be able to run the framework.")
    
    # Step 4: Offer to run the framework
    print("\n" + "=" * 60)
    print("   SETUP COMPLETE")
    print("=" * 60)
    
    print("\n✅ Your framework appears to be properly configured!")
    print("\nWould you like to:")
    print("1. Run the main menu (python main.py)")
    print("2. Run single agent chat (python demos/main.py)")
    print("3. Run tool showcase (python demos/demo_standalone.py)")
    print("4. Exit")
    
    choice = input("\nChoice (1-4): ").strip()
    
    if choice == "1":
        print("\n🚀 Launching main menu...")
        subprocess.run([sys.executable, "main.py"])
    elif choice == "2":
        print("\n💬 Launching single agent chat...")
        subprocess.run([sys.executable, "demos/main.py"])
    elif choice == "3":
        print("\n🛠️  Launching tool showcase...")
        subprocess.run([sys.executable, "demos/demo_standalone.py"])
    else:
        print("\n👋 Setup complete! You can now run:")
        print("   python main.py")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
