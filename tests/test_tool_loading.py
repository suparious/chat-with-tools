#!/usr/bin/env python3
"""
Test script to verify tool loading is working correctly after the fixes.
"""

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

print("=" * 60)
print("TOOL LOADING TEST")
print("=" * 60)

print(f"\n📁 Project root: {project_root}")
print(f"📁 Source path: {src_path}")
print(f"📁 Python path (first 3): {sys.path[:3]}")

try:
    print("\n🔍 Testing tool discovery...")
    from chat_with_tools.tools import discover_tools
    
    # Run tool discovery with debug output
    tools = discover_tools(config={}, silent=False)
    
    print(f"\n✅ Successfully loaded {len(tools)} tools:")
    for tool_name, tool_instance in tools.items():
        print(f"   • {tool_name}: {tool_instance.description[:50]}...")
    
    print("\n🎉 Tool loading is working correctly!")
    
except ImportError as e:
    print(f"\n❌ Import error: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure you're in the project directory")
    print("2. Check that src/chat_with_tools/tools/ exists")
    print("3. Verify all tool files are present")
    
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    
print("\n" + "=" * 60)
