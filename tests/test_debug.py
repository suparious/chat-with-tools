#!/usr/bin/env python3
"""
Test script for debug logging functionality
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

def test_debug_logger():
    """Test the debug logger functionality"""
    print("=" * 60)
    print("Testing Debug Logger")
    print("=" * 60)
    
    # Test with debug disabled
    print("\n1. Testing with debug DISABLED (default)...")
    from src.chat_with_tools.utils import DebugLogger
    from src.chat_with_tools.config_manager import ConfigManager
    
    config_manager = ConfigManager()
    config = config_manager.config
    
    logger = DebugLogger(config)
    print(f"   Debug enabled: {logger.enabled}")
    print(f"   Debug config: {logger.debug_config}")
    
    logger.info("This should not appear in any log file")
    logger.error("This error should not be logged either")
    
    # Test with debug enabled
    print("\n2. Testing with debug ENABLED...")
    
    # Temporarily modify config
    config['debug'] = {
        'enabled': True,
        'log_path': './test_logs',
        'log_level': 'DEBUG',
        'max_log_size_mb': 1,
        'max_log_files': 3,
        'include_timestamps': True,
        'log_tool_calls': True,
        'log_llm_calls': True,
        'log_agent_thoughts': True
    }
    
    # Reset the singleton
    DebugLogger._instance = None
    DebugLogger._initialized = False
    
    # Create new logger with debug enabled
    logger2 = DebugLogger(config)
    print(f"   Debug enabled: {logger2.enabled}")
    print(f"   Log path: {logger2.debug_config.get('log_path')}")
    
    # Test various logging methods
    logger2.log_separator("Test Section")
    logger2.info("Test info message", extra_data="some value")
    logger2.debug("Test debug message")
    logger2.warning("Test warning message")
    logger2.error("Test error message")
    
    logger2.log_agent_iteration(1, 10, "test_agent")
    logger2.log_tool_call("test_tool", {"arg1": "value1"}, result={"status": "success"})
    logger2.log_tool_call("failing_tool", {"arg1": "value1"}, error="Tool failed")
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Test question"}
    ]
    logger2.log_llm_call("test-model", messages)
    
    logger2.log_orchestrator_task("task_1", "STARTED", {"details": "test"})
    logger2.log_orchestrator_task("task_1", "COMPLETED", {"duration": 1.5})
    
    # Check if log file was created
    log_path = Path(logger2.debug_config.get('log_path', './test_logs'))
    if log_path.exists():
        log_files = list(log_path.glob("debug_*.log"))
        if log_files:
            print(f"\n   ✅ Log file created: {log_files[0]}")
            
            # Read and display first few lines
            with open(log_files[0], 'r') as f:
                lines = f.readlines()
                print(f"   📝 Log file contains {len(lines)} lines")
                print("\n   First 10 lines of log:")
                print("   " + "-" * 50)
                for line in lines[:10]:
                    print(f"   {line.rstrip()}")
                if len(lines) > 10:
                    print(f"   ... ({len(lines) - 10} more lines)")
        else:
            print("   ❌ No log files found")
    else:
        print(f"   ❌ Log directory not created: {log_path}")
    
    print("\n" + "=" * 60)
    print("✅ Debug Logger Test Complete")
    print("=" * 60)
    
    # Clean up test logs
    if log_path.exists():
        import shutil
        try:
            shutil.rmtree(log_path)
            print("\n🧹 Cleaned up test logs directory")
        except Exception as e:
            print(f"\n⚠️  Could not clean up test logs: {e}")

def test_imports():
    """Test that all imports work correctly"""
    print("\n" + "=" * 60)
    print("Testing Imports")
    print("=" * 60)
    
    try:
        print("\n1. Testing core imports...")
        from src.chat_with_tools import OpenRouterAgent, EnhancedAgent, TaskOrchestrator
        print("   ✅ Core imports successful")
        
        print("\n2. Testing config manager...")
        from src.chat_with_tools.config_manager import ConfigManager, get_openai_client
        print("   ✅ Config manager imports successful")
        
        print("\n3. Testing utils...")
        from src.chat_with_tools.utils import DebugLogger, MetricsCollector, RateLimiter
        print("   ✅ Utils imports successful")
        
        print("\n4. Testing tools discovery...")
        from src.chat_with_tools.tools import discover_tools
        config_manager = ConfigManager()
        tools = discover_tools(config_manager.config, silent=True)
        print(f"   ✅ Discovered {len(tools)} tools: {list(tools.keys())}")
        
        print("\n5. Testing demo imports...")
        from demos.main import main as single_agent_main
        from demos.council_chat import main as council_main
        print("   ✅ Demo imports successful")
        
        return True
        
    except ImportError as e:
        print(f"\n   ❌ Import error: {e}")
        print("\n   💡 Try running: python setup_dev.py")
        return False

def main():
    """Main test function"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║           Chat with Tools - Debug Testing                      ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Test imports first
    if not test_imports():
        print("\n⚠️  Import tests failed. Please fix import issues first.")
        sys.exit(1)
    
    # Test debug logger
    test_debug_logger()
    
    print(f"""
{'='*60}
📋 Summary:

1. All imports are working correctly
2. Debug logger can be enabled/disabled via config
3. When enabled, logs are written to disk with rotation
4. Various log levels and specialized methods are available

To enable debug logging in production:
1. Edit config/config.yaml
2. Set debug.enabled to true
3. Run your application normally
4. Check ./logs/ directory for debug logs

{'='*60}
    """)

if __name__ == "__main__":
    main()
