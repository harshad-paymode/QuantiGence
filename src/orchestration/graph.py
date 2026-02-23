"""
Main LangGraph Orchestration
Compiles the state graph with all agents and control flow.
"""
import logging
from typing import Dict, Any

from langgraph.graph import StateGraph, START, END

from core.state import QueryResState, init_query_state
from src.core.logger import configure_logging
# Import agent nodes
from src.agents.ingest_user_turn import ingest_user_turn  # noqa
from src.agents.supervisor import supervisor as supervisor_node  # noqa
from src.agents.auditor import auditor as auditor_fn  # noqa
from src.agents.researcher import researcher_node  # noqa
from src.agents.analyst import analyst_node  # noqa
logger = configure_logging(logging.INFO)


# Create small wrappers for auditor input/output so auditor knows mode
def auditor_input_node(state: QueryResState) ->QueryResState:
    logger.debug("GRAPH: auditor_input_node called")
    state["input_state"] = True
    return auditor_fn(state)

def auditor_output_node(state: QueryResState) -> QueryResState:
    logger.debug("GRAPH: auditor_output_node called")
    state["input_state"] = False
    return auditor_fn(state)

# Supervisor router: decide END vs continue
def supervisor_router(state: QueryResState) -> str:
    return "end" if state.get("final_response") else "continue"

# Auditor output router
def auditor_output_router(state: QueryResState) -> str:
    if state.get("auditor_fail", False) or state.get("response_harmful", False):
        return "fail"
    if state.get("analysis_ok", False):
        return "accept"
    if state.get("analysis_retry_count", 0) < state.get("MAX_RETRIES", 3):
        return "retry"
    return "exhaust"


# ---------------------------
# Top-level graph definition
# ---------------------------
main_graph = StateGraph(QueryResState)  # QueryResState type is expected by framework

# nodes
main_graph.add_node("initializer", ingest_user_turn)
main_graph.add_node("supervisor", supervisor_node)
main_graph.add_node("auditor_input", auditor_input_node)
main_graph.add_node("researcher", researcher_node)
main_graph.add_node("analyst", analyst_node)
main_graph.add_node("auditor_output", auditor_output_node)

# edges
main_graph.add_edge(START, "initializer")
main_graph.add_edge("initializer", "supervisor")

# Supervisor conditional: end vs continue
main_graph.add_conditional_edges(
    "supervisor",
    supervisor_router,
    {"end": END, "continue": "auditor_input"},
)

# Auditor input -> if fail -> supervisor, else -> researcher
main_graph.add_conditional_edges(
    "auditor_input",
    lambda s: s.get("auditor_fail", False),
    {True: "supervisor", False: "researcher"},
)

# Researcher -> if retrieval failed -> supervisor, else -> analyst
main_graph.add_conditional_edges(
    "researcher",
    lambda s: s.get("researcher_fail", False),
    {True: "supervisor", False: "analyst"},
)

# Analyst -> Auditor (output)
main_graph.add_edge("analyst", "auditor_output")

# Auditor (output) routing
main_graph.add_conditional_edges(
    "auditor_output",
    auditor_output_router,
    {"fail": "supervisor", "accept": "supervisor", "retry": "researcher", "exhaust": "supervisor"},
)

# compile / executor
main_executor = main_graph.compile()
logger.debug("GRAPH: main_graph compiled")

# Runner helper
def run_pipeline(user_query: str, conversation_id: str = None) -> Dict[str, Any]:
    """
    Initialize state and invoke the compiled graph executor.
    conversation_id can be provided; otherwise helpers will assign one inside init_query_state.
    """
    logger.debug("GRAPH: run_pipeline called with query=%s", user_query)
    state = init_query_state(user_query, conversation_id)
    result = main_executor.invoke(state)
    logger.debug("GRAPH: run_pipeline finished")
    return result