#!/usr/bin/env python3
"""
Quick test script to verify all required packages are installed correctly.
"""

import sys
print("Testing package imports...")
print("-" * 50)

packages_to_test = [
    ("openai", "OpenAI API client"),
    ("requests", "HTTP library"),
    ("bs4", "BeautifulSoup HTML parser"),
    ("yaml", "YAML parser"),
    ("duckduckgo_search", "DuckDuckGo search"),
    ("colorama", "Terminal colors"),
    ("rich", "Rich text formatting"),
]

all_good = True

for package_name, description in packages_to_test:
    try:
        if package_name == "bs4":
            from bs4 import BeautifulSoup
            print(f"✅ {package_name:20} - {description}")
        elif package_name == "duckduckgo_search":
            from duckduckgo_search import DDGS
            print(f"✅ {package_name:20} - {description}")
        else:
            __import__(package_name)
            print(f"✅ {package_name:20} - {description}")
    except ImportError as e:
        print(f"❌ {package_name:20} - MISSING! ({e})")
        all_good = False

print("-" * 50)

if all_good:
    print("\n✅ All required packages are installed!")
    print("\nYou can now run: python main.py")
else:
    print("\n❌ Some packages are missing!")
    print("\nTo install missing packages, run:")
    print("  pip install -r requirements.txt")
    print("\nOr if using uv:")
    print("  uv pip install -r requirements.txt")
    sys.exit(1)
