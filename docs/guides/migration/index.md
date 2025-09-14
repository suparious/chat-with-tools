---
title: Migration Guides
tags: [migration, upgrades, index]
created: 2025-09-13
updated: 2025-09-13
status: active
---

# Migration Guides

Guides for migrating between versions and handling breaking changes.

## Package Migrations

### [[ddgs-migration|DuckDuckGo Search Package Migration]]
Migration from `duckduckgo-search` to `ddgs` package.

**Status**: ✅ Completed (September 13, 2025)

**Key Changes**:
- Package renamed from `duckduckgo-search` to `ddgs`
- Backward compatibility maintained
- No API changes required

## Version Migrations

### v0.1.0 Initial Release
First official release with:
- Package structure finalized
- Entry points configured
- Tools consolidated
- Documentation organized

## Breaking Changes

### Tool Consolidation
- `search_tool_enhanced.py` merged into `search_tool.py`
- All enhanced features now default
- No configuration changes needed

## Migration Best Practices

1. **Test in Development First**
   ```bash
   pip install -e .
   python test_imports.py
   ```

2. **Update Dependencies**
   ```bash
   pip install -r requirements.txt --upgrade
   ```

3. **Verify Tool Loading**
   ```bash
   python test_tool_loading.py
   ```

4. **Check Configuration**
   - Review config.yaml for deprecated options
   - Update API keys if needed

## Upcoming Changes

- No breaking changes planned
- Continuous backward compatibility

## Related Documentation

- [[../troubleshooting/index|Troubleshooting]]
- [[../../references/changelog|Changelog]]
- [[../development/index|Development Guides]]

---

Parent: [[../index|Guides]] | [[../../README|Documentation Home]]
