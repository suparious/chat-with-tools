"""
OpenRouter Agent with enhanced error handling, monitoring, and performance features.
Consolidated version that includes all features from the enhanced agent.
"""

import json
import os
import yaml
import time
import threading
from typing import Dict, Any, List, Optional
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


class ConnectionPool:
    """Connection pool for OpenAI clients to improve performance."""
    
    _instances: Dict[str, OpenAI] = {}
    
    @classmethod
    def get_client(cls, base_url: str, api_key: str) -> OpenAI:
        """Get or create a client for the given configuration."""
        key = f"{base_url}:{api_key[:8] if api_key else 'local'}"  # Use first 8 chars of API key as identifier
        
        if key not in cls._instances:
            cls._instances[key] = OpenAI(
                base_url=base_url,
                api_key=api_key or 'dummy-key-for-local'
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
        
        # Use centralized config manager
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        
        # Initialize debug logger (singleton will use the same config)
        self.debug_logger = DebugLogger(self.config)
        self.debug_logger.log_separator(f"Agent Initialization - {name}")
        self.debug_logger.info(f"Initializing OpenRouterAgent", 
                               config_path=config_path, 
                               silent=silent, 
                               name=name)
        
        # Set up standard logging using unified config
        # Silent mode overrides config level to WARNING
        log_level = "WARNING" if silent else None
        self.logger = setup_logging(f"{__name__}.{name}", config=self.config, level=log_level)
        
        # Get API configuration from config manager
        self.api_key = self.config_manager.get_api_key()
        self.base_url = self.config_manager.get_base_url()
        self.model = self.config_manager.get_model()
        
        self.debug_logger.info(f"API configuration loaded", 
                               model=self.model,
                               base_url=self.base_url,
                               has_api_key=bool(self.api_key))
        
        # Validate API configuration if required
        if self.config_manager.requires_api_key() and not self.api_key:
            self.logger.warning("API key required but not found. Some endpoints may fail.")
        
        # Initialize OpenAI client
        if self.config.get('performance', {}).get('connection_pooling', False):
            # Use connection pool for better performance
            self.client = ConnectionPool.get_client(self.base_url, self.api_key)
            self.debug_logger.info("Using connection pool for API client")
        else:
            # Use standard client
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
        
        self.debug_logger.info(f"Agent configuration loaded",
                               max_iterations=self.max_iterations,
                               temperature=self.temperature,
                               max_tokens=self.max_tokens)
        self.debug_logger.info("Agent initialization complete")
    
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
            self.debug_logger.log_llm_call(self.model, messages)
            
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
                tool_result = self.tool_mapping[tool_name](**validated_args)
                if self.metrics:
                    self.metrics.record_tool_call(tool_name)
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
                
                # Capture assistant content
                if assistant_message.content:
                    full_response_content.append(assistant_message.content)
                
                # Handle tool calls
                if assistant_message.tool_calls:
                    if not self.silent:
                        print(f"🔧 Agent making {len(assistant_message.tool_calls)} tool call(s)")
                        self.logger.info(f"Processing {len(assistant_message.tool_calls)} tool call(s)")
                    
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
                    
                    if task_completed:
                        return "\n\n".join(full_response_content)
                else:
                    if not self.silent:
                        print("💭 Agent responded without tool calls - continuing loop")
                        self.logger.debug("Agent responded without tool calls")
                
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
        final_response = "\n\n".join(full_response_content) if full_response_content else "Maximum iterations reached. The agent may be stuck in a loop."
        
        self.debug_logger.info("Agent run completed (max iterations)", 
                             final_response_length=len(final_response),
                             iterations=iteration)
        self.debug_logger.log_separator(f"Agent Run Completed - {self.name}")
        
        return final_response
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics."""
        if self.metrics:
            return self.metrics.get_summary()
        return {}
    
    def requires_api_key(self) -> bool:
        """Check if an API key is required."""
        return self.config_manager.requires_api_key()
