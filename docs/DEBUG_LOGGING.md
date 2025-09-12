# Debug Logging Feature

## Overview

The Chat with Tools framework now includes a comprehensive debug logging system that can be enabled via configuration. This feature helps with troubleshooting, performance monitoring, and understanding the framework's behavior during execution.

## Features

- **Configurable via YAML**: Enable/disable debug logging through `config.yaml`
- **Rotating Log Files**: Automatic log rotation to prevent disk space issues
- **Detailed Timestamps**: Millisecond-precision timestamps for all log entries
- **Categorized Logging**: Separate logging for agent iterations, tool calls, LLM interactions, and orchestrator tasks
- **Thread-Safe**: Safe to use in multi-threaded orchestrator scenarios
- **Singleton Pattern**: Single logger instance across the entire application
- **Performance Optimized**: Minimal overhead when disabled

## Configuration

Add or modify the `debug` section in your `config/config.yaml`:

```yaml
# Debug logging settings
debug:
  enabled: false  # Set to true to enable debug logging to disk
  log_path: "./logs"  # Directory where log files will be stored
  log_level: "DEBUG"  # Logging level: DEBUG, INFO, WARNING, ERROR
  max_log_size_mb: 10  # Maximum size of each log file in MB
  max_log_files: 5  # Maximum number of log files to keep (rotation)
  include_timestamps: true  # Include detailed timestamps in logs
  log_tool_calls: true  # Log all tool invocations and results
  log_llm_calls: true  # Log LLM API calls and responses
  log_agent_thoughts: true  # Log agent reasoning and iterations
```

## Usage

### Basic Setup

1. **Enable Debug Logging**:
   Edit `config/config.yaml` and set `debug.enabled: true`

2. **Run Your Application**:
   ```bash
   python main.py
   ```

3. **Check Log Files**:
   Logs will be created in the `./logs/` directory (or your configured path)

### Log File Format

Log files are named with timestamps: `debug_YYYYMMDD_HHMMSS.log`

Example log entry:
```
2024-01-20 14:30:45.123 | INFO     | chat_with_tools.debug | log_agent_iteration | Agent Iteration | {"iteration": 1, "max_iterations": 10, "agent_id": "main"}
```

### Log Categories

#### Agent Iterations
Tracks each iteration of the agent's reasoning loop:
```python
self.debug_logger.log_agent_iteration(iteration, max_iterations, agent_id)
```

#### Tool Calls
Records tool invocations with arguments and results:
```python
self.debug_logger.log_tool_call(tool_name, arguments, result=result)
```

#### LLM Calls
Logs API calls to the language model:
```python
self.debug_logger.log_llm_call(model, messages, response=response)
```

#### Orchestrator Tasks
Tracks parallel agent execution in orchestrator mode:
```python
self.debug_logger.log_orchestrator_task(task_id, status, details)
```

## Testing Debug Logging

### Quick Test
Run the provided test script:
```bash
python test_debug.py
```

This will:
- Test with debug disabled (default)
- Test with debug enabled
- Verify log file creation
- Display sample log entries
- Clean up test logs

### Manual Testing

1. **Enable debug in config**:
   ```yaml
   debug:
     enabled: true
   ```

2. **Run a simple query**:
   ```bash
   python main.py
   # Enter: "What is the weather today?"
   ```

3. **Check the logs**:
   ```bash
   ls -la ./logs/
   tail -f ./logs/debug_*.log
   ```

## Log Rotation

The system automatically rotates logs based on your configuration:

- When a log file exceeds `max_log_size_mb`, it's rotated
- Old log files are numbered: `debug_20240120_143045.log.1`, `.2`, etc.
- Only `max_log_files` are kept; older ones are deleted

## Performance Considerations

- **When Disabled**: Zero overhead - no logging operations are performed
- **When Enabled**: Minimal impact - file I/O is handled efficiently
- **Large Responses**: LLM responses and tool results are truncated to 500 characters in logs

## Troubleshooting

### Logs Not Appearing

1. **Check Configuration**:
   ```python
   from src.chat_with_tools.config_manager import ConfigManager
   config = ConfigManager().config
   print(config.get('debug', {}).get('enabled'))  # Should be True
   ```

2. **Check Permissions**:
   Ensure the process has write permissions to the log directory

3. **Check Disk Space**:
   Ensure sufficient disk space for log files

### Too Many Logs

Adjust the configuration:
- Increase `log_level` to "WARNING" or "ERROR"
- Disable specific categories (e.g., `log_tool_calls: false`)
- Reduce `max_log_files` to limit disk usage

## Advanced Usage

### Custom Log Messages

In your tools or extensions:
```python
from src.chat_with_tools.utils import DebugLogger

class MyCustomTool:
    def __init__(self, config):
        self.debug_logger = DebugLogger(config)
    
    def execute(self, **kwargs):
        self.debug_logger.info("Custom tool executing", kwargs=kwargs)
        # Your tool logic here
        result = process_data(kwargs)
        self.debug_logger.info("Custom tool completed", result=result)
        return result
```

### Analyzing Logs

For performance analysis:
```bash
# Count agent iterations
grep "Agent Iteration" ./logs/debug_*.log | wc -l

# Find errors
grep "ERROR" ./logs/debug_*.log

# Track tool usage
grep "Tool Call:" ./logs/debug_*.log | cut -d':' -f6 | sort | uniq -c

# Measure execution time
grep "execution_time" ./logs/debug_*.log
```

## Security Notes

- Log files may contain sensitive information from API calls
- Ensure log directory has appropriate permissions
- Consider log retention policies for production environments
- API keys are not logged, but user inputs and responses are

## Integration with Monitoring Tools

Log files can be integrated with monitoring tools:

- **Filebeat/Logstash**: Ship logs to Elasticsearch
- **CloudWatch**: Monitor AWS deployments
- **Grafana Loki**: Aggregate and query logs
- **Splunk**: Enterprise log analysis

Example Filebeat configuration:
```yaml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /path/to/chat-with-tools/logs/debug_*.log
  multiline.pattern: '^\d{4}-\d{2}-\d{2}'
  multiline.negate: true
  multiline.match: after
```

## Best Practices

1. **Development**: Enable debug logging for troubleshooting
2. **Production**: Use WARNING or ERROR level only
3. **Debugging**: Enable specific categories as needed
4. **Monitoring**: Set up log aggregation for production systems
5. **Cleanup**: Implement log rotation and deletion policies

## Future Enhancements

Planned improvements for the debug logging system:

- [ ] Structured JSON logging option
- [ ] Remote logging support (syslog, HTTP endpoints)
- [ ] Performance metrics dashboard
- [ ] Log filtering and search utilities
- [ ] Integration with OpenTelemetry
- [ ] Async logging for improved performance
- [ ] Log encryption for sensitive environments

## Support

For issues or questions about debug logging:
1. Check this documentation
2. Run `python test_debug.py` to verify setup
3. Check the main README.md for general framework help
4. Open an issue on GitHub with log samples (sanitized)
