#!/usr/bin/env python3
"""
Migration script to use enhanced components in Chat with Tools framework.

This script demonstrates how to use the enhanced components while maintaining
backward compatibility with the original implementation.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def setup_environment():
    """Set up environment for enhanced components."""
    print("🔧 Setting up enhanced Chat with Tools framework...")
    
    # Check for API key
    if not os.environ.get('OPENROUTER_API_KEY'):
        print("\n⚠️  Warning: OPENROUTER_API_KEY environment variable not set!")
        print("   You can set it with:")
        print("   export OPENROUTER_API_KEY='your-api-key-here'\n")
        
        # Try to read from config
        try:
            import yaml
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
                api_key = config.get('openrouter', {}).get('api_key', '')
                if api_key and api_key != "":
                    os.environ['OPENROUTER_API_KEY'] = api_key
                    print("✅ Using API key from config.yaml")
        except Exception:
            pass
    else:
        print("✅ API key found in environment")
    
    print("\n📚 Enhanced components available:")
    print("   - agent_enhanced.py: Agent with logging, retries, and metrics")
    print("   - utils.py: Utility functions for logging, validation, etc.")
    print("   - search_tool_enhanced.py: Search with caching and security")
    print("   - config_enhanced.yaml: Enhanced configuration with documentation")
    print("   - test_framework.py: Comprehensive test suite")


def demo_enhanced_agent():
    """Demonstrate the enhanced agent with new features."""
    print("\n🤖 Demo: Enhanced Agent\n" + "="*50)
    
    try:
        from agent_enhanced import OpenRouterAgent
        
        # Create agent with enhanced features
        agent = OpenRouterAgent(
            config_path="config_enhanced.yaml" if Path("config_enhanced.yaml").exists() else "config.yaml",
            silent=False,
            name="DemoAgent"
        )
        
        print(f"✅ Enhanced agent initialized with model: {agent.model}")
        
        # Example query with metrics
        query = "What is the capital of France? (This is a test query)"
        print(f"\n📝 Query: {query}")
        
        response = agent.run(query)
        print(f"\n💬 Response: {response[:200]}...")
        
        # Show metrics
        metrics = agent.get_metrics()
        print(f"\n📊 Metrics:")
        print(f"   - API calls: {metrics['api_calls']}")
        print(f"   - Total tokens: {metrics['total_tokens']}")
        print(f"   - Tool calls: {metrics['tool_calls']}")
        print(f"   - Errors: {metrics['errors']}")
        
    except ImportError as e:
        print(f"❌ Could not import enhanced agent: {e}")
        print("   Make sure agent_enhanced.py and utils.py are in the project directory")
    except Exception as e:
        print(f"❌ Error during demo: {e}")


def demo_enhanced_search():
    """Demonstrate the enhanced search tool with caching."""
    print("\n🔍 Demo: Enhanced Search Tool\n" + "="*50)
    
    try:
        from tools.search_tool_enhanced import EnhancedSearchTool
        import yaml
        
        # Load config
        config_file = "config_enhanced.yaml" if Path("config_enhanced.yaml").exists() else "config.yaml"
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Create enhanced search tool
        search = EnhancedSearchTool(config)
        
        print("✅ Enhanced search tool initialized")
        
        # First search (will hit API)
        query = "Python programming"
        print(f"\n🔍 First search for: '{query}'")
        results1 = search.execute(query, max_results=2, fetch_content=False)
        print(f"   Found {len(results1)} results (from API)")
        
        # Second search (should use cache)
        print(f"\n🔍 Second search for: '{query}' (should use cache)")
        results2 = search.execute(query, max_results=2, fetch_content=False)
        print(f"   Found {len(results2)} results (from cache)")
        
        # Show a result
        if results1 and not results1[0].get('error'):
            print(f"\n📄 Sample result:")
            print(f"   Title: {results1[0].get('title', 'N/A')}")
            print(f"   URL: {results1[0].get('url', 'N/A')}")
            print(f"   Snippet: {results1[0].get('snippet', 'N/A')[:100]}...")
        
        # Clear cache demo
        search.clear_cache()
        print("\n🗑️  Cache cleared")
        
    except ImportError as e:
        print(f"❌ Could not import enhanced search tool: {e}")
        print("   Make sure search_tool_enhanced.py is in the tools/ directory")
    except Exception as e:
        print(f"❌ Error during demo: {e}")


def run_tests():
    """Run the test suite."""
    print("\n🧪 Running Test Suite\n" + "="*50)
    
    try:
        import test_framework
        print("Starting tests...\n")
        success = test_framework.run_tests()
        
        if success:
            print("\n✅ All tests passed!")
        else:
            print("\n⚠️  Some tests failed. Check output above for details.")
            
    except ImportError:
        print("❌ Could not import test_framework.py")
        print("   Make sure test_framework.py is in the project directory")
    except Exception as e:
        print(f"❌ Error running tests: {e}")


def show_migration_guide():
    """Show migration guide for using enhanced components."""
    print("\n📋 Migration Guide\n" + "="*50)
    
    guide = """
To migrate to enhanced components:

1. **Update Imports**:
   ```python
   # Old
   from agent import OpenRouterAgent
   
   # New
   from agent_enhanced import OpenRouterAgent
   ```

2. **Use Environment Variables**:
   ```bash
   export OPENROUTER_API_KEY="your-key"
   export OPENROUTER_MODEL="anthropic/claude-3-opus-20240229"
   ```

3. **Access New Features**:
   ```python
   # Get metrics
   agent = OpenRouterAgent("config.yaml")
   response = agent.run("query")
   metrics = agent.get_metrics()
   
   # Use enhanced search with caching
   from tools.search_tool_enhanced import EnhancedSearchTool
   search = EnhancedSearchTool(config)
   results = search.execute("query", fetch_content=True)
   ```

4. **Run Tests**:
   ```bash
   python test_framework.py
   ```

5. **Use Enhanced Config**:
   - Copy config_enhanced.yaml over config.yaml
   - Or reference it directly in code

The enhanced components are backward compatible, so existing code
will continue to work while you gradually adopt improvements.
"""
    print(guide)


def main():
    """Main entry point for migration helper."""
    print("\n" + "="*60)
    print("   🚀 Chat with Tools - Enhanced Components Demo")
    print("="*60)
    
    # Set up environment
    setup_environment()
    
    while True:
        print("\n📋 Options:")
        print("1. Demo enhanced agent with metrics")
        print("2. Demo enhanced search with caching")
        print("3. Run test suite")
        print("4. Show migration guide")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            demo_enhanced_agent()
        elif choice == "2":
            demo_enhanced_search()
        elif choice == "3":
            run_tests()
        elif choice == "4":
            show_migration_guide()
        elif choice == "5":
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-5.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
