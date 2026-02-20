"""
Base agent class with common functionality for all agents.
Implements SOLID principles with single responsibility.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict
from src.core.logger import configure_logging

logger = configure_logging(logging.INFO)


class BaseAgent(ABC):
    """Abstract base class for all agents in the orchestration system."""

    def __init__(self, name: str):
        self.name = name
        logger.info(f"Initializing {name}")

    @abstractmethod
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent logic and return updated state."""
        pass

    def _log_execution(self, action: str, details: str = ""):
        """Log agent execution for debugging."""
        logger.debug(f"[{self.name}] {action}: {details}")