---
title: Chat with Tools Framework Documentation
tags: [documentation, index, navigation]
created: 2025-09-13
updated: 2025-09-13
status: active
---

# Chat with Tools Framework Documentation

Welcome to the comprehensive documentation for the Chat with Tools framework - a powerful multi-agent system with tool integration capabilities.

## 📚 Documentation Structure

### 🏗️ [[architecture/index|Architecture]]
- [[architecture/repository-structure|Repository and Package Structure]]
- [[architecture/development-flow|Development Flow and Architecture]]
- [[architecture/system-overview|System Overview]]
- [[architecture/adrs/index|Architecture Decision Records]]

### 📖 [[guides/index|Guides]]
- [[guides/getting-started/index|Getting Started]]
- [[guides/development/index|Development Setup]]
- [[guides/deployment/index|Deployment Guides]]
- [[guides/troubleshooting/index|Troubleshooting]]
- [[guides/migration/index|Migration Guides]]

### 🔧 [[components/index|Components]]
- [[components/agent|Agent System]]
- [[components/orchestrator|Task Orchestrator]]
- [[components/tools/index|Tools Documentation]]
- [[components/config-manager|Configuration Management]]

### 📚 [[references/index|References]]
- [[references/api|API Reference]]
- [[references/dependencies|Dependencies]]
- [[references/changelog|Changelog]]
- [[references/glossary|Glossary]]

## 🚀 Quick Start

1. **Installation**
   ```bash
   pip install chat-with-tools
   ```

2. **Basic Usage**
   ```python
   from chat_with_tools import OpenRouterAgent
   
   agent = OpenRouterAgent()
   response = agent.chat("Hello, how can you help me?")
   ```

3. **Run the Framework**
   ```bash
   chat-with-tools  # Interactive menu
   cwt chat        # CLI mode
   ```

## 📂 Project Structure

```
chat-with-tools/
├── src/chat_with_tools/    # Core package
├── demos/                  # Development demos
├── docs/                   # This documentation
├── tests/                  # Test suite
└── config/                 # Configuration templates
```

## 🛠️ Development

For development setup and contribution guidelines, see:
- [[guides/development/setup|Development Setup]]
- [[guides/development/contributing|Contributing Guidelines]]
- [[guides/development/testing|Testing Guide]]

## 📊 Recent Updates

### September 13, 2025
- ✅ Fixed tool loading issues
- ✅ Consolidated search tools
- ✅ Migrated to ddgs package
- ✅ Improved error handling
- ✅ Documentation reorganization

See [[references/changelog|full changelog]] for details.

## 🔍 Finding Information

- Use Obsidian's graph view to explore connections
- Search with `[[` to find linked documents
- Check [[references/glossary|glossary]] for terminology
- Browse [[archive/index|archive]] for historical documentation

## 📝 Documentation Standards

All documentation follows:
- Obsidian-compatible markdown with wikilinks
- Consistent frontmatter metadata
- Clear navigation structure
- Cross-referenced content

## 🆘 Getting Help

- [[guides/troubleshooting/index|Troubleshooting Guide]]
- [[guides/troubleshooting/common-issues|Common Issues]]
- [[references/faq|Frequently Asked Questions]]

## 📄 License

This project is licensed under the MIT License. See [[LICENSE]] for details.

---

*This documentation is maintained using Obsidian-compatible markdown. Last updated: 2025-09-13*
