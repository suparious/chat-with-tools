#!/usr/bin/env python3
"""
Chat with Tools Framework - Main Entry Point

A powerful multi-agent AI framework with tool integration
Inspired by Grok's deep thinking mode
"""

import sys
import os
import time
from typing import Optional, Dict, Any
from pathlib import Path

# ASCII Art Banner
BANNER = """
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║     ██████╗██╗  ██╗ █████╗ ████████╗                           ║
║    ██╔════╝██║  ██║██╔══██╗╚══██╔══╝                           ║
║    ██║     ███████║███████║   ██║                              ║
║    ██║     ██╔══██║██╔══██║   ██║                              ║
║    ╚██████╗██║  ██║██║  ██║   ██║                              ║
║     ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝                              ║
║                                                                ║
║              WITH TOOLS FRAMEWORK v0.1.0                       ║
║                                                                ║
║        🧠 Multi-Agent AI • 🛠️ Tool Integration                 ║
║        ⚡ Parallel Processing • 🎯 Deep Analysis                ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
"""

class FrameworkLauncher:
    """Main launcher for the Chat with Tools framework"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        sys.path.append(str(self.project_root))
        self.check_environment()
    
    def check_environment(self) -> bool:
        """Check if the environment is properly configured"""
        config_path = self.project_root / "config" / "config.yaml"
        
        if not config_path.exists():
            print("\n⚠️  Configuration file not found!")
            print("   Please copy config/config.example.yaml to config/config.yaml")
            print("   and configure your settings.")
            return False
        
        # Check if API key is configured (but don't block if missing)
        try:
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                api_key = config.get('openrouter', {}).get('api_key', '')
                base_url = config.get('openrouter', {}).get('base_url', '')
                
                if api_key == 'YOUR API KEY HERE' or not api_key:
                    print("\n⚠️  OpenRouter API key not configured!")
                    print("   If using OpenRouter, please add your API key to config/config.yaml")
                    print("   Get your key at: https://openrouter.ai/keys")
                    print("\n   Note: You can continue without an API key if using a local vLLM endpoint.")
                    # Don't return False - just warn and continue
                    
        except Exception as e:
            print(f"\n⚠️  Error reading configuration: {e}")
            return False
        
        return True
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_banner(self):
        """Display the application banner"""
        self.clear_screen()
        print(BANNER)
    
    def show_main_menu(self):
        """Display the main menu with organized options"""
        print("\n" + "═"*60)
        print("   📋 MAIN MENU")
        print("═"*60)
        print("\n🚀 CORE FEATURES:")
        print("   1. 💬 Single Agent Chat     - Interactive AI with tool access")
        print("   2. 🧠 Council Mode (Heavy)  - Multi-agent deep analysis")
        print()
        print("🔬 DEMONSTRATIONS:")
        print("   3. 🛠️  Tool Showcase        - Test individual tools")
        print("   4. 🎯 API Integration Demo  - Advanced tool usage examples")
        print()
        print("🧪 TESTING & DEVELOPMENT:")
        print("   5. 🔍 Run Test Suite        - Verify framework integrity")
        print("   6. 📊 Tool Benchmarks       - Performance testing")
        print()
        print("📚 INFORMATION:")
        print("   7. 📖 Documentation         - View framework docs")
        print("   8. ⚙️  Configuration        - Edit settings")
        print()
        print("   0. 🚪 Exit")
        print("\n" + "─"*60)
    
    def launch_single_agent(self):
        """Launch the single agent chat interface"""
        print("\n🚀 Launching Single Agent Chat...")
        print("   This mode provides a single AI agent with full tool access.")
        print("   Perfect for straightforward queries and tasks.\n")
        time.sleep(1)
        
        try:
            from demos.main import main as single_agent_main
            single_agent_main()
        except ImportError as e:
            print(f"❌ Error loading single agent module: {e}")
            self.handle_import_error()
        except Exception as e:
            print(f"❌ Error running single agent: {e}")
    
    def launch_council_mode(self):
        """Launch the multi-agent council mode"""
        print("\n🧠 Launching Council Mode (Heavy)...")
        print("   This mode deploys multiple specialized agents in parallel.")
        print("   Provides deep, multi-perspective analysis like Grok's heavy mode.\n")
        time.sleep(1)
        
        try:
            from demos.council_chat import main as council_main
            council_main()
        except ImportError as e:
            print(f"❌ Error loading council module: {e}")
            self.handle_import_error()
        except Exception as e:
            print(f"❌ Error running council mode: {e}")
    
    def launch_tool_showcase(self):
        """Launch the interactive tool testing interface"""
        print("\n🛠️  Launching Tool Showcase...")
        print("   Test individual tools without requiring API access.")
        print("   Perfect for understanding tool capabilities.\n")
        time.sleep(1)
        
        try:
            from demos.demo_standalone import main as standalone_main
            standalone_main()
        except ImportError as e:
            print(f"❌ Error loading tool showcase: {e}")
            self.handle_import_error()
        except Exception as e:
            print(f"❌ Error running tool showcase: {e}")
    
    def launch_api_demo(self):
        """Launch the API integration demonstration"""
        print("\n🎯 Launching API Integration Demo...")
        print("   Advanced examples of tool usage with API integration.\n")
        time.sleep(1)
        
        try:
            from demos.demo_api import main as api_main
            api_main()
        except ImportError as e:
            print(f"❌ Error loading API demo: {e}")
            self.handle_import_error()
        except Exception as e:
            print(f"❌ Error running API demo: {e}")
    
    def run_tests(self):
        """Run the test suite"""
        print("\n🔍 Running Test Suite...")
        print("   Verifying framework components and tool functionality.\n")
        time.sleep(1)
        
        test_files = [
            "tests/test_framework.py",
            "tests/test_tools.py"
        ]
        
        for test_file in test_files:
            test_path = self.project_root / test_file
            if test_path.exists():
                print(f"\n▶️  Running {test_file}...")
                os.system(f"python {test_path}")
            else:
                print(f"⚠️  Test file not found: {test_file}")
        
        print("\n✅ Test suite completed!")
        input("\nPress Enter to continue...")
    
    def run_benchmarks(self):
        """Run performance benchmarks"""
        print("\n📊 Running Tool Benchmarks...")
        print("   Measuring performance of individual tools.\n")
        
        # This would run actual benchmarks
        print("🔄 Benchmark suite coming soon...")
        print("   This will test:")
        print("   • Tool execution speed")
        print("   • Memory usage")
        print("   • Parallel processing efficiency")
        print("   • API response times")
        
        input("\nPress Enter to continue...")
    
    def show_documentation(self):
        """Display framework documentation"""
        print("\n📖 Framework Documentation")
        print("═"*60)
        
        docs = {
            "1": ("README.md", "Main documentation"),
            "2": ("docs/NEW_TOOLS.md", "New tools guide"),
            "3": ("docs/TESTING_GUIDE.md", "Testing guide"),
            "4": ("LICENSE", "License information")
        }
        
        print("\nAvailable documentation:")
        for key, (file, desc) in docs.items():
            print(f"   {key}. {desc}")
        print("   0. Back to main menu")
        
        choice = input("\nSelect document (0-4): ").strip()
        
        if choice == "0":
            return
        
        if choice in docs:
            doc_path = self.project_root / docs[choice][0]
            if doc_path.exists():
                print(f"\n{'─'*60}")
                with open(doc_path, 'r') as f:
                    content = f.read()
                    # Show first 50 lines
                    lines = content.split('\n')[:50]
                    print('\n'.join(lines))
                    if len(content.split('\n')) > 50:
                        print(f"\n... (showing first 50 lines of {len(content.split('\n'))} total)")
                print('─'*60)
            else:
                print(f"❌ Document not found: {docs[choice][0]}")
        
        input("\nPress Enter to continue...")
    
    def edit_configuration(self):
        """Open configuration editor"""
        print("\n⚙️  Configuration Editor")
        print("═"*60)
        
        config_path = self.project_root / "config" / "config.yaml"
        
        if not config_path.exists():
            print("❌ Configuration file not found!")
            input("\nPress Enter to continue...")
            return
        
        print(f"\nConfiguration file: {config_path}")
        print("\nOptions:")
        print("   1. View current configuration")
        print("   2. Open in default editor")
        print("   3. Show configuration guide")
        print("   0. Back to main menu")
        
        choice = input("\nSelect option (0-3): ").strip()
        
        if choice == "1":
            with open(config_path, 'r') as f:
                print("\n" + "─"*60)
                print(f.read())
                print("─"*60)
        elif choice == "2":
            if os.name == 'nt':
                os.system(f"notepad {config_path}")
            else:
                editor = os.environ.get('EDITOR', 'nano')
                os.system(f"{editor} {config_path}")
        elif choice == "3":
            print("\n📚 Configuration Guide:")
            print("─"*40)
            print("1. OpenRouter API Key:")
            print("   • Get your key at: https://openrouter.ai/keys")
            print("   • Replace 'YOUR API KEY HERE' with your actual key")
            print("\n2. Model Selection:")
            print("   • anthropic/claude-3.5-sonnet - Best reasoning")
            print("   • openai/gpt-4-mini - Cost efficient")
            print("   • google/gemini-2.0-flash - Fast responses")
            print("\n3. Agent Settings:")
            print("   • parallel_agents: Number of concurrent agents (default: 4)")
            print("   • max_iterations: Max tool calls per agent (default: 10)")
            print("   • task_timeout: Timeout per agent in seconds (default: 300)")
        
        input("\nPress Enter to continue...")
    
    def handle_import_error(self):
        """Handle import errors with helpful messages"""
        print("\n💡 Troubleshooting Tips:")
        print("   1. Ensure all dependencies are installed:")
        print("      uv pip install -r requirements.txt")
        print("   2. Check that you're in the project directory")
        print("   3. Verify Python version is 3.9 or higher")
        print("   4. Try running: uv pip install -e .")
    
    def run(self):
        """Main run loop"""
        self.show_banner()
        
        # Check environment on first run (now just shows warnings, doesn't block)
        if not self.check_environment():
            print("\n❌ Cannot continue due to critical configuration issues.")
            input("\nPress Enter to exit...")
            return
        
        # Add a small pause to let users read any warnings
        if self.check_environment():
            time.sleep(2)
        
        while True:
            try:
                self.show_main_menu()
                choice = input("Enter your choice (0-8): ").strip()
                
                if choice == "0":
                    print("\n👋 Thank you for using Chat with Tools!")
                    print("   Visit https://github.com/Suparious/chat-with-tools for updates.\n")
                    break
                elif choice == "1":
                    self.launch_single_agent()
                elif choice == "2":
                    self.launch_council_mode()
                elif choice == "3":
                    self.launch_tool_showcase()
                elif choice == "4":
                    self.launch_api_demo()
                elif choice == "5":
                    self.run_tests()
                elif choice == "6":
                    self.run_benchmarks()
                elif choice == "7":
                    self.show_documentation()
                elif choice == "8":
                    self.edit_configuration()
                else:
                    print("\n❌ Invalid choice. Please select 0-8.")
                    time.sleep(1)
                
                # Clear screen before showing menu again (except for exit)
                if choice != "0":
                    input("\nPress Enter to return to main menu...")
                    self.show_banner()
                    
            except KeyboardInterrupt:
                print("\n\n⚠️  Interrupted by user")
                print("👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                print("Please report this issue on GitHub.")
                input("\nPress Enter to continue...")


def main():
    """Main entry point"""
    launcher = FrameworkLauncher()
    launcher.run()


if __name__ == "__main__":
    main()
