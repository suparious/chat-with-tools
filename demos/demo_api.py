#!/usr/bin/env python3
"""
API-Based Demo for Chat with Tools Framework
This demo uses the actual agent with your vLLM endpoint to demonstrate the tools.
"""

import json
import yaml
import sys
import os
import time
import traceback
from pathlib import Path
from typing import Dict, Any, List

# Add both the project root and src directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')

# Add src path first so imports work correctly
if src_path not in sys.path:
    sys.path.insert(0, src_path)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import directly from chat_with_tools (not src.chat_with_tools)
from chat_with_tools.agent import OpenRouterAgent


def check_config():
    """Check if config is properly set up for API usage."""
    print("\n" + "="*60)
    print("🔍 CHECKING CONFIGURATION")
    print("="*60)
    
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        print("❌ config.yaml not found!")
        return None
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Check API settings
    api_key = config.get('openrouter', {}).get('api_key', '')
    base_url = config.get('openrouter', {}).get('base_url', '')
    model = config.get('openrouter', {}).get('model', '')
    
    print(f"✅ Config loaded from: {config_path}")
    print(f"📡 Base URL: {base_url}")
    print(f"🤖 Model: {model}")
    
    if base_url == "http://infer.sbx-1.lq.ca.obenv.net:8000/v1":
        print("✅ Using vLLM endpoint (OpenAI-compatible)")
    elif "openrouter" in base_url:
        print("✅ Using OpenRouter API")
        if not api_key or api_key == "your-api-key-here":
            print("⚠️  Warning: OpenRouter API key not set in config.yaml")
    else:
        print("ℹ️  Using custom endpoint")
    
    return config


def test_agent_initialization(silent=False):
    """Test if agent can be initialized with discovered tools."""
    print("\n" + "="*60)
    print("🤖 INITIALIZING AGENT")
    print("="*60)
    
    try:
        agent = OpenRouterAgent(silent=silent)
        print(f"✅ Agent initialized successfully")
        print(f"📦 Tools loaded: {len(agent.tools)}")
        
        # List available tools
        print("\n📋 Available tools:")
        for tool in agent.tools:
            tool_name = tool['function']['name']
            tool_desc = tool['function']['description'][:100] + "..." if len(tool['function']['description']) > 100 else tool['function']['description']
            print(f"   • {tool_name}: {tool_desc}")
        
        return agent
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        traceback.print_exc()
        return None


def demo_sequential_thinking_with_agent(agent: OpenRouterAgent):
    """Demo sequential thinking through the agent."""
    print("\n" + "="*60)
    print("🧠 SEQUENTIAL THINKING VIA AGENT")
    print("="*60)
    
    prompts = [
        "Use the sequential thinking tool to analyze: How can we improve code review processes in a development team? Start a thinking session, add at least 3 thoughts, revise one, and then conclude.",
        
        "Think step-by-step about this problem: What are the trade-offs between microservices and monolithic architecture? Use the sequential thinking tool to explore this systematically."
    ]
    
    print("\n📝 Testing sequential thinking with agent...")
    print(f"Prompt: {prompts[0][:100]}...")
    
    try:
        response = agent.run(prompts[0])
        print("\n🤖 Agent Response:")
        print("-" * 40)
        print(response)
        print("-" * 40)
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def demo_memory_with_agent(agent: OpenRouterAgent):
    """Demo memory tool through the agent."""
    print("\n" + "="*60)
    print("💾 MEMORY TOOL VIA AGENT")
    print("="*60)
    
    prompts = [
        "Store this in your memory as a fact: The Chat with Tools framework supports parallel execution of 4 agents by default. Tag it with 'framework' and 'architecture'.",
        
        "Search your memory for anything related to 'framework' and tell me what you find.",
        
        "Store this preference in memory: Users prefer detailed technical explanations with code examples. Tag it as 'user-preference' and 'communication'.",
        
        "Give me statistics about your current memory storage."
    ]
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n📝 Test {i}: {prompt[:80]}...")
        try:
            response = agent.run(prompt)
            print(f"\n🤖 Response {i}:")
            print("-" * 40)
            print(response[:500] + "..." if len(response) > 500 else response)
            print("-" * 40)
            time.sleep(1)  # Small delay between requests
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    return True


def demo_python_executor_with_agent(agent: OpenRouterAgent):
    """Demo Python executor through the agent."""
    print("\n" + "="*60)
    print("🐍 PYTHON EXECUTOR VIA AGENT")
    print("="*60)
    
    prompts = [
        """Use the Python executor to calculate the factorial of 10 and the first 15 Fibonacci numbers. 
        Show me the code and results.""",
        
        """Execute Python code to analyze this data: [23, 45, 67, 89, 12, 34, 56, 78, 90, 21]. 
        Calculate mean, median, standard deviation, and identify any outliers.""",
        
        """Write and execute Python code to find all prime numbers between 1 and 100 using the Sieve of Eratosthenes algorithm."""
    ]
    
    print("\n📝 Testing Python execution with agent...")
    print(f"Prompt: {prompts[1][:100]}...")
    
    try:
        response = agent.run(prompts[1])
        print("\n🤖 Agent Response:")
        print("-" * 40)
        print(response)
        print("-" * 40)
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def demo_summarization_with_agent(agent: OpenRouterAgent):
    """Demo summarization tool through the agent."""
    print("\n" + "="*60)
    print("📄 SUMMARIZATION VIA AGENT")
    print("="*60)
    
    long_text = """
    Artificial Intelligence has evolved significantly over the past decade, transforming from a specialized 
    research field into a cornerstone of modern technology. Machine learning algorithms now power everything 
    from recommendation systems to autonomous vehicles. Natural language processing has reached a level where 
    AI can engage in meaningful conversations and generate human-like text. Computer vision systems can identify 
    objects, faces, and even emotions with remarkable accuracy. The integration of AI into healthcare has enabled 
    early disease detection and personalized treatment plans. In finance, AI algorithms detect fraud and make 
    split-second trading decisions. The education sector uses AI for personalized learning experiences and 
    automated grading. However, with these advances come important ethical considerations about privacy, bias, 
    and the future of human employment. Researchers and policymakers are working to establish frameworks that 
    ensure AI development remains beneficial and aligned with human values.
    """
    
    prompts = [
        f"Use the summarization tool to analyze this text and give me statistics about its readability: {long_text}",
        
        f"Summarize this text to 30% of its original length: {long_text}",
        
        f"Extract the 3 most important key points from this text: {long_text}"
    ]
    
    print("\n📝 Testing summarization with agent...")
    print("Text sample:", long_text[:100] + "...")
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n📝 Test {i}: {prompt.split(':')[0]}...")
        try:
            response = agent.run(prompt)
            print(f"\n🤖 Response {i}:")
            print("-" * 40)
            print(response)
            print("-" * 40)
            time.sleep(1)
        except Exception as e:
            print(f"❌ Error in test {i}: {e}")
            return False
    
    return True


def demo_combined_tools(agent: OpenRouterAgent):
    """Demo using multiple tools together."""
    print("\n" + "="*60)
    print("🔗 COMBINED TOOLS DEMONSTRATION")
    print("="*60)
    
    complex_prompt = """
    I need you to help me analyze a dataset. First, use the Python executor to generate 50 random 
    data points from a normal distribution with mean=100 and std=15. Calculate basic statistics for this data.
    Then, store the results in your memory as a fact, tagged with 'data-analysis' and 'statistics'.
    Finally, use sequential thinking to propose 3 ways we could visualize this data effectively.
    """
    
    print("\n📝 Complex multi-tool task:")
    print(complex_prompt[:150] + "...")
    
    try:
        print("\n⏳ Processing complex request (this may take a moment)...")
        response = agent.run(complex_prompt)
        print("\n🤖 Agent Response:")
        print("-" * 40)
        print(response)
        print("-" * 40)
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        return False


def run_interactive_demo(agent: OpenRouterAgent):
    """Run an interactive demo where users can test tools through natural language."""
    print("\n" + "="*60)
    print("💬 INTERACTIVE AGENT DEMO")
    print("="*60)
    print("\nYou can now interact with the agent using natural language.")
    print("The agent has access to all tools and will use them as needed.")
    print("\nExample commands:")
    print("  • 'Think through the problem of...' (Sequential Thinking)")
    print("  • 'Remember that...' or 'What do you remember about...' (Memory)")
    print("  • 'Calculate...' or 'Write Python code to...' (Python Executor)")
    print("  • 'Summarize this text...' (Summarization)")
    print("\nType 'quit' to exit.")
    print("-" * 60)
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("\n⏳ Agent thinking...")
            response = agent.run(user_input)
            print(f"\n🤖 Agent: {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Exiting interactive mode...")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or type 'quit' to exit.")


def run_automated_test_suite(agent: OpenRouterAgent):
    """Run automated tests for all tools."""
    print("\n" + "="*60)
    print("🧪 AUTOMATED TEST SUITE")
    print("="*60)
    
    tests = [
        ("Sequential Thinking", demo_sequential_thinking_with_agent),
        ("Memory", demo_memory_with_agent),
        ("Python Executor", demo_python_executor_with_agent),
        ("Summarization", demo_summarization_with_agent),
        ("Combined Tools", demo_combined_tools)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 Testing: {test_name}")
        print("-" * 40)
        try:
            success = test_func(agent)
            results[test_name] = success
            if success:
                print(f"✅ {test_name} test passed")
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test error: {e}")
            results[test_name] = False
        
        time.sleep(2)  # Delay between tests
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name:20} {status}")
    
    print(f"\n📈 Overall: {passed}/{total} tests passed ({(passed/total)*100:.0f}%)")
    
    return results


def main():
    """Main demo function."""
    print("\n" + "="*60)
    print("   🚀 CHAT WITH TOOLS - API DEMO")
    print("="*60)
    print("\nThis demo tests the tools through the actual agent using your API.")
    
    # Check configuration
    config = check_config()
    if not config:
        print("\n❌ Cannot proceed without valid configuration.")
        print("Please ensure config.yaml exists and is properly configured.")
        return
    
    # Initialize agent
    agent = test_agent_initialization(silent=False)
    if not agent:
        print("\n❌ Cannot proceed without agent initialization.")
        print("\nTroubleshooting tips:")
        print("1. Check that your vLLM endpoint is running")
        print("2. Verify the base_url in config.yaml is correct")
        print("3. Ensure all dependencies are installed: pip install pyyaml openai")
        return
    
    while True:
        print("\n" + "-"*40)
        print("Select demo mode:")
        print("1. Sequential Thinking Demo")
        print("2. Memory Tool Demo")
        print("3. Python Executor Demo")
        print("4. Summarization Demo")
        print("5. Combined Tools Demo")
        print("6. Run All Automated Tests")
        print("7. Interactive Mode (Chat with Agent)")
        print("8. Exit")
        
        choice = input("\nChoice (1-8): ").strip()
        
        if choice == "1":
            demo_sequential_thinking_with_agent(agent)
        elif choice == "2":
            demo_memory_with_agent(agent)
        elif choice == "3":
            demo_python_executor_with_agent(agent)
        elif choice == "4":
            demo_summarization_with_agent(agent)
        elif choice == "5":
            demo_combined_tools(agent)
        elif choice == "6":
            run_automated_test_suite(agent)
        elif choice == "7":
            run_interactive_demo(agent)
        elif choice == "8":
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-8.")


if __name__ == "__main__":
    try:
        # First check if we can import required modules
        try:
            import yaml
            from chat_with_tools.agent import OpenRouterAgent
        except ImportError as e:
            print(f"\n❌ Missing required module: {e}")
            print("\nPlease install dependencies:")
            print("  pip install pyyaml openai")
            sys.exit(1)
        
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        traceback.print_exc()
