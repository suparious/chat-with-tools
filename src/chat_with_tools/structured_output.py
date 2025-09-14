"""
Structured output support for vLLM and other backends.
Provides Pydantic models and validation for tool calls.
"""

import json
from typing import Dict, Any, List, Optional, Union, Literal
from enum import Enum

try:
    from pydantic import BaseModel, Field, validator, ValidationError
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object


class ToolCallStatus(str, Enum):
    """Status of a tool call execution."""
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    VALIDATION_ERROR = "validation_error"


class ToolArgument(BaseModel):
    """Base model for tool arguments with validation."""
    
    class Config:
        extra = "forbid"  # Reject unknown fields
        validate_assignment = True
        use_enum_values = True


class SearchToolArgs(ToolArgument):
    """Arguments for web search tool."""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    max_results: Optional[int] = Field(5, ge=1, le=20, description="Maximum number of results")
    
    @validator('query')
    def validate_query(cls, v):
        if not v or v.isspace():
            raise ValueError("Query cannot be empty or whitespace")
        return v.strip()


class CalculatorToolArgs(ToolArgument):
    """Arguments for calculator tool."""
    expression: str = Field(..., description="Mathematical expression to evaluate")
    
    @validator('expression')
    def validate_expression(cls, v):
        # Basic validation - ensure it's not empty and contains valid chars
        if not v or v.isspace():
            raise ValueError("Expression cannot be empty")
        # Check for dangerous operations
        dangerous = ['__', 'import', 'exec', 'eval', 'open', 'file']
        for d in dangerous:
            if d in v.lower():
                raise ValueError(f"Expression contains forbidden operation: {d}")
        return v


class FileToolArgs(ToolArgument):
    """Arguments for file operations."""
    path: str = Field(..., description="File path")
    content: Optional[str] = Field(None, description="File content for write operations")
    
    @validator('path')
    def validate_path(cls, v):
        # Basic path validation
        if not v or v.isspace():
            raise ValueError("Path cannot be empty")
        # Prevent directory traversal
        if '..' in v or v.startswith('/'):
            raise ValueError("Invalid path - no absolute paths or directory traversal")
        return v.strip()


class MemoryToolArgs(ToolArgument):
    """Arguments for memory operations."""
    action: Literal["store", "retrieve", "search", "delete"] = Field(..., description="Memory action")
    key: Optional[str] = Field(None, description="Memory key")
    value: Optional[str] = Field(None, description="Memory value")
    query: Optional[str] = Field(None, description="Search query")
    
    @validator('action')
    def validate_action_requirements(cls, v, values):
        if v == "store" and ('key' not in values or 'value' not in values):
            raise ValueError("Store action requires both key and value")
        elif v == "retrieve" and 'key' not in values:
            raise ValueError("Retrieve action requires key")
        elif v == "search" and 'query' not in values:
            raise ValueError("Search action requires query")
        elif v == "delete" and 'key' not in values:
            raise ValueError("Delete action requires key")
        return v


class PythonExecutorArgs(ToolArgument):
    """Arguments for Python code execution."""
    code: str = Field(..., description="Python code to execute")
    timeout: Optional[int] = Field(5, ge=1, le=30, description="Execution timeout in seconds")
    
    @validator('code')
    def validate_code(cls, v):
        if not v or v.isspace():
            raise ValueError("Code cannot be empty")
        # Check for obviously dangerous operations
        dangerous = ['__import__', 'exec', 'eval', 'compile', 'open(', 'file(']
        for d in dangerous:
            if d in v:
                raise ValueError(f"Code contains potentially dangerous operation: {d}")
        return v


class SequentialThinkingArgs(ToolArgument):
    """Arguments for sequential thinking tool."""
    thought: str = Field(..., min_length=1, description="Current thought step")
    next_thought_needed: bool = Field(..., description="Whether another thought is needed")
    thought_number: int = Field(..., ge=1, description="Current thought number")
    total_thoughts: int = Field(..., ge=1, le=100, description="Estimated total thoughts")
    is_revision: Optional[bool] = Field(False, description="Whether this revises previous thinking")
    revises_thought: Optional[int] = Field(None, ge=1, description="Which thought is being revised")


class ToolCall(BaseModel):
    """Structured representation of a tool call."""
    
    tool_name: str = Field(..., description="Name of the tool to call")
    arguments: Dict[str, Any] = Field(..., description="Arguments for the tool")
    call_id: Optional[str] = Field(None, description="Unique identifier for this call")
    status: ToolCallStatus = Field(ToolCallStatus.PENDING, description="Current status")
    result: Optional[Any] = Field(None, description="Result from tool execution")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    @validator('tool_name')
    def validate_tool_name(cls, v):
        if not v or v.isspace():
            raise ValueError("Tool name cannot be empty")
        return v.strip()


class StructuredToolResponse(BaseModel):
    """Structured response format for tool calls with vLLM."""
    
    thought: Optional[str] = Field(None, description="Agent's reasoning about the tool call")
    tool_calls: List[ToolCall] = Field(..., min_items=1, description="List of tool calls to make")
    requires_followup: bool = Field(True, description="Whether more iterations are needed")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence in tool calls")


class StructuredAgentResponse(BaseModel):
    """Structured final response from agent."""
    
    answer: str = Field(..., min_length=1, description="Final answer to the user")
    tool_calls_made: Optional[List[str]] = Field(None, description="List of tools that were called")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence in answer")
    sources: Optional[List[str]] = Field(None, description="Sources used for the answer")
    requires_clarification: bool = Field(False, description="Whether user clarification is needed")


class ToolRegistry:
    """Registry for tool argument validators."""
    
    _validators = {
        "search_web": SearchToolArgs,
        "calculate": CalculatorToolArgs,
        "read_file": FileToolArgs,
        "write_file": FileToolArgs,
        "memory": MemoryToolArgs,
        "python_executor": PythonExecutorArgs,
        "sequential_thinking": SequentialThinkingArgs,
    }
    
    @classmethod
    def validate_arguments(cls, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate tool arguments using Pydantic models.
        
        Args:
            tool_name: Name of the tool
            arguments: Arguments to validate
            
        Returns:
            Validated arguments as dictionary
            
        Raises:
            ValidationError: If arguments are invalid
        """
        if not PYDANTIC_AVAILABLE:
            # If Pydantic not available, return arguments as-is
            return arguments
        
        validator_class = cls._validators.get(tool_name)
        if not validator_class:
            # No validator registered, return as-is
            return arguments
        
        try:
            # Validate using Pydantic model
            validated = validator_class(**arguments)
            return validated.dict(exclude_none=True)
        except ValidationError as e:
            # Re-raise with cleaner error message
            errors = []
            for error in e.errors():
                field = '.'.join(str(x) for x in error['loc'])
                msg = error['msg']
                errors.append(f"{field}: {msg}")
            raise ValueError(f"Invalid arguments for {tool_name}: " + "; ".join(errors))
    
    @classmethod
    def register_validator(cls, tool_name: str, validator_class: type):
        """Register a custom validator for a tool."""
        if not issubclass(validator_class, ToolArgument):
            raise TypeError("Validator must be a subclass of ToolArgument")
        cls._validators[tool_name] = validator_class
    
    @classmethod
    def get_schema(cls, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get JSON schema for tool arguments."""
        if not PYDANTIC_AVAILABLE:
            return None
        
        validator_class = cls._validators.get(tool_name)
        if not validator_class:
            return None
        
        return validator_class.schema()


def format_for_vllm_structured(
    tools: List[Dict[str, Any]], 
    backend: str = "outlines",
    response_format: Optional[type] = None
) -> Dict[str, Any]:
    """
    Format tools and response format for vLLM structured output.
    
    Args:
        tools: List of tool definitions
        backend: vLLM backend to use ("outlines" or "jsonschema")
        response_format: Optional Pydantic model for response format
        
    Returns:
        Formatted parameters for vLLM API call
    """
    if not PYDANTIC_AVAILABLE:
        return {}
    
    params = {
        "guided_decoding_backend": backend
    }
    
    if response_format:
        if backend == "outlines":
            # For outlines backend, provide the Pydantic model
            params["response_format"] = {
                "type": "json_object",
                "schema": response_format.schema()
            }
        elif backend == "jsonschema":
            # For jsonschema backend, provide the JSON schema
            params["guided_json"] = response_format.schema()
    
    # Add tool schemas if available
    if tools:
        tool_schemas = []
        for tool in tools:
            tool_name = tool.get("function", {}).get("name")
            if tool_name:
                schema = ToolRegistry.get_schema(tool_name)
                if schema:
                    tool_schemas.append({
                        "name": tool_name,
                        "parameters": schema
                    })
        
        if tool_schemas:
            params["tools"] = tool_schemas
    
    return params


def validate_tool_call_response(response: str, expected_format: type = None) -> Dict[str, Any]:
    """
    Validate and parse a tool call response.
    
    Args:
        response: Raw response string
        expected_format: Optional Pydantic model to validate against
        
    Returns:
        Parsed and validated response
        
    Raises:
        ValidationError: If response doesn't match expected format
    """
    try:
        # Parse JSON
        data = json.loads(response)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response: {e}")
    
    if expected_format and PYDANTIC_AVAILABLE:
        try:
            # Validate with Pydantic
            validated = expected_format(**data)
            return validated.dict()
        except ValidationError as e:
            raise ValueError(f"Response validation failed: {e}")
    
    return data


class ToolCallOptimizer:
    """Optimizer for improving tool call accuracy."""
    
    @staticmethod
    def preprocess_query(query: str, tool_name: str) -> str:
        """
        Preprocess a query for better tool matching.
        
        Args:
            query: Original query
            tool_name: Target tool name
            
        Returns:
            Optimized query
        """
        # Tool-specific optimizations
        optimizations = {
            "search_web": lambda q: q.replace("find", "").replace("search for", "").strip(),
            "calculate": lambda q: q.replace("calculate", "").replace("compute", "").strip(),
            "python_executor": lambda q: q.replace("run python:", "").replace("execute:", "").strip(),
        }
        
        optimizer = optimizations.get(tool_name)
        if optimizer:
            return optimizer(query)
        return query
    
    @staticmethod
    def suggest_tool(query: str, available_tools: List[str]) -> Optional[str]:
        """
        Suggest the best tool for a query based on keywords.
        
        Args:
            query: User query
            available_tools: List of available tool names
            
        Returns:
            Suggested tool name or None
        """
        query_lower = query.lower()
        
        # Keyword mapping to tools
        tool_keywords = {
            "search_web": ["search", "find", "look up", "google", "web", "internet"],
            "calculate": ["calculate", "compute", "math", "solve", "equation"],
            "python_executor": ["python", "code", "script", "program", "execute"],
            "memory": ["remember", "recall", "store", "memory", "save"],
            "read_file": ["read", "open", "load", "file", "document"],
            "write_file": ["write", "save", "create", "output", "export"],
            "sequential_thinking": ["think", "reason", "analyze", "consider", "ponder"],
        }
        
        scores = {}
        for tool, keywords in tool_keywords.items():
            if tool in available_tools:
                score = sum(1 for keyword in keywords if keyword in query_lower)
                if score > 0:
                    scores[tool] = score
        
        if scores:
            return max(scores, key=scores.get)
        return None
