#!/usr/bin/env python3
"""
Chat with Tools Framework - Main Entry Point

This script provides easy access to the different demos and functionality.
"""

import sys
import os

def main():
    print("\n" + "="*60)
    print("   🤖 CHAT WITH TOOLS FRAMEWORK")
    print("="*60)
    print("\nSelect what you want to run:\n")
    print("1. Simple Chat Demo (main.py)")
    print("2. Multi-Agent Council Chat (council_chat.py)")
    print("3. API-Based Tool Demo (demo_api.py)")
    print("4. Enhanced Agent Demo (demo_enhanced.py)")
    print("5. New Tools Demo (demo_new_tools.py)")
    print("6. Standalone Demo (demo_standalone.py)")
    print("7. Run Tests")
    print("8. Exit")
    
    choice = input("\nChoice (1-8): ").strip()
    
    # Add src to path for imports
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    if choice == "1":
        from demos.main import main as demo_main
        demo_main()
    elif choice == "2":
        from demos.council_chat import main as council_main
        council_main()
    elif choice == "3":
        from demos.demo_api import main as api_main
        api_main()
    elif choice == "4":
        print("\n⚠️  Enhanced demo requires config_enhanced.yaml to be set up.")
        from demos.demo_enhanced import main as enhanced_main
        enhanced_main()
    elif choice == "5":
        from demos.demo_new_tools import main as new_tools_main
        new_tools_main()
    elif choice == "6":
        from demos.demo_standalone import main as standalone_main
        standalone_main()
    elif choice == "7":
        print("\nRunning tests...")
        os.system("python tests/test_framework.py")
        print("\nPress Enter to continue...")
        input()
        os.system("python tests/test_tools.py")
    elif choice == "8":
        print("\n👋 Goodbye!")
        sys.exit(0)
    else:
        print("\n❌ Invalid choice. Please run the script again.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
