"""
OpenRouter Agent with enhanced error handling, monitoring, and performance features.
Includes optional support for vLLM structured outputs and multiple inference endpoints.
All enhanced features are backwards compatible and disabled by default.
"""

import json
import os
import yaml
import time
import threading
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from openai import OpenAI
from .tools import discover_tools
from .config_manager import ConfigManager, get_openai_client
from .utils import (
    DebugLogger, 
    setup_logging, 
    retry_with_backoff, 
    get_env_or_config,
    MetricsCollector,
    RateLimiter
)

# Only import pydantic if needed for structured output
try:
    from pydantic import BaseModel, Field, validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False


class ModelType(Enum):
    """Enumeration of model types for different use cases."""
    THINKING = "thinking"  # Deep reasoning models (Qwen-QwQ, o1)
    FAST = "fast"          # Quick response models (gpt-4o-mini, sonnet)
    BALANCED = "balanced"  # Balanced performance (gpt-4, claude-3)
    LOCAL = "local"        # Local vLLM models
    CUSTOM = "custom"      # Custom endpoints


class InferenceEndpoint:
    """Configuration for an inference endpoint."""
    def __init__(self, name: str, base_url: str, model: str, **kwargs):
        self.name = name
        self.base_url = base_url
        self.model = model
        self.api_key = kwargs.get('api_key')
        self.model_type = ModelType(kwargs.get('model_type', 'custom'))
        self.temperature = kwargs.get('temperature', 0.7)
        self.max_tokens = kwargs.get('max_tokens')
        self.supports_tools = kwargs.get('supports_tools', True)
        self.supports_structured_output = kwargs.get('supports_structured_output', False)
        self.is_vllm = kwargs.get('is_vllm', False)


class MultiEndpointManager:
    """Manages multiple inference endpoints for different model types."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration."""
        self.config = config
        self.endpoints: Dict[str, InferenceEndpoint] = {}
        self.clients: Dict[str, OpenAI] = {}
        self._enabled = False
        self._load_endpoints()
    
    def _load_endpoints(self):
        """Load endpoints from configuration."""
        # Load primary endpoint from existing config
        primary_config = self.config.get('openrouter', {})
        is_vllm = primary_config.get('is_vllm', False)
        primary_endpoint = InferenceEndpoint(
            name="primary",
            base_url=primary_config.get('base_url', 'https://openrouter.ai/api/v1'),
            model=primary_config.get('model', 'openai/gpt-4-mini'),
            api_key=primary_config.get('api_key'),
            model_type='balanced',
            temperature=primary_config.get('temperature', 0.7),
            max_tokens=primary_config.get('max_tokens'),
            supports_tools=True,
            supports_structured_output=is_vllm,  # If it's vLLM, it supports structured output
            is_vllm=is_vllm
        )
        self.endpoints["primary"] = primary_endpoint
        
        # Load additional endpoints if configured
        endpoints_config = self.config.get('inference_endpoints', {})
        if endpoints_config:
            self._enabled = True
            for name, endpoint_data in endpoints_config.items():
                # Replace environment variables in api_key if present
                if 'api_key' in endpoint_data and isinstance(endpoint_data['api_key'], str):
                    if endpoint_data['api_key'].startswith('${') and endpoint_data['api_key'].endswith('}'):
                        env_var = endpoint_data['api_key'][2:-1]
                        endpoint_data['api_key'] = os.environ.get(env_var, '')
                
                endpoint = InferenceEndpoint(name=name, **endpoint_data)
                self.endpoints[name] = endpoint
    
    def is_enabled(self) -> bool:
        """Check if multi-endpoint feature is enabled."""
        return self._enabled
    
    def get_client(self, endpoint_name: str = "primary") -> OpenAI:
        """Get or create a client for the specified endpoint."""
        if endpoint_name not in self.endpoints:
            endpoint_name = "primary"  # Fallback to primary
        
        if endpoint_name not in self.clients:
            endpoint = self.endpoints[endpoint_name]
            self.clients[endpoint_name] = OpenAI(
                base_url=endpoint.base_url,
                api_key=endpoint.api_key or 'dummy-key-for-local'
            )
        
        return self.clients[endpoint_name]
    
    def get_endpoint(self, endpoint_name: str = "primary") -> InferenceEndpoint:
        """Get endpoint configuration."""
        if endpoint_name not in self.endpoints:
            return self.endpoints["primary"]  # Fallback to primary
        return self.endpoints[endpoint_name]
    
    def get_endpoint_by_type(self, model_type: ModelType) -> Optional[InferenceEndpoint]:
        """Get the first endpoint matching the specified model type."""
        for endpoint in self.endpoints.values():
            if endpoint.model_type == model_type:
                return endpoint
        return None


class ConnectionPool:
    """Connection pool for OpenAI clients to improve performance."""
    
    _instances: Dict[str, OpenAI] = {}
    
    @classmethod
    def get_client(cls, base_url: str, api_key: str) -> OpenAI:
        """Get or create a client for the given configuration."""
        key = f"{base_url}:{api_key[:8] if api_key else 'local'}"
        
        if key not in cls._instances:
            cls._instances[key] = OpenAI(
                base_url=base_url,
                api_key=api_key or 'dummy-key-for-local'
            )
        
        return cls._instances[key]


class OpenRouterAgent:
    """Enhanced OpenRouter agent with robust error handling and monitoring."""
    
    def __init__(self, config_path: str = "config.yaml", silent: bool = False, name: str = "Agent", 
                 endpoint_name: Optional[str] = None, use_structured_output: Optional[bool] = None):
        """
        Initialize the OpenRouter agent.
        
        Args:
            config_path: Path to configuration file (kept for compatibility)
            silent: If True, suppress debug output
            name: Name for this agent instance (useful for multi-agent scenarios)
            endpoint_name: Optional name of the inference endpoint to use
            use_structured_output: Optional override for structured output usage
        """
        self.name = name
        self.silent = silent
        
        # Use centralized config manager
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        
        # Initialize debug logger
        self.debug_logger = DebugLogger(self.config)
        self.debug_logger.log_separator(f"Agent Initialization - {name}")
        self.debug_logger.info(f"Initializing OpenRouterAgent", 
                               config_path=config_path, 
                               silent=silent, 
                               name=name)
        
        # Set up standard logging
        log_level = "WARNING" if silent else None
        self.logger = setup_logging(f"{__name__}.{name}", config=self.config, level=log_level)
        
        # Initialize multi-endpoint manager
        self.endpoint_manager = MultiEndpointManager(self.config)
        
        # Determine which endpoint to use
        if endpoint_name and self.endpoint_manager.is_enabled():
            self.endpoint_name = endpoint_name
        else:
            self.endpoint_name = "primary"
        
        # Get the endpoint configuration
        self.endpoint = self.endpoint_manager.get_endpoint(self.endpoint_name)
        
        # Determine if structured output should be used
        vllm_config = self.config.get('vllm_structured_output', {})
        if use_structured_output is not None:
            self.use_structured_output = use_structured_output
        else:
            self.use_structured_output = (
                vllm_config.get('enabled', False) and 
                self.endpoint.supports_structured_output and
                PYDANTIC_AVAILABLE
            )
        
        # Log structured output status at INFO level
        if self.use_structured_output:
            self.logger.info(f"✅ vLLM Structured Output ENABLED - Backend: {vllm_config.get('backend', 'outlines')}, Enforcement: {vllm_config.get('enforcement_level', 'strict')}")
        elif vllm_config.get('enabled', False) and not self.endpoint.supports_structured_output:
            self.logger.warning(f"⚠️  Structured output enabled in config but endpoint '{self.endpoint_name}' doesn't support it")
        elif vllm_config.get('enabled', False) and not PYDANTIC_AVAILABLE:
            self.logger.warning("⚠️  Structured output enabled but Pydantic not available - install with: pip install pydantic")
        
        # Get API configuration
        self.api_key = self.config_manager.get_api_key()
        self.base_url = self.config_manager.get_base_url()
        self.model = self.config_manager.get_model()
        
        # Override with endpoint configuration if using multi-endpoint
        if self.endpoint_manager.is_enabled() and self.endpoint_name != "primary":
            self.api_key = self.endpoint.api_key or self.api_key
            self.base_url = self.endpoint.base_url
            self.model = self.endpoint.model
        
        self.debug_logger.info(f"API configuration loaded", 
                               model=self.model,
                               base_url=self.base_url,
                               has_api_key=bool(self.api_key),
                               endpoint=self.endpoint_name,
                               multi_endpoint_enabled=self.endpoint_manager.is_enabled(),
                               structured_output_enabled=self.use_structured_output)
        
        # Validate API configuration if required
        if self.config_manager.requires_api_key() and not self.api_key:
            self.logger.warning("API key required but not found. Some endpoints may fail.")
        
        # Initialize OpenAI client
        if self.config.get('performance', {}).get('connection_pooling', False):
            # Use connection pool for better performance
            self.client = ConnectionPool.get_client(self.base_url, self.api_key)
            self.debug_logger.info("Using connection pool for API client")
        else:
            # Use standard client or endpoint-specific client
            if self.endpoint_manager.is_enabled():
                self.client = self.endpoint_manager.get_client(self.endpoint_name)
            else:
                self.client = get_openai_client()
            self.debug_logger.info("Using standard API client")
        
        # Initialize metrics collector if enabled
        if self.config.get('performance', {}).get('collect_metrics', False):
            self.metrics = MetricsCollector()
            self.debug_logger.info("Metrics collection enabled")
        else:
            self.metrics = None
        
        # Initialize rate limiter
        rate_limit = self.config.get('agent', {}).get('rate_limit', 10)
        self.rate_limiter = RateLimiter(rate=rate_limit, per=1.0)
        self.debug_logger.info(f"Rate limiter initialized", rate_limit=rate_limit)
        
        # Discover and load tools
        self.discovered_tools = discover_tools(self.config, silent=self.silent)
        self.tools = [tool.to_openrouter_schema() for tool in self.discovered_tools.values()]
        self.tool_mapping = {name: tool.execute for name, tool in self.discovered_tools.items()}
        
        self.debug_logger.info(f"Discovered {len(self.discovered_tools)} tools", 
                               tools=list(self.discovered_tools.keys()))
        self.logger.info(f"Loaded {len(self.discovered_tools)} tools: {list(self.discovered_tools.keys())}")
        
        # Agent configuration
        agent_config = self.config.get('agent', {})
        self.max_iterations = agent_config.get('max_iterations', 10)
        self.temperature = agent_config.get('temperature', 0.7)
        self.max_tokens = agent_config.get('max_tokens', None)
        
        # Override temperature and max_tokens from endpoint if available
        if self.endpoint_manager.is_enabled() and self.endpoint_name != "primary":
            if self.endpoint.temperature is not None:
                self.temperature = self.endpoint.temperature
            if self.endpoint.max_tokens is not None:
                self.max_tokens = self.endpoint.max_tokens
        
        self.debug_logger.info(f"Agent configuration loaded",
                               max_iterations=self.max_iterations,
                               temperature=self.temperature,
                               max_tokens=self.max_tokens)
        self.debug_logger.info("Agent initialization complete")
    
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def call_llm(self, messages: List[Dict[str, Any]], force_no_tools: bool = False) -> Any:
        """
        Make OpenRouter API call with tools and retry logic.
        
        Args:
            messages: List of message dictionaries
            force_no_tools: If True, don't include tools in the request
            
        Returns:
            OpenAI completion response
            
        Raises:
            Exception: If API call fails after retries
        """
        # Apply rate limiting
        self.rate_limiter.wait_if_needed()
        
        try:
            self.logger.debug(f"Making LLM call with {len(messages)} messages")
            self.debug_logger.log_llm_call(self.model, messages)
            
            # Build request parameters
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature
            }
            
            # Add tools if available and not forced to exclude
            if self.tools and not force_no_tools and self.endpoint.supports_tools:
                request_params["tools"] = self.tools
            
            # Add max_tokens if specified
            if self.max_tokens:
                request_params["max_tokens"] = self.max_tokens
            
            # Add structured output format if using vLLM with structured output
            if self.use_structured_output and self.endpoint.supports_structured_output:
                vllm_config = self.config.get('vllm_structured_output', {})
                backend = vllm_config.get('backend', 'outlines')
                
                # Log at INFO level when using structured output
                self.logger.info(f"📝 Using vLLM structured output for this request (backend: {backend})")
                
                # The vLLM server with Outlines backend requires a proper schema
                # It does NOT support simple json_object type
                try:
                    if backend == "outlines" and self.tools and not force_no_tools:
                        # For tool calling, create a schema that matches expected format
                        tool_names = [tool["function"]["name"] for tool in self.tools if "function" in tool]
                        
                        # Basic schema for structured tool calling
                        schema = {
                            "type": "object",
                            "properties": {
                                "thought": {
                                    "type": "string",
                                    "description": "Brief reasoning about the task"
                                },
                                "action": {
                                    "type": "string",
                                    "enum": ["tool_call", "direct_answer"],
                                    "description": "Whether to call a tool or answer directly"
                                },
                                "tool_name": {
                                    "type": "string",
                                    "enum": tool_names,
                                    "description": "Name of the tool to call (if action is tool_call)"
                                },
                                "tool_args": {
                                    "type": "object",
                                    "description": "Arguments for the tool (if action is tool_call)"
                                },
                                "answer": {
                                    "type": "string",
                                    "description": "Direct answer to user (if action is direct_answer)"
                                }
                            },
                            "required": ["thought", "action"]
                        }
                        
                        # Use guided_json with the schema for Outlines backend
                        request_params["extra_body"] = {
                            "guided_json": schema,
                            "guided_decoding_backend": "outlines"
                        }
                        self.logger.debug(f"Added guided_json schema for {len(tool_names)} tools")
                    elif backend != "outlines":
                        # For other backends, use OpenAI-style format
                        simple_schema = {
                            "type": "object",
                            "properties": {
                                "response": {"type": "string"}
                            },
                            "required": ["response"]
                        }
                        request_params["response_format"] = {
                            "type": "json_schema",
                            "json_schema": {
                                "name": "response",
                                "schema": simple_schema
                            }
                        }
                        self.logger.debug("Added response_format for non-Outlines backend")
                    else:
                        # For non-tool requests with Outlines, skip structured output for now
                        # to avoid crashes until we have a better general-purpose schema
                        self.logger.debug("Skipping structured output for non-tool request with Outlines")
                except Exception as e:
                    self.logger.warning(f"Could not add structured output format: {e}")
                    # Continue without structured output if there's an issue
            
            # Make API call
            response = self.client.chat.completions.create(**request_params)
            
            # Record metrics if enabled
            if self.metrics:
                if hasattr(response, 'usage'):
                    total_tokens = response.usage.total_tokens if response.usage else 0
                    self.metrics.record_api_call(tokens=total_tokens)
                    self.logger.debug(f"API call used {total_tokens} tokens")
            
            self.debug_logger.log_llm_call(self.model, messages, response=response)
            return response
            
        except Exception as e:
            if self.metrics:
                self.metrics.record_error()
            self.logger.error(f"LLM call failed: {str(e)}")
            self.debug_logger.log_llm_call(self.model, messages, error=str(e))
            raise Exception(f"LLM call failed: {str(e)}")
    
    def parse_structured_response(self, response_content: str) -> Optional[Dict[str, Any]]:
        """
        Parse a structured response from vLLM.
        
        Args:
            response_content: Raw response content
            
        Returns:
            Parsed structured response or None if not structured
        """
        if not self.use_structured_output:
            return None
            
        try:
            # Try to parse as JSON
            data = json.loads(response_content)
            
            # Check if it's our structured format
            if isinstance(data, dict) and "action" in data:
                if data["action"] == "tool_call" and "tool_name" in data and "tool_args" in data:
                    # Convert to standard tool call format
                    return {
                        "type": "tool_call",
                        "tool_name": data["tool_name"],
                        "arguments": data.get("tool_args", {}),
                        "thought": data.get("thought", "")
                    }
                elif data["action"] == "direct_answer" and "answer" in data:
                    # Direct answer without tools
                    return {
                        "type": "direct_answer",
                        "content": data["answer"],
                        "thought": data.get("thought", "")
                    }
            
            # Return raw parsed data if it's JSON but not our format
            return data
            
        except json.JSONDecodeError:
            # Not JSON, not structured
            return None
        except Exception as e:
            self.logger.debug(f"Error parsing structured response: {e}")
            return None
    
    def validate_tool_arguments(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate tool arguments before execution.
        
        Args:
            tool_name: Name of the tool
            tool_args: Arguments to validate
            
        Returns:
            Validated and potentially sanitized arguments
        """
        # Ensure tool_args is a dictionary
        if not isinstance(tool_args, dict):
            self.logger.warning(f"Tool arguments for {tool_name} are not a dictionary, converting: {type(tool_args)}")
            if isinstance(tool_args, str):
                # Try to parse as JSON one more time
                try:
                    tool_args = json.loads(tool_args)
                except:
                    # If it fails, wrap in a query parameter if applicable
                    tool = self.discovered_tools.get(tool_name)
                    if tool and 'query' in tool.parameters.get('properties', {}):
                        tool_args = {"query": tool_args}
                    else:
                        tool_args = {}
            else:
                tool_args = {}
        
        # Get tool schema
        tool = self.discovered_tools.get(tool_name)
        if not tool:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        # Get parameter schema
        params_schema = tool.parameters.get('properties', {})
        required_params = tool.parameters.get('required', [])
        
        # Check required parameters
        for param in required_params:
            if param not in tool_args:
                # Try to provide a helpful default or error message
                if param == 'query' and len(tool_args) == 1:
                    # If there's only one argument and we need 'query', use it
                    single_key = list(tool_args.keys())[0]
                    tool_args['query'] = tool_args[single_key]
                else:
                    raise ValueError(f"Missing required parameter '{param}' for tool '{tool_name}'")
        
        # Validate parameter types (basic validation)
        validated_args = {}
        for param, value in tool_args.items():
            if param in params_schema:
                param_type = params_schema[param].get('type')
                
                # Basic type validation
                if param_type == 'string' and not isinstance(value, str):
                    validated_args[param] = str(value)
                elif param_type == 'integer' and not isinstance(value, int):
                    validated_args[param] = int(value)
                elif param_type == 'number' and not isinstance(value, (int, float)):
                    validated_args[param] = float(value)
                elif param_type == 'boolean' and not isinstance(value, bool):
                    validated_args[param] = bool(value)
                else:
                    validated_args[param] = value
            else:
                # Parameter not in schema, include it anyway (for flexibility)
                validated_args[param] = value
        
        return validated_args
    
    def handle_tool_call(self, tool_call: Any) -> Dict[str, Any]:
        """
        Handle a tool call with validation and error handling.
        
        Args:
            tool_call: Tool call object from OpenAI response
            
        Returns:
            Tool result message dictionary
        """
        tool_name = tool_call.function.name
        
        try:
            # Parse tool arguments
            raw_args = tool_call.function.arguments
            
            # Handle different argument formats
            if isinstance(raw_args, str):
                try:
                    tool_args = json.loads(raw_args)
                    # Double-check if the result is still a string (double-encoded JSON)
                    if isinstance(tool_args, str):
                        try:
                            tool_args = json.loads(tool_args)
                        except:
                            pass
                except json.JSONDecodeError:
                    # If it's just a string and the tool expects a 'query' parameter,
                    # wrap it in a dict
                    tool = self.discovered_tools.get(tool_name)
                    if tool and 'query' in tool.parameters.get('properties', {}):
                        tool_args = {"query": raw_args}
                    else:
                        raise json.JSONDecodeError(f"Could not parse arguments: {raw_args}", raw_args, 0)
            elif isinstance(raw_args, dict):
                tool_args = raw_args
            else:
                # Convert to dict if possible
                tool_args = dict(raw_args) if hasattr(raw_args, '__dict__') else {}
            
            # Ensure tool_args is a dictionary
            if not isinstance(tool_args, dict):
                self.logger.error(f"Tool arguments are not a dictionary: {type(tool_args)} - {tool_args}")
                # Try one more time to parse if it's a string
                if isinstance(tool_args, str):
                    try:
                        tool_args = json.loads(tool_args)
                    except:
                        tool_args = {}
                else:
                    tool_args = {}
            
            # Validate arguments if validation is enabled
            if self.config.get('security', {}).get('validate_input', True):
                validated_args = self.validate_tool_arguments(tool_name, tool_args)
            else:
                validated_args = tool_args
            
            self.debug_logger.log_tool_call(tool_name, validated_args)
            
            # Execute tool
            if tool_name in self.tool_mapping:
                if not self.silent:
                    self.logger.debug(f"Executing tool '{tool_name}' with args: {validated_args}")
                
                try:
                    tool_result = self.tool_mapping[tool_name](**validated_args)
                    
                    # Ensure tool_result is JSON serializable
                    if not isinstance(tool_result, (dict, list, str, int, float, bool, type(None))):
                        # Convert to string if not a basic type
                        tool_result = str(tool_result)
                    
                    if self.metrics:
                        self.metrics.record_tool_call(tool_name)
                except TypeError as e:
                    # Handle cases where arguments don't match tool signature
                    error_msg = f"Argument mismatch for tool {tool_name}: {str(e)}"
                    self.logger.error(error_msg)
                    tool_result = {"error": error_msg}
                except Exception as e:
                    # Handle any other tool execution errors
                    error_msg = f"Tool execution error: {str(e)}"
                    self.logger.error(f"Error executing tool {tool_name}: {e}")
                    tool_result = {"error": error_msg}
            else:
                tool_result = {"error": f"Unknown tool: {tool_name}"}
                self.logger.error(f"Unknown tool requested: {tool_name}")
            
            self.debug_logger.log_tool_call(tool_name, validated_args, result=tool_result)
            
            # Return tool result message
            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json.dumps(tool_result)
            }
        
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse tool arguments: {str(e)}"
            self.logger.error(f"Failed to parse tool arguments for '{tool_name}': {e}")
            self.debug_logger.log_tool_call(tool_name, {}, error=error_msg)
            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json.dumps({"error": error_msg})
            }
        
        except ValueError as e:
            error_msg = f"Validation error: {str(e)}"
            self.logger.error(f"Tool argument validation failed for '{tool_name}': {e}")
            self.debug_logger.log_tool_call(tool_name, tool_args if 'tool_args' in locals() else {}, error=error_msg)
            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json.dumps({"error": error_msg})
            }
        
        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            self.logger.error(f"Tool execution failed for '{tool_name}': {e}")
            if self.metrics:
                self.metrics.record_error()
            self.debug_logger.log_tool_call(tool_name, validated_args if 'validated_args' in locals() else {}, error=error_msg)
            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json.dumps({"error": error_msg})
            }
    
    def run(self, user_input: str, context: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Run the agent with user input and return the complete response.
        
        Args:
            user_input: User's input message
            context: Optional conversation context (previous messages)
            
        Returns:
            Complete agent response as a string
        """
        self.debug_logger.log_separator(f"Agent Run Started - {self.name}")
        self.debug_logger.info("User input received", input=user_input[:100] + "..." if len(user_input) > 100 else user_input)
        self.logger.info(f"Processing user input: {user_input[:100]}...")
        
        # Record start time for metrics
        start_time = time.time()
        
        # Initialize messages
        messages = []
        
        # Add context if provided
        if context:
            messages.extend(context)
        else:
            # Add system prompt
            system_prompt = self.config.get('system_prompt', 
                                           "You are a helpful AI assistant.")
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Add user input
        messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Track all assistant responses
        full_response_content = []
        
        # Implement agentic loop
        iteration = 0
        tool_was_used = False
        
        while iteration < self.max_iterations:
            iteration += 1
            self.debug_logger.log_agent_iteration(iteration, self.max_iterations, agent_id=self.name)
            
            if not self.silent:
                print(f"🔄 Agent iteration {iteration}/{self.max_iterations}")
                self.logger.info(f"Agent iteration {iteration}/{self.max_iterations}")
            
            try:
                # Call LLM
                response = self.call_llm(messages)
                
                # Extract assistant message
                assistant_message = response.choices[0].message
                
                # Add to messages
                message_dict = {
                    "role": "assistant",
                    "content": assistant_message.content
                }
                
                # Add tool calls if present
                if assistant_message.tool_calls:
                    message_dict["tool_calls"] = assistant_message.tool_calls
                
                messages.append(message_dict)
                
                # Capture assistant content if present
                if assistant_message.content:
                    full_response_content.append(assistant_message.content)
                
                # Handle tool calls
                if assistant_message.tool_calls:
                    if not self.silent:
                        print(f"🔧 Agent making {len(assistant_message.tool_calls)} tool call(s)")
                        self.logger.info(f"Processing {len(assistant_message.tool_calls)} tool call(s)")
                    
                    tool_was_used = True
                    task_completed = False
                    
                    for tool_call in assistant_message.tool_calls:
                        if not self.silent:
                            print(f"   📞 Calling tool: {tool_call.function.name}")
                            self.logger.debug(f"Calling tool: {tool_call.function.name}")
                        
                        tool_result = self.handle_tool_call(tool_call)
                        messages.append(tool_result)
                        
                        # Check for task completion
                        if tool_call.function.name == "mark_task_complete":
                            task_completed = True
                            self.debug_logger.info("Task completion tool called - ending agent loop")
                            
                            # If we have tool results but no final response, get one
                            if tool_was_used and len(full_response_content) == 0:
                                # Get final response without tools
                                final_messages = messages + [{
                                    "role": "system",
                                    "content": "Please provide a final response summarizing the results."
                                }]
                                
                                try:
                                    final_response_obj = self.call_llm(final_messages, force_no_tools=True)
                                    final_content = final_response_obj.choices[0].message.content
                                    if final_content:
                                        full_response_content.append(final_content)
                                except:
                                    pass
                            
                            if not self.silent:
                                print("✅ Task completion tool called - exiting loop")
                                self.logger.info("Task marked as complete")
                            
                            # Record metrics
                            if self.metrics:
                                execution_time = time.time() - start_time
                                self.metrics.record_response_time(execution_time)
                            
                            final_response = "\n\n".join(full_response_content)
                            self.debug_logger.info("Agent run completed", 
                                                 final_response_length=len(final_response),
                                                 execution_time=execution_time if self.metrics else None)
                            self.debug_logger.log_separator(f"Agent Run Completed - {self.name}")
                            return final_response
                    
                    # After tool calls, continue to get the assistant's response
                    # that incorporates the tool results
                    if not task_completed:
                        continue
                else:
                    # No tool calls, check if we got a response
                    if assistant_message.content:
                        # We have a direct response, we're likely done
                        if not self.silent:
                            print("💭 Agent provided direct response")
                            self.logger.debug("Agent responded without tool calls")
                        
                        # If this is the first iteration with a direct answer, we're done
                        if iteration == 1 or not tool_was_used:
                            break
                        
                        # If tools were used and we got a final response, we're done
                        if tool_was_used and assistant_message.content:
                            break
                
            except Exception as e:
                self.logger.error(f"Error in agent iteration {iteration}: {e}")
                if self.metrics:
                    self.metrics.record_error()
                
                # Add error to response
                error_message = f"I encountered an error: {str(e)}. Let me try a different approach."
                full_response_content.append(error_message)
                
                # Add error message to conversation
                messages.append({
                    "role": "assistant",
                    "content": error_message
                })
                
                # Continue to next iteration unless we're at the limit
                if iteration >= self.max_iterations - 1:
                    break
        
        # Log metrics summary if enabled
        if self.metrics and not self.silent:
            metrics_summary = self.metrics.get_summary()
            self.logger.info(f"Agent metrics: {metrics_summary}")
        
        # Record final execution time
        if self.metrics:
            execution_time = time.time() - start_time
            self.metrics.record_response_time(execution_time)
        
        # Return accumulated response
        if full_response_content:
            final_response = "\n\n".join(full_response_content)
        else:
            final_response = "I apologize, but I couldn't generate a proper response. Please try rephrasing your question."
        
        self.debug_logger.info("Agent run completed (max iterations)", 
                             final_response_length=len(final_response),
                             iterations=iteration)
        self.debug_logger.log_separator(f"Agent Run Completed - {self.name}")
        
        return final_response
    
    def run_thinking(self, user_input: str, context: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Run the agent using a thinking model for deep reasoning.
        Automatically switches to a thinking endpoint if available.
        
        Args:
            user_input: User's input message
            context: Optional conversation context
            
        Returns:
            Complete agent response as a string
        """
        # Only try to use thinking endpoint if multi-endpoint is enabled
        if not self.endpoint_manager.is_enabled():
            self.logger.debug("Multi-endpoint not configured, using standard run")
            return self.run(user_input, context)
        
        # Try to find a thinking endpoint
        thinking_endpoint = self.endpoint_manager.get_endpoint_by_type(ModelType.THINKING)
        if thinking_endpoint:
            # Temporarily switch to thinking endpoint
            original_endpoint = self.endpoint_name
            original_model = self.model
            original_temp = self.temperature
            original_max_tokens = self.max_tokens
            
            self.endpoint_name = thinking_endpoint.name
            self.endpoint = thinking_endpoint
            self.client = self.endpoint_manager.get_client(thinking_endpoint.name)
            self.model = thinking_endpoint.model
            self.temperature = thinking_endpoint.temperature or self.temperature
            self.max_tokens = thinking_endpoint.max_tokens or self.max_tokens
            
            try:
                response = self.run(user_input, context)
            finally:
                # Restore original endpoint
                self.endpoint_name = original_endpoint
                self.endpoint = self.endpoint_manager.get_endpoint(original_endpoint)
                self.client = self.endpoint_manager.get_client(original_endpoint)
                self.model = original_model
                self.temperature = original_temp
                self.max_tokens = original_max_tokens
            
            return response
        else:
            # No thinking endpoint available, use regular run
            self.logger.warning("No thinking endpoint configured, using regular model")
            return self.run(user_input, context)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics."""
        if self.metrics:
            return self.metrics.get_summary()
        return {}
    
    def requires_api_key(self) -> bool:
        """Check if an API key is required."""
        return self.config_manager.requires_api_key()
