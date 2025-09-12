#!/usr/bin/env python3
"""
Demo script for new tools in Chat with Tools Framework

This script demonstrates the new tools:
- Sequential Thinking Tool
- Memory Tool
- Python Executor Tool
- Summarization Tool
"""

import json
import yaml
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from src.agent import OpenRouterAgent


def demo_sequential_thinking():
    """Demonstrate the sequential thinking tool."""
    print("\n" + "="*60)
    print("🧠 SEQUENTIAL THINKING TOOL DEMO")
    print("="*60)
    
    # Initialize agent
    agent = OpenRouterAgent(silent=True)
    
    # Find the sequential thinking tool
    if "sequential_thinking" not in agent.tool_mapping:
        print("❌ Sequential thinking tool not found. Make sure sequential_thinking_tool.py is in the tools/ directory")
        return
    
    tool = agent.tool_mapping["sequential_thinking"]
    
    # Start a thinking session
    print("\n📝 Starting thinking session about: 'How to make Chat with Tools better?'")
    result = tool(
        action="start",
        problem="How to make Chat with Tools framework even better?"
    )
    session_id = result.get("session_id")
    print(f"✅ Session started: {session_id}")
    
    # Add thoughts
    print("\n💭 Adding analysis thoughts...")
    tool(
        action="think",
        thought="The framework already has good architecture with agents, orchestrator, and tools.",
        thought_type="analysis",
        confidence=0.9,
        session_id=session_id
    )
    
    tool(
        action="think",
        thought="What features are missing that would make it more powerful?",
        thought_type="question",
        confidence=1.0,
        session_id=session_id
    )
    
    tool(
        action="think",
        thought="Adding persistent memory would allow agents to learn over time.",
        thought_type="hypothesis",
        confidence=0.8,
        session_id=session_id
    )
    
    # Revise a thought
    print("✏️  Revising thought #3...")
    tool(
        action="revise",
        thought="Adding persistent memory AND a vector database would enable semantic search and better learning.",
        revises_thought_number=3,
        confidence=0.95,
        session_id=session_id
    )
    
    # Branch exploration
    print("🌿 Creating alternative branch...")
    tool(
        action="branch",
        thought="Instead of memory, focus on improving tool discovery and integration.",
        branch_from_thought=2,
        branch_name="tools_focus",
        confidence=0.7,
        session_id=session_id
    )
    
    # Conclude
    print("📋 Adding conclusion...")
    conclusion_result = tool(
        action="conclude",
        thought="The framework would benefit most from: 1) Persistent memory with vector DB, 2) More sophisticated tool discovery, 3) Better error recovery mechanisms.",
        session_id=session_id
    )
    
    # Display summary
    print("\n📊 Thinking Session Summary:")
    summary = conclusion_result.get("summary", {})
    for key, value in summary.items():
        print(f"   {key}: {value}")
    
    print("\n🎯 Insights:")
    insights = conclusion_result.get("insights", {})
    for key, value in insights.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for k, v in value.items():
                print(f"      {k}: {v}")
        else:
            print(f"   {key}: {value}")


def demo_memory_tool():
    """Demonstrate the memory tool."""
    print("\n" + "="*60)
    print("🧠 MEMORY TOOL DEMO")
    print("="*60)
    
    agent = OpenRouterAgent(silent=True)
    
    if "memory" not in agent.tool_mapping:
        print("❌ Memory tool not found. Make sure memory_tool.py is in the tools/ directory")
        return
    
    tool = agent.tool_mapping["memory"]
    
    # Store memories
    print("\n💾 Storing memories...")
    
    mem1 = tool(
        action="store",
        content="The Chat with Tools framework was created to emulate Grok heavy functionality.",
        memory_type="fact",
        tags=["framework", "origin", "grok"]
    )
    print(f"✅ Stored: {mem1.get('memory_id')}")
    
    mem2 = tool(
        action="store",
        content="The framework uses parallel agents with an orchestrator for multi-perspective analysis.",
        memory_type="fact",
        tags=["architecture", "agents", "orchestrator"]
    )
    print(f"✅ Stored: {mem2.get('memory_id')}")
    
    mem3 = tool(
        action="store",
        content="Users prefer comprehensive, multi-angle responses over simple answers.",
        memory_type="preference",
        tags=["users", "responses"]
    )
    print(f"✅ Stored: {mem3.get('memory_id')}")
    
    # Search memories
    print("\n🔍 Searching memories with query 'agents'...")
    search_result = tool(
        action="search",
        query="agents"
    )
    
    print(f"Found {search_result.get('count', 0)} results:")
    for result in search_result.get("results", []):
        print(f"   - [{result['type']}] {result['summary'][:50]}...")
    
    # Get statistics
    print("\n📊 Memory Statistics:")
    stats_result = tool(action="stats")
    stats = stats_result.get("statistics", {})
    print(f"   Total memories: {stats.get('total_memories', 0)}")
    print(f"   Memory types: {stats.get('memory_types', {})}")
    print(f"   Popular tags: {stats.get('popular_tags', [])}")


def demo_python_executor():
    """Demonstrate the Python executor tool."""
    print("\n" + "="*60)
    print("🐍 PYTHON EXECUTOR TOOL DEMO")
    print("="*60)
    
    agent = OpenRouterAgent(silent=True)
    
    if "python_executor" not in agent.tool_mapping:
        print("❌ Python executor tool not found. Make sure python_executor_tool.py is in the tools/ directory")
        return
    
    tool = agent.tool_mapping["python_executor"]
    
    # Example 1: Math calculation
    print("\n📐 Mathematical Calculation:")
    result = tool(
        code="""
import math

# Calculate the area of a circle
radius = 5
area = math.pi * radius ** 2
print(f"Area of circle with radius {radius}: {area:.2f}")

# Calculate factorial
n = 10
factorial = math.factorial(n)
print(f"Factorial of {n}: {factorial}")

# Result
area
""",
        description="Circle area and factorial calculation"
    )
    
    if result["status"] == "success":
        print(f"✅ Output:\n{result['output']}")
        if result.get("result"):
            print(f"📊 Result: {result['result']}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Example 2: Data analysis
    print("\n📊 Data Analysis:")
    result = tool(
        code="""
import statistics
import random

# Generate sample data
random.seed(42)
data = [random.gauss(100, 15) for _ in range(100)]

# Calculate statistics
mean = statistics.mean(data)
median = statistics.median(data)
stdev = statistics.stdev(data)

print(f"Dataset Statistics:")
print(f"  Mean: {mean:.2f}")
print(f"  Median: {median:.2f}")
print(f"  Std Dev: {stdev:.2f}")
print(f"  Min: {min(data):.2f}")
print(f"  Max: {max(data):.2f}")

# Return summary
{"mean": mean, "median": median, "stdev": stdev}
""",
        description="Statistical analysis of random data"
    )
    
    if result["status"] == "success":
        print(f"✅ Output:\n{result['output']}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Example 3: String processing
    print("\n📝 String Processing:")
    result = tool(
        code="""
import re

text = "The Chat with Tools framework is amazing! It has 4 agents and 100% awesomeness."

# Extract numbers
numbers = re.findall(r'\\d+', text)
print(f"Numbers found: {numbers}")

# Count words
words = len(text.split())
print(f"Word count: {words}")

# Find capitalized words
capitals = re.findall(r'\\b[A-Z][a-z]+\\b', text)
print(f"Capitalized words: {capitals}")
""",
        description="Text analysis with regex"
    )
    
    if result["status"] == "success":
        print(f"✅ Output:\n{result['output']}")
    else:
        print(f"❌ Error: {result.get('error')}")


def demo_summarization_tool():
    """Demonstrate the summarization tool."""
    print("\n" + "="*60)
    print("📄 SUMMARIZATION TOOL DEMO")
    print("="*60)
    
    agent = OpenRouterAgent(silent=True)
    
    if "summarizer" not in agent.tool_mapping:
        print("❌ Summarization tool not found. Make sure summarization_tool.py is in the tools/ directory")
        return
    
    tool = agent.tool_mapping["summarizer"]
    
    # Sample text
    sample_text = """
    The Chat with Tools framework represents a significant advancement in multi-agent AI systems,
    designed to emulate the comprehensive analysis capabilities of advanced AI models like Grok's heavy mode.
    At its core, the framework employs a sophisticated orchestration system that coordinates multiple
    intelligent agents working in parallel to provide deep, multi-perspective analysis of user queries.
    
    The architecture consists of three main components: the Agent System, the Orchestrator, and the
    Tool System. The Agent System provides self-contained agents with full tool access, implementing
    an agentic loop that continues processing until task completion. Each agent can utilize various
    tools through the framework's dynamic discovery system, which automatically loads tools from the
    tools directory without requiring manual registration.
    
    The Orchestrator serves as the brain of the multi-agent system, using AI to dynamically generate
    specialized questions that approach the user's query from different angles. It manages parallel
    execution of multiple agents, typically four by default, and then synthesizes their responses
    into a comprehensive final answer. This synthesis process uses another AI call to combine the
    best information from all agents while resolving any contradictions.
    
    The Tool System provides a standardized interface for extending the framework's capabilities.
    All tools inherit from a BaseTool class and are automatically discovered at runtime. Currently
    available tools include web search using DuckDuckGo, mathematical calculations, file operations,
    and a task completion marker. The framework's hot-swappable design means new tools can be added
    simply by dropping Python files into the tools directory.
    
    Recent enhancements have focused on production-readiness, including structured logging, retry
    mechanisms with exponential backoff, connection pooling for API clients, comprehensive error
    handling, and security features like URL validation. The framework now includes a robust test
    suite and supports environment variables for secure credential management.
    """
    
    # Test summarization
    print("\n📝 Original Text Statistics:")
    stats_result = tool(action="statistics", text=sample_text)
    stats = stats_result.get("statistics", {})
    print(f"   Words: {stats.get('word_count', 0)}")
    print(f"   Sentences: {stats.get('sentence_count', 0)}")
    print(f"   Reading Level: {stats.get('reading_level', 'Unknown')}")
    
    # Create summary
    print("\n✂️  Creating Summary (30% of original)...")
    summary_result = tool(
        action="summarize",
        text=sample_text,
        ratio=0.3
    )
    
    if summary_result.get("status") == "summarized":
        print(f"\n📄 Summary:\n{summary_result['summary']}")
        print(f"\n📊 Reduction: {summary_result['reduction_percentage']}%")
    
    # Extract key points
    print("\n🎯 Extracting Key Points...")
    points_result = tool(
        action="key_points",
        text=sample_text,
        num_points=5
    )
    
    if points_result.get("status") == "extracted":
        print("\n📌 Key Points:")
        for i, point in enumerate(points_result.get("key_points", []), 1):
            print(f"   {i}. {point}")


def main():
    """Main demo function."""
    print("\n" + "="*60)
    print("   🚀 CHAT WITH TOOLS - NEW TOOLS DEMO")
    print("="*60)
    
    print("\nThis demo showcases the new tools added to the framework:")
    print("1. Sequential Thinking - Step-by-step reasoning with revisions")
    print("2. Memory - Persistent storage and retrieval")
    print("3. Python Executor - Safe code execution")
    print("4. Summarization - Text condensing and analysis")
    
    while True:
        print("\n" + "-"*40)
        print("Select a demo to run:")
        print("1. Sequential Thinking Tool")
        print("2. Memory Tool")
        print("3. Python Executor Tool")
        print("4. Summarization Tool")
        print("5. Run All Demos")
        print("6. Exit")
        
        choice = input("\nChoice (1-6): ").strip()
        
        if choice == "1":
            demo_sequential_thinking()
        elif choice == "2":
            demo_memory_tool()
        elif choice == "3":
            demo_python_executor()
        elif choice == "4":
            demo_summarization_tool()
        elif choice == "5":
            print("\n🎬 Running all demos...")
            demo_sequential_thinking()
            demo_memory_tool()
            demo_python_executor()
            demo_summarization_tool()
            print("\n✅ All demos completed!")
        elif choice == "6":
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-6.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
