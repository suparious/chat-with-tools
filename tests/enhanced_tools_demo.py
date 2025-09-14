#!/usr/bin/env python3
"""
Example script demonstrating the new enhanced tools in the Chat with Tools framework.
"""

import sys
import os
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from chat_with_tools.agent import OpenRouterAgent
import json


def demonstrate_data_analysis():
    """Demonstrate data analysis tool."""
    print("\n" + "="*60)
    print("DATA ANALYSIS TOOL DEMO")
    print("="*60)
    
    agent = OpenRouterAgent(silent=True)
    
    # Create sample CSV data
    csv_data = """name,age,salary,department
Alice,30,75000,Engineering
Bob,25,65000,Marketing
Charlie,35,85000,Engineering
Diana,28,70000,Sales
Eve,32,80000,Engineering"""
    
    query = f"""Load this CSV data and analyze it:
{csv_data}

Then:
1. Describe the statistics
2. Find the average salary by department
3. Identify any correlations"""
    
    print(f"\nQuery: {query[:100]}...")
    print("\nAgent Response:")
    response = agent.run(query)
    print(response)


def demonstrate_database_tool():
    """Demonstrate database tool."""
    print("\n" + "="*60)
    print("DATABASE TOOL DEMO")
    print("="*60)
    
    agent = OpenRouterAgent(silent=True)
    
    query = """Create a SQLite database with a 'products' table containing:
- id (integer, primary key)
- name (text, not null)
- price (real)
- stock (integer)

Then insert these products:
- Laptop, $999.99, 10 units
- Mouse, $29.99, 50 units
- Keyboard, $79.99, 25 units

Finally, query to find all products with price less than $100."""
    
    print(f"\nQuery: {query[:100]}...")
    print("\nAgent Response:")
    response = agent.run(query)
    print(response)


def demonstrate_api_tool():
    """Demonstrate API request tool."""
    print("\n" + "="*60)
    print("API REQUEST TOOL DEMO")
    print("="*60)
    
    agent = OpenRouterAgent(silent=True)
    
    query = """Make a GET request to https://api.github.com/users/torvalds 
    and tell me about Linus Torvalds' public GitHub profile including 
    the number of public repos and followers."""
    
    print(f"\nQuery: {query}")
    print("\nAgent Response:")
    response = agent.run(query)
    print(response)


def demonstrate_combined_tools():
    """Demonstrate multiple tools working together."""
    print("\n" + "="*60)
    print("COMBINED TOOLS DEMO")
    print("="*60)
    
    agent = OpenRouterAgent(silent=True)
    
    query = """Use sequential thinking to analyze this problem step by step:
    
    I have sales data for 3 months:
    - January: $45,000
    - February: $52,000
    - March: $48,000
    
    Calculate:
    1. The total sales
    2. The average monthly sales
    3. The month-over-month growth rates
    4. Store this analysis in memory for future reference
    5. Create a summary of the findings"""
    
    print(f"\nQuery: {query[:150]}...")
    print("\nAgent Response:")
    response = agent.run(query)
    print(response)


def main():
    """Run all demonstrations."""
    print("\n🚀 ENHANCED TOOLS DEMONSTRATION")
    print("="*60)
    
    import argparse
    parser = argparse.ArgumentParser(description="Demonstrate enhanced tools")
    parser.add_argument("--tool", choices=["data", "database", "api", "combined", "all"],
                       default="all", help="Which tool demo to run")
    
    args = parser.parse_args()
    
    try:
        if args.tool == "data" or args.tool == "all":
            demonstrate_data_analysis()
        
        if args.tool == "database" or args.tool == "all":
            demonstrate_database_tool()
        
        if args.tool == "api" or args.tool == "all":
            demonstrate_api_tool()
        
        if args.tool == "combined" or args.tool == "all":
            demonstrate_combined_tools()
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("DEMO COMPLETE!")
    print("="*60)


if __name__ == "__main__":
    main()
