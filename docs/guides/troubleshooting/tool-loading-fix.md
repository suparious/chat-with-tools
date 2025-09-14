---
title: Tool Loading Fix
tags: [troubleshooting, tools, imports, fix]
created: 2025-09-13
updated: 2025-09-13
status: resolved
source: archive/2025-09-13/tool-loading-fix-original.md
---

# Tool Loading Fix

## Issue Identified

The tools were not being loaded (showing "Loaded 0 tools") due to import path issues after repository structure changes.

## Root Cause

The `discover_tools` function in `/src/chat_with_tools/tools/__init__.py` was using a hardcoded package name `'chat_with_tools.tools'` for importing modules, which didn't work correctly when the package was imported from different contexts.

## Fixes Applied

### 1. Fixed `discover_tools` Function

**File**: `/src/chat_with_tools/tools/__init__.py`

**Changes:**
- Changed from hardcoded package name to using `__name__` for dynamic package resolution
- Added comprehensive debug output to help diagnose issues
- Improved error handling with detailed traceback information
- Added detection for tool classes within modules

**Key Change:**
```python
# OLD (broken)
module = importlib.import_module(f'.{module_name}', package='chat_with_tools.tools')

# NEW (fixed)
module = importlib.import_module(f'.{module_name}', package=__name__)
```

### 2. Fixed Import Paths in Demo Files

Updated all demo files to properly add the `src` directory to the Python path:

**Files Updated:**
- `/demos/main.py`
- `/demos/council_chat.py`
- `/demos/demo_api.py`
- `/demos/demo_standalone.py`
- `/demos/demo_new_tools.py`

**Pattern Applied:**
```python
# Add both the project root and src directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')

# Add src path first so imports work correctly
if src_path not in sys.path:
    sys.path.insert(0, src_path)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import directly from chat_with_tools (not src.chat_with_tools)
from chat_with_tools.agent import OpenRouterAgent
```

### 3. Created Test Script

**File**: `/test_tool_loading.py`

A standalone test script to verify that tool loading is working correctly after the fixes.

## Testing Instructions

### Quick Test
```bash
cd /home/shaun/repos/chat-with-tools
python test_tool_loading.py
```
This should show all tools being loaded successfully with debug output.

### Full Test
```bash
uv run python main.py
```
Then select option 1 for "Single Agent Chat" - you should now see tools being loaded.

### Verify Tools are Available
The agent initialization should now show something like:
```
Loaded 11 tools: [calculate, memory, python_executor, ...]
```

## Debug Features Added

The updated `discover_tools` function now includes:
- Debug output showing the tools directory path
- Current module name for package resolution
- List of tool files found
- Import attempt notifications
- Tool class discovery within each module
- Detailed error messages with tracebacks
- Summary of total tools loaded

## Benefits of the Fix

1. **Dynamic Package Resolution** - Tool discovery works regardless of import context
2. **Better Debugging** - Comprehensive debug output for troubleshooting
3. **Consistent Imports** - All demo files use the same import pattern
4. **Robust Error Handling** - Better error messages help identify problems

## Implementation Details

### Dynamic Package Resolution
The fix uses `__name__` which automatically resolves to the correct package path:
- When imported as `chat_with_tools.tools`, `__name__` is `'chat_with_tools.tools'`
- Works correctly in all contexts (development, installed, testing)

### Debug Output
Debug information can be suppressed by passing `silent=True` to agent initialization:
```python
agent = OpenRouterAgent(silent=True)  # No debug output
```

## Verification

After applying these fixes, running any agent mode should show:
- Tools being discovered and loaded
- Debug output showing the discovery process (unless silent mode)
- Full tool functionality available to agents

## Common Issues

### Still Not Loading Tools?

1. **Check Python Path**
   ```python
   import sys
   print(sys.path)  # Should include src directory
   ```

2. **Verify Tool Files Exist**
   ```bash
   ls src/chat_with_tools/tools/*.py
   ```

3. **Check for Import Errors**
   Run with debug output to see specific import failures

### Import Errors in Tools

If a specific tool fails to import:
- Check its dependencies are installed
- Look for syntax errors in the tool file
- Verify the tool class inherits from `BaseTool`

## Notes

- All demo files now properly add the `src` directory to `sys.path` before importing
- The debug output can be suppressed by passing `silent=True` to the agent initialization
- The fix ensures tools load correctly in both development and installed modes

---

Related: [[recent-fixes|Recent Fixes]], [[components/tools/index|Tools Documentation]]
Source: [[archive/2025-09-13/tool-loading-fix-original]]
