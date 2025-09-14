import sys
import os
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


def run_interactive():
    """Run in interactive mode with user input."""
    print("OpenRouter Agent with DuckDuckGo Search")
    print("Type 'quit', 'exit', or 'bye' to exit")
    print("-" * 50)
    
    try:
        agent = OpenRouterAgent()
        print("Agent initialized successfully!")
        print(f"Using model: {agent.config['openrouter']['model']}")
        
        # Check if using vLLM
        if agent.config['openrouter'].get('is_vllm', False):
            print("✅ Using vLLM backend")
            if agent.config.get('vllm_structured_output', {}).get('enabled', False):
                print("✅ Structured output enabled")
        
        print("Note: Make sure to set your OpenRouter API key in config.yaml")
        print("-" * 50)
    except Exception as e:
        print(f"Error initializing agent: {e}")
        print("Make sure you have:")
        print("1. Set your OpenRouter API key in config/config.yaml")
        print("2. Installed all dependencies with: pip install -r requirements.txt")
        return
    
    while True:
        try:
            user_input = input("\nUser: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("Goodbye!")
                break
            
            if not user_input:
                print("Please enter a question or command.")
                continue
            
            print("Agent: Thinking...")
            response = agent.run(user_input)
            print(f"Agent: {response}")
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except EOFError:
            # Handle non-interactive mode gracefully
            print("\nNo input available. Exiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
            print("Please try again or type 'quit' to exit.")


def run_demo(query: str = None):
    """Run a non-interactive demo with a predefined query."""
    print("OpenRouter Agent Demo (Non-Interactive Mode)")
    print("-" * 50)
    
    try:
        agent = OpenRouterAgent(silent=False)
        print("Agent initialized successfully!")
        print(f"Using model: {agent.config['openrouter']['model']}")
        
        # Check configuration
        config_info = []
        if agent.config['openrouter'].get('is_vllm', False):
            config_info.append("vLLM backend")
        if agent.config.get('vllm_structured_output', {}).get('enabled', False):
            config_info.append("Structured output")
        if agent.endpoint_manager.is_enabled():
            config_info.append(f"{len(agent.endpoint_manager.endpoints)} endpoints")
        
        if config_info:
            print(f"Features: {', '.join(config_info)}")
        
        print("-" * 50)
        
        # Use provided query or default
        if not query:
            query = "What is the weather like today and calculate 15% tip on a $45 meal"
        
        print(f"\nDemo Query: {query}")
        print("\nAgent: Processing...")
        
        response = agent.run(query)
        
        print("\n" + "=" * 50)
        print("Agent Response:")
        print("=" * 50)
        print(response)
        print("=" * 50)
        
        # Show metrics if available
        if agent.metrics:
            metrics = agent.get_metrics()
            print("\nPerformance Metrics:")
            print(f"  API Calls: {metrics.get('api_calls', 0)}")
            print(f"  Tool Calls: {metrics.get('tool_calls', {})}")
            print(f"  Total Tokens: {metrics.get('total_tokens', 0)}")
            print(f"  Avg Response Time: {metrics.get('avg_response_time', 0):.2f}s")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point for the OpenRouter agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenRouter Agent with Tool Support")
    parser.add_argument("--demo", action="store_true", help="Run in demo mode (non-interactive)")
    parser.add_argument("--query", type=str, help="Query for demo mode")
    parser.add_argument("--endpoint", type=str, help="Specific endpoint to use (e.g., 'fast', 'thinking')")
    
    args = parser.parse_args()
    
    if args.demo:
        run_demo(args.query)
    else:
        # Check if running in a terminal
        if sys.stdin.isatty():
            run_interactive()
        else:
            # Non-interactive environment, run demo
            print("Non-interactive environment detected, running demo mode...")
            run_demo()


if __name__ == "__main__":
    main()
