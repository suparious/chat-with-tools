"""Utility functions for the Chat with Tools framework."""

import json
import logging
import logging.handlers
import os
import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from urllib.parse import urlparse

# Type variable for generic decorator
F = TypeVar('F', bound=Callable[..., Any])


def setup_logging(name: str, level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with consistent formatting.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
) -> Callable[[F], F]:
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay after each retry
        max_delay: Maximum delay between retries
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        # Log retry attempt
                        if hasattr(args[0], 'logger'):
                            args[0].logger.warning(
                                f"Attempt {attempt + 1} failed: {str(e)}. "
                                f"Retrying in {delay:.1f} seconds..."
                            )
                        
                        time.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                    else:
                        # Max retries exceeded
                        if hasattr(args[0], 'logger'):
                            args[0].logger.error(
                                f"Max retries ({max_retries}) exceeded. Last error: {str(e)}"
                            )
                        raise last_exception
            
            return None  # Should never reach here
        
        return wrapper
    return decorator


def validate_url(url: str, allowed_schemes: Optional[list] = None) -> bool:
    """
    Validate a URL for safety and correctness.
    
    Args:
        url: URL to validate
        allowed_schemes: List of allowed URL schemes (default: ['http', 'https'])
        
    Returns:
        True if URL is valid and safe, False otherwise
    """
    if allowed_schemes is None:
        allowed_schemes = ['http', 'https']
    
    try:
        result = urlparse(url)
        
        # Check if URL has required components
        if not all([result.scheme, result.netloc]):
            return False
        
        # Check if scheme is allowed
        if result.scheme not in allowed_schemes:
            return False
        
        # Basic safety checks
        dangerous_patterns = [
            'localhost',
            '127.0.0.1',
            '0.0.0.0',
            '::1',
            'file://',
            'javascript:',
            'data:'
        ]
        
        url_lower = url.lower()
        for pattern in dangerous_patterns:
            if pattern in url_lower:
                return False
        
        return True
        
    except Exception:
        return False


def get_env_or_config(key: str, config: dict, default: Any = None) -> Any:
    """
    Get a value from environment variable or config, with environment taking precedence.
    
    Args:
        key: Environment variable key (will be uppercased)
        config: Configuration dictionary
        default: Default value if not found
        
    Returns:
        Value from environment, config, or default
    """
    # Check environment variable first (uppercase key)
    env_value = os.environ.get(key.upper())
    if env_value is not None:
        return env_value
    
    # Check config dictionary (navigate nested keys with dots)
    keys = key.lower().split('.')
    value = config
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value if value != config else default


def format_time_duration(seconds: float) -> str:
    """
    Format seconds into a human-readable duration string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string (e.g., "2m 30s", "1h 15m")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours < 24:
            return f"{hours}h {minutes}m {secs}s"
        else:
            days = int(hours // 24)
            hours = int(hours % 24)
            return f"{days}d {hours}h {minutes}m"


class RateLimiter:
    """Simple rate limiter using a token bucket algorithm."""
    
    def __init__(self, rate: float, per: float = 1.0):
        """
        Initialize rate limiter.
        
        Args:
            rate: Number of allowed requests
            per: Time period in seconds (default: 1.0)
        """
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.time()
    
    def allow_request(self) -> bool:
        """
        Check if a request is allowed under the rate limit.
        
        Returns:
            True if request is allowed, False if rate limited
        """
        current = time.time()
        time_passed = current - self.last_check
        self.last_check = current
        
        # Replenish tokens based on time passed
        self.allowance += time_passed * (self.rate / self.per)
        
        # Cap at maximum rate
        if self.allowance > self.rate:
            self.allowance = self.rate
        
        # Check if we have tokens available
        if self.allowance < 1.0:
            return False
        else:
            self.allowance -= 1.0
            return True
    
    def wait_if_needed(self) -> None:
        """Wait until a request is allowed."""
        while not self.allow_request():
            time.sleep(0.1)


class MetricsCollector:
    """Simple metrics collector for monitoring framework performance."""
    
    def __init__(self):
        self.metrics = {
            'api_calls': 0,
            'tool_calls': {},
            'errors': 0,
            'total_tokens': 0,
            'response_times': []
        }
    
    def record_api_call(self, tokens: int = 0) -> None:
        """Record an API call."""
        self.metrics['api_calls'] += 1
        self.metrics['total_tokens'] += tokens
    
    def record_tool_call(self, tool_name: str) -> None:
        """Record a tool call."""
        if tool_name not in self.metrics['tool_calls']:
            self.metrics['tool_calls'][tool_name] = 0
        self.metrics['tool_calls'][tool_name] += 1
    
    def record_error(self) -> None:
        """Record an error."""
        self.metrics['errors'] += 1
    
    def record_response_time(self, duration: float) -> None:
        """Record a response time."""
        self.metrics['response_times'].append(duration)
    
    def get_summary(self) -> dict:
        """Get metrics summary."""
        avg_response_time = (
            sum(self.metrics['response_times']) / len(self.metrics['response_times'])
            if self.metrics['response_times'] else 0
        )
        
        return {
            'api_calls': self.metrics['api_calls'],
            'tool_calls': self.metrics['tool_calls'],
            'errors': self.metrics['errors'],
            'total_tokens': self.metrics['total_tokens'],
            'avg_response_time': avg_response_time,
            'total_response_time': sum(self.metrics['response_times'])
        }


class DebugLogger:
    """Debug logger for framework debugging and troubleshooting."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, config: Optional[Dict[str, Any]] = None):
        """Singleton pattern to ensure only one debug logger instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the debug logger with configuration."""
        if self._initialized:
            return
            
        self.config = config or {}
        self.debug_config = self.config.get('debug', {})
        self.enabled = self.debug_config.get('enabled', False)
        self.logger = None
        
        if self.enabled:
            self._setup_logger()
        
        self._initialized = True
    
    def _setup_logger(self) -> None:
        """Set up the debug logger with file rotation."""
        # Create logs directory if it doesn't exist
        log_path = Path(self.debug_config.get('log_path', './logs'))
        log_path.mkdir(parents=True, exist_ok=True)
        
        # Generate log filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_path / f"debug_{timestamp}.log"
        
        # Create logger
        self.logger = logging.getLogger('chat_with_tools.debug')
        self.logger.setLevel(getattr(logging, self.debug_config.get('log_level', 'DEBUG')))
        self.logger.handlers.clear()
        
        # Create rotating file handler
        max_bytes = self.debug_config.get('max_log_size_mb', 10) * 1024 * 1024
        backup_count = self.debug_config.get('max_log_files', 5)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        
        # Create formatter with detailed information
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S.%f'[:-3]  # Include milliseconds
        )
        
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Log initialization
        self.logger.info("=" * 80)
        self.logger.info("Debug Logger Initialized")
        self.logger.info(f"Log file: {log_file}")
        self.logger.info(f"Debug config: {json.dumps(self.debug_config, indent=2)}")
        self.logger.info("=" * 80)
    
    def log(self, level: str, message: str, **kwargs) -> None:
        """Log a message if debug logging is enabled.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Message to log
            **kwargs: Additional key-value pairs to include in the log
        """
        if not self.enabled or not self.logger:
            return
        
        # Add any additional context
        if kwargs:
            message = f"{message} | {json.dumps(kwargs, default=str)}"
        
        # Log at the appropriate level
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        self.log('DEBUG', message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log an info message."""
        self.log('INFO', message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        self.log('WARNING', message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log an error message."""
        self.log('ERROR', message, **kwargs)
    
    def log_agent_iteration(self, iteration: int, max_iterations: int, agent_id: Optional[str] = None) -> None:
        """Log agent iteration information."""
        if not self.enabled or not self.debug_config.get('log_agent_thoughts', True):
            return
        
        self.info(
            f"Agent Iteration",
            iteration=iteration,
            max_iterations=max_iterations,
            agent_id=agent_id or "main"
        )
    
    def log_tool_call(self, tool_name: str, arguments: Dict[str, Any], result: Any = None, error: Optional[str] = None) -> None:
        """Log tool invocation and results."""
        if not self.enabled or not self.debug_config.get('log_tool_calls', True):
            return
        
        if error:
            self.error(
                f"Tool Call Failed: {tool_name}",
                arguments=arguments,
                error=error
            )
        else:
            self.info(
                f"Tool Call: {tool_name}",
                arguments=arguments,
                result_preview=str(result)[:500] if result else None
            )
    
    def log_llm_call(self, model: str, messages: list, response: Optional[Any] = None, error: Optional[str] = None) -> None:
        """Log LLM API calls and responses."""
        if not self.enabled or not self.debug_config.get('log_llm_calls', True):
            return
        
        # Summarize messages for logging
        message_summary = [
            {"role": msg.get("role"), "content_preview": str(msg.get("content", ""))[:200]}
            for msg in messages[-3:]  # Only last 3 messages for brevity
        ]
        
        if error:
            self.error(
                f"LLM Call Failed",
                model=model,
                messages=message_summary,
                error=error
            )
        else:
            response_preview = None
            if response:
                try:
                    if hasattr(response, 'choices') and response.choices:
                        content = response.choices[0].message.content
                        response_preview = str(content)[:500] if content else "<no content>"
                except:
                    response_preview = str(response)[:500]
            
            self.info(
                f"LLM Call",
                model=model,
                messages=message_summary,
                response_preview=response_preview
            )
    
    def log_orchestrator_task(self, task_id: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log orchestrator task status."""
        if not self.enabled:
            return
        
        self.info(
            f"Orchestrator Task",
            task_id=task_id,
            status=status,
            details=details or {}
        )
    
    def log_separator(self, title: Optional[str] = None) -> None:
        """Log a separator line for better readability."""
        if not self.enabled:
            return
        
        if title:
            self.info(f"{'=' * 30} {title} {'=' * 30}")
        else:
            self.info("=" * 80)
