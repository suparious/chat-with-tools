#!/usr/bin/env python3
"""
Standalone Demo Script for Chat with Tools Framework New Tools
This version tests tools directly without requiring OpenRouter/OpenAI.
"""

import json
import sys
import os
import traceback
from pathlib import Path
from datetime import datetime

# Add project to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import tools directly
from src.tools.sequential_thinking_tool import SequentialThinkingTool
from src.tools.memory_tool import MemoryTool
from src.tools.python_executor_tool import PythonExecutorTool
from src.tools.summarization_tool import SummarizationTool


def print_section(title, emoji="📌"):
    """Print a formatted section header."""
    print(f"\n{emoji} {title}")
    print("-" * 50)


def demo_sequential_thinking():
    """Comprehensive demo of the sequential thinking tool."""
    print("\n" + "="*60)
    print("🧠 SEQUENTIAL THINKING TOOL DEMO")
    print("="*60)
    
    try:
        tool = SequentialThinkingTool({})
        
        # Start a thinking session
        print_section("Starting New Thinking Session", "🚀")
        result = tool.execute(
            action="start",
            problem="How to optimize database query performance in a high-traffic application?"
        )
        session_id = result.get("session_id")
        print(f"✅ Session started: {session_id}")
        print(f"📝 Problem: {result.get('problem')}")
        
        # Add analysis thoughts
        print_section("Adding Analysis Thoughts", "💭")
        
        thought1 = tool.execute(
            action="think",
            thought="First, I need to identify the current bottlenecks. Common issues include missing indexes, N+1 queries, and inefficient joins.",
            thought_type="analysis",
            confidence=0.9,
            session_id=session_id
        )
        print(f"✅ Thought #{thought1['thought']['thought_number']}: Added analysis")
        
        thought2 = tool.execute(
            action="think",
            thought="What specific metrics should we monitor to identify slow queries?",
            thought_type="question",
            confidence=1.0,
            session_id=session_id
        )
        print(f"✅ Thought #{thought2['thought']['thought_number']}: Added question")
        
        thought3 = tool.execute(
            action="think",
            thought="We should monitor query execution time, rows examined vs rows returned, and cache hit rates.",
            thought_type="analysis",
            confidence=0.85,
            session_id=session_id
        )
        print(f"✅ Thought #{thought3['thought']['thought_number']}: Added analysis")
        
        thought4 = tool.execute(
            action="think",
            thought="Implementing query result caching with Redis could significantly reduce database load.",
            thought_type="hypothesis",
            confidence=0.8,
            session_id=session_id
        )
        print(f"✅ Thought #{thought4['thought']['thought_number']}: Added hypothesis")
        
        # Revise a thought
        print_section("Revising Previous Thought", "✏️")
        revision = tool.execute(
            action="revise",
            thought="Actually, we should implement a multi-layer caching strategy: Redis for hot data, and application-level caching for frequently accessed computed results.",
            revises_thought_number=4,
            confidence=0.95,
            session_id=session_id
        )
        print(f"✅ Revised thought #{revision['original_thought']['thought_number']}")
        print(f"   Original confidence: {revision['original_thought']['confidence']}")
        print(f"   New confidence: {revision['revision']['confidence']}")
        
        # Create a branch for alternative approach
        print_section("Creating Alternative Branch", "🌿")
        branch = tool.execute(
            action="branch",
            thought="Instead of caching, we could consider database sharding and read replicas for horizontal scaling.",
            branch_from_thought=3,
            branch_name="scaling_approach",
            confidence=0.75,
            session_id=session_id
        )
        print(f"✅ Created branch: {branch['branch_name']}")
        print(f"   Total branches: {branch['total_branches']}")
        
        # Get current summary
        print_section("Current Session Summary", "📊")
        summary = tool.execute(
            action="get_summary",
            session_id=session_id
        )
        for key, value in summary['summary'].items():
            print(f"   {key}: {value}")
        
        # Add conclusion
        print_section("Adding Conclusion", "🎯")
        conclusion = tool.execute(
            action="conclude",
            thought="To optimize database performance: 1) Add missing indexes on frequently queried columns, 2) Implement multi-layer caching with Redis and application cache, 3) Use query profiling to identify slow queries, 4) Consider read replicas for read-heavy workloads, 5) Implement connection pooling.",
            session_id=session_id
        )
        
        print("\n📈 Thinking Process Insights:")
        insights = conclusion.get('insights', {})
        print(f"   Thinking style: {insights.get('thinking_style', 'unknown')}")
        print(f"   Average confidence: {insights.get('average_confidence', 0)}")
        print(f"   Revision rate: {insights.get('revision_rate', 0)}")
        print(f"   Branches explored: {insights.get('branches_explored', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in sequential thinking demo: {e}")
        traceback.print_exc()
        return False


def demo_memory_tool():
    """Comprehensive demo of the memory tool."""
    print("\n" + "="*60)
    print("💾 MEMORY TOOL DEMO")
    print("="*60)
    
    try:
        tool = MemoryTool({"memory": {"storage_path": "./agent_memory_demo"}})
        
        # Store various types of memories
        print_section("Storing Different Memory Types", "💾")
        
        memories_to_store = [
            {
                "content": "The Chat with Tools framework was created to emulate Grok's heavy mode functionality with multi-agent analysis.",
                "memory_type": "fact",
                "tags": ["framework", "origin", "grok", "architecture"]
            },
            {
                "content": "Users prefer comprehensive, multi-perspective responses that consider different angles of their queries.",
                "memory_type": "preference",
                "tags": ["users", "responses", "quality"]
            },
            {
                "content": "Successfully debugged a race condition in the parallel agent execution by implementing proper thread locks.",
                "memory_type": "experience",
                "tags": ["debugging", "threading", "parallel", "agents"]
            },
            {
                "content": "Always validate user input before processing to prevent injection attacks and ensure data integrity.",
                "memory_type": "instruction",
                "tags": ["security", "validation", "best-practice"]
            },
            {
                "content": "Current project focus is on implementing new tools: sequential thinking, memory, code execution, and summarization.",
                "memory_type": "context",
                "tags": ["project", "current", "tools", "development"]
            }
        ]
        
        stored_ids = []
        for mem_data in memories_to_store:
            result = tool.execute(action="store", **mem_data)
            memory_id = result.get('memory_id')
            stored_ids.append(memory_id)
            print(f"✅ Stored [{mem_data['memory_type']}]: {memory_id}")
        
        # Search memories by query
        print_section("Searching Memories by Query", "🔍")
        
        search_queries = ["agents", "security", "tools"]
        for query in search_queries:
            result = tool.execute(
                action="search",
                query=query,
                limit=5
            )
            print(f"\n📝 Query: '{query}' - Found {result.get('count', 0)} results")
            for mem in result.get("results", [])[:2]:
                print(f"   • [{mem['type']}] {mem['summary'][:60]}...")
        
        # Search by tags
        print_section("Searching Memories by Tags", "🏷️")
        
        tag_result = tool.execute(
            action="search",
            tags=["framework", "architecture"],
            limit=5
        )
        print(f"Found {tag_result.get('count', 0)} memories with tags 'framework' or 'architecture'")
        for mem in tag_result.get("results", []):
            print(f"   • {mem['summary'][:60]}...")
        
        # Search by type
        print_section("Searching Memories by Type", "📁")
        
        type_result = tool.execute(
            action="search",
            memory_type="instruction",
            limit=5
        )
        print(f"Found {type_result.get('count', 0)} instruction-type memories")
        for mem in type_result.get("results", []):
            print(f"   • {mem['summary'][:60]}...")
        
        # Retrieve specific memory
        print_section("Retrieving Specific Memory", "📖")
        
        if stored_ids:
            specific_result = tool.execute(
                action="retrieve",
                memory_id=stored_ids[0]
            )
            if specific_result.get("status") == "retrieved":
                memory = specific_result["memory"]
                print(f"Retrieved memory: {memory['id']}")
                print(f"   Content: {memory['content'][:100]}...")
                print(f"   Created: {memory['created_at']}")
                print(f"   Accessed: {memory['accessed_count']} times")
        
        # Get statistics
        print_section("Memory Statistics", "📊")
        
        stats_result = tool.execute(action="stats")
        stats = stats_result.get("statistics", {})
        print(f"   Total memories: {stats.get('total_memories', 0)}")
        print(f"   Memory types: {stats.get('memory_types', {})}")
        print(f"   Total tags: {stats.get('total_tags', 0)}")
        print(f"   Popular tags: {stats.get('popular_tags', [])[:5]}")
        
        # Delete a memory
        print_section("Memory Management", "🗑️")
        
        if stored_ids and len(stored_ids) > 1:
            delete_result = tool.execute(
                action="forget",
                memory_id=stored_ids[-1]
            )
            print(f"Deleted memory: {delete_result.get('message', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in memory demo: {e}")
        traceback.print_exc()
        return False


def demo_python_executor():
    """Comprehensive demo of the Python executor tool."""
    print("\n" + "="*60)
    print("🐍 PYTHON EXECUTOR TOOL DEMO")
    print("="*60)
    
    try:
        tool = PythonExecutorTool({"code_execution": {"timeout": 5, "max_memory_mb": 100}})
        
        # Mathematical calculations
        print_section("Mathematical Calculations", "📐")
        
        math_code = """
import math

# Calculate various mathematical operations
radius = 7
circle_area = math.pi * radius ** 2
circle_circumference = 2 * math.pi * radius

# Fibonacci sequence
def fibonacci(n):
    a, b = 0, 1
    fib_sequence = []
    for _ in range(n):
        fib_sequence.append(a)
        a, b = b, a + b
    return fib_sequence

fib_10 = fibonacci(10)

print(f"Circle with radius {radius}:")
print(f"  Area: {circle_area:.2f}")
print(f"  Circumference: {circle_circumference:.2f}")
print(f"\\nFirst 10 Fibonacci numbers: {fib_10}")

# Return results as dict
{"circle_area": circle_area, "fibonacci_10": fib_10}
"""
        
        result = tool.execute(code=math_code, description="Mathematical calculations")
        if result["status"] == "success":
            print("✅ Execution successful!")
            print(f"Output:\n{result['output']}")
            if result.get('result'):
                print(f"Returned value: {result['result']}")
        else:
            print(f"❌ Error: {result.get('error')}")
        
        # Data analysis with statistics
        print_section("Statistical Analysis", "📊")
        
        stats_code = """
import statistics
import random

# Generate sample data
random.seed(42)
data = [random.gauss(100, 15) for _ in range(100)]

# Calculate various statistics
mean = statistics.mean(data)
median = statistics.median(data)
stdev = statistics.stdev(data)
q1 = statistics.quantiles(data, n=4)[0]
q3 = statistics.quantiles(data, n=4)[2]

# Find outliers (values beyond 1.5*IQR)
iqr = q3 - q1
lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr
outliers = [x for x in data if x < lower_bound or x > upper_bound]

print("Dataset Statistics:")
print(f"  Count: {len(data)}")
print(f"  Mean: {mean:.2f}")
print(f"  Median: {median:.2f}")
print(f"  Std Dev: {stdev:.2f}")
print(f"  Q1: {q1:.2f}, Q3: {q3:.2f}")
print(f"  IQR: {iqr:.2f}")
print(f"  Outliers: {len(outliers)} values")
print(f"  Range: [{min(data):.2f}, {max(data):.2f}]")

{"mean": mean, "median": median, "stdev": stdev, "outlier_count": len(outliers)}
"""
        
        result = tool.execute(code=stats_code, description="Statistical analysis of random data")
        if result["status"] == "success":
            print("✅ Execution successful!")
            print(f"Output:\n{result['output']}")
            print(f"Execution time: {result['execution_time']} seconds")
        else:
            print(f"❌ Error: {result.get('error')}")
        
        # String processing and regex
        print_section("Text Processing", "📝")
        
        text_code = """
import re
from collections import Counter

text = '''
The Chat with Tools framework is an innovative solution for multi-agent AI systems.
It leverages parallel processing with 4 agents by default, each with access to 10+ tools.
The framework has been tested with over 1000 queries and achieves 95% user satisfaction.
Version 2.0 will include vector databases and improved error handling.
'''

# Extract numbers
numbers = re.findall(r'\\d+(?:\\.\\d+)?', text)
print(f"Numbers found: {numbers}")

# Extract capitalized words (potential entities)
entities = re.findall(r'\\b[A-Z][a-z]+(?:\\s+[A-Z][a-z]+)*\\b', text)
print(f"\\nPotential entities: {entities}")

# Word frequency analysis
words = re.findall(r'\\b[a-z]+\\b', text.lower())
word_freq = Counter(words)
top_words = word_freq.most_common(5)
print(f"\\nTop 5 words: {top_words}")

# Sentence analysis
sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
print(f"\\nNumber of sentences: {len(sentences)}")
avg_words_per_sentence = len(words) / len(sentences)
print(f"Average words per sentence: {avg_words_per_sentence:.1f}")

{"numbers": numbers, "entities": entities, "top_words": dict(top_words)}
"""
        
        result = tool.execute(code=text_code, description="Text analysis with regex")
        if result["status"] == "success":
            print("✅ Execution successful!")
            print(f"Output:\n{result['output']}")
        else:
            print(f"❌ Error: {result.get('error')}")
        
        # Test error handling
        print_section("Error Handling Test", "⚠️")
        
        error_code = """
# This should trigger a timeout
import time
print("Starting infinite loop test...")
while True:
    pass
"""
        
        result = tool.execute(code=error_code, description="Testing timeout protection")
        if result["status"] == "timeout":
            print("✅ Timeout protection worked!")
            print(f"   Error: {result.get('error')}")
        else:
            print(f"❌ Unexpected result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in Python executor demo: {e}")
        traceback.print_exc()
        return False


def demo_summarization_tool():
    """Comprehensive demo of the summarization tool."""
    print("\n" + "="*60)
    print("📄 SUMMARIZATION TOOL DEMO")
    print("="*60)
    
    try:
        tool = SummarizationTool({})
        
        # Long sample text for testing
        long_text = """
        The Chat with Tools framework represents a paradigm shift in how we approach multi-agent AI systems.
        Traditional single-agent systems often struggle with complex queries that require diverse perspectives.
        By employing multiple specialized agents working in parallel, the framework achieves unprecedented depth.
        
        Each agent in the system operates independently with its own set of tools and capabilities.
        The first agent might focus on data analysis and mathematical computations.
        The second agent could specialize in research and information gathering from various sources.
        The third agent might handle code generation and technical implementation details.
        The fourth agent typically synthesizes information from all other agents into coherent responses.
        
        The orchestrator component is the brain of the entire operation.
        It receives user queries and intelligently distributes subtasks to appropriate agents.
        The orchestrator uses advanced natural language processing to understand query intent.
        It then formulates specific questions for each agent to maximize information coverage.
        After agents complete their tasks, the orchestrator combines their outputs intelligently.
        
        Tool discovery is another innovative feature of the framework.
        Instead of hardcoding tool integrations, the system automatically discovers available tools.
        New tools can be added simply by placing them in the designated directory.
        Each tool follows a standardized interface, making integration seamless.
        This plugin-like architecture ensures the framework remains extensible and maintainable.
        
        Performance optimization has been a key focus area in recent updates.
        The framework now implements connection pooling for external API calls.
        Retry mechanisms with exponential backoff handle transient failures gracefully.
        Caching layers reduce redundant computations and API calls significantly.
        These optimizations have resulted in 40% faster response times on average.
        
        Security considerations are built into the framework's core design.
        All user inputs undergo rigorous validation to prevent injection attacks.
        The Python executor tool runs code in a sandboxed environment with resource limits.
        Sensitive data is encrypted both in transit and at rest.
        Regular security audits ensure the framework maintains high security standards.
        """
        
        # Get text statistics
        print_section("Text Statistics Analysis", "📊")
        
        stats_result = tool.execute(action="statistics", text=long_text)
        stats = stats_result.get("statistics", {})
        
        print("Original Text Metrics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # Create summaries with different ratios
        print_section("Extractive Summarization", "✂️")
        
        ratios = [0.2, 0.4, 0.6]
        for ratio in ratios:
            summary_result = tool.execute(
                action="summarize",
                text=long_text,
                ratio=ratio,
                min_sentences=2
            )
            
            if summary_result.get("status") == "summarized":
                print(f"\n📌 Summary at {int(ratio*100)}% retention:")
                print(f"   Length: {summary_result['summary_length']} chars " +
                      f"(reduced by {summary_result['reduction_percentage']}%)")
                print(f"   Summary: {summary_result['summary'][:200]}...")
        
        # Extract key points
        print_section("Key Points Extraction", "🎯")
        
        for num_points in [3, 5]:
            points_result = tool.execute(
                action="key_points",
                text=long_text,
                num_points=num_points
            )
            
            if points_result.get("status") == "extracted":
                print(f"\n📍 Top {num_points} Key Points:")
                for i, point in enumerate(points_result.get("key_points", []), 1):
                    # Truncate long points for display
                    display_point = point[:100] + "..." if len(point) > 100 else point
                    print(f"   {i}. {display_point}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in summarization demo: {e}")
        traceback.print_exc()
        return False


def run_comprehensive_test():
    """Run all demos and provide a comprehensive report."""
    print("\n" + "="*60)
    print("   🚀 COMPREHENSIVE TOOL TEST SUITE")
    print("="*60)
    print(f"\n📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📦 Testing 4 new tools for Chat with Tools Framework")
    
    # Track results
    results = {
        "Sequential Thinking": False,
        "Memory": False,
        "Python Executor": False,
        "Summarization": False
    }
    
    # Run each demo
    demos = [
        ("Sequential Thinking", demo_sequential_thinking),
        ("Memory", demo_memory_tool),
        ("Python Executor", demo_python_executor),
        ("Summarization", demo_summarization_tool)
    ]
    
    for name, demo_func in demos:
        print(f"\n{'='*60}")
        print(f"Testing: {name}")
        print('='*60)
        
        try:
            success = demo_func()
            results[name] = success
        except Exception as e:
            print(f"❌ Fatal error in {name}: {e}")
            results[name] = False
    
    # Print summary report
    print("\n" + "="*60)
    print("   📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    print(f"📈 Success Rate: {(passed/total)*100:.1f}%")
    
    print("\n📋 Individual Results:")
    for tool_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {tool_name:20} {status}")
    
    if passed == total:
        print("\n🎉 All tools are working correctly!")
    else:
        print("\n⚠️  Some tools need attention. Check the output above for details.")
    
    return results


def interactive_menu():
    """Interactive menu for testing individual tools."""
    while True:
        print("\n" + "="*60)
        print("   🎮 INTERACTIVE TOOL TESTING")
        print("="*60)
        print("\n1. Sequential Thinking Tool")
        print("2. Memory Tool")
        print("3. Python Executor Tool")
        print("4. Summarization Tool")
        print("5. Run All Tests")
        print("6. Run Comprehensive Test Suite")
        print("7. Exit")
        
        choice = input("\nSelect option (1-7): ").strip()
        
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
        elif choice == "6":
            run_comprehensive_test()
        elif choice == "7":
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-7.")


def main():
    """Main entry point."""
    print("\n" + "="*60)
    print("   🚀 CHAT WITH TOOLS - STANDALONE DEMO")
    print("="*60)
    print("\nThis demo tests all new tools without requiring OpenRouter/OpenAI")
    print("Tools: Sequential Thinking, Memory, Python Executor, Summarization")
    
    print("\n" + "-"*40)
    print("Select mode:")
    print("1. Interactive Menu")
    print("2. Run Comprehensive Test Suite")
    print("3. Quick Test (one demo of each tool)")
    
    mode = input("\nChoice (1-3): ").strip()
    
    if mode == "1":
        interactive_menu()
    elif mode == "2":
        run_comprehensive_test()
    elif mode == "3":
        print("\n🎬 Running quick test...")
        demo_sequential_thinking()
        demo_memory_tool()
        demo_python_executor()
        demo_summarization_tool()
        print("\n✅ Quick test completed!")
    else:
        print("❌ Invalid choice. Running interactive menu...")
        interactive_menu()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        traceback.print_exc()
