---
title: ADR-001 - Plugin-Based Tool Architecture
tags: [adr, architecture, tools, plugin]
created: 2024-12-30
updated: 2024-12-30
status: accepted
---

# ADR-001: Plugin-Based Tool Architecture

## Status
Accepted

## Date
2024-12-01

## Context

The Chat with Tools framework needed a flexible system for adding and managing tools that agents can use. Traditional approaches would require modifying core code for each new tool, making the system difficult to extend and maintain. We needed a solution that would:

- Allow easy addition of new tools without modifying core code
- Enable hot-swapping of tools at runtime
- Provide consistent interface for all tools
- Support OpenAI function-calling format
- Allow tools to be discovered automatically

## Decision

We implemented a plugin-based architecture where tools:
1. Inherit from an abstract `BaseTool` class
2. Are placed in the `src/tools/` directory
3. Are automatically discovered at runtime using Python's importlib
4. Must implement standard properties: `name`, `description`, `parameters`, and `execute()`

## Rationale

### Considered Alternatives

1. **Hardcoded Tool Registry**: Manually register each tool in a central location
   - Pros: Explicit control, simple to understand
   - Cons: Requires code changes for each tool, not scalable

2. **Configuration-Based Tools**: Define tools in YAML/JSON configuration
   - Pros: No code changes needed
   - Cons: Limited flexibility, complex tool logic difficult to express

3. **Decorator-Based Registration**: Use decorators to register tools
   - Pros: Clean syntax, explicit registration
   - Cons: Still requires importing tools somewhere

### Why Plugin Architecture

- **Zero-Touch Integration**: Drop a tool file in the directory and it's available
- **Clean Separation**: Tools are completely isolated from core logic
- **Standard Interface**: `BaseTool` enforces consistent implementation
- **Framework Agnostic**: Tools don't need to know about the agent framework
- **Testing Friendly**: Tools can be tested in isolation

## Consequences

### Positive
- Adding new tools requires no changes to core code
- Tools can be developed and tested independently
- Framework automatically discovers all available tools
- Easy to disable tools (just remove/rename file)
- Supports community-contributed tools

### Negative
- Slightly more complex initial setup with abstract base class
- Potential for runtime errors if tools don't implement interface correctly
- Need to handle tool discovery failures gracefully

### Neutral
- All tools must follow the same interface pattern
- Tool files must be in specific directory structure
- Import errors in tools can affect startup time

## Implementation Notes

The auto-discovery mechanism in `src/tools/__init__.py`:
```python
# Scan directory for *_tool.py files
# Import each module
# Find classes inheriting from BaseTool
# Add to AVAILABLE_TOOLS dictionary
```

## References

- Implementation: [[components/tools/overview]]
- Base Tool Class: [[components/tools/base-tool]]
- Source: [[archive/agent-summaries-2024-12/technical-handover-document]]
- Related: [[architecture/adrs/ADR-002-multi-agent-orchestration]]