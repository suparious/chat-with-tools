"""
Chat with Tools Framework

A modular framework for building AI agents with customizable tools.
"""

__version__ = "0.1.0"

from .agent import OpenRouterAgent
from .agent_enhanced import OpenRouterAgent as EnhancedAgent
from .orchestrator import TaskOrchestrator
from .config_manager import ConfigManager, get_openai_client

__all__ = [
    "OpenRouterAgent",
    "EnhancedAgent", 
    "TaskOrchestrator",
    "ConfigManager",
    "get_openai_client"
]
