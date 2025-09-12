"""
Configuration management for the Chat with Tools framework.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from openai import OpenAI


class ConfigManager:
    """Manages configuration loading and access for the framework."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Optional path to config file. If None, searches for config.yaml
                        in standard locations.
        """
        self.config_path = self._find_config_file(config_path)
        self.config = self._load_config()
    
    def _find_config_file(self, config_path: Optional[str] = None) -> Path:
        """
        Find the configuration file.
        
        Args:
            config_path: Optional explicit path to config file
            
        Returns:
            Path to the configuration file
            
        Raises:
            FileNotFoundError: If no configuration file can be found
        """
        if config_path:
            path = Path(config_path)
            if path.exists():
                return path
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        # Search for config file in standard locations
        search_paths = [
            Path.cwd() / "config" / "config.yaml",
            Path.cwd() / "config.yaml",
            Path(__file__).parent.parent.parent / "config" / "config.yaml",
            Path.home() / ".chat-with-tools" / "config.yaml",
        ]
        
        for path in search_paths:
            if path.exists():
                return path
        
        # If no config found, check for example config
        example_path = Path(__file__).parent.parent.parent / "config" / "config.example.yaml"
        if example_path.exists():
            raise FileNotFoundError(
                f"No config.yaml found. Please copy {example_path} to "
                f"{search_paths[0]} and configure your settings."
            )
        
        raise FileNotFoundError(
            "No configuration file found. Please create config/config.yaml "
            "with your OpenRouter API settings."
        )
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Returns:
            Configuration dictionary
        """
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Apply environment variable overrides
        self._apply_env_overrides(config)
        
        # Validate required settings
        self._validate_config(config)
        
        return config
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> None:
        """
        Apply environment variable overrides to configuration.
        
        Args:
            config: Configuration dictionary to modify in place
        """
        # Check for OpenRouter API key in environment
        if 'OPENROUTER_API_KEY' in os.environ:
            config.setdefault('openrouter', {})['api_key'] = os.environ['OPENROUTER_API_KEY']
        
        # Check for base URL override
        if 'OPENROUTER_BASE_URL' in os.environ:
            config.setdefault('openrouter', {})['base_url'] = os.environ['OPENROUTER_BASE_URL']
        
        # Check for model override
        if 'OPENROUTER_MODEL' in os.environ:
            config.setdefault('openrouter', {})['model'] = os.environ['OPENROUTER_MODEL']
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate configuration has required settings.
        
        Args:
            config: Configuration dictionary to validate
            
        Raises:
            ValueError: If required settings are missing or invalid
        """
        # Check for OpenRouter section
        if 'openrouter' not in config:
            raise ValueError("Missing 'openrouter' section in configuration")
        
        openrouter = config['openrouter']
        
        # Check if API key is required
        api_key_required = openrouter.get('api_key_required', True)
        
        # Only require API key if explicitly needed
        if api_key_required:
            if not openrouter.get('api_key'):
                raise ValueError(
                    "OpenRouter API key not configured. Please set it in config.yaml "
                    "or via OPENROUTER_API_KEY environment variable."
                )
            
            if openrouter.get('api_key') == 'YOUR API KEY HERE':
                raise ValueError(
                    "Please replace 'YOUR API KEY HERE' with your actual OpenRouter API key "
                    "in config.yaml or set OPENROUTER_API_KEY environment variable."
                )
        
        # Check for base URL
        if not openrouter.get('base_url'):
            # Default to OpenRouter's public endpoint
            openrouter['base_url'] = 'https://openrouter.ai/api/v1'
        
        # Check for model
        if not openrouter.get('model'):
            # Default to a reasonable model
            openrouter['model'] = 'openai/gpt-3.5-turbo'
            print(f"Warning: No model specified, defaulting to {openrouter['model']}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation for nested keys)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_model(self) -> str:
        """Get the configured model name."""
        return self.config['openrouter']['model']
    
    def get_api_key(self) -> str:
        """Get the OpenRouter API key."""
        return self.config['openrouter'].get('api_key', '')
    
    def get_base_url(self) -> str:
        """Get the OpenRouter base URL."""
        return self.config['openrouter']['base_url']
    
    def get_orchestrator_config(self) -> Dict[str, Any]:
        """Get orchestrator-specific configuration."""
        return self.config.get('orchestrator', {
            'parallel_agents': 4,
            'task_timeout': 300,
            'aggregation_strategy': 'consensus',
            'verbose': True
        })
    
    def requires_api_key(self) -> bool:
        """Check if an API key is required."""
        return self.config['openrouter'].get('api_key_required', True)
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration."""
        return self.config.get('performance', {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return self.config.get('security', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.config.get('logging', {})
    
    def get_debug_config(self) -> Dict[str, Any]:
        """Get debug configuration from unified logging section."""
        # Debug config is now nested within logging
        return self.config.get('logging', {}).get('debug', {})
    
    def get_tools_config(self) -> Dict[str, Any]:
        """Get tools configuration."""
        return self.config.get('tools', {})
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self.config = self._load_config()


def get_openai_client(config: Optional[Dict[str, Any]] = None) -> OpenAI:
    """
    Get an OpenAI client configured for OpenRouter.
    
    Args:
        config: Optional configuration dictionary. If None, loads from ConfigManager.
        
    Returns:
        Configured OpenAI client
    """
    if config is None:
        config_manager = ConfigManager()
        config = config_manager.config
    
    openrouter = config.get('openrouter', {})
    
    # Create OpenAI client with OpenRouter settings
    client = OpenAI(
        api_key=openrouter.get('api_key', 'dummy-key-for-local'),  # Use dummy key for local endpoints
        base_url=openrouter.get('base_url', 'https://openrouter.ai/api/v1')
    )
    
    return client
