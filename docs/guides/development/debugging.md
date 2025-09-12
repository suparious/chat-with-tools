---
title: Debug Logging Guide
tags: [guide, development, debugging, logging]
created: 2024-12-30
updated: 2024-12-30
audience: developer
source: archive/agent-summaries-2024-12/debug-logging-documentation.md
---

# Debug Logging Guide

## Overview

The Chat with Tools framework includes a comprehensive debug logging system that provides detailed insights into the framework's operation. This guide covers configuration, usage, and best practices for debugging with the logging system.

## Prerequisites

- [ ] Access to `config/config.yaml`
- [ ] Write permissions for log directory
- [ ] Basic understanding of log levels

## Configuration

### Enable Debug Logging

Debug logging is configured in the `logging` section of `config/config.yaml`:

```yaml
logging:
  level: "INFO"                    # Master log level
  
  console:                         # Console output settings
    enabled: true
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    colored: true
  
  file:                           # File logging settings
    enabled: false
    path: "./logs"
    filename: "chat_with_tools.log"
    max_size_mb: 10
    max_files: 5
  
  debug:                          # Debug mode settings
    enabled: false                # Set to true to enable debug logging
    verbose: false               # Extra verbose output
    log_tool_calls: true
    log_llm_calls: true
    log_agent_thoughts: true
    
    debug_file:                  # Separate debug file
      enabled: true
      path: "./logs/debug"
      max_size_mb: 20
      max_files: 10
```

### Quick Enable

To quickly enable debug logging:

```yaml
logging:
  debug:
    enabled: true
```

## Debug Logger Features

### Singleton Pattern
The `DebugLogger` class uses a singleton pattern to ensure a single logger instance across the application:

```python
from src.chat_with_tools.utils import DebugLogger

logger = DebugLogger.get_instance(config)
```

### Automatic Log Rotation
- Logs rotate when file size exceeds configured limit
- Keeps only the configured number of log files
- Old logs are automatically deleted

### Millisecond Precision Timestamps
All log entries include precise timestamps for performance analysis:
```
2024-12-30 10:15:23.456 [DEBUG] Agent Iteration 1 starting
```

### Structured Logging
Complex data is JSON-serialized for easy parsing:
```python
logger.log_tool_call(
    tool_name="search_web",
    arguments={"query": "AI news"},
    result={"status": "success", "results": [...]}
)
```

## Logging Categories

### Agent Iterations
Track the agent's reasoning loop:
```
[DEBUG] ========== Agent Iteration 1 ==========
[DEBUG] LLM Request: messages=[...]
[DEBUG] LLM Response: content="I'll search for that information"
[DEBUG] Tool calls detected: ['search_web']
```

### Tool Execution
Monitor tool invocations and results:
```
[DEBUG] Tool Call: search_web
[DEBUG] Arguments: {"query": "latest AI developments"}
[DEBUG] Result: {"status": "success", "results": [...]}
[DEBUG] Execution time: 1.23s
```

### LLM API Calls
Track all LLM interactions:
```
[DEBUG] LLM Call: model=gpt-4, messages=3, max_tokens=1000
[DEBUG] Response: tokens=450, finish_reason=stop
```

### Orchestrator Tasks
Monitor multi-agent execution:
```
[DEBUG] Orchestrator: Starting 4 parallel agents
[DEBUG] Agent 0: Processing question "What are the technical aspects?"
[DEBUG] Agent 1: Processing question "What are the business implications?"
[DEBUG] Agent 2: Complete
[DEBUG] Agent 3: Working
```

## Usage Examples

### Basic Debugging

1. Enable debug logging:
```yaml
logging:
  debug:
    enabled: true
```

2. Run your application:
```bash
python main.py
```

3. Monitor logs in real-time:
```bash
tail -f ./logs/debug/debug_*.log
```

### Filtering Logs

Find specific information in logs:

```bash
# Count agent iterations
grep "Agent Iteration" ./logs/debug/debug_*.log | wc -l

# Find errors
grep "ERROR" ./logs/debug/debug_*.log

# Track tool usage
grep "Tool Call:" ./logs/debug/debug_*.log | cut -d':' -f3 | sort | uniq -c

# Find slow operations
grep "execution_time" ./logs/debug/debug_*.log | awk '{if ($NF > 2.0) print}'
```

### Performance Analysis

Extract performance metrics:

```bash
# Average response time
grep "execution_time" ./logs/debug/debug_*.log | \
  awk '{sum+=$NF; count++} END {print sum/count}'

# Token usage
grep "tokens=" ./logs/debug/debug_*.log | \
  sed 's/.*tokens=\([0-9]*\).*/\1/' | \
  awk '{sum+=$1} END {print "Total tokens:", sum}'
```

## Log File Management

### File Naming
Log files are named with timestamps:
```
debug_20241230_101523.log
```

### Rotation Settings
Configure rotation in `config.yaml`:
```yaml
logging:
  debug:
    debug_file:
      max_size_mb: 20      # Rotate when file reaches 20MB
      max_files: 10        # Keep last 10 files
```

### Manual Cleanup
Remove old logs:
```bash
# Remove logs older than 7 days
find ./logs -name "debug_*.log" -mtime +7 -delete
```

## Best Practices

### Development vs Production

**Development**:
```yaml
logging:
  level: "DEBUG"
  debug:
    enabled: true
    verbose: true
```

**Production**:
```yaml
logging:
  level: "WARNING"
  debug:
    enabled: false
```

### Security Considerations

> [!WARNING]
> Debug logs may contain sensitive information including:
> - API keys (if logged accidentally)
> - User queries
> - Tool arguments and results
> 
> Ensure proper access controls on log directories.

### Performance Impact

- **Disabled**: Zero overhead - no logging operations performed
- **Enabled**: Minimal impact (~1-2% overhead)
- **Verbose**: Noticeable impact (~5-10% overhead)

### Log Levels

Use appropriate log levels:
- **CRITICAL**: System failures
- **ERROR**: Operation failures
- **WARNING**: Potential issues
- **INFO**: Important events
- **DEBUG**: Detailed diagnostic info

## Troubleshooting

### Logs Not Created

1. Check directory permissions:
```bash
ls -la ./logs
```

2. Verify configuration:
```python
from src.chat_with_tools.config_manager import ConfigManager
config = ConfigManager("config/config.yaml")
print(config.get_debug_config())
```

### Logs Too Large

Adjust rotation settings:
```yaml
logging:
  debug:
    debug_file:
      max_size_mb: 5    # Smaller files
      max_files: 20     # Keep more files
```

### Missing Information

Enable verbose mode:
```yaml
logging:
  debug:
    verbose: true
    log_tool_calls: true
    log_llm_calls: true
    log_agent_thoughts: true
```

## Integration with Monitoring Tools

### Export to Elasticsearch

Use Filebeat to ship logs:
```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  paths:
    - /path/to/logs/debug/*.log
  json.keys_under_root: true
  json.add_error_key: true
```

### Prometheus Metrics

Parse logs for metrics:
```python
# Extract metrics from logs
import re
from prometheus_client import Counter, Histogram

tool_calls = Counter('tool_calls_total', 'Total tool calls')
response_time = Histogram('response_time_seconds', 'Response time')
```

## Next Steps

- [[guides/development/testing|Testing Guide]]
- [[guides/troubleshooting/common-issues|Common Issues]]
- [[references/logging|Logging Reference]]

## References

- Configuration: [[references/configuration]]
- Source: [[archive/agent-summaries-2024-12/debug-logging-documentation]]
- Implementation: [[archive/agent-summaries-2024-12/implementation-debug-logging-fixes]]