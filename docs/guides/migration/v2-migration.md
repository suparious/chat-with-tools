---
title: Migration Guide - v2.0
tags: [migration, upgrade, guide, version]
created: 2025-09-14
updated: 2025-09-14
status: active
audience: developer
---

# Migration Guide - Version 2.0

## Overview

Version 2.0 of the Chat with Tools framework introduces powerful new features while maintaining **complete backwards compatibility**. This guide helps you migrate from v1.x to v2.0.

## Key Points

> [!NOTE]
> **No Breaking Changes** - Your existing code continues to work without any modifications.

All new features are:
- **Optional** - Only enabled when configured
- **Disabled by default** - Won't affect existing behavior
- **Fully backwards compatible** - Old configurations remain valid

## What's New in v2.0

### Major Features

1. **[[../features/enhanced-features|Enhanced Features]]**
   - Multiple inference endpoints
   - vLLM structured output support
   - Query routing intelligence
   - Tool-specific endpoint configuration

2. **[[../../components/vllm/index|vLLM Integration]]**
   - Guided decoding for accurate tool calling
   - Schema validation with Pydantic
   - Performance improvements

3. **[[../../references/tools/index|New Tools]]**
   - `data_analysis` - Statistical analysis and visualization
   - `api_request` - HTTP requests with authentication
   - `database` - SQLite operations

## Migration Paths

### Path 1: No Changes (Default)

If you're happy with current functionality, **no action required**:

```python
# This continues to work exactly as before
agent = OpenRouterAgent()
response = agent.run("Your query")
```

Your existing `config.yaml` remains valid and functional.

### Path 2: Gradual Enhancement

Enable features incrementally as needed:

#### Step 1: Review Available Features
Check `config.full.yaml` for all available options with detailed explanations.

#### Step 2: Enable Desired Features
Add only the features you need to your `config.yaml`:

```yaml
# Example: Enable multiple endpoints
inference_endpoints:
  fast:
    base_url: "http://localhost:8000/v1"
    model: "llama-3.3-8b"
    model_type: "fast"
```

#### Step 3: Test Changes
```bash
uv run python tests/test_enhanced_integration.py
```

### Path 3: Full Feature Adoption

For maximum capabilities:

1. **Copy Full Configuration**
   ```bash
   cp config.full.yaml config.yaml
   ```

2. **Customize Settings**
   - Update API keys and endpoints
   - Configure model preferences
   - Set routing rules

3. **Enable All Features**
   ```yaml
   vllm_structured_output:
     enabled: true
   
   agent:
     auto_select_endpoint: true
   ```

## Configuration Changes

### Configuration Files

| File | Purpose | Action |
|------|---------|--------|
| `config.example.yaml` | Minimal starter config | Use for new projects |
| `config.full.yaml` | Complete reference | Copy sections as needed |
| `config.yaml` | Your actual config | Update with desired features |

### New Configuration Sections

#### Multiple Endpoints (Optional)
```yaml
inference_endpoints:
  fast:
    base_url: "..."
    model: "..."
  thinking:
    base_url: "..."
    model: "..."
```

#### Structured Output (Optional)
```yaml
vllm_structured_output:
  enabled: true
  backend: "outlines"
```

#### Query Routing (Optional)
```yaml
agent:
  auto_select_endpoint: true
  query_routing:
    thinking_keywords: ["explain", "analyze"]
    fast_keywords: ["quick", "simple"]
```

## Code Migration Examples

### Example 1: Basic Usage (No Changes)
```python
# v1.x code - still works in v2.0
from chat_with_tools import OpenRouterAgent

agent = OpenRouterAgent()
response = agent.run("Calculate 2+2")
print(response)
```

### Example 2: Using New Features
```python
# v2.0 with enhanced features
from chat_with_tools import OpenRouterAgent

# Use specific endpoint (if configured)
agent = OpenRouterAgent(endpoint_name="fast")

# Use thinking mode for complex queries
response = agent.run_thinking("Explain quantum computing")

# Enable structured output
agent_structured = OpenRouterAgent(use_structured_output=True)
```

### Example 3: Tool Enhancements
```python
# New tools are automatically available
agent = OpenRouterAgent()

# Use new data analysis tool
response = agent.run("Analyze this CSV data and create a chart: ...")

# Use new API request tool
response = agent.run("Make a GET request to the GitHub API")

# Use new database tool
response = agent.run("Create a SQLite table for user data")
```

## Testing Your Migration

### Run Integration Tests
```bash
# Test backwards compatibility
uv run python tests/test_enhanced_integration.py

# Test specific features
uv run python demos/vllm_demo.py

# Test tools
uv run python tests/test_tools.py
```

### Verify Configuration
```python
from chat_with_tools.agent import OpenRouterAgent

# Check loaded configuration
agent = OpenRouterAgent()
print(f"Endpoints available: {agent.endpoints}")
print(f"Structured output: {agent.use_structured_output}")
```

## Common Migration Scenarios

### Scenario 1: Local Development to Production

**Development Config:**
```yaml
openrouter:
  base_url: "http://localhost:8000/v1"
  model: "local-model"
```

**Production Config:**
```yaml
openrouter:
  base_url: "https://api.openrouter.ai/v1"
  model: "openai/gpt-4"
  api_key: "${OPENROUTER_API_KEY}"
```

### Scenario 2: Single Model to Multi-Model

**Before:**
```yaml
openrouter:
  model: "one-size-fits-all"
```

**After:**
```yaml
inference_endpoints:
  fast:
    model: "gpt-4o-mini"
  thinking:
    model: "o1-preview"
  balanced:
    model: "claude-3"
```

### Scenario 3: Adding vLLM Support

**Before:**
```yaml
openrouter:
  base_url: "https://api.openrouter.ai/v1"
```

**After:**
```yaml
openrouter:
  base_url: "http://your-vllm-server:8000/v1"
  is_vllm: true

vllm_structured_output:
  enabled: true
  backend: "outlines"
```

## Rollback Procedure

If you need to rollback to v1.x:

1. **Keep your old config.yaml** - It remains compatible
2. **Disable new features**:
   ```yaml
   vllm_structured_output:
     enabled: false
   ```
3. **Remove new configuration sections** if added
4. **Revert code changes** if using new methods

## Troubleshooting

### Issue: Features Not Working
- **Check:** Configuration properly added to `config.yaml`
- **Verify:** Required dependencies installed
- **Test:** Run integration tests

### Issue: Performance Degradation
- **Disable:** Structured output if not needed
- **Adjust:** Timeout settings
- **Use:** Appropriate endpoints for tasks

### Issue: Tool Errors
- **Update:** All tools are fixed in v2.0
- **Check:** New tool documentation
- **Verify:** Tool parameters

## Getting Help

1. **Documentation**: [[../../README|Main Documentation]]
2. **Feature Guide**: [[../features/enhanced-features|Enhanced Features]]
3. **Tool Reference**: [[../../references/tools/index|Tools Documentation]]
4. **Changelog**: [[../../references/changelog/2025-09|Release Notes]]

## Summary

Version 2.0 is designed for seamless migration:

- ✅ **Zero breaking changes**
- ✅ **Optional feature adoption**
- ✅ **Gradual enhancement path**
- ✅ **Full backwards compatibility**
- ✅ **Comprehensive documentation**

Start with your existing setup and enhance as needed. The framework grows with your requirements while maintaining stability.

---

*Source: [[../../archive/2025-09-14/integration-complete-original|Integration Complete Notes]]*