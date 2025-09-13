import os
import sys
import importlib
import traceback
from typing import Dict, List
from .base_tool import BaseTool

def discover_tools(config: dict = None, silent: bool = False) -> Dict[str, BaseTool]:
    """Automatically discover and load all tools from the tools directory"""
    tools = {}
    
    # Get the tools directory path
    tools_dir = os.path.dirname(__file__)
    
    # Debug output
    if not silent:
        print(f"[DEBUG] Discovering tools in: {tools_dir}")
        print(f"[DEBUG] Current module __name__: {__name__}")
    
    # Scan for Python files (excluding __init__.py and base_tool.py)
    tool_files = [f for f in os.listdir(tools_dir) 
                  if f.endswith('.py') and f not in ['__init__.py', 'base_tool.py']]
    
    if not silent:
        print(f"[DEBUG] Found tool files: {tool_files}")
    
    for filename in tool_files:
        module_name = filename[:-3]  # Remove .py extension
        
        try:
            # Import the module using the current package's __name__
            # This makes it work regardless of how the package is imported
            if not silent:
                print(f"[DEBUG] Attempting to import: {module_name}")
            
            # Use __name__ which will be the correct package path
            module = importlib.import_module(f'.{module_name}', package=__name__)
            
            if not silent:
                print(f"[DEBUG] Successfully imported module: {module_name}")
            
            # Find tool classes that inherit from BaseTool
            tool_classes_found = []
            for item_name in dir(module):
                item = getattr(module, item_name)
                if (isinstance(item, type) and 
                    issubclass(item, BaseTool) and 
                    item != BaseTool):
                    
                    tool_classes_found.append(item_name)
                    
                    try:
                        # Instantiate the tool
                        tool_instance = item(config or {})
                        tools[tool_instance.name] = tool_instance
                        if not silent:
                            print(f"✓ Loaded tool: {tool_instance.name} (from {module_name}.{item_name})")
                    except Exception as inst_e:
                        if not silent:
                            print(f"Warning: Could not instantiate {item_name} from {filename}: {inst_e}")
                            if not silent:
                                traceback.print_exc()
            
            if not silent and not tool_classes_found:
                print(f"[DEBUG] No tool classes found in {filename}")
                        
        except ImportError as e:
            if not silent:
                print(f"Warning: Import error for {filename}: {e}")
                # Print more detailed import error info
                print(f"[DEBUG] sys.path: {sys.path[:3]}...")  # Show first 3 paths
                traceback.print_exc()
        except Exception as e:
            if not silent:
                print(f"Warning: Could not load tool from {filename}: {e}")
                traceback.print_exc()
    
    if not silent:
        print(f"[DEBUG] Total tools loaded: {len(tools)}")
        if tools:
            print(f"[DEBUG] Tool names: {list(tools.keys())}")
    
    return tools