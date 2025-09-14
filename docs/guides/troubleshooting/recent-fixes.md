---
title: Recent Fixes and Improvements
tags: [troubleshooting, fixes, changelog]
created: 2025-09-13
updated: 2025-09-13
status: active
source: archive/2025-09-13/fixes-readme-original.md
---

# Recent Fixes and Improvements

## Date: September 13, 2025

This document details recent bug fixes and improvements made to the Chat with Tools framework.

## Issues Fixed

### 1. Tool Argument Parsing Error

#### Problem
When using the search tool, the agent was failing with error: `'str' object has no attribute 'items'`

#### Root Cause
The LLM was sometimes sending tool arguments in unexpected formats (plain strings instead of JSON objects), and the agent wasn't handling these cases properly.

#### Solution
Enhanced the `handle_tool_call` method in `agent.py` to:
- Detect different argument formats (string, JSON string, dictionary)
- Automatically wrap plain strings in a `query` parameter for search tools
- Add robust type checking and conversion
- Provide better error messages for debugging

**Files Modified:**
- `src/chat_with_tools/agent.py` (lines 247-273, 196-234)

### 2. Configuration Validation

#### Problem
The configuration manager was raising hard errors when API keys were missing, preventing users from testing with local vLLM endpoints.

#### Root Cause
The `_validate_config` method was too strict about API key requirements.

#### Solution
Modified `config_manager.py` to:
- Show warnings instead of errors for missing API keys
- Allow the framework to continue with local endpoints
- Provide helpful guidance about API key configuration

**Files Modified:**
- `src/chat_with_tools/config_manager.py` (lines 110-143)

### 3. Tool Loading Issues

#### Problem
Tools were not being loaded (showing "Loaded 0 tools") due to import path issues.

#### Root Cause
The `discover_tools` function was using a hardcoded package name that didn't work correctly when imported from different contexts.

#### Solution
- Changed from hardcoded package name to using `__name__` for dynamic package resolution
- Added comprehensive debug output
- Improved error handling with detailed traceback information

**Key Change:**
```python
# OLD (broken)
module = importlib.import_module(f'.{module_name}', package='chat_with_tools.tools')

# NEW (fixed)
module = importlib.import_module(f'.{module_name}', package=__name__)
```

See [[tool-loading-fix|Tool Loading Fix]] for details.

### 4. Python Executor Tool Bug

#### Problem
The `print` function wasn't available in the sandboxed environment.

#### Solution
Fixed the `_create_safe_globals` method to properly import built-in functions using the `builtins` module.

## Testing the Fixes

### Test Imports
```bash
uv run python test_imports.py
```

### Test Tool Argument Parsing
```bash
uv run python test_tool_fix.py
```

### Run Main Application
```bash
uv run python main.py
```

## How the Fixes Work

### Tool Argument Handling

The agent now handles tool arguments more robustly:

1. **JSON String Arguments** - Parsed normally with `json.loads()`
2. **Plain String Arguments** - Wrapped in `{"query": "string value"}` if needed
3. **Dictionary Arguments** - Used directly without parsing
4. **Other Types** - Converted to dictionary if possible

### Example Usage

```python
# In the chat interface
User: Search the web for 3rd gen camaro LS engine swap kits

# The agent should now:
1. Parse the request
2. Call the search_web tool with appropriate arguments
3. Return search results
4. Summarize the findings
```

## Additional Improvements

1. **Better Debug Logging** - Enhanced error messages to help identify issues
2. **Graceful Fallbacks** - The system tries multiple approaches before failing
3. **Type Safety** - Added type checking to prevent similar issues
4. **Warning System** - Configuration issues show warnings instead of blocking

## Verification Checklist

- [x] Tool argument parsing works with various formats
- [x] Configuration warnings don't block execution
- [x] Tool discovery and loading works correctly
- [x] All imports and module paths verified
- [x] Python executor has access to built-in functions
- [x] Framework works with both OpenRouter and local vLLM

## Next Steps

If you encounter other issues:
1. Check the logs for detailed error messages
2. Run the test scripts to verify functionality
3. Ensure your config.yaml is properly configured
4. Try with different LLM models if one is causing issues

## Notes

- The framework now works with both OpenRouter API keys and local vLLM endpoints
- Configuration warnings don't block execution
- Tool discovery and loading is working correctly
- All imports and module paths have been verified

---

Related: [[tool-loading-fix|Tool Loading Fix]], [[search-tool-consolidation|Search Tool Consolidation]]
Source: [[archive/2025-09-13/fixes-readme-original]]
