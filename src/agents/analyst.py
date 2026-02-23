"""
Analyst Agent: Response Generation
Generates comprehensive answers using SEC filings and transcript data.
"""
import logging
from typing import Any, Dict, List
from src.core.state import QueryResState
from services.analyst_service import (
    generate_sec_answer,
    generate_transcript_commentary
)

from src.core.logger import configure_logging

logger = configure_logging(logging.INFO)


def analyst_node(state: QueryResState) -> QueryResState:
    """
    Analyst node:
      - Generate SEC answer
      - Generate Transcript commentary
      - Return raw LLM outputs (no UI formatting)
    """
    logger.debug("ANALYST: enter node; conversation_memory_len=%d", len(state.get("conversation_memory", [])))

    query_type = state.get("query_classification")
    query = state.get("modif_query") if state.get("query_modified") else state.get("last_user_message", "")

    # Build chat history from most recent conversation memory (up to 3)
    chat_history: List[Dict[str, str]] = []
    conv_mem = state.get("conversation_memory", [])
    recent = conv_mem[-3:] if len(conv_mem) >= 3 else conv_mem
    for val in recent:
        chat_history.append({"user": val.get("modif_query"), "system": val.get("llm_response_sec")})

    logger.debug("ANALYST: chat_history size=%d", len(chat_history))

    sec_out = generate_sec_answer(
        query_type=query_type,
        query=query,
        sec_chunks=state.get("sec_context", []),
        sec_graph=state.get("sec_graph_ui", []),
        chat_history=chat_history,
    )
    logger.debug("ANALYST: generate_sec_answer returned keys=%s", list(sec_out.keys()) if isinstance(sec_out, dict) else [])

    transcript_out = None
    if state.get("trans_context"):
        transcript_out = generate_transcript_commentary(
            transcript_query=state.get("transcript_query"),
            transcript_items=state.get("trans_context", []),
        )
        logger.debug("ANALYST: generate_transcript_commentary returned keys=%s", list(transcript_out.keys()) if isinstance(transcript_out, dict) else [])

    return {
        "llm_response_sec": sec_out.get("answer") if isinstance(sec_out, dict) else sec_out,
        "llm_response_trans": transcript_out.get("transcript_commentary") if transcript_out else None,
        "sec_graph_ui": sec_out.get("sec_graph_ui", []) if isinstance(sec_out, dict) else [],
        "transcript_graph_ui": transcript_out.get("transcript_graph_ui", []) if transcript_out else [],
    }