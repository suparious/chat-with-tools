# vLLM Structured Output Integration

This document explains the new vLLM structured output features and multi-endpoint support added to the Chat with Tools framework.

## Features

### 1. Structured Output with vLLM

The framework now supports vLLM's guided decoding features for more accurate tool calling:

- **Pydantic Model Validation**: Tool arguments are validated using Pydantic models
- **Guided JSON Generation**: vLLM constrains output to valid JSON matching schemas
- **Backend Support**: Works with both Outlines and JSONSchema backends
- **Automatic Retry**: Failed validations trigger automatic retries with schema enforcement

#### Configuration

Enable structured output in `config.yaml`:

```yaml
vllm_structured_output:
  enabled: true
  backend: "outlines"  # or "jsonschema"
  validate_with_pydantic: true
  retry_on_failure: true
  max_retries: 3
  enforcement_level: "strict"  # or "relaxed"
```

### 2. Multi-Endpoint Support

Define multiple inference endpoints for different use cases:

```yaml
inference_endpoints:
  # Fast response models for quick tasks
  fast:
    base_url: "http://localhost:8000/v1"
    model: "gpt-4o-mini"
    model_type: "fast"
    temperature: 0.6
    max_tokens: 2000
    supports_structured_output: true
    is_vllm: true
  
  # Deep reasoning models for complex analysis
  thinking:
    base_url: "http://localhost:8001/v1"
    model: "Qwen/QwQ-32B-preview"
    model_type: "thinking"
    temperature: 0.7
    max_tokens: 30000
    supports_structured_output: true
    is_vllm: true
  
  # Balanced performance models
  balanced:
    base_url: "http://localhost:8002/v1"
    model: "NousResearch/Hermes-3-Llama-3.1-70B"
    model_type: "balanced"
    temperature: 0.7
    max_tokens: 8000
    supports_structured_output: true
    is_vllm: true
```

### 3. Automatic Query Routing

The agent can automatically select the best endpoint based on query complexity:

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
      - "summarize"
      - "yes or no"
    
    default_type: "balanced"
```

### 4. Tool-Specific Endpoint Overrides

Route specific tools to optimized endpoints:

```yaml
tool_endpoint_overrides:
  sequential_thinking: "thinking"  # Use thinking model for deep reasoning
  python_executor: "fast"          # Use fast model for code execution
  search_web: "balanced"           # Use balanced model for web search
  memory: "fast"                   # Use fast model for memory operations
```

## Usage Examples

### Basic Usage with vLLM

```python
from chat_with_tools.agent import OpenRouterAgent

# Initialize with vLLM backend
agent = OpenRouterAgent(
    use_structured_output=True  # Enable structured output
)

# The agent will automatically use structured output for tool calls
response = agent.run("Calculate 15% of 250 and search for information about tipping etiquette")
```

### Using Specific Endpoints

```python
# Use thinking endpoint for complex queries
agent = OpenRouterAgent(endpoint_name="thinking")
response = agent.run("Explain the philosophical implications of artificial consciousness")

# Use fast endpoint for simple queries
agent = OpenRouterAgent(endpoint_name="fast")
response = agent.run("What is 2+2?")
```

### Advanced vLLM Backend Usage

```python
from chat_with_tools.backends.vllm_backend import VLLMBackend, VLLMConfig
from chat_with_tools.structured_output import StructuredToolResponse

# Configure vLLM backend
config = VLLMConfig(
    base_url="http://localhost:8000/v1",
    model="NousResearch/Hermes-3",
    use_structured_output=True,
    guided_backend="outlines",
    enforce_schema=True
)

# Initialize backend
backend = VLLMBackend(config)

# Make structured request
response = backend.complete(
    messages=[
        {"role": "user", "content": "Calculate the area of a circle with radius 5"}
    ],
    tools=tools,
    response_format=StructuredToolResponse  # Pydantic model for validation
)
```

## Tool Argument Validation

All tools now have Pydantic models for argument validation:

```python
from chat_with_tools.structured_output import (
    SearchToolArgs,
    CalculatorToolArgs,
    PythonExecutorArgs,
    ToolRegistry
)

# Validate tool arguments
try:
    validated_args = ToolRegistry.validate_arguments(
        "search_web",
        {"query": "latest AI news", "max_results": 10}
    )
    # Arguments are valid and normalized
except ValueError as e:
    print(f"Invalid arguments: {e}")
```

## Performance Optimizations

### 1. Connection Pooling

Enable connection pooling for better performance:

```yaml
performance:
  connection_pooling: true
  pool_size: 10
```

### 2. Parallel Tool Execution

Tools can be executed in parallel when using vLLM:

```yaml
vllm_structured_output:
  parallel_tool_calls: true
  max_tool_iterations: 10
```

### 3. Schema Caching

Schemas are cached to reduce overhead:

```yaml
vllm_structured_output:
  schema_cache_size: 100
```

## Running the Examples

### 1. Basic Demo

```bash
# Run interactive mode
uv run python demos/main.py

# Run non-interactive demo
uv run python demos/main.py --demo --query "Your query here"

# Use specific endpoint
uv run python demos/main.py --demo --endpoint thinking --query "Complex philosophical question"
```

### 2. vLLM Structured Output Demo

```bash
uv run python examples/vllm_structured_demo.py
```

This demo shows:
- Tool call optimization
- Multi-endpoint selection
- Structured output with vLLM

### 3. Council Mode with Multi-Endpoints

```bash
uv run python demos/council_chat.py
```

Each agent in the council can use a different endpoint:

```yaml
orchestrator:
  agent_endpoints:
    research: "balanced"
    analysis: "thinking"
    verification: "fast"
    synthesis: "balanced"
```

## Troubleshooting

### vLLM Server Not Responding

Check that your vLLM server is running:

```bash
# Check health endpoint
curl http://localhost:8000/health

# Check loaded models
curl http://localhost:8000/v1/models
```

### Structured Output Not Working

1. Ensure `vllm_structured_output.enabled = true` in config
2. Verify your vLLM server supports guided decoding
3. Check that Pydantic is installed: `pip install pydantic`

### Endpoint Selection Issues

Enable debug logging to see endpoint selection:

```yaml
logging:
  level: "DEBUG"
  debug:
    enabled: true
    log_orchestrator: true
```

## Best Practices

1. **Use Structured Output for Critical Tools**: Enable for tools that require precise argument formatting
2. **Configure Endpoints by Task**: Use fast models for simple tasks, thinking models for complex reasoning
3. **Monitor Token Usage**: Different endpoints may have different token limits
4. **Cache Schemas**: Enable schema caching for frequently used tools
5. **Validate Early**: Use Pydantic validation before sending to vLLM

## Future Enhancements

- [ ] Support for more vLLM backends (vLLM-native, TGI)
- [ ] Dynamic schema generation from tool descriptions
- [ ] Automatic endpoint performance profiling
- [ ] Grammar-based constraints for tool selection
- [ ] Response streaming with structured output
- [ ] Multi-modal support with structured output
