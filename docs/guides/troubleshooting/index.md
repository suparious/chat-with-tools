---
title: Troubleshooting Guide
tags: [troubleshooting, index, fixes]
created: 2025-09-13
updated: 2025-09-13
status: active
---

# Troubleshooting Guide

Solutions to common issues and problems with the Chat with Tools framework.

## Recent Issues and Fixes

- [[recent-fixes|Recent Fixes (September 13, 2025)]] - Latest bug fixes and improvements
- [[tool-loading-fix|Tool Loading Fix]] - Resolving tool discovery issues

## Common Issues

### Installation Problems
- Missing dependencies
- Version conflicts
- Package installation errors

### Configuration Issues
- API key warnings
- Config file location
- Environment variables

### Tool-Related Problems
- Tools not loading
- Tool execution errors
- Argument parsing issues

### Agent Issues
- Connection errors
- Response formatting
- Memory problems

## Debug Techniques

### Enable Debug Mode
```python
agent = OpenRouterAgent(debug=True, silent=False)
```

### Check Tool Loading
```bash
python test_tool_loading.py
```

### Verify Imports
```bash
python test_imports.py
```

## Getting Help

1. Check the logs for detailed error messages
2. Run test scripts to isolate issues
3. Review recent fixes for similar problems
4. Check configuration settings

## Related Resources

- [[../migration/index|Migration Guides]]
- [[../development/testing|Testing Guide]]
- [[../../references/changelog|Changelog]]

---

Parent: [[../index|Guides]] | [[../../README|Documentation Home]]
