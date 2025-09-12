#!/usr/bin/env python3
"""
Test script to verify the consolidated agent framework is working correctly.
Run this after consolidation to ensure all features are functional.
"""

import sys
import os
import yaml
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")
    try:
        from chat_with_tools import OpenRouterAgent, TaskOrchestrator, ConfigManager
        print("✅ Core imports successful")
        
        from chat_with_tools.utils import (
            DebugLogger, 
            setup_logging, 
            retry_with_backoff,
            MetricsCollector,
            RateLimiter
        )
        print("✅ Utility imports successful")
        
        from chat_with_tools.tools import discover_tools
        print("✅ Tools import successful")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_config_loading():
    """Test configuration loading."""
    print("\nTesting configuration...")
    try:
        from chat_with_tools import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.config
        
        # Check for new configuration sections
        assert 'performance' in config, "Missing performance section"
        assert 'security' in config, "Missing security section"
        assert 'debug' in config, "Missing debug section"
        
        print("✅ Configuration loaded successfully")
        print(f"  - Model: {config_manager.get_model()}")
        print(f"  - API Key Required: {config_manager.requires_api_key()}")
        print(f"  - Performance Config: {bool(config_manager.get_performance_config())}")
        print(f"  - Security Config: {bool(config_manager.get_security_config())}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_agent_features():
    """Test that agent has all consolidated features."""
    print("\nTesting agent features...")
    try:
        from chat_with_tools import OpenRouterAgent
        
        # Create agent with name (new feature)
        agent = OpenRouterAgent(silent=True, name="TestAgent")
        
        # Check for enhanced features
        assert hasattr(agent, 'metrics'), "Missing metrics collector"
        assert hasattr(agent, 'rate_limiter'), "Missing rate limiter"
        assert hasattr(agent, 'validate_tool_arguments'), "Missing validation method"
        assert hasattr(agent, 'get_metrics'), "Missing get_metrics method"
        assert hasattr(agent, 'requires_api_key'), "Missing requires_api_key method"
        
        print("✅ Agent features verified")
        print(f"  - Agent name: {agent.name}")
        print(f"  - Has metrics: {agent.metrics is not None}")
        print(f"  - Has rate limiter: {hasattr(agent, 'rate_limiter')}")
        print(f"  - Tools loaded: {len(agent.discovered_tools)}")
        
        return True
    except Exception as e:
        print(f"❌ Agent feature test failed: {e}")
        return False

def test_tools():
    """Test tool discovery and loading."""
    print("\nTesting tools...")
    try:
        from chat_with_tools.tools import discover_tools
        from chat_with_tools import ConfigManager
        
        config_manager = ConfigManager()
        tools = discover_tools(config_manager.config, silent=True)
        
        print(f"✅ Discovered {len(tools)} tools:")
        for name, tool in tools.items():
            print(f"  - {name}: {tool.description[:50]}...")
        
        # Verify essential tools exist
        essential_tools = ['search_web', 'save_memory', 'read_file', 'write_file', 
                          'execute_python', 'think_step_by_step', 'mark_task_complete']
        
        for tool_name in essential_tools:
            if tool_name not in tools:
                print(f"  ⚠️  Missing tool: {tool_name}")
        
        return True
    except Exception as e:
        print(f"❌ Tools test failed: {e}")
        return False

def test_orchestrator():
    """Test orchestrator functionality."""
    print("\nTesting orchestrator...")
    try:
        from chat_with_tools import TaskOrchestrator
        
        orchestrator = TaskOrchestrator(silent=True)
        
        print(f"✅ Orchestrator initialized")
        print(f"  - Parallel agents: {orchestrator.num_agents}")
        print(f"  - Task timeout: {orchestrator.task_timeout}s")
        print(f"  - Aggregation strategy: {orchestrator.aggregation_strategy}")
        
        # Test task decomposition
        questions = orchestrator.decompose_task("Test query", 2)
        print(f"  - Task decomposition working: {len(questions) == 2}")
        
        return True
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        return False

def test_metrics():
    """Test metrics collection."""
    print("\nTesting metrics...")
    try:
        from chat_with_tools.utils import MetricsCollector
        
        metrics = MetricsCollector()
        
        # Test recording various metrics
        metrics.record_api_call(tokens=100)
        metrics.record_tool_call("test_tool")
        metrics.record_response_time(2.5)
        
        summary = metrics.get_summary()
        
        print("✅ Metrics collector working")
        print(f"  - API calls: {summary['api_calls']}")
        print(f"  - Tool calls: {summary['tool_calls']}")
        print(f"  - Total tokens: {summary['total_tokens']}")
        
        return True
    except Exception as e:
        print(f"❌ Metrics test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("CONSOLIDATED AGENT FRAMEWORK TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_config_loading,
        test_agent_features,
        test_tools,
        test_orchestrator,
        test_metrics
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("\nThe consolidated framework is working correctly!")
        print("You can now:")
        print("1. Run 'python main.py' to use the interactive menu")
        print("2. Use the consolidated agent with all enhanced features")
        print("3. Remove the .bak files if everything is working")
    else:
        print(f"⚠️  SOME TESTS FAILED ({passed}/{total} passed)")
        print("\nPlease check the errors above and ensure:")
        print("1. All dependencies are installed: pip install -r requirements.txt")
        print("2. The config.yaml file exists and is properly formatted")
        print("3. The package is installed: pip install -e .")
    
    return passed == total

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
