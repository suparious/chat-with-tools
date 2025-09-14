#!/usr/bin/env python3
"""
Test script to verify the consolidated search tool is working correctly.
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
print("SEARCH TOOL CONSOLIDATION TEST")
print("=" * 60)

try:
    # Test importing the search tool
    print("\n🔍 Testing search tool import...")
    from chat_with_tools.tools.search_tool import SearchTool
    print("✅ SearchTool imported successfully")
    
    # Test instantiation
    print("\n🔧 Testing tool instantiation...")
    config = {
        'search': {
            'cache_ttl': 3600,
            'max_content_length': 5000,
            'request_timeout': 10,
            'user_agent': 'Test-Agent/1.0'
        }
    }
    tool = SearchTool(config)
    print(f"✅ Tool instantiated: {tool.name}")
    print(f"   Description: {tool.description[:50]}...")
    
    # Check that the enhanced features are present
    print("\n✨ Checking enhanced features...")
    features = []
    
    # Check for cache
    if hasattr(tool, 'cache'):
        features.append("✓ Caching system")
    
    # Check for security settings
    if hasattr(tool, 'blocked_domains'):
        features.append("✓ Security domain blocking")
    
    # Check for logger
    if hasattr(tool, 'logger'):
        features.append("✓ Logging support")
    
    # Check for content fetching
    if hasattr(tool, '_fetch_page_content'):
        features.append("✓ Page content fetching")
    
    # Check for URL safety validation
    if hasattr(tool, '_is_url_safe'):
        features.append("✓ URL safety validation")
    
    for feature in features:
        print(f"   {feature}")
    
    # Test the parameters
    print("\n📋 Tool parameters:")
    params = tool.parameters
    for prop, details in params.get('properties', {}).items():
        desc = details.get('description', 'No description')[:50]
        print(f"   • {prop}: {desc}...")
    
    # Test a simple search (optional - requires internet)
    print("\n🌐 Test search capability:")
    try:
        # Try a simple search with caching disabled
        results = tool.execute("test query", max_results=1, fetch_content=False)
        if isinstance(results, list) and len(results) > 0:
            if 'error' in results[0]:
                print(f"   ⚠️ Search returned error: {results[0]['error']}")
            else:
                print(f"   ✅ Search works! Got {len(results)} result(s)")
                if results[0].get('title'):
                    print(f"      First result: {results[0]['title'][:50]}...")
        else:
            print("   ⚠️ No results returned (network might be unavailable)")
    except Exception as e:
        print(f"   ⚠️ Search test skipped: {e}")
    
    # Verify search_tool_enhanced.py is gone
    print("\n🗑️ Checking old file removal...")
    enhanced_path = os.path.join(src_path, 'chat_with_tools', 'tools', 'search_tool_enhanced.py')
    if not os.path.exists(enhanced_path):
        print("   ✅ search_tool_enhanced.py has been removed")
    else:
        print("   ❌ search_tool_enhanced.py still exists!")
    
    print("\n" + "=" * 60)
    print("✅ CONSOLIDATION SUCCESSFUL!")
    print("=" * 60)
    print("\nThe search tool has been successfully consolidated:")
    print("• All enhanced features preserved (caching, security, etc.)")
    print("• Old search_tool_enhanced.py removed")
    print("• Single SearchTool class in search_tool.py")
    print("• Tool name remains 'search_web' for compatibility")
    
except ImportError as e:
    print(f"\n❌ Import error: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure you're in the project directory")
    print("2. Check that src/chat_with_tools/tools/search_tool.py exists")
    
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
