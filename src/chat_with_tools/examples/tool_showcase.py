"""
Tool Showcase Example

Interactive demonstration of available tools without requiring API access.
"""

import json
import traceback
from typing import Dict, Any
from ..tools import discover_tools


def run_tool_showcase():
    """Run interactive tool testing interface."""
    print("\n" + "="*60)
    print("   🛠️  TOOL SHOWCASE")
    print("="*60)
    print("\nTest individual tools without requiring API access")
    print("Perfect for understanding tool capabilities\n")
    
    # Discover available tools
    try:
        tools = discover_tools(silent=True)
        print(f"✅ Discovered {len(tools)} tools")
    except Exception as e:
        print(f"❌ Error discovering tools: {e}")
        return
    
    while True:
        print("\n" + "-"*60)
        print("Available Tools:")
        print("-"*60)
        
        tool_list = list(tools.keys())
        for i, tool_name in enumerate(tool_list, 1):
            tool = tools[tool_name]
            desc_lines = tool.description.split('\n')
            short_desc = desc_lines[0] if desc_lines else "No description"
            print(f"{i}. {tool_name}: {short_desc[:50]}...")
        
        print(f"\n0. Exit Tool Showcase")
        
        try:
            choice = input("\nSelect a tool to test (0-{}): ".format(len(tool_list))).strip()
            
            if choice == "0":
                print("\n👋 Exiting Tool Showcase")
                break
            
            try:
                tool_index = int(choice) - 1
                if 0 <= tool_index < len(tool_list):
                    selected_tool_name = tool_list[tool_index]
                    selected_tool = tools[selected_tool_name]
                    test_tool(selected_tool)
                else:
                    print("❌ Invalid selection")
            except ValueError:
                print("❌ Please enter a number")
                
        except KeyboardInterrupt:
            print("\n\n👋 Tool Showcase interrupted")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def test_tool(tool):
    """Test a specific tool interactively."""
    print("\n" + "="*60)
    print(f"   Testing: {tool.name}")
    print("="*60)
    print(f"\nDescription: {tool.description}")
    
    # Show parameters
    params = tool.parameters.get('properties', {})
    required = tool.parameters.get('required', [])
    
    print("\nParameters:")
    for param_name, param_info in params.items():
        param_type = param_info.get('type', 'unknown')
        param_desc = param_info.get('description', 'No description')
        required_marker = " (required)" if param_name in required else " (optional)"
        print(f"  - {param_name} [{param_type}]{required_marker}: {param_desc}")
    
    print("\n" + "-"*40)
    print("Enter parameters as JSON, or 'back' to return to tool list")
    print("Example: {\"query\": \"test search\", \"limit\": 5}")
    print("-"*40)
    
    while True:
        try:
            user_input = input("\nParameters (JSON or 'back'): ").strip()
            
            if user_input.lower() == 'back':
                break
            
            if not user_input:
                print("Please enter parameters or 'back'")
                continue
            
            # Parse parameters
            try:
                params = json.loads(user_input)
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON: {e}")
                continue
            
            # Execute tool
            print("\n🔄 Executing tool...")
            try:
                result = tool.execute(**params)
                
                print("\n✅ Tool executed successfully!")
                print("Result:")
                print("-"*40)
                
                # Pretty print the result
                if isinstance(result, dict):
                    print(json.dumps(result, indent=2, default=str))
                else:
                    print(result)
                    
            except Exception as e:
                print(f"\n❌ Tool execution failed: {e}")
                traceback.print_exc()
            
            # Ask if they want to test again
            again = input("\nTest this tool again? (y/n): ").strip().lower()
            if again != 'y':
                break
                
        except KeyboardInterrupt:
            print("\n\nReturning to tool list...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    run_tool_showcase()
