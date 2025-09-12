# Configuration Update - Unified Logging System

## Overview
The Chat with Tools framework configuration has been updated to consolidate all logging-related settings into a single, unified `logging` section. This eliminates confusion from having multiple overlapping sections (`logging`, `debug`, `development`) and provides a cleaner, more maintainable configuration structure.

## What Changed

### Before (Old Structure)
The old configuration had three separate sections with overlapping functionality:
- `logging` - Basic logging configuration
- `debug` - Debug mode settings
- `development` - Development/testing settings

This created confusion about which settings to use and where to configure logging behavior.

### After (New Structure)
All logging-related configuration is now consolidated under a single `logging` section with clear subsections:

```yaml
logging:
  level: "INFO"                    # Master log level
  
  console:                         # Console output settings
    enabled: true
    format: "..."
    colored: true
  
  file:                           # File logging settings
    enabled: false
    path: "./logs"
    filename: "chat_with_tools.log"
    max_size_mb: 10
    max_files: 5
  
  debug:                          # Debug mode settings
    enabled: false                # Master debug switch
    verbose: false               # Extra verbose output
    log_tool_calls: true
    log_llm_calls: true
    log_agent_thoughts: true
    
    debug_file:                  # Separate debug file
      enabled: true
      path: "./logs/debug"
      max_size_mb: 20
      max_files: 10
  
  development:                   # Development/testing features
    save_responses: false
    save_history: false
    profile: false
    trace_tools: false
    mock_api: false
```

## Migration

### Automatic Migration
Use the provided migration script to automatically update your existing config:

```bash
python migrate_config.py
```

The script will:
1. Find your existing config.yaml
2. Create a backup with timestamp
3. Migrate all settings to the new format
4. Save the updated configuration

### Manual Migration
If you prefer to manually update your config:

1. Copy the new `config.example.yaml` to `config.yaml`
2. Transfer your API keys and custom settings
3. Configure logging according to the new structure

## Benefits

1. **Clarity**: All logging configuration in one place
2. **Consistency**: No more duplicate or conflicting settings
3. **Hierarchy**: Clear precedence (debug.enabled overrides level)
4. **Flexibility**: Separate controls for console, file, and debug logging
5. **Simplicity**: Easier to understand and configure

## Logging Behavior

### Log Levels
- `CRITICAL`: Only critical errors
- `ERROR`: Errors and above
- `WARNING`: Warnings and above (default)
- `INFO`: Informational messages and above
- `DEBUG`: All messages including debug

### Debug Mode
When `logging.debug.enabled` is `true`:
- Enables detailed debug logging to separate files
- Logs tool calls, LLM interactions, and agent thoughts
- Creates timestamped debug files with rotation

### Verbose Mode
When `logging.debug.verbose` is `true`:
- Overrides log level to DEBUG
- Provides maximum detail in all outputs
- Useful for troubleshooting complex issues

## Silent Mode
The `silent` parameter in agent initialization now properly integrates with the unified logging:
- When `silent=True`: Sets log level to WARNING (reduces output)
- When `silent=False`: Uses configured log level

## Examples

### Basic Setup (Production)
```yaml
logging:
  level: "WARNING"
  console:
    enabled: true
  file:
    enabled: false
  debug:
    enabled: false
```

### Development Setup
```yaml
logging:
  level: "INFO"
  console:
    enabled: true
    colored: true
  file:
    enabled: true
    path: "./logs"
  debug:
    enabled: true
    verbose: false
    log_tool_calls: true
```

### Debugging Setup
```yaml
logging:
  level: "DEBUG"
  console:
    enabled: true
  debug:
    enabled: true
    verbose: true
    log_tool_calls: true
    log_llm_calls: true
    log_agent_thoughts: true
```

## Troubleshooting

If you encounter issues after the update:

1. **Run the migration script**: `python migrate_config.py`
2. **Check your backup**: Backups are created with timestamp
3. **Use config.example.yaml**: Start fresh with the example
4. **Verify paths**: Ensure log directories exist or are writable

## Support

For questions or issues:
- Check the example configuration: `config/config.example.yaml`
- Run tests: `python tests/test_framework.py`
- Review the migration script output for specific issues

## Backward Compatibility

The framework maintains backward compatibility:
- Old config files are automatically detected
- Migration script safely converts to new format
- Backups ensure you can always revert if needed
