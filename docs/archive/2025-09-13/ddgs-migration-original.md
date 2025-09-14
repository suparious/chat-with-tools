# DuckDuckGo Search Package Migration Fix

## Issue
The `duckduckgo_search` package has been renamed to `ddgs`. Using the old package name generates a deprecation warning:
```
RuntimeWarning: This package (`duckduckgo_search`) has been renamed to `ddgs`! Use `pip install ddgs` instead.
```

## Solution Applied

### 1. Updated Import Statements
Modified both search tool files to use the new package with backward compatibility:

**Files Updated:**
- `/src/chat_with_tools/tools/search_tool.py`
- `/src/chat_with_tools/tools/search_tool_enhanced.py`

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

This approach:
- First tries to import from the new `ddgs` package
- Falls back to the old `duckduckgo_search` if the new one isn't available
- Provides a clear error message if neither is installed

### 2. Updated Dependencies
Changed package requirements in both configuration files:

**Files Updated:**
- `requirements.txt`: Changed from `duckduckgo-search>=3.9.0` to `ddgs>=0.1.0`
- `pyproject.toml`: Changed from `duckduckgo-search>=3.9.0` to `ddgs>=0.1.0`

### 3. Created Migration Script
Added `migrate_ddgs.py` to help with the transition:
- Checks which packages are installed
- Offers to install the new package
- Offers to uninstall the old package
- Provides clear status and instructions

## How to Apply the Fix

### Option 1: Using uv (Recommended)
```bash
cd /home/shaun/repos/chat-with-tools
uv pip install ddgs
uv pip uninstall duckduckgo-search
```

### Option 2: Using the Migration Script
```bash
cd /home/shaun/repos/chat-with-tools
python migrate_ddgs.py
```

### Option 3: Manual Update
```bash
cd /home/shaun/repos/chat-with-tools
pip uninstall -y duckduckgo-search
pip install ddgs
```

### Option 4: Full Dependency Update
```bash
cd /home/shaun/repos/chat-with-tools
pip install -r requirements.txt --upgrade
```

## Verification

After applying the fix, test that the search tools work:

1. **Quick Test:**
   ```python
   from ddgs import DDGS
   ddgs = DDGS()
   results = ddgs.text("test query", max_results=2)
   print(f"Search working: {len(results)} results found")
   ```

2. **Full Test:**
   ```bash
   uv run python main.py
   # Select option 1 (Single Agent Chat)
   # Ask the agent to search for something
   ```

The warning should no longer appear, and search functionality should work normally.

## Benefits of the Migration

1. **No More Warnings**: Eliminates the deprecation warning
2. **Future Compatibility**: Uses the actively maintained package
3. **Backward Compatibility**: Code still works if old package is installed
4. **Same API**: The DDGS class interface remains the same

## Technical Details

The package rename doesn't change the API - only the package name changed:
- Old: `pip install duckduckgo-search` → `from duckduckgo_search import DDGS`
- New: `pip install ddgs` → `from ddgs import DDGS`

The functionality and class methods remain identical, making this a simple drop-in replacement.

## Troubleshooting

If you encounter issues:

1. **Import Error**: Make sure the new package is installed:
   ```bash
   pip install ddgs
   ```

2. **Search Not Working**: Verify the package is working:
   ```python
   python -c "from ddgs import DDGS; print('✅ Package imported successfully')"
   ```

3. **Conflicts**: If both packages are installed, uninstall the old one:
   ```bash
   pip uninstall -y duckduckgo-search
   ```

4. **Version Issues**: Make sure you have the latest version:
   ```bash
   pip install --upgrade ddgs
   ```

## Notes

- The API remains completely compatible - no code changes needed beyond imports
- The fallback import ensures the code works during the transition period
- Once all environments are updated, the fallback can be removed
- The `ddgs` package is the official successor and is actively maintained
