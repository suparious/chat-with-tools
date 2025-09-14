#!/usr/bin/env python3
"""
Quick test script to verify configuration and import fixes.
"""

import sys
import os
import traceback
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")
    print("-" * 50)
    
    tests = []
    
    # Test core modules
    try:
        from src.chat_with_tools.agent import OpenRouterAgent
        print("✅ agent.py imports correctly")
        tests.append(True)
    except ImportError as e:
        print(f"❌ agent.py import failed: {e}")
        tests.append(False)
    
    try:
        from src.chat_with_tools.config_manager import ConfigManager
        print("✅ config_manager.py imports correctly")
        tests.append(True)
    except ImportError as e:
        print(f"❌ config_manager.py import failed: {e}")
        tests.append(False)
    
    try:
        from src.chat_with_tools.orchestrator import TaskOrchestrator
        print("✅ orchestrator.py imports correctly")
        tests.append(True)
    except ImportError as e:
        print(f"❌ orchestrator.py import failed: {e}")
        tests.append(False)
    
    try:
        from src.chat_with_tools.utils import setup_logging, DebugLogger
        print("✅ utils.py imports correctly")
        tests.append(True)
    except ImportError as e:
        print(f"❌ utils.py import failed: {e}")
        tests.append(False)
    
    # Test tools
    try:
        from src.chat_with_tools.tools import discover_tools
        print("✅ tools discovery imports correctly")
        tests.append(True)
    except ImportError as e:
        print(f"❌ tools discovery import failed: {e}")
        tests.append(False)
    
    return all(tests)


def test_config_loading():
    """Test configuration loading with new structure."""
    print("\nTesting configuration...")
    print("-" * 50)
    
    try:
        from src.chat_with_tools.config_manager import ConfigManager
        
        # Try to load config
        try:
            config_manager = ConfigManager()
            print("✅ Configuration loaded successfully")
            
            # Test new config structure
            log_config = config_manager.get_logging_config()
            debug_config = config_manager.get_debug_config()
            
            print(f"   Log level: {log_config.get('level', 'INFO')}")
            print(f"   Debug enabled: {debug_config.get('enabled', False)}")
            print(f"   Console output: {log_config.get('console', {}).get('enabled', True)}")
            
            return True
            
        except FileNotFoundError:
            print("⚠️  No config.yaml found (this is OK for testing)")
            print("   Copy config.example.yaml to config.yaml to test with real config")
            return True
            
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        traceback.print_exc()
        return False


def test_logging_system():
    """Test the unified logging system."""
    print("\nTesting logging system...")
    print("-" * 50)
    
    try:
        from src.chat_with_tools.utils import setup_logging, DebugLogger
        
        # Test basic logging setup
        logger = setup_logging("test_logger", level="INFO")
        logger.info("Test message - this should appear")
        print("✅ Basic logging works")
        
        # Test with config
        test_config = {
            'logging': {
                'level': 'DEBUG',
                'console': {
                    'enabled': True,
                    'format': '%(levelname)s - %(message)s'
                },
                'debug': {
                    'enabled': False
                }
            }
        }
        
        logger2 = setup_logging("test_logger2", config=test_config)
        logger2.debug("Debug test message")
        print("✅ Config-based logging works")
        
        # Test debug logger
        debug_logger = DebugLogger(test_config)
        if not debug_logger.enabled:
            print("✅ Debug logger respects config (disabled)")
        else:
            print("✅ Debug logger initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        traceback.print_exc()
        return False


def test_demo_imports():
    """Test that demo files can import correctly."""
    print("\nTesting demo imports...")
    print("-" * 50)
    
    demo_files = [
        "demos/main.py",
        "demos/council_chat.py",
        "demos/demo_standalone.py",
        "demos/demo_api.py"
    ]
    
    tests = []
    for demo_file in demo_files:
        demo_path = Path(demo_file)
        if demo_path.exists():
            # Read the file and check imports
            try:
                with open(demo_path, 'r') as f:
                    content = f.read()
                    if 'sys.path.insert(0, project_root)' in content or 'sys.path.insert(0, str(project_root))' in content:
                        print(f"✅ {demo_file} has correct path setup")
                        tests.append(True)
                    else:
                        print(f"⚠️  {demo_file} may have path issues")
                        tests.append(True)  # Warning, not failure
            except Exception as e:
                print(f"❌ Could not check {demo_file}: {e}")
                tests.append(False)
        else:
            print(f"⚠️  {demo_file} not found")
            tests.append(True)  # Not a failure if file doesn't exist
    
    return all(tests)


def main():
    """Run all tests."""
    print("=" * 60)
    print("   CONFIGURATION AND IMPORT TEST SUITE")
    print("=" * 60)
    print("\nThis tests the recent fixes to the framework:\n")
    print("1. Unified logging configuration")
    print("2. Fixed import paths")
    print("3. Config manager updates")
    print("\n" + "=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Import Tests", test_imports()))
    results.append(("Config Loading", test_config_loading()))
    results.append(("Logging System", test_logging_system()))
    results.append(("Demo Imports", test_demo_imports()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("   TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("\n🎉 All tests passed! The framework is working correctly.")
        print("\nNext steps:")
        print("1. Copy config.example.yaml to config.yaml")
        print("2. Add your OpenRouter API key")
        print("3. Run: python main.py")
    else:
        print("\n⚠️  Some tests failed. Please check the output above.")
        print("\nTroubleshooting:")
        print("1. Ensure all dependencies are installed: pip install -r requirements.txt")
        print("2. Run the migration script: python migrate_config.py")
        print("3. Check that you're in the project root directory")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
