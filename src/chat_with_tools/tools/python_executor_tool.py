"""
Python Code Execution Tool for Chat with Tools Framework

This tool allows safe execution of Python code with sandboxing
and resource limits to prevent system damage.
"""

import sys
import io
import traceback
import ast
import time
import signal
import resource
import multiprocessing
import builtins
from typing import Dict, Any, Optional, Tuple
from contextlib import contextmanager, redirect_stdout, redirect_stderr
from .base_tool import BaseTool


class SafeExecutor:
    """Safe Python code executor with sandboxing."""
    
    # Restricted built-ins for safety
    SAFE_BUILTINS = {
        'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes',
        'chr', 'complex', 'dict', 'dir', 'divmod', 'enumerate', 'filter',
        'float', 'format', 'frozenset', 'hex', 'int', 'isinstance', 'issubclass',
        'iter', 'len', 'list', 'map', 'max', 'min', 'next', 'oct', 'ord',
        'pow', 'print', 'range', 'repr', 'reversed', 'round', 'set',
        'slice', 'sorted', 'str', 'sum', 'tuple', 'type', 'zip',
        # Math functions
        'math', 'random', 'statistics',
        # Collections
        'collections', 'itertools',
        # JSON
        'json',
        # Datetime
        'datetime', 'time',
        # Regular expressions
        're',
        # Data manipulation
        'pandas', 'numpy',
    }
    
    # Dangerous modules to block
    BLOCKED_MODULES = {
        'os', 'sys', 'subprocess', 'socket', 'urllib', 'requests',
        '__builtins__', '__import__', 'eval', 'exec', 'compile',
        'open', 'file', 'input', 'raw_input', '__loader__'
    }
    
    def __init__(self, timeout: int = 5, max_memory_mb: int = 100):
        self.timeout = timeout
        self.max_memory_mb = max_memory_mb
    
    @contextmanager
    def _timeout_context(self, seconds):
        """Context manager for execution timeout."""
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Code execution exceeded {seconds} seconds")
        
        # Set the timeout handler
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    
    def _validate_code(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate code for safety before execution."""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax error: {str(e)}"
        
        # Check for dangerous imports and function calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split('.')[0] in self.BLOCKED_MODULES:
                        return False, f"Import of '{alias.name}' is not allowed"
            
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split('.')[0] in self.BLOCKED_MODULES:
                    return False, f"Import from '{node.module}' is not allowed"
            
            elif isinstance(node, ast.Name):
                if node.id in self.BLOCKED_MODULES:
                    return False, f"Use of '{node.id}' is not allowed"
            
            elif isinstance(node, ast.Attribute):
                # Check for dangerous attributes like __globals__, __code__, etc.
                if node.attr.startswith('__') and node.attr.endswith('__'):
                    if node.attr not in ['__name__', '__doc__', '__class__', '__dict__']:
                        return False, f"Access to '{node.attr}' is not allowed"
        
        return True, None
    
    def _create_safe_globals(self) -> Dict[str, Any]:
        """Create a safe global namespace for code execution."""
        safe_globals = {}
        
        # Add safe built-ins
        for name in self.SAFE_BUILTINS:
            if name in ['math', 'random', 'statistics', 'collections', 'itertools', 
                       'json', 'datetime', 'time', 're']:
                try:
                    safe_globals[name] = __import__(name)
                except ImportError:
                    pass
            elif name in ['pandas', 'numpy']:
                try:
                    if name == 'pandas':
                        safe_globals['pd'] = __import__('pandas')
                    elif name == 'numpy':
                        safe_globals['np'] = __import__('numpy')
                except ImportError:
                    pass
        
        # Add safe built-in functions
        safe_builtins = {}
        
        # Get built-in functions from the builtins module
        for name in self.SAFE_BUILTINS:
            if name not in ['math', 'random', 'statistics', 'collections', 'itertools',
                           'json', 'datetime', 'time', 're', 'pandas', 'numpy']:
                # These are actual built-in functions, not modules
                if hasattr(builtins, name):
                    safe_builtins[name] = getattr(builtins, name)
        
        safe_globals['__builtins__'] = safe_builtins
        
        return safe_globals
    
    def execute(self, code: str) -> Dict[str, Any]:
        """Execute Python code safely with sandboxing."""
        # Validate code first
        is_valid, error_msg = self._validate_code(code)
        if not is_valid:
            return {
                "status": "error",
                "error": error_msg,
                "output": "",
                "execution_time": 0
            }
        
        # Prepare execution environment
        output_buffer = io.StringIO()
        error_buffer = io.StringIO()
        start_time = time.time()
        
        try:
            # Create safe globals
            safe_globals = self._create_safe_globals()
            safe_locals = {}
            
            # Execute with timeout and output capture
            with self._timeout_context(self.timeout):
                with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
                    exec(code, safe_globals, safe_locals)
            
            execution_time = time.time() - start_time
            
            # Capture results
            output = output_buffer.getvalue()
            errors = error_buffer.getvalue()
            
            # Try to get the last expression value
            result = None
            try:
                # Parse code to find last expression
                tree = ast.parse(code)
                if tree.body and isinstance(tree.body[-1], ast.Expr):
                    last_expr = ast.unparse(tree.body[-1].value)
                    result = eval(last_expr, safe_globals, safe_locals)
            except:
                pass
            
            return {
                "status": "success",
                "output": output,
                "errors": errors,
                "result": str(result) if result is not None else None,
                "execution_time": round(execution_time, 3),
                "variables": {k: str(v)[:100] for k, v in safe_locals.items() 
                            if not k.startswith('_')}
            }
            
        except TimeoutError as e:
            return {
                "status": "timeout",
                "error": str(e),
                "output": output_buffer.getvalue(),
                "execution_time": self.timeout
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "output": output_buffer.getvalue(),
                "execution_time": time.time() - start_time
            }


class PythonExecutorTool(BaseTool):
    """
    Python code execution tool for running Python code safely.
    
    This tool allows agents to execute Python code for calculations,
    data analysis, and algorithm testing in a sandboxed environment.
    """
    
    def __init__(self, config: dict):
        self.config = config
        timeout = config.get('code_execution', {}).get('timeout', 5)
        max_memory = config.get('code_execution', {}).get('max_memory_mb', 100)
        self.executor = SafeExecutor(timeout=timeout, max_memory_mb=max_memory)
    
    @property
    def name(self) -> str:
        return "python_executor"
    
    @property
    def description(self) -> str:
        return """Execute Python code safely in a sandboxed environment.
        
        Available libraries: math, random, statistics, collections, itertools,
        json, datetime, time, re, pandas (as pd), numpy (as np)
        
        Use this for:
        - Mathematical calculations
        - Data analysis and manipulation
        - Algorithm implementation and testing
        - String/text processing
        - Date/time operations
        
        Note: File I/O, network access, and system operations are restricted for safety.
        """
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of what the code does"
                }
            },
            "required": ["code"]
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute Python code safely."""
        code = kwargs.get("code")
        description = kwargs.get("description", "")
        
        if not code:
            return {"error": "No code provided"}
        
        # Add description as comment if provided
        if description:
            result_description = f"Executing: {description}\n"
        else:
            result_description = ""
        
        # Execute the code
        result = self.executor.execute(code)
        
        # Format response
        response = {
            "status": result["status"],
            "description": description
        }
        
        if result["status"] == "success":
            response.update({
                "output": result["output"],
                "result": result["result"],
                "errors": result["errors"],
                "execution_time": result["execution_time"],
                "variables": result["variables"]
            })
        else:
            response.update({
                "error": result.get("error", "Unknown error"),
                "output": result.get("output", ""),
                "execution_time": result.get("execution_time", 0)
            })
            
            if "traceback" in result:
                response["traceback"] = result["traceback"]
        
        return response
