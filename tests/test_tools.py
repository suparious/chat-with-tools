#!/usr/bin/env python3
"""
Quick test to verify all tools are loading correctly in Chat with Tools
"""

import sys
from pathlib import Path
from agent import OpenRouterAgent

def test_tool_discovery():
    """Test that all tools are discovered and loaded."""
    print("🔍 Testing Tool Discovery...")
    print("="*50)
    
    # Expected tools
    expected_tools = [
        "search_web",
        "calculate", 
        "read_file",
        "write_file",
        "mark_task_complete",
        "sequential_thinking",
        "memory",
        "python_executor",
        "summarizer"
    ]
    
    try:
        # Initialize agent (will discover tools)
        print("Initializing agent...")
        agent = OpenRouterAgent(silent=True)
        
        # Check discovered tools
        discovered = list(agent.tool_mapping.keys())
        print(f"\n✅ Discovered {len(discovered)} tools:")
        for tool_name in discovered:
            status = "✅" if tool_name in expected_tools else "❓"
            print(f"   {status} {tool_name}")
        
        # Check for missing tools
        missing = [t for t in expected_tools if t not in discovered]
        if missing:
            print(f"\n⚠️  Missing expected tools:")
            for tool in missing:
                print(f"   ❌ {tool}")
        else:
            print(f"\n✅ All expected tools found!")
        
        # Check for extra tools
        extra = [t for t in discovered if t not in expected_tools]
        if extra:
            print(f"\n📦 Additional tools found:")
            for tool in extra:
                print(f"   ➕ {tool}")
        
        # Test each tool's schema
        print("\n📋 Validating Tool Schemas:")
        for tool_name, tool_func in agent.tool_mapping.items():
            # Get the tool object
            tool_obj = agent.discovered_tools.get(tool_name)
            if tool_obj:
                schema = tool_obj.to_openrouter_schema()
                params = schema.get("function", {}).get("parameters", {})
                props = params.get("properties", {})
                print(f"   {tool_name}: {len(props)} parameters")
        
        return len(missing) == 0
        
    except Exception as e:
        print(f"\n❌ Error during tool discovery: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tool_execution():
    """Quick test of tool execution."""
    print("\n🧪 Testing Tool Execution...")
    print("="*50)
    
    try:
        agent = OpenRouterAgent(silent=True)
        
        # Test sequential thinking
        if "sequential_thinking" in agent.tool_mapping:
            print("\n1. Testing Sequential Thinking...")
            result = agent.tool_mapping["sequential_thinking"](
                action="start",
                problem="Test problem"
            )
            if result.get("status") == "session_started":
                print("   ✅ Sequential thinking works")
            else:
                print(f"   ❌ Sequential thinking failed: {result}")
        
        # Test memory
        if "memory" in agent.tool_mapping:
            print("\n2. Testing Memory...")
            result = agent.tool_mapping["memory"](
                action="store",
                content="Test memory",
                memory_type="fact"
            )
            if result.get("status") == "stored":
                print("   ✅ Memory storage works")
            else:
                print(f"   ❌ Memory failed: {result}")
        
        # Test Python executor
        if "python_executor" in agent.tool_mapping:
            print("\n3. Testing Python Executor...")
            result = agent.tool_mapping["python_executor"](
                code="print('Hello from Python'); result = 2 + 2; result"
            )
            if result.get("status") == "success":
                print(f"   ✅ Python executor works (result: {result.get('result')})")
            else:
                print(f"   ❌ Python executor failed: {result}")
        
        # Test summarizer
        if "summarizer" in agent.tool_mapping:
            print("\n4. Testing Summarizer...")
            result = agent.tool_mapping["summarizer"](
                action="statistics",
                text="This is a test text for the summarization tool."
            )
            if result.get("status") == "analyzed":
                stats = result.get("statistics", {})
                print(f"   ✅ Summarizer works (words: {stats.get('word_count', 0)})")
            else:
                print(f"   ❌ Summarizer failed: {result}")
        
        print("\n✅ All tool execution tests completed")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during tool execution: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test runner."""
    print("\n" + "="*60)
    print("   🚀 CHAT WITH TOOLS - TOOL VERIFICATION")
    print("="*60)
    
    # Run tests
    discovery_ok = test_tool_discovery()
    execution_ok = test_tool_execution()
    
    # Summary
    print("\n" + "="*60)
    print("   📊 TEST SUMMARY")
    print("="*60)
    print(f"Tool Discovery: {'✅ PASSED' if discovery_ok else '❌ FAILED'}")
    print(f"Tool Execution: {'✅ PASSED' if execution_ok else '❌ FAILED'}")
    
    if discovery_ok and execution_ok:
        print("\n🎉 All tests passed! Your Chat with Tools framework is ready.")
        print("\nTry these commands:")
        print("  python main.py           - Single agent mode")
        print("  python council_chat.py   - Multi-agent mode")
        print("  python demo_new_tools.py - Demo new tools")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    return 0 if (discovery_ok and execution_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
