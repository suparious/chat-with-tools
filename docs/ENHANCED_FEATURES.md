# Enhanced Features Documentation

## Overview

The Chat with Tools framework now includes several optional enhanced features that are **disabled by default** to maintain backwards compatibility. These features can be enabled through configuration when needed.

## Key Enhancements

### 1. Multiple Inference Endpoints

Configure different models for different tasks:

```yaml
# In config.yaml
inference_endpoints:
  fast:
    base_url: "http://localhost:8000/v1"
    model: "llama-3.3-8b"
    model_type: "fast"
    temperature: 0.5
    max_tokens: 1000
    
  thinking:
    base_url: "https://openrouter.ai/api/v1"
    model: "qwen/qwq-32b-preview"
    model_type: "thinking"
    temperature: 0.7
    max_tokens: 8000
```

**Usage:**
```python
# Use a specific endpoint
agent = OpenRouterAgent(endpoint_name="fast")

# Or use the thinking endpoint for complex queries
response = agent.run_thinking("Complex philosophical question...")
```

### 2. vLLM Structured Output Support

Enable structured outputs for vLLM endpoints:

```yaml
# In config.yaml
vllm_structured_output:
  enabled: true
  backend: "outlines"
  validate_with_pydantic: true
```

This feature requires:
- A vLLM server with guided decoding enabled
- The endpoint must have `supports_structured_output: true`

### 3. Improved Tool Handling

Several fixes and improvements:
- **Fixed:** Empty responses when using tools
- **Fixed:** Python executor import issues
- **Fixed:** Double-encoded JSON arguments
- **Improved:** Smarter tool usage decisions

### 4. Backwards Compatibility

All new features are **optional** and **disabled by default**:

- If `inference_endpoints` is not configured → Single endpoint mode (original behavior)
- If `vllm_structured_output` is not configured → Standard output mode
- If using minimal config → Everything works as before

## Configuration Files

### config.example.yaml
Minimal configuration for quick start. Contains only essential settings.

### config.full.yaml
Complete reference showing ALL available options with detailed explanations.

### config.yaml
Your actual configuration (not tracked in git). Start with `config.example.yaml` and add features as needed.

## Migration Guide

### From Original Framework

No changes required! Your existing configuration will continue to work.

### To Enable New Features

1. **Multiple Endpoints:**
   ```yaml
   inference_endpoints:
     fast: { ... }
     thinking: { ... }
   ```

2. **Structured Output:**
   ```yaml
   vllm_structured_output:
     enabled: true
   ```

3. **Per-Tool Endpoints:**
   ```yaml
   tool_endpoint_overrides:
     python_executor: "fast"
     sequential_thinking: "thinking"
   ```

## Example Use Cases

### 1. Local vLLM with Fallback

```yaml
openrouter:
  base_url: "http://localhost:8000/v1"
  model: "local-model"
  api_key_required: false

inference_endpoints:
  fallback:
    base_url: "https://openrouter.ai/api/v1"
    api_key: "${OPENROUTER_API_KEY}"
    model: "openai/gpt-4o-mini"
```

### 2. Different Models for Different Agents

```yaml
orchestrator:
  agent_endpoints:
    research: "balanced"
    analysis: "thinking"
    verification: "fast"
```

### 3. Query-Based Routing

```yaml
agent:
  auto_select_endpoint: true
  query_routing:
    thinking_keywords: ["explain", "analyze", "complex"]
    fast_keywords: ["quick", "simple", "yes or no"]
```

## Testing

Run the integration tests to verify everything works:

```bash
uv run python tests/test_enhanced_integration.py
```

## Troubleshooting

### Multi-endpoint not working
- Check that `inference_endpoints` is properly configured
- Verify endpoint names match exactly when using `endpoint_name` parameter

### Structured output errors
- Ensure vLLM server has `--guided-decoding-backend outlines`
- Check that `supports_structured_output: true` for the endpoint
- Verify pydantic is installed: `uv pip install pydantic`

### Tool errors after update
- The Python executor now properly supports imports
- Memory tool properly returns IDs
- All tool arguments are properly parsed (handles double-encoded JSON)

## Performance Tips

1. **Use connection pooling** (enabled by default):
   ```yaml
   performance:
     connection_pooling: true
   ```

2. **Configure appropriate timeouts**:
   ```yaml
   agent:
     max_iterations: 7  # Reduced from 10
   ```

3. **Use fast models for simple tasks**:
   ```python
   agent_fast = OpenRouterAgent(endpoint_name="fast")
   ```

## Summary

The enhanced framework provides powerful new capabilities while maintaining complete backwards compatibility. Enable only the features you need, when you need them. Your existing code and configurations will continue to work without any changes.
