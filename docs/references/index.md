---
title: Reference Documentation
tags: [references, index, navigation]
created: 2025-09-13
updated: 2025-09-13
status: active
---

# Reference Documentation

Quick reference materials and technical specifications for the Chat with Tools framework.

## Core References

### [[changelog|Changelog]]
Complete history of changes, fixes, and improvements.

### [[api|API Reference]]
Detailed API documentation for all public interfaces.

### [[dependencies|Dependencies]]
List of external packages and version requirements.

### [[glossary|Glossary]]
Terminology and definitions used throughout the project.

## Technical Specifications

### Package Information
- **Name**: chat-with-tools
- **Version**: 0.1.0
- **Python**: >=3.8
- **License**: MIT

### Entry Points
```bash
chat-with-tools    # Main interactive menu
cwt               # CLI interface
```

### Import Structure
```python
from chat_with_tools import OpenRouterAgent, TaskOrchestrator
from chat_with_tools.tools import discover_tools
from chat_with_tools.examples import run_single_agent
```

## Configuration Reference

### Config File Locations
1. `./config/config.yaml` (development)
2. `~/.chat-with-tools/config.yaml` (user)
3. `/etc/chat-with-tools/config.yaml` (system)
4. `./config.yaml` (current directory)

### Environment Variables
- `CWT_CONFIG` - Override config file path
- `CWT_DEBUG` - Enable debug output
- `OPENROUTER_API_KEY` - API key for OpenRouter

## Tool Reference

Available tools and their parameters:
- `search_web(query, max_results, fetch_content)`
- `calculate(expression)`
- `memory(operation, data)`
- `python_executor(code)`
- `read_file(path)`
- `write_file(path, content)`
- `sequential_thinking(steps)`
- `summarize(text, max_length)`
- `task_done()`

## Model Support

### OpenRouter Models
- GPT-4 variants
- Claude variants
- Llama variants
- Custom models via API

### Local Models
- vLLM endpoint support
- Custom endpoint configuration

## Quick Links

- [GitHub Repository](https://github.com/Suparious/chat-with-tools)
- [PyPI Package](https://pypi.org/project/chat-with-tools/)
- [Issue Tracker](https://github.com/Suparious/chat-with-tools/issues)

## Related Documentation

- [[../guides/index|User Guides]]
- [[../architecture/index|Architecture]]
- [[../components/index|Components]]

---

Parent: [[../README|Documentation Home]]
