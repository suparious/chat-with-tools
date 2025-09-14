---
title: Components Documentation
tags: [components, index, navigation]
created: 2025-09-13
updated: 2025-09-13
status: active
---

# Components Documentation

Technical documentation for the core components of the Chat with Tools framework.

## Core Components

### [[agent|Agent System]]
The `OpenRouterAgent` class provides the main interface for single-agent interactions.

### [[orchestrator|Task Orchestrator]]
The `TaskOrchestrator` manages multi-agent collaboration and task delegation.

### [[config-manager|Configuration Manager]]
Handles configuration loading, validation, and management.

### [[tools/index|Tools System]]
Modular tool system with dynamic discovery and loading.

## Component Architecture

```
chat_with_tools/
├── agent.py              # Single agent
├── orchestrator.py       # Multi-agent
├── config_manager.py     # Configuration
├── utils.py             # Utilities
└── tools/               # Tool modules
    ├── base_tool.py     # Base class
    └── ...              # Tool implementations
```

## Key Features

### Agent System
- OpenRouter API integration
- Local vLLM support
- Tool execution
- Response streaming

### Orchestrator
- Multi-agent coordination
- Task delegation
- Council mode
- Parallel execution

### Tools
- Dynamic discovery
- Modular design
- Configurable parameters
- Security features

## Integration Points

- **Configuration**: All components use `ConfigManager`
- **Tools**: Agents and orchestrator use tool discovery
- **Utils**: Shared utilities across components

## Related Documentation

- [[../architecture/index|Architecture]]
- [[../guides/development/index|Development Guides]]
- [[../references/api|API Reference]]

---

Parent: [[../README|Documentation Home]]
