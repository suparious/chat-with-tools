#!/usr/bin/env python3
"""
Chat with Tools Framework - Package Entry Point

This module provides the main entry point when the package is run directly
or installed via pip.
"""

import sys
from pathlib import Path

def main():
    """
    Main entry point for the chat-with-tools package.
    
    This function imports and runs the main launcher from the root main.py
    when the package is invoked via `python -m chat_with_tools` or via
    the installed scripts `chat-with-tools` or `cwt`.
    """
    # Add the project root to the path
    project_root = Path(__file__).parent.parent.parent
    if project_root.exists() and str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Try to import from the main.py in project root first (development mode)
    try:
        # Check if we're in development mode (main.py exists in project root)
        main_py = project_root / "main.py"
        if main_py.exists():
            # Development mode - use the main.py file
            import importlib.util
            spec = importlib.util.spec_from_file_location("main_launcher", main_py)
            main_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(main_module)
            main_module.main()
        else:
            # Installed mode - use the framework launcher directly
            from .launcher import FrameworkLauncher
            launcher = FrameworkLauncher()
            launcher.run()
    except ImportError as e:
        # Fallback to a minimal launcher
        print("Chat with Tools Framework v0.1.0")
        print("\nError: Could not import launcher:", str(e))
        print("\nPlease ensure the package is properly installed:")
        print("  pip install -e .")
        print("\nOr run directly from the project directory:")
        print("  python main.py")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        print("👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please report this issue on GitHub.")
        sys.exit(1)


if __name__ == "__main__":
    main()
