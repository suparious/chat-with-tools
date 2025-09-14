"""
Single Agent Chat Example

This module provides a simple interactive chat with a single AI agent.
"""

from ..agent import OpenRouterAgent


def run_single_agent():
    """Run single agent chat interface."""
    print("OpenRouter Agent with Tool Access")
    print("Type 'quit', 'exit', or 'bye' to exit")
    print("-" * 50)
    
    try:
        agent = OpenRouterAgent(silent=False, name="Assistant")
        print("Agent initialized successfully!")
        print(f"Using model: {agent.model}")
        print("-" * 50)
    except Exception as e:
        print(f"Error initializing agent: {e}")
        print("\nMake sure you have:")
        print("1. Set your OpenRouter API key in config/config.yaml")
        print("2. Or configured a local vLLM endpoint")
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
        except Exception as e:
            print(f"Error: {e}")
            print("Please try again or type 'quit' to exit.")


if __name__ == "__main__":
    run_single_agent()
