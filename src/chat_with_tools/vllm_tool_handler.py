"""
Advanced vLLM structured output handler for improved tool calling accuracy.
This module implements smart schema generation and validation for tool calls.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ToolCallSchema:
    """Schema for a specific tool call."""
    name: str
    parameters_schema: Dict[str, Any]
    description: str
    
    def to_json_schema(self) -> Dict[str, Any]:
        """Convert to JSON schema format."""
        return {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "const": self.name,
                    "description": f"Call the {self.name} tool"
                },
                "arguments": self.parameters_schema
            },
            "required": ["tool_name", "arguments"]
        }


class VLLMToolCallHandler:
    """
    Handles structured output for tool calling with vLLM.
    Generates appropriate schemas and validates responses.
    """
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """Initialize the handler."""
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.vllm_config = config.get('vllm_structured_output', {})
        self.enabled = self.vllm_config.get('enabled', False)
        self.backend = self.vllm_config.get('backend', 'outlines')
        
    def should_use_structured_output(
        self, 
        tools: List[Dict[str, Any]], 
        query: str,
        force_no_tools: bool = False
    ) -> bool:
        """
        Determine if structured output should be used for this request.
        
        Args:
            tools: Available tools
            query: User query
            force_no_tools: If True, don't use structured output
            
        Returns:
            True if structured output should be used
        """
        if not self.enabled or force_no_tools or not tools:
            return False
        
        # Check if query likely needs tools
        tool_indicators = [
            'calculate', 'compute', 'search', 'find', 'read', 'write',
            'analyze', 'summarize', 'remember', 'recall', 'think'
        ]
        
        query_lower = query.lower()
        needs_tools = any(indicator in query_lower for indicator in tool_indicators)
        
        return needs_tools
    
    def generate_tool_call_schema(self, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a JSON schema for tool calling that matches OpenAI's format.
        
        Args:
            tools: List of available tools
            
        Returns:
            JSON schema for tool calling
        """
        # Extract tool names and create enum
        tool_names = []
        tool_schemas = {}
        
        for tool in tools:
            if "function" in tool:
                func = tool["function"]
                name = func.get("name")
                if name:
                    tool_names.append(name)
                    # Store the parameter schema for each tool
                    tool_schemas[name] = func.get("parameters", {})
        
        if not tool_names:
            return {}
        
        # Create a schema that matches OpenAI's tool calling format
        # This helps the model generate proper tool calls
        schema = {
            "type": "object",
            "properties": {
                "reasoning": {
                    "type": "string",
                    "description": "Brief reasoning about which tool to use and why"
                },
                "tool_calls": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "const": "function"
                            },
                            "function": {
                                "type": "object",
                                "properties": {
                                    "name": {
                                        "type": "string",
                                        "enum": tool_names
                                    },
                                    "arguments": {
                                        "type": "string",
                                        "description": "JSON string of arguments"
                                    }
                                },
                                "required": ["name", "arguments"]
                            }
                        },
                        "required": ["type", "function"]
                    },
                    "minItems": 1,
                    "maxItems": 3
                }
            },
            "required": ["tool_calls"]
        }
        
        return schema
    
    def generate_simple_response_schema(self) -> Dict[str, Any]:
        """
        Generate a simple schema for non-tool responses.
        
        Returns:
            Simple response schema
        """
        return {
            "type": "object",
            "properties": {
                "response": {
                    "type": "string",
                    "description": "The response to the user"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Confidence in the response (0-1)"
                }
            },
            "required": ["response"]
        }
    
    def add_structured_output_to_request(
        self,
        request_params: Dict[str, Any],
        tools: Optional[List[Dict[str, Any]]] = None,
        query: Optional[str] = None,
        force_no_tools: bool = False
    ) -> Dict[str, Any]:
        """
        Add structured output parameters to the request.
        
        Args:
            request_params: Base request parameters
            tools: Available tools
            query: User query
            force_no_tools: If True, don't add tool schemas
            
        Returns:
            Modified request parameters
        """
        if not self.enabled:
            return request_params
        
        # Determine what kind of schema to use
        use_tool_schema = self.should_use_structured_output(tools or [], query or "", force_no_tools)
        
        if use_tool_schema and tools:
            # Generate tool calling schema
            schema = self.generate_tool_call_schema(tools)
            if schema:
                self._add_schema_to_request(request_params, schema, "tool_call")
        else:
            # Use simple JSON mode for better structure
            # This is less restrictive and less likely to cause errors
            request_params["response_format"] = {"type": "json_object"}
        
        return request_params
    
    def _add_schema_to_request(
        self, 
        request_params: Dict[str, Any], 
        schema: Dict[str, Any],
        schema_name: str = "response"
    ):
        """
        Add schema to request based on backend configuration.
        
        Args:
            request_params: Request parameters to modify
            schema: JSON schema
            schema_name: Name for the schema
        """
        if self.backend == "outlines":
            # For outlines backend, use extra_body with guided_json
            request_params["extra_body"] = {
                "guided_json": schema,
                "guided_decoding_backend": "outlines"
            }
            self.logger.debug(f"Added guided_json schema for {schema_name}")
        else:
            # For other backends, use response_format
            request_params["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "schema": schema,
                    "strict": self.vllm_config.get('enforcement_level', 'strict') == 'strict'
                }
            }
            self.logger.debug(f"Added response_format schema for {schema_name}")
    
    def parse_structured_response(self, response_content: str) -> Tuple[bool, Any]:
        """
        Parse and validate a structured response.
        
        Args:
            response_content: Raw response content
            
        Returns:
            Tuple of (is_valid, parsed_content)
        """
        try:
            # Try to parse as JSON
            parsed = json.loads(response_content)
            
            # Check if it contains tool calls
            if isinstance(parsed, dict) and "tool_calls" in parsed:
                # Validate tool calls structure
                tool_calls = parsed["tool_calls"]
                if isinstance(tool_calls, list) and all(
                    isinstance(tc, dict) and 
                    tc.get("type") == "function" and 
                    "function" in tc
                    for tc in tool_calls
                ):
                    return True, parsed
            
            # Otherwise, return as-is if it's valid JSON
            return True, parsed
            
        except json.JSONDecodeError:
            # Not valid JSON, return as plain text
            return False, response_content
        except Exception as e:
            self.logger.warning(f"Error parsing structured response: {e}")
            return False, response_content
    
    def validate_tool_arguments(
        self,
        tool_name: str,
        arguments: Any,
        tool_schema: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """
        Validate tool arguments against schema.
        
        Args:
            tool_name: Name of the tool
            arguments: Arguments to validate (string or dict)
            tool_schema: Tool's parameter schema
            
        Returns:
            Tuple of (is_valid, parsed_arguments, error_message)
        """
        # Parse arguments if they're a string
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError as e:
                return False, {}, f"Invalid JSON in arguments: {e}"
        
        if not isinstance(arguments, dict):
            return False, {}, f"Arguments must be a dictionary, got {type(arguments)}"
        
        # Get required parameters
        properties = tool_schema.get("properties", {})
        required = tool_schema.get("required", [])
        
        # Check required parameters
        for param in required:
            if param not in arguments:
                return False, arguments, f"Missing required parameter: {param}"
        
        # Basic type validation
        validated_args = {}
        for param, value in arguments.items():
            if param in properties:
                param_schema = properties[param]
                param_type = param_schema.get("type")
                
                # Try to coerce to correct type
                try:
                    if param_type == "string":
                        validated_args[param] = str(value)
                    elif param_type == "number":
                        validated_args[param] = float(value)
                    elif param_type == "integer":
                        validated_args[param] = int(value)
                    elif param_type == "boolean":
                        validated_args[param] = bool(value)
                    else:
                        validated_args[param] = value
                except (ValueError, TypeError) as e:
                    return False, arguments, f"Type error for {param}: {e}"
            else:
                # Include unknown parameters (might be optional)
                validated_args[param] = value
        
        return True, validated_args, None


def create_tool_call_handler(config: Dict[str, Any]) -> VLLMToolCallHandler:
    """
    Factory function to create a tool call handler.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        VLLMToolCallHandler instance
    """
    return VLLMToolCallHandler(config)
