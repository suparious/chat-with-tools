"""
vLLM backend integration for structured outputs and improved tool calling.
"""

import json
import time
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

import requests
from openai import OpenAI

try:
    from pydantic import BaseModel
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object


@dataclass
class VLLMConfig:
    """Configuration for vLLM backend."""
    base_url: str
    model: str
    api_key: Optional[str] = None
    timeout: int = 30
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 50
    repetition_penalty: float = 1.0
    stop_sequences: Optional[List[str]] = None
    
    # Structured output settings
    use_structured_output: bool = False
    guided_backend: str = "outlines"  # "outlines" or "jsonschema"
    enforce_schema: bool = True
    schema_cache_size: int = 100
    
    # Tool calling optimizations
    use_grammar_constraints: bool = False
    tool_choice_mode: str = "auto"  # "auto", "required", "none"
    parallel_tool_calls: bool = True
    max_tool_iterations: int = 10


class VLLMBackend:
    """
    Enhanced vLLM backend with structured output support.
    """
    
    def __init__(self, config: VLLMConfig):
        """
        Initialize vLLM backend.
        
        Args:
            config: vLLM configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI client for vLLM
        self.client = OpenAI(
            base_url=config.base_url,
            api_key=config.api_key or "dummy-key-for-local"
        )
        
        # Schema cache for structured outputs
        self._schema_cache = {}
        
        # Check vLLM server health
        self._check_server_health()
    
    def _check_server_health(self) -> bool:
        """Check if vLLM server is healthy."""
        try:
            health_url = f"{self.config.base_url.rstrip('/v1')}/health"
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                self.logger.info(f"vLLM server is healthy at {self.config.base_url}")
                return True
        except Exception as e:
            self.logger.warning(f"Could not check vLLM health: {e}")
        return False
    
    def _get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        try:
            models_url = f"{self.config.base_url}/models"
            response = requests.get(models_url, timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.logger.warning(f"Could not get model info: {e}")
        return {}
    
    def _prepare_structured_request(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[type] = None
    ) -> Dict[str, Any]:
        """
        Prepare request with structured output constraints.
        
        Args:
            messages: Chat messages
            tools: Available tools
            response_format: Expected response format (Pydantic model)
            
        Returns:
            Request parameters for vLLM
        """
        request_params = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "max_tokens": self.config.max_tokens,
        }
        
        # Add stop sequences if configured
        if self.config.stop_sequences:
            request_params["stop"] = self.config.stop_sequences
        
        # Add structured output parameters if enabled
        if self.config.use_structured_output and response_format:
            if PYDANTIC_AVAILABLE and issubclass(response_format, BaseModel):
                # Get or cache schema
                schema_key = response_format.__name__
                if schema_key not in self._schema_cache:
                    self._schema_cache[schema_key] = response_format.schema()
                
                schema = self._schema_cache[schema_key]
                
                # Add vLLM-specific parameters for structured output
                if self.config.guided_backend == "outlines":
                    request_params["extra_body"] = {
                        "guided_json": schema,
                        "guided_decoding_backend": "outlines"
                    }
                elif self.config.guided_backend == "jsonschema":
                    request_params["response_format"] = {
                        "type": "json_schema",
                        "json_schema": {
                            "name": schema_key,
                            "schema": schema,
                            "strict": self.config.enforce_schema
                        }
                    }
        
        # Add tools if provided
        if tools:
            request_params["tools"] = tools
            request_params["tool_choice"] = self.config.tool_choice_mode
            
            # Add grammar constraints for tool calling if enabled
            if self.config.use_grammar_constraints:
                request_params["extra_body"] = request_params.get("extra_body", {})
                request_params["extra_body"]["guided_grammar"] = self._generate_tool_grammar(tools)
        
        return request_params
    
    def _generate_tool_grammar(self, tools: List[Dict[str, Any]]) -> str:
        """
        Generate a grammar for constrained tool calling.
        
        Args:
            tools: List of tool definitions
            
        Returns:
            Grammar string for vLLM
        """
        # This is a simplified example - actual grammar would be more complex
        tool_names = [tool["function"]["name"] for tool in tools]
        
        grammar = f"""
        root ::= tool_call | direct_answer
        tool_call ::= "{{" '"tool":' tool_name ',' '"arguments":' arguments "}}"
        tool_name ::= {' | '.join(f'"{name}"' for name in tool_names)}
        arguments ::= "{{" (argument ("," argument)*)? "}}"
        argument ::= string ":" value
        value ::= string | number | boolean | null
        string ::= '"' ([^"\\\\] | "\\\\" | '\\"')* '"'
        number ::= "-"? [0-9]+ ("." [0-9]+)?
        boolean ::= "true" | "false"
        null ::= "null"
        direct_answer ::= "{{" '"answer":' string "}}"
        """
        
        return grammar.strip()
    
    def complete(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[type] = None,
        **kwargs
    ) -> Any:
        """
        Make a completion request to vLLM.
        
        Args:
            messages: Chat messages
            tools: Available tools
            response_format: Expected response format
            **kwargs: Additional parameters
            
        Returns:
            Completion response
        """
        # Prepare request with structured output if configured
        request_params = self._prepare_structured_request(messages, tools, response_format)
        
        # Override with any provided kwargs
        request_params.update(kwargs)
        
        # Log request for debugging
        self.logger.debug(f"vLLM request: {json.dumps(request_params, indent=2)}")
        
        try:
            # Make request to vLLM
            response = self.client.chat.completions.create(**request_params)
            
            # Log response for debugging
            if response.choices:
                self.logger.debug(f"vLLM response: {response.choices[0].message}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"vLLM completion failed: {e}")
            raise
    
    def complete_with_retry(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[type] = None,
        max_retries: int = 3,
        **kwargs
    ) -> Any:
        """
        Make a completion request with retry logic.
        
        Args:
            messages: Chat messages
            tools: Available tools
            response_format: Expected response format
            max_retries: Maximum number of retries
            **kwargs: Additional parameters
            
        Returns:
            Completion response
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return self.complete(messages, tools, response_format, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    self.logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
        
        raise last_error
    
    def validate_response(
        self,
        response: Any,
        expected_format: Optional[type] = None
    ) -> Dict[str, Any]:
        """
        Validate and parse response.
        
        Args:
            response: Raw response from vLLM
            expected_format: Expected format (Pydantic model)
            
        Returns:
            Validated response dictionary
        """
        if not response.choices:
            raise ValueError("No response choices available")
        
        message = response.choices[0].message
        
        # Extract content
        content = message.content
        if not content:
            raise ValueError("Empty response content")
        
        # Try to parse as JSON if it looks like JSON
        if content.strip().startswith('{'):
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse JSON response: {e}")
                data = {"content": content}
        else:
            data = {"content": content}
        
        # Validate with Pydantic if format provided
        if expected_format and PYDANTIC_AVAILABLE:
            try:
                validated = expected_format(**data)
                return validated.dict()
            except Exception as e:
                self.logger.warning(f"Response validation failed: {e}")
                # Return raw data if validation fails
                return data
        
        return data
    
    def stream_complete(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        """
        Stream completion from vLLM.
        
        Args:
            messages: Chat messages
            tools: Available tools
            **kwargs: Additional parameters
            
        Yields:
            Response chunks
        """
        request_params = self._prepare_structured_request(messages, tools)
        request_params.update(kwargs)
        request_params["stream"] = True
        
        try:
            stream = self.client.chat.completions.create(**request_params)
            for chunk in stream:
                yield chunk
        except Exception as e:
            self.logger.error(f"vLLM streaming failed: {e}")
            raise


class VLLMToolExecutor:
    """
    Enhanced tool executor with vLLM optimizations.
    """
    
    def __init__(self, backend: VLLMBackend, tools: Dict[str, Any]):
        """
        Initialize tool executor.
        
        Args:
            backend: vLLM backend instance
            tools: Dictionary of tool name to tool function
        """
        self.backend = backend
        self.tools = tools
        self.logger = logging.getLogger(__name__)
    
    def execute_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a tool call with validation.
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            validate: Whether to validate arguments
            
        Returns:
            Tool execution result
        """
        # Check if tool exists
        if tool_name not in self.tools:
            return {
                "error": f"Unknown tool: {tool_name}",
                "status": "failed"
            }
        
        # Validate arguments if requested
        if validate and PYDANTIC_AVAILABLE:
            try:
                from ..structured_output import ToolRegistry
                validated_args = ToolRegistry.validate_arguments(tool_name, arguments)
            except Exception as e:
                return {
                    "error": f"Argument validation failed: {e}",
                    "status": "validation_error"
                }
        else:
            validated_args = arguments
        
        # Execute tool
        try:
            result = self.tools[tool_name](**validated_args)
            return {
                "result": result,
                "status": "success"
            }
        except Exception as e:
            self.logger.error(f"Tool execution failed for {tool_name}: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def batch_execute(
        self,
        tool_calls: List[Dict[str, Any]],
        parallel: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple tool calls.
        
        Args:
            tool_calls: List of tool call specifications
            parallel: Whether to execute in parallel
            
        Returns:
            List of execution results
        """
        results = []
        
        if parallel:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for call in tool_calls:
                    future = executor.submit(
                        self.execute_tool_call,
                        call.get("name"),
                        call.get("arguments", {})
                    )
                    futures.append(future)
                
                for future in concurrent.futures.as_completed(futures):
                    results.append(future.result())
        else:
            for call in tool_calls:
                result = self.execute_tool_call(
                    call.get("name"),
                    call.get("arguments", {})
                )
                results.append(result)
        
        return results
