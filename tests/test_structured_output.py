#!/usr/bin/env python3
"""
Test the structured output implementation with actual tool calling.
"""

import json
import sys
import os
sys.path.insert(0, '/home/shaun/repos/chat-with-tools/src')

from chat_with_tools.agent import OpenRouterAgent

def test_basic_tool_call():
    """Test basic tool calling with structured output."""
    print("\n=== Test: Basic Tool Call with Structured Output ===")
    
    # Create agent
    agent = OpenRouterAgent(silent=True)
    print(f"Agent created: structured_output={agent.use_structured_output}")
    
    # Test a simple calculation
    query = "Calculate 25% of 80"
    print(f"Query: {query}")
    
    try:
        response = agent.run(query)
        print(f"✅ Success! Response: {response[:200]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_without_structured_output():
    """Test with structured output disabled."""
    print("\n=== Test: Without Structured Output ===")
    
    # Create agent with structured output disabled
    agent = OpenRouterAgent(silent=True, use_structured_output=False)
    print(f"Agent created: structured_output={agent.use_structured_output}")
    
    # Test a simple calculation
    query = "Calculate 25% of 80"
    print(f"Query: {query}")
    
    try:
        response = agent.run(query)
        print(f"✅ Success! Response: {response[:200]}...")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_complex_query():
    """Test a more complex query requiring multiple tools."""
    print("\n=== Test: Complex Query ===")
    
    agent = OpenRouterAgent(silent=True)
    
    query = "Search for information about the Python programming language and calculate 15 factorial"
    print(f"Query: {query}")
    
    try:
        response = agent.run(query)
        print(f"✅ Success! Response length: {len(response)} chars")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Testing Structured Output Implementation")
    print("=" * 50)
    
    # Run tests
    test_basic_tool_call()
    test_without_structured_output()
    # test_complex_query()  # Commented out for now to avoid long-running test
    
    print("\n" + "=" * 50)
    print("Testing complete!")
