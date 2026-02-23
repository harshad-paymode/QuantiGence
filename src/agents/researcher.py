"""Researcher agent for query processing and retrieval."""

from src.core.logger import configure_logging
from typing import Dict, Any, Literal
from copy import deepcopy
from typing import Any, Dict, List
from sklearn.metrics.pairwise import cosine_similarity
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from core.state import QueryResState
from services.query_processor import query_processor
from retrieval.neo4j_retriever import get_query_embeddings
from src.core.database import  connect_neo4j
from services.retrieval_service import retrieve_simple, retrieve_multi_query, retrieve_change_detection
from services.memory import load_conversation_memory
from src.retrieval.retrieval_helpers import build_retrieval_jobs

logger = configure_logging()

# Constants
SIM_THRESHOLD = 0.70
SECTION_OVERLAP_THRESHOLD = 0.95
MAX_RETRIES = 3


def metadata_match_score(current_meta: dict, previous_meta: dict) -> float:
    """
    Strict metadata comparison.
    - Companies must match exactly
    - Years & quarters must match exactly
    - Filing type must match
    - Section hints overlap must be >= 95%
    """
    if not previous_meta:
        return 0.0

    # Companies exact match
    if current_meta.get("companies") != previous_meta.get("companies"):
        return 0.0

    # Period exact match
    if sorted(current_meta.get("years", [])) != sorted(previous_meta.get("years", [])):
        return 0.0

    if sorted(current_meta.get("quarters", [])) != sorted(previous_meta.get("quarters", [])):
        return 0.0

    # Filing type
    if current_meta.get("filing_type_hint") != previous_meta.get("filing_type_hint"):
        return 0.0

    # Section hints overlap
    curr_sections = set(current_meta.get("section_hints", []))
    prev_sections = set(previous_meta.get("section_hints", []))

    if not curr_sections or not prev_sections:
        return 0.0

    overlap = len(curr_sections.intersection(prev_sections)) / max(len(curr_sections), 1)
    return overlap


def parse_query_node(state: QueryResState) -> QueryResState:
    """Parse the user query into structured components."""
    return {
        "parsed_query": query_processor.parse_query(state["last_user_message"]),
        "research_retry_count": state.get("research_retry_count", 0),
    }


def decide_query_refinement(state: QueryResState) -> QueryResState:
    """Decide if query needs refinement based on parsed components."""
    parsed = state.get("parsed_query", {})
    needs_company = not parsed.get("companies")
    needs_period = not parsed.get("years") and not parsed.get("quarters")

    return {
        "needs_refinement": needs_company or needs_period,
        "research_retry_count": state.get("research_retry_count", 0),
    }


def refine_query(state: QueryResState) -> QueryResState:
    """Refine query using conversation history."""
    refined = query_processor.normalize_query_with_history(
        state["last_user_message"],
        state.get("messages", [])
    )

    updated_messages = state["messages"][:-1] + [
        HumanMessage(
            content=refined,
            additional_kwargs={"turn_id": state["turn_id"]}
        )
    ]

    return {
        "modif_query": refined,
        "last_user_message": refined,
        "messages": updated_messages,
        "query_modified": True,
    }


def processor_query(state: QueryResState) -> QueryResState:
    """Process query to determine type and decompose into sub-queries."""
    user_query = state.get("modif_query") if state["query_modified"] else state["last_user_message"]
    
    data_source_classification = query_processor.classify_source(user_query)
    data_type = data_source_classification['source_type']
    
    classification = query_processor.classify_query(user_query)
    query_type = classification["query_type"]
    
    sub_queries = build_retrieval_jobs(user_query, query_type)
    
    return {
        "query_classification": query_type,
        "data_source_classification": data_type,
        "sub_queries": sub_queries,
    }


def decide_context_reuse(state: QueryResState) -> QueryResState:
    """
    Decide whether to reuse previously retrieved context
    instead of running retrieval again.
    """
    turns = state.get("conversation_memory", [])

    if not turns:
        return {"reuse_context": False}

    current_query = state.get("modif_query") or state.get("last_user_message")
    current_meta = state.get("parsed_query", {})
    current_embedding = get_query_embeddings(current_query)

    best_match = None
    best_score = 0.0

    for turn in turns:
        prev_meta = turn.get("parsed_metadata")
        prev_embedding = turn.get("embedding")

        if not prev_meta or prev_embedding is None:
            continue
        
        if prev_embedding:
            sim_score = cosine_similarity([current_embedding], [prev_embedding])[0][0]
        
        meta_score = metadata_match_score(current_meta, prev_meta)

        if sim_score >= SIM_THRESHOLD and meta_score >= SECTION_OVERLAP_THRESHOLD:
            if sim_score > best_score:
                best_score = sim_score
                best_match = turn

    if best_match:
        logger.info(f"Reusing context for query (similarity: {best_score:.2f})")
        return {
            "reuse_context": True,
            "sec_context": best_match.get("sec_context", []),
            "trans_context": best_match.get("trans_context", []),
        }

    return {"reuse_context": False}


def retrieval_controller_node(state: QueryResState) -> QueryResState:
    """Execute retrieval based on query type."""
    original_query = state.get("modif_query") or state["org_query"]
    query_type = state["query_classification"]
    sub_queries = state.get("sub_queries", [])
    data_type = state.get("data_source_classification")
    query_embedding = get_query_embeddings(original_query)

    driver = connect_neo4j()
    
    try:
        if query_type == "SIMPLE":
            result = retrieve_simple(
                driver=driver,
                original_query=original_query,
                sub_queries=sub_queries,
                data_type=data_type,
                query_embedding=query_embedding,
            )

        elif query_type in {"BROAD", "COMPARISON"}:
            result = retrieve_multi_query(
                driver=driver,
                original_query=original_query,
                sub_queries=sub_queries,
                data_type=data_type,
                query_embedding=query_embedding,
            )

        elif query_type == "CHANGE_DETECTION":
            auto_headings = sub_queries[0]["headings"] if sub_queries else []
            all_periods = sorted(set(sub_queries[0]["periods"])) if sub_queries else []

            if all_periods:
                result = retrieve_change_detection(
                    driver=driver,
                    original_query=original_query,
                    periods=all_periods,
                    company=sub_queries[0]["company"],
                    sub_queries=sub_queries,
                    headings=auto_headings,
                    start_period=all_periods[0],
                    end_period=all_periods[-1],
                    data_type=data_type,
                    query_embedding=query_embedding
                )
            else:
                result = {
                    "org_query": original_query,
                    "data_type": data_type,
                    "query_embedding": query_embedding,
                    "query_embedding_trans": [],
                    "sub_queries": [],
                    "sec_context": [],
                    "trans_context": [],
                    "sec_graph_ui": [],
                    "transcript_graph_ui": [],
                    "transcript_query": "",
                }
        else:
            result = {
                "org_query": original_query,
                "data_type": data_type,
                "sub_queries": [],
                "query_embedding": query_embedding,
                "query_embedding_trans": [],
                "sec_context": [],
                "trans_context": [],
                "sec_graph_ui": [],
                "transcript_graph_ui": [],
                "transcript_query": "",
            }
    finally:
        driver.close()

    return result


def evaluate_context(state: QueryResState) -> QueryResState:
    """Evaluate if retrieved context is sufficient."""
    sec_chunks = state.get("sec_context", [])
    sufficient = len(sec_chunks) >= 1

    retry_count = state.get("research_retry_count", 0) + (0 if sufficient else 1)

    return {
        "context_sufficient": sufficient,
        "research_retry_count": retry_count,
    }


def retry_or_exit(state: QueryResState) -> Literal["retry", "exit"]:
    """Decide whether to retry retrieval or exit the researcher."""
    if state.get("context_sufficient"):
        return "exit"
    if state.get("research_retry_count", 0) >= MAX_RETRIES:
        return "exit"
    return "retry"


def _build_researcher_subgraph() -> StateGraph:
    """Build the researcher subgraph."""
    graph = StateGraph(QueryResState)

    graph.add_node("parse", parse_query_node)
    graph.add_node("decide_refinement", decide_query_refinement)
    graph.add_node("refine", refine_query)
    graph.add_node("retrieve_prep", processor_query)
    graph.add_node("decide_context_reuse", decide_context_reuse)
    graph.add_node("retrieve", retrieval_controller_node)
    graph.add_node("evaluate", evaluate_context)

    graph.set_entry_point("parse")

    graph.add_edge("parse", "decide_refinement")
    graph.add_conditional_edges(
        "decide_refinement",
        lambda s: s["needs_refinement"],
        {True: "refine", False: "retrieve_prep"},
    )
    graph.add_edge("refine", "retrieve_prep")
    graph.add_edge("retrieve_prep", "decide_context_reuse")
    graph.add_conditional_edges(
        "decide_context_reuse",
        lambda s: s.get("reuse_context", False),
        {True: "evaluate", False: "retrieve"},
    )
    graph.add_edge("retrieve", "evaluate")
    graph.add_conditional_edges(
        "evaluate",
        retry_or_exit,
        {"retry": "decide_refinement", "exit": END},
    )

    return graph


# Compile the researcher subgraph
_researcher_subgraph = _build_researcher_subgraph().compile()


def researcher_node(state: QueryResState) -> QueryResState:
    """
    Researcher node: loads conversation memory and invokes a researcher subgraph/executor.
    """
    logger.debug("RESEARCHER: starting researcher_node for conversation_id=%s", state.get("conversation_id"))

    conversation_id = state.get("conversation_id")
    conversation_memory: List[Dict[str, Any]] = load_conversation_memory(conversation_id) or []
    logger.debug("RESEARCHER: loaded conversation_memory length=%d", len(conversation_memory))
    state["conversation_memory"] = conversation_memory

    # Run researcher subgraph / executor (assumed to return a dict of updates)
    logger.debug("RESEARCHER: invoking researcher_executor")
    updated = _researcher_subgraph.invoke(state) or {}
    logger.debug("RESEARCHER: researcher_executor returned keys=%s", list(updated.keys()))

    exhausted = (
        not updated.get("context_sufficient", False)
        and updated.get("research_retry_count", 0) >= MAX_RETRIES
    )
    logger.debug("RESEARCHER: exhausted=%s", exhausted)

    # find max turn id from conversation memory
    max_turn_id = -1
    for turn in conversation_memory:
        tid = turn.get("turn_id", -1)
        if tid > max_turn_id:
            max_turn_id = tid

    logger.debug("RESEARCHER: max_turn_id=%d, next turn will be %d", max_turn_id, max_turn_id + 1)

    return {
        "parsed_query": updated.get("parsed_query", state.get("parsed_query")),
        "modif_query": updated.get("modif_query", state.get("org_query")),
        "turn_id": max_turn_id + 1,
        "query_classification": updated.get("query_classification", state.get("query_classification")),
        "sub_queries": updated.get("sub_queries", state.get("sub_queries")),
        "sec_context": updated.get("sec_context", []),
        "trans_context": updated.get("trans_context", []),
        "sec_graph_ui": updated.get("sec_graph_ui", []),
        "transcript_graph_ui": updated.get("transcript_graph_ui", []),
        "transcript_query": updated.get("transcript_query"),
        "research_retry_count": updated.get("research_retry_count", 0),
        "context_sufficient": updated.get("context_sufficient", False),
        "query_embedding": updated.get("query_embedding", []),
        "query_embedding_trans": updated.get("query_embedding_trans", []),
        "data_type": updated.get("data_type", "SEC"),
        "conversation_memory": updated.get("conversation_memory", conversation_memory),
        "reuse_context": updated.get("reuse_context", False),
        "researcher_fail": exhausted,
    }