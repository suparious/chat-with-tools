"""Enhanced OpenRouter Agent with improved error handling and logging."""

import json
import os
import yaml
from typing import Dict, Any, List, Optional
from openai import OpenAI
from .tools import discover_tools
from .config_manager import ConfigManager, get_openai_client
from .utils import (
    setup_logging, 
    retry_with_backoff, 
    get_env_or_config,
    MetricsCollector,
    RateLimiter
)


class ConnectionPool:
    """Connection pool for OpenAI clients to improve performance."""
    
    _instances: Dict[str, OpenAI] = {}
    
    @classmethod
    def get_client(cls, base_url: str, api_key: str) -> OpenAI:
        """Get or create a client for the given configuration."""
        key = f"{base_url}:{api_key[:8]}"  # Use first 8 chars of API key as identifier
        
        if key not in cls._instances:
            cls._instances[key] = OpenAI(
                base_url=base_url,
                api_key=api_key
            )
        
        return cls._instances[key]


class OpenRouterAgent:
    """Enhanced OpenRouter agent with robust error handling and monitoring."""
    
    def __init__(self, config_path: str = "config.yaml", silent: bool = False, name: str = "Agent"):
        """
        Initialize the OpenRouter agent.
        
        Args:
            config_path: Path to configuration file (kept for compatibility)
            silent: If True, suppress debug output
            name: Name for this agent instance (useful for multi-agent scenarios)
        """
        self.name = name
        self.silent = silent
        
        # Set up logging
        log_level = "WARNING" if silent else "INFO"
        self.logger = setup_logging(f"{__name__}.{name}", level=log_level)
        
        # Use centralized config manager
        try:
            self.config_manager = ConfigManager()
            self.config = self.config_manager.config
            self.logger.info(f"Loaded configuration via ConfigManager")
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
        
        # Get API configuration from config manager
        self.api_key = self.config_manager.get_api_key()
        self.base_url = self.config_manager.get_base_url()
        self.model = self.config_manager.get_model()
        
        # Validate API configuration if required
        if self.config_manager.requires_api_key() and not self.api_key:
            self.logger.warning("API key required but not found. Some endpoints may fail.")
        
        # Initialize OpenAI client using centralized function
        self.client = get_openai_client()
        self.logger.info(f"Initialized client for model: {self.model}")
        
        # Initialize metrics collector
        self.metrics = MetricsCollector()
        
        # Initialize rate limiter (10 requests per second by default)
        rate_limit = self.config.get('agent', {}).get('rate_limit', 10)
        self.rate_limiter = RateLimiter(rate=rate_limit, per=1.0)
        
        # Discover and load tools
        self.discovered_tools = discover_tools(self.config, silent=self.silent)
        self.tools = [tool.to_openrouter_schema() for tool in self.discovered_tools.values()]
        self.tool_mapping = {name: tool.execute for name, tool in self.discovered_tools.items()}
        
        self.logger.info(f"Loaded {len(self.discovered_tools)} tools: {list(self.discovered_tools.keys())}")
        
        # Agent configuration
        self.max_iterations = self.config.get('agent', {}).get('max_iterations', 10)
        self.temperature = self.config.get('agent', {}).get('temperature', 0.7)
        self.max_tokens = self.config.get('agent', {}).get('max_tokens', None)
    
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def call_llm(self, messages: List[Dict[str, Any]]) -> Any:
        """
        Make OpenRouter API call with tools and retry logic.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            OpenAI completion response
            
        Raises:
            Exception: If API call fails after retries
        """
        # Apply rate limiting
        self.rate_limiter.wait_if_needed()
        
        try:
            self.logger.debug(f"Making LLM call with {len(messages)} messages")
            
            # Build request parameters
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature
            }
            
            # Add tools if available
            if self.tools:
                request_params["tools"] = self.tools
            
            # Add max_tokens if specified
            if self.max_tokens:
                request_params["max_tokens"] = self.max_tokens
            
            # Make API call
            response = self.client.chat.completions.create(**request_params)
            
            # Record metrics
            if hasattr(response, 'usage'):
                total_tokens = response.usage.total_tokens if response.usage else 0
                self.metrics.record_api_call(tokens=total_tokens)
                self.logger.debug(f"API call used {total_tokens} tokens")
            
            return response
            
        except Exception as e:
            self.metrics.record_error()
            self.logger.error(f"LLM call failed: {str(e)}")
            raise Exception(f"LLM call failed: {str(e)}")
    
    def validate_tool_arguments(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate tool arguments before execution.
        
        Args:
            tool_name: Name of the tool
            tool_args: Arguments to validate
            
        Returns:
            Validated and potentially sanitized arguments
        """
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
            tool_args = json.loads(tool_call.function.arguments)
            
            # Validate arguments
            validated_args = self.validate_tool_arguments(tool_name, tool_args)
            
            # Execute tool
            if tool_name in self.tool_mapping:
                self.logger.debug(f"Executing tool '{tool_name}' with args: {validated_args}")
                tool_result = self.tool_mapping[tool_name](**validated_args)
                self.metrics.record_tool_call(tool_name)
            else:
                tool_result = {"error": f"Unknown tool: {tool_name}"}
                self.logger.error(f"Unknown tool requested: {tool_name}")
            
            # Return tool result message
            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json.dumps(tool_result)
            }
        
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse tool arguments for '{tool_name}': {e}")
            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json.dumps({"error": f"Invalid tool arguments: {str(e)}"})
            }
        
        except ValueError as e:
            self.logger.error(f"Tool argument validation failed for '{tool_name}': {e}")
            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json.dumps({"error": f"Validation error: {str(e)}"})
            }
        
        except Exception as e:
            self.logger.error(f"Tool execution failed for '{tool_name}': {e}")
            self.metrics.record_error()
            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json.dumps({"error": f"Tool execution failed: {str(e)}"})
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
        self.logger.info(f"Processing user input: {user_input[:100]}...")
        
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
        
        while iteration < self.max_iterations:
            iteration += 1
            
            if not self.silent:
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
                
                # Capture assistant content
                if assistant_message.content:
                    full_response_content.append(assistant_message.content)
                
                # Handle tool calls
                if assistant_message.tool_calls:
                    if not self.silent:
                        self.logger.info(f"Processing {len(assistant_message.tool_calls)} tool call(s)")
                    
                    task_completed = False
                    
                    for tool_call in assistant_message.tool_calls:
                        if not self.silent:
                            self.logger.debug(f"Calling tool: {tool_call.function.name}")
                        
                        tool_result = self.handle_tool_call(tool_call)
                        messages.append(tool_result)
                        
                        # Check for task completion
                        if tool_call.function.name == "mark_task_complete":
                            task_completed = True
                            if not self.silent:
                                self.logger.info("Task marked as complete")
                            return "\n\n".join(full_response_content)
                    
                    if task_completed:
                        return "\n\n".join(full_response_content)
                else:
                    if not self.silent:
                        self.logger.debug("Agent responded without tool calls")
                
            except Exception as e:
                self.logger.error(f"Error in agent iteration {iteration}: {e}")
                self.metrics.record_error()
                
                # Add error to response
                error_message = f"I encountered an error: {str(e)}. Let me try a different approach."
                full_response_content.append(error_message)
                
                # Add error message to conversation
                messages.append({
                    "role": "assistant",
                    "content": error_message
                })
                
                # Continue to next iteration
                if iteration >= self.max_iterations - 1:
                    break
        
        # Log metrics summary
        if not self.silent:
            metrics_summary = self.metrics.get_summary()
            self.logger.info(f"Agent metrics: {metrics_summary}")
        
        # Return accumulated response
        final_response = "\n\n".join(full_response_content) if full_response_content else "I apologize, but I couldn't generate a proper response. Please try again."
        
        return final_response
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics."""
        return self.metrics.get_summary()
