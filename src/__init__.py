"""
Chat with Tools Framework

A modular framework for building AI agents with customizable tools.
"""

__version__ = "0.1.0"

from src.agent import OpenRouterAgent
from src.agent_enhanced import OpenRouterAgent as EnhancedAgent
from src.orchestrator import TaskOrchestrator

__all__ = [
    "OpenRouterAgent",
    "EnhancedAgent", 
    "TaskOrchestrator"
]
