---
title: Architecture Documentation
tags: [architecture, index, navigation]
created: 2025-09-13
updated: 2025-09-13
status: active
---

# Architecture Documentation

This section contains architectural documentation for the Chat with Tools framework, including system design, structure, and key decisions.

## Core Architecture

- [[repository-structure|Repository and Package Structure]] - Dual structure design for development and distribution
- [[development-flow|Development Flow and Architecture]] - How development files work with the package
- [[system-overview|System Overview]] - High-level architecture overview

## Architecture Decision Records (ADRs)

[[adrs/index|View all ADRs →]]

Document key architectural decisions with context, rationale, and consequences.

## Key Concepts

### Single Source of Truth
All code logic resides in `src/chat_with_tools/`, with development files serving as thin wrappers for testing and debugging.

### Development vs Distribution
- **Development**: Rich testing environment with debug features
- **Distribution**: Clean, self-contained package for end users

### Tool Architecture
Modular tool system with dynamic discovery and loading capabilities.

## Diagrams

Architecture diagrams showing:
- Component relationships
- Data flow
- Tool integration points
- Multi-agent orchestration

## Related Documentation

- [[guides/development/setup|Development Setup]]
- [[components/index|Component Documentation]]
- [[references/api|API Reference]]

---

Parent: [[../README|Documentation Home]]
