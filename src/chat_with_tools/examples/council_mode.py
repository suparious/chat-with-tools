"""
Council Mode Example

Multi-agent council mode with parallel processing.
"""

import time
from typing import List, Dict, Any
from ..orchestrator import TaskOrchestrator
from ..config_manager import ConfigManager


def run_council_mode():
    """Run multi-agent council mode for deep analysis."""
    print("\n" + "="*60)
    print("   🧠 COUNCIL MODE - Multi-Agent Analysis")
    print("="*60)
    print("\nThis mode deploys multiple agents in parallel for comprehensive analysis.")
    print("Each agent provides a unique perspective on your query.")
    print("\nType 'quit', 'exit', or 'bye' to exit")
    print("-" * 60)
    
    try:
        # Initialize configuration
        config_manager = ConfigManager()
        config = config_manager.config
        
        # Get orchestrator configuration
        orch_config = config_manager.get_orchestrator_config()
        num_agents = orch_config.get('parallel_agents', 4)
        
        print(f"\nInitializing council with {num_agents} parallel agents...")
        
        # Create orchestrator
        orchestrator = TaskOrchestrator(config)
        print("✅ Council initialized successfully!")
        print("-" * 60)
        
    except Exception as e:
        print(f"Error initializing council: {e}")
        print("\nMake sure you have:")
        print("1. Set your OpenRouter API key in config/config.yaml")
        print("2. Or configured a local vLLM endpoint")
        return
    
    while True:
        try:
            user_input = input("\n🎯 Your Query: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\n👋 Council session ended. Goodbye!")
                break
            
            if not user_input:
                print("Please enter a question for the council to analyze.")
                continue
            
            print(f"\n🔄 Council deliberating with {num_agents} agents...")
            print("   This may take a moment as agents work in parallel...\n")
            
            start_time = time.time()
            
            # Process with orchestrator
            result = orchestrator.process(user_input)
            
            elapsed_time = time.time() - start_time
            
            # Display results
            print("\n" + "="*60)
            print("   📊 COUNCIL CONSENSUS")
            print("="*60)
            
            if isinstance(result, dict):
                # Show individual agent responses if available
                if "agent_responses" in result:
                    print("\n🎭 Individual Agent Perspectives:\n")
                    for i, response in enumerate(result["agent_responses"], 1):
                        print(f"Agent {i}:")
                        print(f"  {response[:200]}..." if len(response) > 200 else f"  {response}")
                        print()
                
                # Show final synthesis
                if "final_response" in result:
                    print("🎯 Synthesized Response:")
                    print("-" * 40)
                    print(result["final_response"])
                elif "synthesis" in result:
                    print("🎯 Synthesized Response:")
                    print("-" * 40)
                    print(result["synthesis"])
                else:
                    print(result)
            else:
                print(result)
            
            print(f"\n⏱️  Analysis completed in {elapsed_time:.2f} seconds")
            print("="*60)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Council session interrupted")
            break
        except Exception as e:
            print(f"\n❌ Error during council deliberation: {e}")
            print("Please try again with a different query.")


if __name__ == "__main__":
    run_council_mode()
