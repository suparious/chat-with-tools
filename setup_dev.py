#!/usr/bin/env python3
"""
Development setup script for Chat with Tools framework
Ensures the package is properly installed in editable mode
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle output"""
    print(f"\n{'='*60}")
    print(f"📦 {description}")
    print(f"Command: {' '.join(cmd)}")
    print('-'*60)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if result.stdout:
            print(result.stdout)
        print(f"✅ {description} - Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def main():
    """Main setup process"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║           Chat with Tools - Development Setup                  ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Get project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Check Python version
    python_version = sys.version_info
    print(f"🐍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 9):
        print("❌ Python 3.9 or higher is required")
        sys.exit(1)
    
    # Install package in editable mode
    print("\n🔧 Installing package in editable mode...")
    
    # Try with uv first (if available)
    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
        has_uv = True
        print("✅ Using uv package manager")
    except (subprocess.CalledProcessError, FileNotFoundError):
        has_uv = False
        print("ℹ️  uv not found, using pip")
    
    success = True
    
    if has_uv:
        # Install with uv
        success = run_command(
            ["uv", "pip", "install", "-e", "."],
            "Installing package with uv"
        )
        if success:
            success = run_command(
                ["uv", "pip", "install", "-r", "requirements.txt"],
                "Installing requirements with uv"
            )
    else:
        # Install with pip
        success = run_command(
            [sys.executable, "-m", "pip", "install", "-e", "."],
            "Installing package with pip"
        )
        if success:
            success = run_command(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                "Installing requirements with pip"
            )
    
    if success:
        print(f"""
{'='*60}
✨ Setup Complete!

The package has been installed in editable mode.
You can now run the framework with:

    python main.py

Or import it in Python:

    from chat_with_tools import OpenRouterAgent
    
To enable debug logging:
1. Edit config/config.yaml
2. Set debug.enabled to true
3. Logs will be saved to ./logs/

{'='*60}
        """)
    else:
        print(f"""
{'='*60}
⚠️  Setup encountered issues

Please try the following:
1. Ensure you have write permissions
2. Check that requirements.txt exists
3. Try running with administrator/sudo privileges if needed

Manual installation:
    pip install -e .
    pip install -r requirements.txt

{'='*60}
        """)
        sys.exit(1)

if __name__ == "__main__":
    main()
