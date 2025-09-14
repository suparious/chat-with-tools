#!/usr/bin/env python3
"""
Test the improved vLLM structured output implementation.
This version properly handles the Outlines backend requirements.
"""

import sys
import os
sys.path.insert(0, '/home/shaun/repos/chat-with-tools/src')

from chat_with_tools.agent import OpenRouterAgent

def test_structured_tool_call():
    """Test tool calling with the fixed structured output."""
    print("\n=== Test: Tool Call with Fixed Structured Output ===")
    
    # Create agent
    agent = OpenRouterAgent(silent=False)
    print(f"Agent created: structured_output={agent.use_structured_output}")
    print(f"vLLM backend: {agent.config.get('vllm_structured_output', {}).get('backend')}")
    
    # Test a simple calculation
    queries = [
        "Calculate 25% of 80",
        "What is the square root of 144?",
        "What is 2 + 2?"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        try:
            response = agent.run(query)
            print(f"✅ Success! Response: {response[:200]}...")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            break

if __name__ == "__main__":
    print("Testing Fixed vLLM Structured Output Implementation")
    print("=" * 50)
    print("This test uses proper schema format that won't crash the vLLM server")
    
    test_structured_tool_call()
    
    print("\n" + "=" * 50)
    print("Testing complete!")
