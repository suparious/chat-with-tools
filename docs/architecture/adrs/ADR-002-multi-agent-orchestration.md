---
title: ADR-002 - Multi-Agent Orchestration with Parallel Execution
tags: [adr, architecture, orchestration, multi-agent]
created: 2024-12-30
updated: 2024-12-30
status: accepted
---

# ADR-002: Multi-Agent Orchestration with Parallel Execution

## Status
Accepted

## Date
2024-12-01

## Context

To emulate Grok's "heavy mode" deep thinking capabilities, we needed a system that could analyze complex queries from multiple perspectives simultaneously. Single-agent approaches were limited in their ability to provide comprehensive analysis, especially for multifaceted questions. We needed:

- Multiple agents working on different aspects of a problem
- Parallel execution for performance
- Coordination between agents
- Synthesis of multiple perspectives
- Real-time progress tracking

## Decision

We implemented a multi-agent orchestration system using:
1. **ThreadPoolExecutor** for parallel agent execution
2. **AI-driven question decomposition** to generate specialized sub-questions
3. **Shared state management** with thread locks for progress tracking
4. **Synthesis agent** to combine all responses into a unified answer
5. **Visual progress display** showing real-time agent status

## Rationale

### Considered Alternatives

1. **Sequential Agent Processing**: Run agents one after another
   - Pros: Simple, no concurrency issues
   - Cons: Slow, doesn't leverage parallel processing

2. **Async/Await Pattern**: Use asyncio for concurrent execution
   - Pros: More efficient than threads, better for I/O bound tasks
   - Cons: More complex, requires async throughout codebase

3. **Message Queue System**: Use RabbitMQ/Celery for distributed execution
   - Pros: Scalable, fault-tolerant
   - Cons: Over-engineered for current needs, adds infrastructure complexity

4. **Process Pool**: Use multiprocessing instead of threads
   - Pros: True parallelism, better for CPU-bound tasks
   - Cons: Higher overhead, complex inter-process communication

### Why ThreadPoolExecutor

- **Simplicity**: Easy to implement and understand
- **Adequate Performance**: I/O bound (API calls), threads are sufficient
- **Shared Memory**: Easy to share state between agents
- **Python GIL**: Not an issue for I/O bound operations
- **Future Migration Path**: Can move to async or distributed later if needed

## Consequences

### Positive
- 4+ agents can analyze queries simultaneously
- Response time only slightly longer than single agent
- Each agent can focus on specific aspects
- Progress tracking enables better UX
- Synthesis provides comprehensive answers

### Negative
- Thread management adds complexity
- Potential for race conditions (mitigated with locks)
- Fixed thread pool size may not be optimal for all queries
- Synthesis quality depends on individual agent outputs

### Neutral
- Requires more API calls (cost consideration)
- Thread pool size needs tuning based on API rate limits
- Progress tracking adds slight overhead

## Implementation Notes

Key implementation details:
```python
# In orchestrator.py
with ThreadPoolExecutor(max_workers=num_agents) as executor:
    futures = []
    for i, question in enumerate(questions):
        future = executor.submit(run_agent, question, agent_id=i)
        futures.append(future)
    
    # Wait for all agents to complete
    results = [future.result() for future in futures]
```

Progress tracking via shared dictionary:
```python
progress = {
    'agent_0': 'working',
    'agent_1': 'complete',
    # ...
}
```

## Configuration

```yaml
orchestrator:
  parallel_agents: 4       # Number of parallel agents
  task_timeout: 300       # Timeout per agent (seconds)
  synthesis_model: null   # Use same model as agents
```

## Future Improvements

- Dynamic agent allocation based on query complexity
- Async implementation for better scalability
- Distributed execution for cloud deployment
- Adaptive timeout based on query type
- Agent specialization (research, analysis, verification, etc.)

## References

- Implementation: [[components/orchestrator/overview]]
- Council Mode: [[guides/getting-started/council-mode]]
- Source: [[archive/agent-summaries-2024-12/technical-handover-document]]
- Related: [[architecture/adrs/ADR-001-plugin-tool-architecture]]