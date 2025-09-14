#!/usr/bin/env python3
"""
Example demonstrating vLLM structured output capabilities.
This script shows how to use the enhanced agent with vLLM backend for better tool calling accuracy.
"""

import sys
import os
import json
import yaml
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from chat_with_tools.agent import OpenRouterAgent
from chat_with_tools.backends.vllm_backend import VLLMBackend, VLLMConfig, VLLMToolExecutor
from chat_with_tools.structured_output import (
    StructuredToolResponse,
    StructuredAgentResponse,
    ToolRegistry,
    ToolCallOptimizer
)


def demonstrate_structured_tool_calling():
    """Demonstrate structured tool calling with vLLM."""
    print("=" * 60)
    print("vLLM Structured Tool Calling Demo")
    print("=" * 60)
    
    # Load config
    config_path = project_root / "config" / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Check if vLLM is configured
    if not config.get('vllm_structured_output', {}).get('enabled', False):
        print("\n⚠️  vLLM structured output is not enabled in config.")
        print("To enable, set vllm_structured_output.enabled = true")
        return
    
    # Initialize vLLM backend
    vllm_config = VLLMConfig(
        base_url=config['openrouter']['base_url'],
        model=config['openrouter']['model'],
        use_structured_output=True,
        guided_backend=config['vllm_structured_output'].get('backend', 'outlines'),
        enforce_schema=config['vllm_structured_output'].get('enforcement_level', 'strict') == 'strict'
    )
    
    print(f"\n✅ vLLM Backend Configuration:")
    print(f"   Base URL: {vllm_config.base_url}")
    print(f"   Model: {vllm_config.model}")
    print(f"   Backend: {vllm_config.guided_backend}")
    print(f"   Schema Enforcement: {'Strict' if vllm_config.enforce_schema else 'Relaxed'}")
    
    # Initialize backend
    backend = VLLMBackend(vllm_config)
    
    # Test structured response
    test_query = "Calculate the sum of 42 and 58, then search for information about the result."
    print(f"\n📝 Test Query: {test_query}")
    
    # Prepare messages
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant with access to tools. Always use tools when appropriate and structure your responses clearly."
        },
        {
            "role": "user",
            "content": test_query
        }
    ]
    
    # Define available tools (simplified for demo)
    tools = [
        {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "Perform mathematical calculations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate"
                        }
                    },
                    "required": ["expression"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_web",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]
    
    print("\n🔧 Making structured tool call request...")
    
    try:
        # Request with structured output format
        response = backend.complete(
            messages=messages,
            tools=tools,
            response_format=StructuredToolResponse
        )
        
        # Validate and parse response
        result = backend.validate_response(response, StructuredToolResponse)
        
        print("\n✅ Structured Response Received:")
        print(json.dumps(result, indent=2))
        
        # Demonstrate tool argument validation
        if result.get('tool_calls'):
            print("\n🔍 Validating Tool Arguments:")
            for call in result['tool_calls']:
                tool_name = call.get('tool_name')
                arguments = call.get('arguments')
                
                try:
                    validated_args = ToolRegistry.validate_arguments(tool_name, arguments)
                    print(f"   ✅ {tool_name}: Arguments valid")
                    print(f"      {validated_args}")
                except Exception as e:
                    print(f"   ❌ {tool_name}: Validation failed - {e}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def demonstrate_tool_optimization():
    """Demonstrate tool call optimization features."""
    print("\n" + "=" * 60)
    print("Tool Call Optimization Demo")
    print("=" * 60)
    
    # Test queries
    test_queries = [
        "Search for the latest news about AI",
        "Calculate 15% of 250",
        "Write a Python script to sort a list",
        "Remember that my favorite color is blue",
        "Read the contents of config.yaml"
    ]
    
    available_tools = [
        "search_web", "calculate", "python_executor",
        "memory", "read_file", "write_file", "sequential_thinking"
    ]
    
    optimizer = ToolCallOptimizer()
    
    print("\n🎯 Tool Suggestion Analysis:")
    for query in test_queries:
        suggested_tool = optimizer.suggest_tool(query, available_tools)
        print(f"\n   Query: '{query}'")
        print(f"   Suggested Tool: {suggested_tool or 'No suggestion'}")
        
        if suggested_tool:
            optimized_query = optimizer.preprocess_query(query, suggested_tool)
            if optimized_query != query:
                print(f"   Optimized Query: '{optimized_query}'")


def demonstrate_multi_endpoint_selection():
    """Demonstrate automatic endpoint selection based on query type."""
    print("\n" + "=" * 60)
    print("Multi-Endpoint Selection Demo")
    print("=" * 60)
    
    # Load config
    config_path = project_root / "config" / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Check if multi-endpoint is configured
    endpoints = config.get('inference_endpoints', {})
    if not endpoints:
        print("\n⚠️  No inference endpoints configured.")
        return
    
    print("\n📡 Available Endpoints:")
    for name, endpoint_config in endpoints.items():
        print(f"   • {name}: {endpoint_config.get('model')} ({endpoint_config.get('model_type')})")
    
    # Test queries with different complexity
    test_cases = [
        ("What is 2+2?", "fast"),  # Simple query -> fast endpoint
        ("Explain quantum computing in detail with examples", "thinking"),  # Complex -> thinking
        ("List the capitals of European countries", "balanced"),  # Moderate -> balanced
    ]
    
    print("\n🔄 Query Routing Analysis:")
    for query, expected_type in test_cases:
        print(f"\n   Query: '{query[:50]}...' if len(query) > 50 else '{query}'")
        print(f"   Expected Endpoint Type: {expected_type}")
        
        # Analyze query for routing
        query_lower = query.lower()
        
        # Check for thinking keywords
        thinking_keywords = config['agent']['query_routing']['thinking_keywords']
        fast_keywords = config['agent']['query_routing']['fast_keywords']
        
        if any(keyword in query_lower for keyword in thinking_keywords):
            selected = "thinking"
        elif any(keyword in query_lower for keyword in fast_keywords):
            selected = "fast"
        else:
            selected = "balanced"
        
        print(f"   Selected Endpoint Type: {selected}")
        print(f"   Match: {'✅' if selected == expected_type else '❌'}")


def main():
    """Run all demonstrations."""
    print("\n🚀 vLLM Structured Output & Tool Optimization Demo")
    print("=" * 60)
    
    # Check if running with vLLM
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    is_vllm = config.get('openrouter', {}).get('is_vllm', False)
    
    if not is_vllm:
        print("\n⚠️  Warning: vLLM is not configured as the backend.")
        print("   To use vLLM features, set openrouter.is_vllm = true in config.yaml")
        print("\n   Running demos anyway to show functionality...")
    
    # Run demonstrations
    try:
        # Basic tool optimization (works without vLLM)
        demonstrate_tool_optimization()
        
        # Multi-endpoint selection (works without vLLM)
        demonstrate_multi_endpoint_selection()
        
        # Structured output (requires vLLM)
        if is_vllm:
            demonstrate_structured_tool_calling()
        else:
            print("\n⏭️  Skipping structured output demo (requires vLLM)")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
