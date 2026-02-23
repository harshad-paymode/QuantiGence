# src/agents/__init__.py

"""
Agents package initializer.

Exports all core agent nodes so they can be imported directly from:
    from src.agents import ingest_user_turn, supervisor, auditor, researcher_node, analyst_node
"""

import logging

# Configure package-level logger (basic setup, can be overridden by app)
logging.getLogger(__name__).addHandler(logging.NullHandler())

from .ingest_user_turn import ingest_user_turn
from .supervisor import supervisor
from .auditor import auditor
from .researcher import researcher_node
from .analyst import analyst_node

__all__ = [
    "ingest_user_turn",
    "supervisor",
    "auditor",
    "researcher_node",
    "analyst_node",
]