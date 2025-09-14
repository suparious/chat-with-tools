#!/usr/bin/env python3
"""Test script to verify all imports and basic functionality"""

import sys
import os

# Add both the project root and src directory to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')

# Add src path first so imports work correctly
if src_path not in sys.path:
    sys.path.insert(0, src_path)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("Testing imports and basic functionality...")
print("=" * 60)

# Test 1: Import agent
try:
    from chat_with_tools.agent import OpenRouterAgent
    print("✓ Successfully imported OpenRouterAgent")
except ImportError as e:
    print(f"✗ Failed to import OpenRouterAgent: {e}")
    sys.exit(1)

# Test 2: Import config manager
try:
    from chat_with_tools.config_manager import ConfigManager
    print("✓ Successfully imported ConfigManager")
except ImportError as e:
    print(f"✗ Failed to import ConfigManager: {e}")
    sys.exit(1)

# Test 3: Import tools
try:
    from chat_with_tools.tools import discover_tools
    print("✓ Successfully imported discover_tools")
except ImportError as e:
    print(f"✗ Failed to import discover_tools: {e}")
    sys.exit(1)

# Test 4: Import utils
try:
    from chat_with_tools.utils import setup_logging, DebugLogger
    print("✓ Successfully imported utils")
except ImportError as e:
    print(f"✗ Failed to import utils: {e}")
    sys.exit(1)

# Test 5: Import orchestrator
try:
    from chat_with_tools.orchestrator import MultiAgentOrchestrator
    print("✓ Successfully imported MultiAgentOrchestrator")
except ImportError as e:
    print(f"✗ Failed to import MultiAgentOrchestrator: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("Testing tool discovery...")
print("-" * 60)

# Test 6: Discover tools
try:
    config = {'logging': {'level': 'WARNING'}}  # Minimal config for testing
    tools = discover_tools(config, silent=True)
    print(f"✓ Discovered {len(tools)} tools:")
    for tool_name in tools:
        print(f"  - {tool_name}")
except Exception as e:
    print(f"✗ Failed to discover tools: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Testing configuration...")
print("-" * 60)

# Test 7: Load configuration
try:
    config_manager = ConfigManager()
    print("✓ Successfully loaded configuration")
    print(f"  - Config path: {config_manager.config_path}")
    print(f"  - Model: {config_manager.get_model()}")
    print(f"  - Base URL: {config_manager.get_base_url()}")
    api_key = config_manager.get_api_key()
    if api_key and api_key != 'YOUR API KEY HERE':
        print(f"  - API Key: {'*' * 8}{api_key[-4:] if len(api_key) > 4 else '****'}")
    else:
        print(f"  - API Key: Not configured")
except FileNotFoundError as e:
    print(f"⚠ Configuration file not found (this is expected if config.yaml doesn't exist): {e}")
except Exception as e:
    print(f"✗ Failed to load configuration: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("All import tests completed!")
print("=" * 60)
