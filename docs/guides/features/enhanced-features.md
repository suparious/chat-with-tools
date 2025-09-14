---
title: Enhanced Features Guide
tags: [features, guide, configuration, vllm, endpoints]
created: 2025-09-14
updated: 2025-09-14
status: active
audience: developer
---

# Enhanced Features Guide

## Overview

The Chat with Tools framework includes several optional enhanced features that are **disabled by default** to maintain backwards compatibility. These features can be enabled through configuration when needed.

## Key Enhancements

### [[#multiple-inference-endpoints|1. Multiple Inference Endpoints]]

Configure different models for different tasks to optimize performance and cost:

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

**Usage Examples:**
```python
# Use a specific endpoint
agent = OpenRouterAgent(endpoint_name="fast")

# Use the thinking endpoint for complex queries
response = agent.run_thinking("Complex philosophical question...")
```

### [[#vllm-structured-output|2. vLLM Structured Output Support]]

Enable structured outputs for vLLM endpoints to improve tool calling accuracy:

```yaml
# In config.yaml
vllm_structured_output:
  enabled: true
  backend: "outlines"
  validate_with_pydantic: true
```

**Requirements:**
- A vLLM server with guided decoding enabled
- The endpoint must have `supports_structured_output: true`

> [!TIP]
> See [[../components/vllm/index|vLLM Component Documentation]] for detailed configuration

### [[#improved-tool-handling|3. Improved Tool Handling]]

Several fixes and improvements to tool functionality:

**Fixed Issues:**
- ✅ Empty responses when using tools
- ✅ Python executor import issues
- ✅ Double-encoded JSON arguments
- ✅ Smarter tool usage decisions

**New Features:**
- Tool-specific endpoint routing
- Parallel tool execution
- Enhanced error handling
- Argument validation with Pydantic

### [[#backwards-compatibility|4. Complete Backwards Compatibility]]

All new features are **optional** and **disabled by default**:

| Configuration | Not Set | Result |
|--------------|---------|--------|
| `inference_endpoints` | Not configured | Single endpoint mode (original) |
| `vllm_structured_output` | Not configured | Standard output mode |
| Minimal config | Used | Everything works as before |

## Configuration Examples

### Minimal Configuration
Start with `config.example.yaml` for quick setup with default behavior.

### Full Configuration
Use `config.full.yaml` as reference for all available options with detailed explanations.

### Production Configuration
Your actual `config.yaml` (not tracked in git). Start minimal and add features as needed.

## Migration Guide

### From Original Framework

> [!NOTE]
> No changes required! Your existing configuration will continue to work.

### Enabling New Features

#### Multiple Endpoints
```yaml
inference_endpoints:
  fast: 
    base_url: "http://localhost:8000/v1"
    model: "fast-model"
  thinking: 
    base_url: "http://localhost:8001/v1"
    model: "thinking-model"
```

#### Structured Output
```yaml
vllm_structured_output:
  enabled: true
  backend: "outlines"
```

#### Per-Tool Endpoints
```yaml
tool_endpoint_overrides:
  python_executor: "fast"
  sequential_thinking: "thinking"
```

## Use Case Examples

### Local vLLM with Cloud Fallback

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

### Different Models for Different Agents

```yaml
orchestrator:
  agent_endpoints:
    research: "balanced"
    analysis: "thinking"
    verification: "fast"
```

### Query-Based Automatic Routing

```yaml
agent:
  auto_select_endpoint: true
  query_routing:
    thinking_keywords: ["explain", "analyze", "complex"]
    fast_keywords: ["quick", "simple", "yes or no"]
```

## Testing Your Configuration

Run integration tests to verify everything works:

```bash
# Test enhanced features
uv run python tests/test_enhanced_integration.py

# Test specific endpoint
uv run python demos/main.py --endpoint thinking --query "Your query"

# Test structured output
uv run python demos/vllm_demo.py
```

## Troubleshooting

### Multi-endpoint Issues
- **Problem**: Endpoints not being recognized
- **Solution**: Check exact name matching in `inference_endpoints`
- **Verify**: Endpoint names with `--list-endpoints` flag

### Structured Output Errors
- **Problem**: vLLM server errors with structured output
- **Solution**: Ensure server has `--guided-decoding-backend outlines`
- **Check**: `supports_structured_output: true` for endpoint
- **Verify**: Pydantic installed: `uv pip install pydantic`

### Tool Execution Problems
- **Problem**: Tools failing after update
- **Solution**: Python executor now properly supports imports
- **Fix**: Memory tool properly returns IDs
- **Note**: All tool arguments properly handle JSON encoding

## Performance Optimization

### Connection Pooling
```yaml
performance:
  connection_pooling: true
  pool_size: 10
```

### Timeout Configuration
```yaml
agent:
  max_iterations: 7  # Reduced from 10 for faster responses
  timeout: 30
```

### Model Selection Strategy
```python
# Fast models for simple tasks
agent_fast = OpenRouterAgent(endpoint_name="fast")
response = agent_fast.run("Quick calculation: 2+2")

# Thinking models for complex tasks
agent_think = OpenRouterAgent(endpoint_name="thinking")
response = agent_think.run("Analyze this complex problem...")
```

## Best Practices

1. **Start Simple**: Begin with minimal configuration
2. **Enable Gradually**: Add features as needed
3. **Monitor Performance**: Track response times and accuracy
4. **Use Appropriate Models**: Match model capabilities to task complexity
5. **Test Thoroughly**: Verify each feature before production use

## Future Roadmap

### Planned Enhancements
- [ ] Dynamic endpoint selection based on load
- [ ] Cost-optimized routing
- [ ] Response streaming with structured output
- [ ] ML-based query classification
- [ ] Tool result caching

### Under Development
- Advanced grammar constraints
- Multi-modal support
- Plugin system for custom tools
- Web UI for configuration

## Related Documentation

- [[../components/vllm/index|vLLM Integration Details]]
- [[../../references/tools/index|Tool Reference]]
- [[../../architecture/adrs/index|Architecture Decisions]]
- [[../troubleshooting/index|Troubleshooting Guide]]

## Summary

The enhanced framework provides powerful new capabilities while maintaining complete backwards compatibility. Enable only the features you need, when you need them. Your existing code and configurations will continue to work without any changes.

---

*Source: [[../../archive/2025-09-14/enhanced-features-original|Original Enhancement Notes]]*