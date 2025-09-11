# 🚀 vLLM Integration Guide for Chat with Tools

This guide shows how to use vLLM v0.11+ with the Chat with Tools framework, taking advantage of the new tool calling features.

## 📋 Table of Contents
- [vLLM v0.11 Features](#vllm-v011-features)
- [Setup Instructions](#setup-instructions)
- [Configuration](#configuration)
- [Testing Tool Calls](#testing-tool-calls)
- [Performance Tuning](#performance-tuning)
- [Troubleshooting](#troubleshooting)

## 🎯 vLLM v0.11 Features

### New Tool Calling Capabilities
- **Tool Call Parser**: Native support for Hermes and Mistral tool formats
- **Auto Tool Choice**: Automatic tool selection based on context
- **Structured Output**: Better handling of tool responses
- **Parallel Tool Calls**: Support for multiple simultaneous tool executions

### Performance Improvements
- **Chunked Prefill**: Better handling of long contexts
- **Prefix Caching**: Reuse computed prefixes for better performance
- **FP8 KV Cache**: Reduced memory usage with quantized cache

## 🔧 Setup Instructions

### 1. Start vLLM Server

Use the enhanced startup script:

```bash
# Make scripts executable
chmod +x vllm_start_enhanced.sh vllm_monitor.sh

# Copy example config (optional)
sudo mkdir -p /opt/inference/config
sudo cp vllm.conf.example /opt/inference/config/vllm.conf

# Edit configuration
sudo nano /opt/inference/config/vllm.conf

# Start the server
./vllm_start_enhanced.sh
```

### 2. Verify Server is Running

```bash
# Check health
curl http://localhost:8081/health

# Check loaded models
curl http://localhost:8081/v1/models

# Monitor server
./vllm_monitor.sh dashboard
```

### 3. Update Chat with Tools Configuration

Edit your `config.yaml` or `config_enhanced.yaml`:

```yaml
# For vLLM backend
openrouter:
  api_key: "dummy-key-for-local"  # vLLM doesn't need a real key
  base_url: "http://localhost:8081/v1"  # Point to vLLM
  model: "Orion-zhen/DeepHermes-3-Llama-3-8B-Preview-AWQ"  # Must match vLLM model

# Optimize for local inference
agent:
  max_iterations: 10
  temperature: 0.7
  rate_limit: 100  # Higher rate limit for local server
```

## 🧪 Testing Tool Calls

### Test Script for vLLM Tool Calling

Create `test_vllm_tools.py`:

```python
#!/usr/bin/env python3
"""Test vLLM tool calling with Chat with Tools framework."""

import json
import requests
from openai import OpenAI

# vLLM server configuration
VLLM_URL = "http://localhost:8081/v1"
MODEL_NAME = "Orion-zhen/DeepHermes-3-Llama-3-8B-Preview-AWQ"

def test_basic_tool_call():
    """Test basic tool calling functionality."""
    
    client = OpenAI(
        base_url=VLLM_URL,
        api_key="dummy"  # vLLM doesn't validate this
    )
    
    # Define a simple tool
    tools = [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City and state, e.g. San Francisco, CA"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit"
                    }
                },
                "required": ["location"]
            }
        }
    }]
    
    # Test message
    messages = [
        {"role": "user", "content": "What's the weather in San Francisco?"}
    ]
    
    try:
        # Make request with tools
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=tools,
            tool_choice="auto"  # Let model decide
        )
        
        print("✅ Tool Call Test Successful!")
        print(f"Response: {response.choices[0].message}")
        
        # Check if tool was called
        if response.choices[0].message.tool_calls:
            print(f"Tool called: {response.choices[0].message.tool_calls[0].function.name}")
            print(f"Arguments: {response.choices[0].message.tool_calls[0].function.arguments}")
        
    except Exception as e:
        print(f"❌ Tool Call Test Failed: {e}")

def test_with_framework():
    """Test using the enhanced agent with vLLM."""
    
    from agent_enhanced import OpenRouterAgent
    
    # Create agent pointing to vLLM
    agent = OpenRouterAgent("config.yaml", silent=False)
    
    # Test query that should trigger tool use
    response = agent.run("Search for the latest news about AI advancements")
    
    print(f"Framework Response: {response}")
    
    # Check metrics
    metrics = agent.get_metrics()
    print(f"Metrics: {metrics}")

def benchmark_tool_calls():
    """Benchmark tool calling performance."""
    
    import time
    
    client = OpenAI(
        base_url=VLLM_URL,
        api_key="dummy"
    )
    
    # Simple calculation tool
    tools = [{
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform a calculation",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression"
                    }
                },
                "required": ["expression"]
            }
        }
    }]
    
    queries = [
        "What is 25 * 4?",
        "Calculate the square root of 144",
        "What's 15% of 200?",
        "Solve: 2x + 5 = 15"
    ]
    
    print("Running benchmark...")
    times = []
    
    for query in queries:
        start = time.time()
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": query}],
            tools=tools,
            max_tokens=100
        )
        
        duration = time.time() - start
        times.append(duration)
        
        print(f"Query: {query[:30]}... - Time: {duration:.3f}s")
    
    avg_time = sum(times) / len(times)
    print(f"\nAverage response time: {avg_time:.3f}s")
    print(f"Throughput: {1/avg_time:.2f} req/s")

if __name__ == "__main__":
    print("🧪 Testing vLLM Tool Calling\n" + "="*40)
    
    # Check if server is running
    try:
        response = requests.get(f"{VLLM_URL}/health")
        if response.status_code != 200:
            print("❌ vLLM server is not healthy")
            exit(1)
    except:
        print("❌ Cannot connect to vLLM server")
        print("Start it with: ./vllm_start_enhanced.sh")
        exit(1)
    
    print("\n1. Basic Tool Call Test")
    print("-" * 40)
    test_basic_tool_call()
    
    print("\n2. Framework Integration Test")
    print("-" * 40)
    test_with_framework()
    
    print("\n3. Performance Benchmark")
    print("-" * 40)
    benchmark_tool_calls()
```

## ⚙️ Configuration Options

### Model-Specific Settings

Different models require different tool call parsers:

| Model Family | Tool Parser | Recommended Settings |
|-------------|-------------|---------------------|
| Hermes/OpenHermes | `hermes` | Default settings work well |
| Mistral/Mixtral | `mistral` | Use Mistral's function calling format |
| Llama 3 | `hermes` | Works with Hermes parser |
| Qwen | `hermes` | May need custom chat template |

### Performance Profiles

#### High Throughput
```bash
MAX_NUM_SEQS="256"
MAX_NUM_BATCHED_TOKENS="16384"
GPU_MEMORY_UTILIZATION="0.95"
ENABLE_PREFIX_CACHING="true"
```

#### Low Latency
```bash
MAX_NUM_SEQS="16"
MAX_NUM_BATCHED_TOKENS="2048"
NUM_SCHEDULER_STEPS="1"
GPU_MEMORY_UTILIZATION="0.85"
```

#### Memory Optimized
```bash
GPU_MEMORY_UTILIZATION="0.80"
KV_CACHE_DTYPE="fp8"
MAX_NUM_SEQS="32"
BLOCK_SIZE="8"
```

## 📊 Monitoring

### Real-time Monitoring
```bash
# Continuous monitoring with refresh every 5 seconds
./vllm_monitor.sh monitor

# Include inference tests
./vllm_monitor.sh -t monitor

# Show error logs
./vllm_monitor.sh -e monitor
```

### Performance Benchmark
```bash
# Run 50 benchmark requests
./vllm_monitor.sh benchmark 50
```

### Container Management
```bash
# View logs
./vllm_monitor.sh logs

# View errors only
./vllm_monitor.sh errors

# Restart server
./vllm_monitor.sh restart

# Stop server
./vllm_monitor.sh stop
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Tool calls not working
- **Check model support**: Not all models support tool calling
- **Verify parser**: Ensure correct `--tool-call-parser` for your model
- **Check format**: Tool definitions must match expected schema

#### 2. Out of memory errors
- **Reduce batch size**: Lower `MAX_NUM_SEQS`
- **Reduce model length**: Lower `MODEL_LENGTH`
- **Use quantization**: Use AWQ or GPTQ quantized models
- **Enable FP8 cache**: Set `KV_CACHE_DTYPE="fp8"`

#### 3. Slow inference
- **Enable prefix caching**: Set `ENABLE_PREFIX_CACHING="true"`
- **Adjust scheduling**: Increase `NUM_SCHEDULER_STEPS`
- **Use tensor parallelism**: Set `TENSOR_PARALLEL_SIZE` > 1 for multi-GPU

#### 4. Connection refused
- **Check port**: Ensure `VLLM_PORT` is not in use
- **Check Docker**: Verify Docker daemon is running
- **Check firewall**: Ensure port is not blocked

### Debug Commands

```bash
# Check if container is running
docker ps | grep vllm-server

# View detailed logs
docker logs vllm-server --tail 100

# Check GPU usage
nvidia-smi

# Test API directly
curl -X POST http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "model", "messages": [{"role": "user", "content": "Hi"}]}'

# Check resource usage
docker stats vllm-server
```

## 🚀 Advanced Usage

### Custom Chat Templates

For models requiring specific formatting:

```python
# Create custom template
cat > /opt/inference/templates/custom.jinja2 << 'EOF'
{%- for message in messages %}
{%- if message['role'] == 'user' %}
User: {{ message['content'] }}
{%- elif message['role'] == 'assistant' %}
Assistant: {{ message['content'] }}
{%- endif %}
{%- endfor %}
Assistant:
EOF

# Use in config
CHAT_TEMPLATE="/opt/inference/templates/custom.jinja2"
```

### Multi-GPU Setup

```bash
# For 2 GPUs
TENSOR_PARALLEL_SIZE="2"
CUDA_VISIBLE_DEVICES="0,1"

# For 4 GPUs with pipeline parallelism
TENSOR_PARALLEL_SIZE="2"
PIPELINE_PARALLEL_SIZE="2"
CUDA_VISIBLE_DEVICES="0,1,2,3"
```

### API Authentication

```bash
# Set API key in config
API_KEY="your-secret-key-123"

# Use in requests
curl -H "Authorization: Bearer your-secret-key-123" \
  http://localhost:8081/v1/models
```

## 📚 Additional Resources

- [vLLM Documentation](https://docs.vllm.ai/)
- [vLLM CLI Arguments](https://docs.vllm.ai/en/latest/cli/serve.html)
- [Tool Calling Guide](https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html#tool-calling)
- [Performance Tuning](https://docs.vllm.ai/en/latest/serving/performance.html)

## 🎉 Conclusion

With vLLM v0.11+ and the Chat with Tools framework, you have:
- ✅ High-performance local inference
- ✅ Native tool calling support
- ✅ Production-ready monitoring
- ✅ Easy configuration management
- ✅ Seamless framework integration

The combination of vLLM's speed and the framework's multi-agent orchestration creates a powerful system for complex AI tasks with tool usage!
