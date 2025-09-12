# Chat with Tools - Testing & Demo Guide

## 📚 Three Testing Approaches

Your Chat with Tools framework now has **three different ways** to test and demonstrate the new tools:

### 1. 🔧 **Direct Tool Testing** (`demo_standalone.py`)
**Purpose**: Test tools in isolation without any API or agent dependencies

**When to use**:
- Verifying tool implementation works correctly
- Testing without API connectivity
- Understanding tool internals
- Quick debugging of tool issues

**How it works**:
- Imports tools directly from `tools/` directory
- Instantiates tool classes manually
- Calls tool methods directly
- No LLM or API calls needed

**Run with**:
```bash
python demo_standalone.py
```

---

### 2. 🤖 **API-Based Agent Demo** (`demo_api.py`)
**Purpose**: Test tools through the full agent pipeline using your vLLM endpoint

**When to use**:
- Testing the complete framework integration
- Demonstrating natural language tool usage
- Verifying API connectivity
- Testing agent's tool selection logic

**How it works**:
- Uses `OpenRouterAgent` from `agent.py`
- Sends natural language prompts to the LLM
- LLM decides which tools to use
- Tools are called through the agent's tool calling mechanism
- Requires working API endpoint (vLLM or OpenRouter)

**Run with**:
```bash
python demo_api.py
```

---

### 3. 🔀 **Hybrid Testing** (`demo_new_tools.py`)
**Purpose**: Use agent for tool discovery but call tools directly

**When to use**:
- Testing tool discovery mechanism
- Debugging tool integration issues
- Testing with agent initialization but without API calls

**How it works**:
- Uses `OpenRouterAgent` for tool discovery
- Accesses tools via `agent.tool_mapping`
- Calls tool execute methods directly
- No actual LLM API calls for tool execution

**Run with**:
```bash
python demo_new_tools.py
```

---

## 🎯 Which Demo Should You Use?

### For Testing Tool Implementation
Use **`demo_standalone.py`** - It tests tools without any dependencies and provides comprehensive examples.

### For Testing with vLLM Endpoint
Use **`demo_api.py`** - It demonstrates the full framework with your API:
- Tests natural language understanding
- Shows agent tool selection
- Verifies API connectivity
- Demonstrates real-world usage

### For Quick Tool Discovery Testing
Use **`demo_new_tools.py`** - It's a middle ground that tests tool discovery without full API usage.

---

## 📋 Configuration for API-Based Testing

For `demo_api.py` to work with your vLLM endpoint, ensure `config.yaml` has:

```yaml
openrouter:
  api_key: ""  # Not needed for vLLM
  base_url: "http://infer.sbx-1.lq.ca.obenv.net:8000/v1"  # Your vLLM endpoint
  model: "NousResearch/Hermes-4-14B"  # Your model
```

Your vLLM endpoint is OpenAI-compatible, so it should work seamlessly.

---

## 🧪 Testing Workflow

### Step 1: Verify Tools Work
```bash
python demo_standalone.py
# Choose option 2 for comprehensive test
```

### Step 2: Test with API
```bash
python demo_api.py
# Choose option 6 for automated tests
# Choose option 7 for interactive mode
```

### Step 3: Test in Production Mode
```bash
# Single agent mode
python main.py

# Multi-agent mode (4 parallel agents)
python council_chat.py
```

---

## 🔍 Troubleshooting

### If tools aren't discovered:
1. Check that tool files are in `tools/` directory
2. Verify tools inherit from `BaseTool`
3. Check for import errors in tool files

### If API demos fail:
1. Verify vLLM endpoint is running
2. Check `base_url` in config.yaml
3. Test endpoint directly:
```bash
curl http://infer.sbx-1.lq.ca.obenv.net:8000/v1/models
```

### If dependencies are missing:
```bash
pip install pyyaml openai pandas numpy
```

---

## 📊 Feature Comparison

| Feature | `demo_standalone.py` | `demo_api.py` | `demo_new_tools.py` |
|---------|---------------------|---------------|---------------------|
| Requires API | ❌ | ✅ | ❌ |
| Tests tool logic | ✅ | ✅ | ✅ |
| Tests LLM integration | ❌ | ✅ | ❌ |
| Tests tool discovery | ❌ | ✅ | ✅ |
| Interactive mode | ✅ | ✅ | ✅ |
| Comprehensive examples | ✅ | ✅ | ⚠️ |
| Natural language input | ❌ | ✅ | ❌ |

---

## 🚀 Quick Start

For immediate testing without API:
```bash
python demo_standalone.py
```

For full framework testing with your vLLM:
```bash
python demo_api.py
```

For production use:
```bash
python main.py  # or council_chat.py
```

---

## ✅ All Tools Status

| Tool | Implementation | Standalone Test | API Test | Status |
|------|---------------|-----------------|----------|--------|
| Sequential Thinking | ✅ | ✅ | ✅ | **READY** |
| Memory | ✅ | ✅ | ✅ | **READY** |
| Python Executor | ✅ | ✅ | ✅ | **READY** |
| Summarization | ✅ | ✅ | ✅ | **READY** |

**🎉 All tools are fully implemented and ready for use!**
