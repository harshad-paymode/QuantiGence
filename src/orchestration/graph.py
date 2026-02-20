"""
Main LangGraph Orchestration
Compiles the state graph with all agents and control flow.
"""
import logging
from typing import Dict, Any

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from core.state import QueryResState, init_query_state
from agents.supervisor import SupervisorAgent
from agents.auditor import AuditorAgent
from agents.researcher import ResearcherAgent
from agents.analyst import AnalystAgent
from src.core.logger import configure_logging

logger = configure_logging(logging.INFO)


def build_orchestration_graph() -> StateGraph:
    """
    Build the main orchestration graph.

    Flow:
    START → Supervisor → Auditor (input check)
      → Researcher (query processing & retrieval)
      → Analyst (answer generation)
      → Auditor (output check)
      → Supervisor (final response)
      → END
    """

    graph = StateGraph(QueryResState)

    # Initialize agents
    supervisor = SupervisorAgent()
    auditor = AuditorAgent()
    researcher = ResearcherAgent()
    analyst = AnalystAgent()

    # Add nodes
    graph.add_node("supervisor", supervisor.execute)
    graph.add_node("auditor", auditor.execute)
    graph.add_node("researcher", researcher.execute)
    graph.add_node("analyst", analyst.execute)

    # Add edges: main flow
    graph.add_edge(START, "supervisor")

    # Supervisor → Auditor (input phase)
    graph.add_edge("supervisor", "auditor")

    # Conditional: Auditor passes/fails
    graph.add_conditional_edges(
        "auditor",
        _auditor_decision,
        {
            "pass": "researcher",
            "fail": "supervisor",
        },
    )

    # Researcher → Analyst
    graph.add_edge("researcher", "analyst")

    # Analyst → Auditor (output phase)
    graph.add_edge("analyst", "auditor")

    # Conditional: Output audit
    graph.add_conditional_edges(
        "auditor",
        _auditor_output_decision,
        {
            "pass": "supervisor",
            "retry": "analyst",
            "fail": "supervisor",
        },
    )

    # Supervisor → END
    graph.add_edge("supervisor", END)

    return graph


def _auditor_decision(state: Dict[str, Any]) -> str:
    """Route based on input audit result."""
    if state.get("auditor_fail"):
        return "fail"
    return "pass"


def _auditor_output_decision(state: Dict[str, Any]) -> str:
    """Route based on output audit result."""
    if state.get("response_harmful"):
        return "fail"

    if not state.get("analysis_ok"):
        retry_count = state.get("analysis_retry_count", 0)
        if retry_count < 3:
            return "retry"
        return "fail"

    return "pass"


def compile_graph() -> Any:
    """Compile the orchestration graph with memory checkpointing."""
    graph = build_orchestration_graph()
    memory = MemorySaver()
    compiled = graph.compile(checkpointer=memory)
    logger.info("Orchestration graph compiled successfully")
    return compiled