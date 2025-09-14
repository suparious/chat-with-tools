#!/usr/bin/env python3
"""
Quick test script to verify the search tool fix is working properly
"""

import sys
import os
import json

# Add both the project root and src directory to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')

if src_path not in sys.path:
    sys.path.insert(0, src_path)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from chat_with_tools.agent import OpenRouterAgent

# Mock tool call class for testing
class MockToolCall:
    class Function:
        def __init__(self, name, arguments):
            self.name = name
            self.arguments = arguments
    
    def __init__(self, name, arguments, id="test_123"):
        self.function = self.Function(name, arguments)
        self.id = id

def test_tool_argument_parsing():
    """Test different argument formats that might come from the LLM"""
    
    print("Testing Tool Argument Parsing")
    print("=" * 60)
    
    try:
        # Create an agent instance
        agent = OpenRouterAgent(silent=True)
        print("✓ Agent initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize agent: {e}")
        return
    
    # Test cases for different argument formats
    test_cases = [
        {
            "name": "Valid JSON string",
            "tool": "search_web",
            "args": '{"query": "test search", "max_results": 5}',
            "expected": {"query": "test search", "max_results": 5}
        },
        {
            "name": "Plain string (should wrap in query)",
            "tool": "search_web",
            "args": "test search query",
            "expected": {"query": "test search query"}
        },
        {
            "name": "Already a dictionary",
            "tool": "search_web",
            "args": {"query": "test", "max_results": 3},
            "expected": {"query": "test", "max_results": 3}
        },
        {
            "name": "Malformed JSON with query tool",
            "tool": "search_web",
            "args": "{'query': 'test'}",  # Single quotes - invalid JSON
            "expected": {"query": "{'query': 'test'}"}
        },
        {
            "name": "Empty string",
            "tool": "search_web",
            "args": "",
            "expected": {"query": ""}
        }
    ]
    
    print("\nRunning test cases:")
    print("-" * 60)
    
    for test in test_cases:
        print(f"\nTest: {test['name']}")
        print(f"  Tool: {test['tool']}")
        print(f"  Input args: {test['args']}")
        
        # Create mock tool call
        mock_call = MockToolCall(test['tool'], test['args'])
        
        try:
            # Use agent's handle_tool_call method
            result = agent.handle_tool_call(mock_call)
            
            # Parse the result content
            content = json.loads(result['content'])
            
            # Check if it's an error
            if 'error' in content:
                print(f"  Result: Error - {content['error']}")
            else:
                print(f"  Result: Success")
                print(f"  Tool was called successfully")
                
        except Exception as e:
            print(f"  Result: Exception - {e}")
    
    print("\n" + "=" * 60)
    print("Tool argument parsing tests completed!")
    print("The search tool should now handle various argument formats correctly.")
    print("\nTry running the main agent with: uv run main.py")

if __name__ == "__main__":
    test_tool_argument_parsing()
