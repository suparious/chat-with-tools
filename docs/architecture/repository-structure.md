---
title: Repository and Package Structure
tags: [architecture, structure, package, development]
created: 2025-09-13
updated: 2025-09-13
status: active
source: archive/2025-09-13/repository-structure-original.md
---

# Repository and Package Structure

## Overview

The Chat with Tools framework has a dual structure design:

1. **Development Structure** - Files in the repository for development and testing
2. **Package Structure** - What gets distributed via PyPI to end users

This architecture ensures a clean separation between development tools and distributed code while maintaining a single source of truth for all functionality.

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

## Package Distribution

### What Gets Installed via PyPI

When users run `pip install chat-with-tools`, they receive:
- ✅ `src/chat_with_tools/` and all subdirectories
- ✅ Entry point scripts defined in `pyproject.toml`
- ✅ Package metadata and dependencies

They do NOT receive:
- ❌ `main.py` (development launcher)
- ❌ `cwt` (development CLI)
- ❌ `demos/` folder
- ❌ `tests/` folder
- ❌ `config/` folder (users create their own)
- ❌ Documentation files

## Usage Patterns

### Development Mode (Working from Repository)

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

### Installed Package Mode (From PyPI)

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

## Architecture Benefits

### Single Source of Truth

All code logic resides in `src/chat_with_tools/`:
- **No duplication** - Development files import from the package
- **Instant testing** - Changes are immediately available
- **Clean separation** - Development tools stay out of distribution

### Development Features

Repository files provide development-specific functionality:
- Debug output and profiling
- Complex test scenarios
- Multiple entry points for different testing needs
- Direct access to internal components

### Distribution Features

The package provides:
- Clean, self-contained functionality
- Simple examples for end users
- Stable API surface
- Professional structure

## Configuration Locations

The framework searches for `config.yaml` in this order:

1. `./config/config.yaml` (development)
2. `~/.chat-with-tools/config.yaml` (user home)
3. `/etc/chat-with-tools/config.yaml` (system-wide)
4. `./config.yaml` (current directory)

## Import Structure

### Development Imports
```python
# demos/main.py adds src to path
sys.path.insert(0, os.path.join(project_root, 'src'))
from chat_with_tools.agent import OpenRouterAgent
```

### Package Imports
```python
# Users import directly
from chat_with_tools import OpenRouterAgent
from chat_with_tools.tools import discover_tools
```

## Key Differences

| Feature | Repository | Installed Package |
|---------|------------|-------------------|
| Entry Point | `main.py` | `chat_with_tools.__main__` |
| CLI Script | `./cwt` | `cwt` (installed in PATH) |
| Examples | `demos/` folder | `chat_with_tools.examples` module |
| Config | `config/config.yaml` | User creates in `~/.chat-with-tools/` |
| Tools | Same location | Same location |

## Best Practices

### For Development
- Keep development-specific files in repository root
- Use `demos/` for complex testing scenarios
- Run `pip install -e .` to test package structure
- Add debug features without affecting users

### For Distribution
- Everything must be self-contained in `src/chat_with_tools/`
- Examples should be simple and use only package imports
- Don't reference repository-specific paths
- Maintain clean API surface

### For Users
- Install via pip for production use
- Create config in home directory for persistence
- Use package imports in their own code
- Follow documented patterns

## Summary

This dual structure provides:
- **Development flexibility** - Rich testing and debugging capabilities
- **Clean distribution** - Professional package for end users
- **No code duplication** - Single source of truth
- **Easy maintenance** - Clear separation of concerns

---

Related: [[development-flow|Development Flow]], [[guides/getting-started/installation|Installation Guide]]
Source: [[archive/2025-09-13/repository-structure-original]]
