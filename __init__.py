"""
Chat with Tools Framework

A powerful multi-agent AI framework with tool integration,
inspired by Grok's deep thinking mode.
"""

__version__ = "0.1.0"
__author__ = "Suparious"
__license__ = "MIT"

from pathlib import Path
import sys

# Ensure src is in the path
package_dir = Path(__file__).parent
if str(package_dir) not in sys.path:
    sys.path.insert(0, str(package_dir))

# Core imports for easier access
try:
    from src.chat_with_tools.agent import OpenRouterAgent
    from src.chat_with_tools.orchestrator import TaskOrchestrator
    from src.chat_with_tools.utils import setup_logging
    
    __all__ = [
        "OpenRouterAgent",
        "TaskOrchestrator",
        "setup_logging",
        "__version__",
    ]
except ImportError:
    # If running from different context
    __all__ = ["__version__"]

def get_version():
    """Get the current version of the framework"""
    return __version__

def get_project_root():
    """Get the project root directory"""
    return Path(__file__).parent

def check_setup():
    """Check if the framework is properly set up"""
    project_root = get_project_root()
    config_path = project_root / "config" / "config.yaml"
    
    issues = []
    
    if not config_path.exists():
        issues.append("Configuration file not found at config/config.yaml")
    
    # Check for required directories
    required_dirs = ["src", "demos", "config", "src/chat_with_tools", "src/chat_with_tools/tools"]
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            issues.append(f"Required directory not found: {dir_name}")
    
    if issues:
        return False, issues
    return True, []
