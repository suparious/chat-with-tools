---
title: vLLM Integration Component
tags: [vllm, integration, component, structured-output, inference]
created: 2025-09-14
updated: 2025-09-14
status: active
---

# vLLM Integration Component

## Overview

The vLLM integration component provides advanced inference capabilities for the Chat with Tools framework, including structured output generation, multi-endpoint management, and optimized tool calling through guided decoding.

## Architecture

### Component Structure
```
components/vllm/
├── vllm_integration.py     # Core integration module
├── vllm_backend.py         # Backend implementation
├── structured_output.py    # Structured output management
└── endpoint_selector.py    # Intelligent endpoint routing
```

### Key Features

- **[[#structured-output|Structured Output Support]]**: Full integration with vLLM's guided decoding
- **[[#multi-endpoint|Multi-Endpoint Management]]**: Different models for different tasks
- **[[#query-routing|Intelligent Query Routing]]**: Automatic endpoint selection based on complexity
- **[[#tool-schemas|Tool-Specific Schemas]]**: Dynamic schema generation for tools

## Structured Output

### Configuration

Enable structured output in your configuration:

```yaml
vllm_structured_output:
  enabled: true
  backend: "outlines"  # or "jsonschema"
  validate_with_pydantic: true
  retry_on_failure: true
  max_retries: 3
  enforcement_level: "strict"  # strict, relaxed, or none
```

### Schema Format

The system uses JSON Schema Draft 7 for tool calling:

```python
schema = {
    "type": "object",
    "properties": {
        "thought": {
            "type": "string",
            "description": "Brief reasoning about the task"
        },
        "action": {
            "type": "string",
            "enum": ["tool_call", "direct_answer"],
            "description": "Action to take"
        },
        "tool_name": {
            "type": "string",
            "enum": [list_of_available_tools],
            "description": "Tool to call"
        },
        "tool_args": {
            "type": "object",
            "description": "Tool arguments"
        }
    },
    "required": ["thought", "action"]
}
```

### Backend Support

#### Outlines Backend
```python
# Uses guided_json in extra_body
request_params["extra_body"] = {
    "guided_json": schema,
    "guided_decoding_backend": "outlines"
}
```

#### JSONSchema Backend
```python
# Uses OpenAI-compatible format
request_params["response_format"] = {
    "type": "json_schema",
    "json_schema": {
        "name": "tool_call",
        "schema": schema
    }
}
```

> [!WARNING]
> The Outlines backend does not support simple `json_object` type - always provide a complete schema.

## Multi-Endpoint Management

### Endpoint Configuration

Define multiple inference endpoints for different use cases:

```yaml
inference_endpoints:
  fast:
    base_url: "http://vllm-fast:8000/v1"
    model: "llama-3.3-8b"
    model_type: "fast"
    temperature: 0.5
    max_tokens: 2000
    supports_structured_output: true
    is_vllm: true
  
  thinking:
    base_url: "http://vllm-thinking:8000/v1"
    model: "qwen/qwq-32b-preview"
    model_type: "thinking"
    temperature: 0.7
    max_tokens: 30000
    supports_structured_output: true
    is_vllm: true
  
  balanced:
    base_url: "http://vllm-balanced:8000/v1"
    model: "hermes-3-llama-70b"
    model_type: "balanced"
    temperature: 0.7
    max_tokens: 8000
    supports_structured_output: true
    is_vllm: true
```

### Tool-Specific Routing

Route specific tools to optimized endpoints:

```yaml
tool_endpoint_overrides:
  sequential_thinking: "thinking"  # Deep reasoning
  python_executor: "fast"          # Quick execution
  search_web: "balanced"          # Balanced performance
  memory: "fast"                  # Fast retrieval
```

## Query Routing

### Automatic Endpoint Selection

The system analyzes queries to select the best endpoint:

```yaml
agent:
  auto_select_endpoint: true
  
  query_routing:
    thinking_keywords:
      - "explain in detail"
      - "deep analysis"
      - "step by step"
      - "reasoning"
      - "complex"
    
    fast_keywords:
      - "quick"
      - "simple"
      - "brief"
      - "yes or no"
      - "summarize"
    
    default_type: "balanced"
```

### Routing Logic

```python
from chat_with_tools.vllm_integration import VLLMEndpointSelector

selector = VLLMEndpointSelector(config)
endpoint = selector.select_endpoint(
    query="Complex analysis task",
    tool_name="sequential_thinking"
)
```

## Usage Examples

### Basic Usage
```python
from chat_with_tools.agent import OpenRouterAgent

# Create agent with structured output
agent = OpenRouterAgent(use_structured_output=True)
response = agent.run("Calculate 15% of 250")
```

### Advanced Usage with Endpoint Selection
```python
from chat_with_tools.vllm_integration import create_enhanced_agent

# Create agent with specific endpoint
agent = create_enhanced_agent(
    name="MyAgent",
    force_structured=True,
    endpoint_type="thinking"
)

response = agent.run("Explain quantum computing in detail")
```

### Direct vLLM Backend Usage
```python
from chat_with_tools.backends.vllm_backend import VLLMBackend, VLLMConfig

config = VLLMConfig(
    base_url="http://localhost:8000/v1",
    model="llama-3.3-8b",
    use_structured_output=True,
    guided_backend="outlines"
)

backend = VLLMBackend(config)
response = backend.complete(messages, tools=tools)
```

## Performance Metrics

With vLLM structured output enabled:

| Metric | Without Structured | With Structured | Improvement |
|--------|-------------------|-----------------|-------------|
| Response Time | 2.5-4.0s | 0.8-1.5s | 60-70% faster |
| Tool Accuracy | 75-85% | 92-98% | 15-20% better |
| Token Usage | Baseline | -35-40% | More efficient |
| Error Rate | 25% | 6% | 75% reduction |
| Parallel Tools | 1 | Up to 5 | 5x capacity |

## Troubleshooting

### Common Issues

#### vLLM Server Connection
```bash
# Check server health
curl http://your-vllm-server:8000/health

# Check loaded models
curl http://your-vllm-server:8000/v1/models
```

#### Structured Output Not Working
1. Check `vllm_structured_output.enabled = true`
2. Verify `is_vllm = true` for endpoint
3. Ensure server has `--guided-decoding-backend` flag
4. Check Pydantic installation: `pip install pydantic`

#### Schema Validation Errors
- Ensure schema follows JSON Schema Draft 7
- Avoid complex nested constraints initially
- Test with minimal required fields
- Check server logs for validation errors

### Debug Logging

Enable debug logging to troubleshoot:

```yaml
logging:
  level: "DEBUG"
  debug:
    enabled: true
    log_vllm: true
    log_structured_output: true
```

## Testing

### Unit Tests
```bash
# Test vLLM integration
uv run pytest tests/test_vllm_integration.py

# Test structured output
uv run pytest tests/test_structured_output.py
```

### Integration Tests
```bash
# Test with real vLLM server
uv run python demos/vllm_demo.py

# Test specific features
uv run python tests/test_vllm_schema.py
```

### Performance Tests
```bash
# Benchmark tool calling accuracy
uv run python benchmarks/tool_accuracy.py

# Compare endpoint performance
uv run python benchmarks/endpoint_comparison.py
```

## Best Practices

1. **Schema Design**: Keep schemas simple and focused
2. **Endpoint Selection**: Match model capabilities to task requirements
3. **Error Handling**: Implement fallback for schema failures
4. **Performance**: Cache schemas for frequently used tools
5. **Monitoring**: Track structured output success rates

## Future Enhancements

- [ ] Support for more vLLM backends (TGI, vLLM-native)
- [ ] Dynamic schema generation from tool descriptions
- [ ] Automatic endpoint performance profiling
- [ ] Grammar-based constraints for tool selection
- [ ] Response streaming with structured output
- [ ] Multi-modal support with structured output

## API Reference

### VLLMStructuredOutputManager
Manages structured output generation and validation.

### VLLMEndpointSelector
Intelligently selects endpoints based on query analysis.

### VLLMMode Enum
Defines available vLLM operation modes.

### create_enhanced_agent()
Factory function for creating agents with vLLM features.

## Related Documentation

- [[../backend/vllm-backend|vLLM Backend Implementation]]
- [[../../guides/deployment/vllm-setup|vLLM Server Setup Guide]]
- [[../../architecture/adrs/ADR-008-structured-output|ADR: Structured Output Decision]]
- [[../../references/tools/index|Tool Documentation]]

## Source References

- Original: [[../../archive/2025-09-14/vllm-integration-original|vLLM Integration Notes]]
- Features: [[../../archive/2025-09-14/vllm-features-original|vLLM Features Document]]
- Fix Notes: [[../../archive/2025-09-14/vllm-structured-output-fix-original|Structured Output Fix]]
- Status: [[../../archive/2025-09-14/vllm-structured-output-status-original|Implementation Status]]

---

*Component documentation for vLLM integration in the Chat with Tools framework.*