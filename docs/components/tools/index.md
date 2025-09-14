---
title: Tools Documentation
tags: [tools, components, index]
created: 2025-09-13
updated: 2025-09-13
status: active
---

# Tools Documentation

Documentation for the modular tool system in the Chat with Tools framework.

## Available Tools

### Core Tools

#### 🔍 [[search-tool|Search Tool]]
Web search with caching, security features, and content fetching.
- [[search-tool-consolidation|Recent Consolidation]]

#### 🧮 Calculator Tool
Mathematical calculations and expressions.

#### 🧠 Memory Tool
Knowledge graph for storing and retrieving information.

#### 🐍 Python Executor Tool
Safe Python code execution in sandboxed environment.

#### 📄 File Tools
- **Read File Tool** - Read file contents
- **Write File Tool** - Write content to files

#### 🤔 Sequential Thinking Tool
Step-by-step reasoning and problem-solving.

#### 📝 Summarization Tool
Text summarization and extraction.

#### ✅ Task Done Tool
Mark tasks as completed in multi-agent scenarios.

## Tool Architecture

### Base Tool Class
All tools inherit from `BaseTool`:
```python
class BaseTool:
    def __init__(self, config: dict = None)
    def execute(self, **kwargs)
    def validate_args(self, **kwargs)
```

### Tool Discovery
Dynamic tool loading system:
```python
from chat_with_tools.tools import discover_tools
tools = discover_tools()
```

### Tool Configuration
Tools can be configured via `config.yaml`:
```yaml
tools:
  search:
    cache_ttl: 3600
    max_results: 10
  python_executor:
    timeout: 30
    max_memory: 100MB
```

## Recent Updates

- [[search-tool-consolidation|Search Tool Consolidation]] - Enhanced features merged
- [[../guides/troubleshooting/tool-loading-fix|Tool Loading Fix]] - Dynamic import resolution
- Python Executor Fix - Built-in functions now available

## Creating Custom Tools

1. Inherit from `BaseTool`
2. Implement `execute()` method
3. Add validation logic
4. Place in `tools/` directory

Example:
```python
from chat_with_tools.tools.base_tool import BaseTool

class MyCustomTool(BaseTool):
    def __init__(self, config=None):
        super().__init__(config)
        self.name = "my_custom_tool"
        
    def execute(self, **kwargs):
        # Tool logic here
        return result
```

## Security Considerations

- URL validation for web tools
- Sandboxed execution for code tools
- Input sanitization
- Resource limits

## Related Documentation

- [[../architecture/index|Architecture]]
- [[../guides/development/index|Development Guides]]
- [[../guides/troubleshooting/index|Troubleshooting]]

---

Parent: [[../index|Components]] | [[../../README|Documentation Home]]
