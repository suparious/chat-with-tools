"""
Complete vLLM integration for structured outputs and improved tool calling accuracy.
This module provides seamless integration between the agent framework and vLLM's
structured output capabilities without duplicating existing functionality.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union, Type
from dataclasses import dataclass
from enum import Enum

try:
    from pydantic import BaseModel, Field, validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object


class VLLMMode(Enum):
    """vLLM operation modes."""
    STANDARD = "standard"  # Regular completion
    STRUCTURED = "structured"  # With JSON schema constraints
    GRAMMAR = "grammar"  # With grammar constraints
    TOOLS = "tools"  # Optimized for tool calling


@dataclass
class VLLMStructuredConfig:
    """Configuration for vLLM structured output."""
    enabled: bool = False
    backend: str = "outlines"  # outlines or jsonschema
    validate_with_pydantic: bool = True
    retry_on_failure: bool = True
    max_retries: int = 3
    enforcement_level: str = "strict"  # strict, relaxed, or none
    cache_schemas: bool = True
    log_structured_calls: bool = True


class VLLMStructuredOutputManager:
    """
    Manages structured output generation with vLLM backend.
    Integrates with existing agent framework without duplication.
    """
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize the structured output manager.
        
        Args:
            config: Configuration dictionary from config.yaml
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Load vLLM structured output configuration
        vllm_config = config.get('vllm_structured_output', {})
        self.structured_config = VLLMStructuredConfig(
            enabled=vllm_config.get('enabled', False),
            backend=vllm_config.get('backend', 'outlines'),
            validate_with_pydantic=vllm_config.get('validate_with_pydantic', True),
            retry_on_failure=vllm_config.get('retry_on_failure', True),
            max_retries=vllm_config.get('max_retries', 3),
            enforcement_level=vllm_config.get('enforcement_level', 'strict'),
            cache_schemas=vllm_config.get('cache_schemas', True),
            log_structured_calls=vllm_config.get('log_structured_calls', True)
        )
        
        # Schema cache
        self._schema_cache = {} if self.structured_config.cache_schemas else None
        
        # Log configuration
        if self.structured_config.enabled:
            self.logger.info(f"vLLM Structured Output enabled with backend: {self.structured_config.backend}")
            self.logger.debug(f"Configuration: {self.structured_config}")
    
    def is_enabled(self) -> bool:
        """Check if structured output is enabled."""
        return self.structured_config.enabled and PYDANTIC_AVAILABLE
    
    def should_use_structured_output(self, endpoint_config: Dict[str, Any]) -> bool:
        """
        Determine if structured output should be used for this endpoint.
        
        Args:
            endpoint_config: Endpoint configuration dictionary
            
        Returns:
            True if structured output should be used
        """
        if not self.is_enabled():
            return False
        
        # Check if endpoint supports structured output
        supports_structured = endpoint_config.get('supports_structured_output', False)
        is_vllm = endpoint_config.get('is_vllm', False)
        
        return supports_structured and is_vllm
    
    def prepare_structured_request(
        self,
        request_params: Dict[str, Any],
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Type[BaseModel]] = None,
        mode: VLLMMode = VLLMMode.STANDARD
    ) -> Dict[str, Any]:
        """
        Prepare a request with structured output constraints.
        
        Args:
            request_params: Base request parameters
            tools: Optional list of tools
            response_format: Optional Pydantic model for response format
            mode: vLLM operation mode
            
        Returns:
            Modified request parameters with structured output settings
        """
        if not self.is_enabled():
            return request_params
        
        # Log structured call if enabled
        if self.structured_config.log_structured_calls:
            self.logger.debug(f"Preparing structured request with mode: {mode.value}")
        
        # Add structured output parameters based on backend
        if self.structured_config.backend == "outlines":
            return self._prepare_outlines_request(request_params, tools, response_format, mode)
        elif self.structured_config.backend == "jsonschema":
            return self._prepare_jsonschema_request(request_params, tools, response_format, mode)
        else:
            self.logger.warning(f"Unknown backend: {self.structured_config.backend}")
            return request_params
    
    def _prepare_outlines_request(
        self,
        request_params: Dict[str, Any],
        tools: Optional[List[Dict[str, Any]]],
        response_format: Optional[Type[BaseModel]],
        mode: VLLMMode
    ) -> Dict[str, Any]:
        """Prepare request for Outlines backend."""
        extra_body = request_params.get("extra_body", {})
        
        if mode == VLLMMode.STRUCTURED and response_format:
            # Get or cache schema
            schema = self._get_schema(response_format)
            extra_body["guided_json"] = schema
            extra_body["guided_decoding_backend"] = "outlines"
            
        elif mode == VLLMMode.TOOLS and tools:
            # Optimize for tool calling
            extra_body["guided_tools"] = True
            extra_body["guided_decoding_backend"] = "outlines"
            
            # Add tool schemas if available
            if self.structured_config.enforcement_level == "strict":
                tool_schemas = self._generate_tool_schemas(tools)
                if tool_schemas:
                    extra_body["tool_schemas"] = tool_schemas
        
        elif mode == VLLMMode.GRAMMAR:
            # Use grammar constraints
            grammar = self._generate_grammar(tools)
            if grammar:
                extra_body["guided_grammar"] = grammar
                extra_body["guided_decoding_backend"] = "outlines"
        
        request_params["extra_body"] = extra_body
        return request_params
    
    def _prepare_jsonschema_request(
        self,
        request_params: Dict[str, Any],
        tools: Optional[List[Dict[str, Any]]],
        response_format: Optional[Type[BaseModel]],
        mode: VLLMMode
    ) -> Dict[str, Any]:
        """Prepare request for JSON Schema backend."""
        if mode == VLLMMode.STRUCTURED and response_format:
            schema = self._get_schema(response_format)
            request_params["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": response_format.__name__,
                    "schema": schema,
                    "strict": self.structured_config.enforcement_level == "strict"
                }
            }
        
        elif mode == VLLMMode.TOOLS and tools:
            # For tools, we can provide a schema that describes the expected tool call format
            tool_call_schema = self._generate_tool_call_schema(tools)
            if tool_call_schema:
                request_params["response_format"] = {
                    "type": "json_schema",
                    "json_schema": tool_call_schema
                }
        
        return request_params
    
    def _get_schema(self, model_class: Type[BaseModel]) -> Dict[str, Any]:
        """Get or cache a Pydantic model's JSON schema."""
        if not PYDANTIC_AVAILABLE:
            return {}
        
        # Check cache if enabled
        if self._schema_cache is not None:
            cache_key = model_class.__name__
            if cache_key in self._schema_cache:
                return self._schema_cache[cache_key]
        
        # Generate schema
        schema = model_class.schema()
        
        # Cache if enabled
        if self._schema_cache is not None:
            self._schema_cache[model_class.__name__] = schema
        
        return schema
    
    def _generate_tool_schemas(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate schemas for tools."""
        schemas = []
        
        for tool in tools:
            function = tool.get("function", {})
            if function:
                schema = {
                    "name": function.get("name"),
                    "description": function.get("description"),
                    "parameters": function.get("parameters", {})
                }
                schemas.append(schema)
        
        return schemas
    
    def _generate_tool_call_schema(self, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a JSON schema for tool calls."""
        tool_names = [tool["function"]["name"] for tool in tools if "function" in tool]
        
        return {
            "name": "tool_call",
            "schema": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string",
                        "description": "Reasoning about which tool to use"
                    },
                    "tool_calls": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "tool_name": {
                                    "type": "string",
                                    "enum": tool_names
                                },
                                "arguments": {
                                    "type": "object"
                                }
                            },
                            "required": ["tool_name", "arguments"]
                        }
                    }
                },
                "required": ["tool_calls"]
            },
            "strict": self.structured_config.enforcement_level == "strict"
        }
    
    def _generate_grammar(self, tools: Optional[List[Dict[str, Any]]]) -> Optional[str]:
        """Generate a grammar for constrained generation."""
        if not tools:
            return None
        
        tool_names = [tool["function"]["name"] for tool in tools if "function" in tool]
        
        # Create a simple grammar for tool calling
        grammar = f"""
        root ::= tool_call | answer
        tool_call ::= "{{" ws '"tool":' ws tool_name ws "," ws '"arguments":' ws arguments ws "}}"
        tool_name ::= {' | '.join(f'"{name}"' for name in tool_names)}
        arguments ::= object
        object ::= "{{" ws (pair (ws "," ws pair)*)? ws "}}"
        pair ::= string ws ":" ws value
        value ::= string | number | boolean | null | object | array
        array ::= "[" ws (value (ws "," ws value)*)? ws "]"
        string ::= '"' ([^"\\\\] | "\\\\" | '\\\\"')* '"'
        number ::= "-"? ("0" | [1-9][0-9]*) ("." [0-9]+)? ([eE][+-]?[0-9]+)?
        boolean ::= "true" | "false"
        null ::= "null"
        ws ::= [ \\t\\n\\r]*
        answer ::= "{{" ws '"answer":' ws string ws "}}"
        """
        
        return grammar.strip()
    
    def validate_response(
        self,
        response_content: str,
        expected_format: Optional[Type[BaseModel]] = None,
        retry_on_failure: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Validate and parse a response with optional Pydantic validation.
        
        Args:
            response_content: Raw response content
            expected_format: Optional Pydantic model for validation
            retry_on_failure: Override retry setting
            
        Returns:
            Parsed and validated response
            
        Raises:
            ValueError: If validation fails and retry is disabled
        """
        if retry_on_failure is None:
            retry_on_failure = self.structured_config.retry_on_failure
        
        # Try to parse as JSON
        try:
            data = json.loads(response_content)
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON response: {e}")
            
            # If it's not JSON, wrap it
            data = {"content": response_content}
        
        # Validate with Pydantic if configured
        if expected_format and self.structured_config.validate_with_pydantic and PYDANTIC_AVAILABLE:
            try:
                validated = expected_format(**data)
                return validated.dict()
            except Exception as e:
                self.logger.warning(f"Pydantic validation failed: {e}")
                
                if not retry_on_failure:
                    raise ValueError(f"Response validation failed: {e}")
                
                # Return raw data if retry is enabled
                return data
        
        return data
    
    def extract_tool_calls(self, response_content: str) -> List[Dict[str, Any]]:
        """
        Extract tool calls from a response.
        
        Args:
            response_content: Response content that may contain tool calls
            
        Returns:
            List of tool call dictionaries
        """
        tool_calls = []
        
        try:
            # Try to parse as JSON first
            data = json.loads(response_content)
            
            # Check for tool_calls field
            if isinstance(data, dict):
                if "tool_calls" in data:
                    tool_calls = data["tool_calls"]
                elif "tool" in data and "arguments" in data:
                    # Single tool call format
                    tool_calls = [{
                        "tool_name": data["tool"],
                        "arguments": data["arguments"]
                    }]
        except json.JSONDecodeError:
            # Try to extract tool calls from text
            # This is a fallback for non-JSON responses
            pass
        
        return tool_calls
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get structured output metrics."""
        return {
            "enabled": self.is_enabled(),
            "backend": self.structured_config.backend,
            "enforcement_level": self.structured_config.enforcement_level,
            "cache_size": len(self._schema_cache) if self._schema_cache else 0
        }


class VLLMEndpointSelector:
    """
    Intelligent endpoint selector for multi-endpoint configurations.
    Automatically selects the best endpoint based on query characteristics.
    """
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize the endpoint selector.
        
        Args:
            config: Configuration dictionary
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Load endpoint configurations
        self.endpoints = config.get('inference_endpoints', {})
        
        # Load routing configuration
        agent_config = config.get('agent', {})
        self.auto_select = agent_config.get('auto_select_endpoint', False)
        self.routing_config = agent_config.get('query_routing', {})
        
        # Tool endpoint overrides
        self.tool_overrides = config.get('tool_endpoint_overrides', {})
        
        self.logger.debug(f"Endpoint selector initialized with {len(self.endpoints)} endpoints")
    
    def select_endpoint(
        self,
        query: str,
        tool_name: Optional[str] = None,
        force_type: Optional[str] = None
    ) -> Optional[str]:
        """
        Select the best endpoint for a query.
        
        Args:
            query: User query
            tool_name: Optional tool name being called
            force_type: Force a specific endpoint type
            
        Returns:
            Endpoint name or None if no selection
        """
        if not self.auto_select and not force_type:
            return None
        
        # Check for tool-specific override
        if tool_name and tool_name in self.tool_overrides:
            endpoint_type = self.tool_overrides[tool_name]
            return self._find_endpoint_by_type(endpoint_type)
        
        # Force specific type if requested
        if force_type:
            return self._find_endpoint_by_type(force_type)
        
        # Analyze query for automatic selection
        if self.auto_select:
            endpoint_type = self._analyze_query(query)
            return self._find_endpoint_by_type(endpoint_type)
        
        return None
    
    def _analyze_query(self, query: str) -> str:
        """
        Analyze a query to determine the best endpoint type.
        
        Args:
            query: User query
            
        Returns:
            Endpoint type (thinking, fast, or balanced)
        """
        query_lower = query.lower()
        
        # Check for thinking keywords
        thinking_keywords = self.routing_config.get('thinking_keywords', [])
        thinking_score = sum(1 for keyword in thinking_keywords if keyword in query_lower)
        
        # Check for fast keywords
        fast_keywords = self.routing_config.get('fast_keywords', [])
        fast_score = sum(1 for keyword in fast_keywords if keyword in query_lower)
        
        # Determine based on scores
        if thinking_score > fast_score and thinking_score > 0:
            self.logger.debug(f"Query analysis: Selected 'thinking' (score: {thinking_score})")
            return "thinking"
        elif fast_score > thinking_score and fast_score > 0:
            self.logger.debug(f"Query analysis: Selected 'fast' (score: {fast_score})")
            return "fast"
        else:
            default = self.routing_config.get('default_type', 'balanced')
            self.logger.debug(f"Query analysis: Selected '{default}' (default)")
            return default
    
    def _find_endpoint_by_type(self, endpoint_type: str) -> Optional[str]:
        """
        Find an endpoint by type.
        
        Args:
            endpoint_type: Type of endpoint to find
            
        Returns:
            Endpoint name or None
        """
        for name, config in self.endpoints.items():
            if config.get('model_type') == endpoint_type:
                return name
        
        self.logger.warning(f"No endpoint found for type: {endpoint_type}")
        return None
    
    def get_endpoint_config(self, endpoint_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific endpoint.
        
        Args:
            endpoint_name: Name of the endpoint
            
        Returns:
            Endpoint configuration or None
        """
        return self.endpoints.get(endpoint_name)


def create_enhanced_agent(
    config_path: str = "config.yaml",
    silent: bool = False,
    name: str = "Agent",
    force_structured: bool = False,
    endpoint_type: Optional[str] = None
) -> Any:
    """
    Factory function to create an agent with vLLM enhancements.
    
    Args:
        config_path: Path to configuration file
        silent: Suppress debug output
        name: Agent name
        force_structured: Force structured output usage
        endpoint_type: Force specific endpoint type
        
    Returns:
        Enhanced OpenRouterAgent instance
    """
    from .agent import OpenRouterAgent
    from .config_manager import ConfigManager
    
    # Load configuration
    config_manager = ConfigManager()
    config = config_manager.config
    
    # Initialize structured output manager
    structured_manager = VLLMStructuredOutputManager(config)
    
    # Initialize endpoint selector
    endpoint_selector = VLLMEndpointSelector(config)
    
    # Determine endpoint to use
    endpoint_name = None
    if endpoint_type:
        endpoint_name = endpoint_selector._find_endpoint_by_type(endpoint_type)
    
    # Determine if structured output should be used
    use_structured = force_structured or structured_manager.is_enabled()
    
    # Create agent with enhancements
    agent = OpenRouterAgent(
        config_path=config_path,
        silent=silent,
        name=name,
        endpoint_name=endpoint_name,
        use_structured_output=use_structured
    )
    
    # Attach managers to agent for access
    agent.structured_manager = structured_manager
    agent.endpoint_selector = endpoint_selector
    
    # Log creation
    logger = logging.getLogger(__name__)
    logger.info(f"Created enhanced agent '{name}' with structured={use_structured}, endpoint={endpoint_name}")
    
    return agent
