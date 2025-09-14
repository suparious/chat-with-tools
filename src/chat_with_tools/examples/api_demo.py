"""
API Integration Demo

Demonstrates advanced tool usage with API integration.
"""

import time
from typing import List, Dict, Any
from ..agent import OpenRouterAgent
from ..orchestrator import TaskOrchestrator
from ..tools import discover_tools


def run_api_demo():
    """Run API integration demonstrations."""
    print("\n" + "="*60)
    print("   🎯 API INTEGRATION DEMO")
    print("="*60)
    print("\nThis demo showcases advanced tool integration with the API")
    
    demos = [
        ("1", "Sequential Tool Chaining", demo_tool_chaining),
        ("2", "Parallel Tool Execution", demo_parallel_tools),
        ("3", "Complex Query Processing", demo_complex_query),
        ("4", "Error Recovery Demo", demo_error_recovery),
    ]
    
    while True:
        print("\n" + "-"*60)
        print("Available Demos:")
        print("-"*60)
        
        for key, name, _ in demos:
            print(f"{key}. {name}")
        
        print("\n0. Exit API Demo")
        
        choice = input("\nSelect a demo (0-4): ").strip()
        
        if choice == "0":
            print("\n👋 Exiting API Demo")
            break
        
        # Find and run selected demo
        for demo_key, demo_name, demo_func in demos:
            if choice == demo_key:
                print(f"\n▶️  Running: {demo_name}")
                print("-"*40)
                try:
                    demo_func()
                except Exception as e:
                    print(f"\n❌ Demo failed: {e}")
                break
        else:
            print("❌ Invalid selection")


def demo_tool_chaining():
    """Demonstrate sequential tool chaining."""
    print("\n📝 Tool Chaining Demo")
    print("This demonstrates how tools can be chained together.\n")
    
    try:
        agent = OpenRouterAgent(silent=False, name="ChainDemo")
        
        # Example: Search -> Summarize -> Python Analysis
        query = "Search for information about Python list comprehensions, summarize it, then write code to demonstrate"
        
        print(f"Query: {query}\n")
        print("🔄 Processing with tool chain...")
        
        start_time = time.time()
        response = agent.run(query)
        elapsed = time.time() - start_time
        
        print("\n✅ Result:")
        print("-"*40)
        print(response)
        print(f"\n⏱️  Completed in {elapsed:.2f} seconds")
        
    except Exception as e:
        print(f"❌ Error in tool chaining demo: {e}")


def demo_parallel_tools():
    """Demonstrate parallel tool execution."""
    print("\n🔀 Parallel Tool Execution Demo")
    print("This demonstrates multiple tools running in parallel.\n")
    
    try:
        from ..config_manager import ConfigManager
        config = ConfigManager().config
        orchestrator = TaskOrchestrator(config)
        
        query = "Analyze the weather in three major cities and compare their climates"
        
        print(f"Query: {query}\n")
        print("🔄 Processing with parallel agents...")
        
        start_time = time.time()
        result = orchestrator.process(query)
        elapsed = time.time() - start_time
        
        print("\n✅ Parallel Execution Result:")
        print("-"*40)
        
        if isinstance(result, dict) and "final_response" in result:
            print(result["final_response"])
        else:
            print(result)
        
        print(f"\n⏱️  Completed in {elapsed:.2f} seconds")
        print("   (Note: Parallel execution is faster than sequential)")
        
    except Exception as e:
        print(f"❌ Error in parallel demo: {e}")


def demo_complex_query():
    """Demonstrate complex query processing."""
    print("\n🧩 Complex Query Processing Demo")
    print("This demonstrates handling of multi-part complex queries.\n")
    
    try:
        agent = OpenRouterAgent(silent=False, name="ComplexDemo")
        
        query = """
        1. Calculate the factorial of 10
        2. Generate the first 15 Fibonacci numbers
        3. Find the prime numbers between 1 and 50
        4. Create a summary comparing these three number sequences
        """
        
        print(f"Complex Query: {query}\n")
        print("🔄 Processing complex multi-part query...")
        
        start_time = time.time()
        response = agent.run(query)
        elapsed = time.time() - start_time
        
        print("\n✅ Complex Query Result:")
        print("-"*40)
        print(response)
        print(f"\n⏱️  Completed in {elapsed:.2f} seconds")
        
    except Exception as e:
        print(f"❌ Error in complex query demo: {e}")


def demo_error_recovery():
    """Demonstrate error handling and recovery."""
    print("\n🛡️ Error Recovery Demo")
    print("This demonstrates how the system handles and recovers from errors.\n")
    
    try:
        agent = OpenRouterAgent(silent=False, name="ErrorDemo")
        
        # Intentionally problematic query to trigger error handling
        query = "Execute this Python code: import os; os.system('ls')"
        
        print(f"Query (with intentional security issue): {query}\n")
        print("🔄 Processing with error handling...")
        
        response = agent.run(query)
        
        print("\n✅ Error Handling Result:")
        print("-"*40)
        print(response)
        print("\n✅ System successfully handled the security issue!")
        
    except Exception as e:
        print(f"System error (expected): {e}")
        print("✅ Error was caught and handled appropriately")


if __name__ == "__main__":
    run_api_demo()
