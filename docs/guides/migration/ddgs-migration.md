---
title: DuckDuckGo Search Package Migration
tags: [migration, ddgs, search, dependencies]
created: 2025-09-13
updated: 2025-09-13
status: completed
source: archive/2025-09-13/ddgs-migration-original.md
---

# DuckDuckGo Search Package Migration

## Overview

The `duckduckgo_search` package has been renamed to `ddgs`. This migration guide documents the changes made to support the new package while maintaining backward compatibility.

## Issue Description

Using the old package name generates a deprecation warning:
```
RuntimeWarning: This package (`duckduckgo_search`) has been renamed to `ddgs`! 
Use `pip install ddgs` instead.
```

## Migration Changes

### 1. Updated Import Statements

Modified search tool files for backward compatibility:

**Files Updated:**
- `/src/chat_with_tools/tools/search_tool.py`

**Import Pattern:**
```python
# Updated to use the new ddgs package name
try:
    from ddgs import DDGS
except ImportError:
    # Fallback to old package name for compatibility
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        raise ImportError("Please install the 'ddgs' package: pip install ddgs")
```

### 2. Updated Dependencies

Changed package requirements:

| File | Old Dependency | New Dependency |
|------|---------------|----------------|
| `requirements.txt` | `duckduckgo-search>=3.9.0` | `ddgs>=0.1.0` |
| `pyproject.toml` | `duckduckgo-search>=3.9.0` | `ddgs>=0.1.0` |

## How to Apply the Migration

### Option 1: Using uv (Recommended)
```bash
cd /home/shaun/repos/chat-with-tools
uv pip install ddgs
uv pip uninstall duckduckgo-search
```

### Option 2: Manual Update
```bash
cd /home/shaun/repos/chat-with-tools
pip uninstall -y duckduckgo-search
pip install ddgs
```

### Option 3: Full Dependency Update
```bash
cd /home/shaun/repos/chat-with-tools
pip install -r requirements.txt --upgrade
```

## Verification

### Quick Test
```python
from ddgs import DDGS
ddgs = DDGS()
results = ddgs.text("test query", max_results=2)
print(f"Search working: {len(results)} results found")
```

### Full Test
```bash
uv run python main.py
# Select option 1 (Single Agent Chat)
# Ask the agent to search for something
```

The warning should no longer appear, and search functionality should work normally.

## Benefits

1. **No More Warnings** - Eliminates the deprecation warning
2. **Future Compatibility** - Uses the actively maintained package
3. **Backward Compatibility** - Code still works if old package is installed
4. **Same API** - The DDGS class interface remains the same

## Technical Details

The package rename doesn't change the API:
- **Old**: `pip install duckduckgo-search` → `from duckduckgo_search import DDGS`
- **New**: `pip install ddgs` → `from ddgs import DDGS`

The functionality and class methods remain identical, making this a simple drop-in replacement.

## Troubleshooting

### Import Error
Make sure the new package is installed:
```bash
pip install ddgs
```

### Search Not Working
Verify the package is working:
```python
python -c "from ddgs import DDGS; print('✅ Package imported successfully')"
```

### Conflicts
If both packages are installed, uninstall the old one:
```bash
pip uninstall -y duckduckgo-search
```

### Version Issues
Make sure you have the latest version:
```bash
pip install --upgrade ddgs
```

## Notes

- The API remains completely compatible
- The fallback import ensures the code works during transition
- Once all environments are updated, the fallback can be removed
- The `ddgs` package is the official successor and is actively maintained

---

Related: [[components/tools/search-tool|Search Tool Documentation]], [[guides/troubleshooting/dependencies|Dependency Issues]]
Source: [[archive/2025-09-13/ddgs-migration-original]]
