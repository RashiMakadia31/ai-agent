"""
This package contains all agent classes for handling specific code-related tasks.
Each agent follows the BaseAgent interface and is registered in agent_registry.py.
"""

from agents.base_agent import BaseAgent
from agents.master_agent import MasterAgent

# Optional: preload all agents (not required if using agent_registry.py explicitly)
