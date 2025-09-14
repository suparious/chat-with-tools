# Chat with Tools Framework - Repository and Package Structure

## Overview
This document explains the dual structure of the Chat with Tools framework:
1. **Development Structure** - Files in the repository for development
2. **Package Structure** - What gets distributed via PyPI

## Repository Structure (Development)

```
chat-with-tools/                    # Git repository root
├── main.py                         # Development launcher (NOT distributed)
├── cwt                            # Development CLI script (NOT distributed) 
├── demos/                         # Original demo files (NOT distributed)
│   ├── main.py                   # Single agent demo
│   ├── council_chat.py           # Council mode demo  
│   ├── demo_standalone.py        # Tool showcase
│   └── demo_api.py              # API integration demo
│
├── src/                           # Source code (THIS gets distributed)
│   └── chat_with_tools/          # The actual Python package
│       ├── __init__.py           # Package exports
│       ├── __main__.py           # Package entry point
│       ├── launcher.py           # Self-contained launcher
│       ├── agent.py              # Core agent implementation
│       ├── orchestrator.py       # Multi-agent orchestrator
│       ├── config_manager.py     # Configuration management
│       ├── utils.py              # Utilities
│       ├── tools/                # Tool implementations
│       │   ├── __init__.py       # Tool discovery
│       │   ├── base_tool.py      # Base tool class
│       │   └── ...               # Individual tools
│       └── examples/             # Self-contained examples (distributed)
│           ├── __init__.py       # Example exports
│           ├── single_agent.py   # Single agent example
│           ├── council_mode.py   # Council mode example
│           ├── tool_showcase.py  # Tool testing example
│           └── api_demo.py       # API demo example
│
├── tests/                         # Test files (NOT distributed)
├── config/                        # Configuration templates (NOT distributed)
├── docs/                         # Documentation (NOT distributed)
├── backends/                      # Backend files (NOT distributed)
├── pyproject.toml                # Package configuration
└── README.md                     # Repository readme

```

## What Gets Installed via PyPI

When users run `pip install chat-with-tools`, they ONLY get:
- `src/chat_with_tools/` and all its subdirectories
- Entry point scripts defined in `pyproject.toml`

They do NOT get:
- `main.py` (development launcher)
- `cwt` (development CLI)
- `demos/` folder
- `tests/` folder
- `config/` folder (users create their own)
- Documentation files

## Usage Patterns

### 1. Development Mode (Working from Repository)
```bash
# Clone the repository
git clone https://github.com/Suparious/chat-with-tools
cd chat-with-tools

# Install in development mode
pip install -e .

# Run using repository files
python main.py              # Uses root main.py
./cwt                       # Uses root cwt script
python demos/main.py        # Run demos directly
```

### 2. Installed Package Mode (From PyPI)
```bash
# Install from PyPI
pip install chat-with-tools

# Run using installed commands
chat-with-tools             # Uses __main__.py entry point
cwt                        # Uses __main__.py entry point

# Import in Python
from chat_with_tools import OpenRouterAgent
from chat_with_tools.examples import run_single_agent
```

## Why This Structure?

### Repository Files (main.py, cwt, demos/)
- **Purpose**: Development and testing
- **Users**: Developers working on the framework
- **Benefit**: Easy to test and modify without reinstalling

### Package Files (src/chat_with_tools/)
- **Purpose**: Distributed functionality
- **Users**: End users installing via pip
- **Benefit**: Clean, self-contained package

### Examples Module (src/chat_with_tools/examples/)
- **Purpose**: Provide working examples in the installed package
- **Users**: Both developers and end users
- **Benefit**: Examples are always available, even when installed from PyPI

## Key Differences

| Feature | Repository | Installed Package |
|---------|------------|-------------------|
| Entry Point | `main.py` | `chat_with_tools.__main__` |
| CLI Script | `./cwt` | `cwt` (installed in PATH) |
| Examples | `demos/` folder | `chat_with_tools.examples` module |
| Config | `config/config.yaml` | User creates in `~/.chat-with-tools/` |
| Tools | Same location | Same location |

## Configuration Locations

The framework searches for config.yaml in this order:
1. `./config/config.yaml` (development)
2. `~/.chat-with-tools/config.yaml` (user home)
3. `/etc/chat-with-tools/config.yaml` (system-wide)
4. `./config.yaml` (current directory)

## Best Practices

### For Development
- Keep development-specific files in repository root
- Use `demos/` for complex testing scenarios
- Run `pip install -e .` to test package structure

### For Distribution
- Everything must be self-contained in `src/chat_with_tools/`
- Examples should be simple and use only package imports
- Don't reference repository-specific paths

### For Users
- Install via pip for production use
- Create config in home directory for persistence
- Use package imports in their own code

## Migration from Repository to Package

When moving from development to package:

1. **Imports change from:**
   ```python
   from demos.main import main
   ```
   **To:**
   ```python
   from chat_with_tools.examples import run_single_agent
   ```

2. **File paths change from:**
   ```python
   config_path = "./config/config.yaml"
   ```
   **To:**
   ```python
   config_path = Path.home() / ".chat-with-tools" / "config.yaml"
   ```

3. **Entry points change from:**
   ```bash
   python main.py
   ```
   **To:**
   ```bash
   chat-with-tools
   ```

## Summary

- **Repository**: Full development environment with tests, demos, and documentation
- **Package**: Clean, installable module with just the core functionality and examples
- **Both work**: The structure supports both development and distribution seamlessly
