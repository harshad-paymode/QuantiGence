"""
Analyst Agent: Response Generation
Generates comprehensive answers using SEC filings and transcript data.
"""
import logging
from typing import Any, Dict
from src.core.state import QueryResState

from agents.base_agent import BaseAgent
from services.analyst_service import (
    generate_sec_answer,
    generate_transcript_commentary
)

from src.core.logger import configure_logging

logger = configure_logging(logging.INFO)


class AnalystAgent(BaseAgent):
    """
    Analyst Agent: Generates comprehensive financial analysis.
    - SEC filing analysis with citations
    - Management tone analysis from transcripts
    - Change detection and trend analysis
    """

    def __init__(self):
        super().__init__("Analyst")

    def execute(self, state: QueryResState) -> Dict[str, Any]:
        """Generate analyst response based on retrieved context."""
        self._log_execution("INIT", f"Generating answer for query type: {state['query_classification']}")

        # Generate SEC answer
        if state.get("sec_context"):
            try:
                sec_result = generate_sec_answer(
                    query_type=state["query_classification"],
                    query=state.get("modif_query") or state["last_user_message"],
                    sec_chunks=state["sec_context"],
                    sec_graph=state.get("sec_graph_ui", []),
                    chat_history="",  # Can be populated from messages
                )
                state["llm_response_sec"] = sec_result.get("answer", "")
                state["sec_graph_ui"] = sec_result.get("sec_graph_ui", [])
                self._log_execution("SEC_ANSWER", "Generated SEC analysis")
            except Exception as e:
                logger.error(f"SEC answer generation failed: {str(e)}")
                state["llm_response_sec"] = ""

        # Generate transcript commentary
        if state.get("trans_context"):
            try:
                transcript_result = generate_transcript_commentary(
                    transcript_query=state.get("transcript_query", ""),
                    transcript_items=state["trans_context"],
                )
                state["llm_response_trans"] = transcript_result.get("transcript_commentary", "")
                state["transcript_graph_ui"] = transcript_result.get("transcript_graph_ui", [])
                self._log_execution("TRANSCRIPT_ANSWER", "Generated transcript analysis")
            except Exception as e:
                logger.error(f"Transcript analysis generation failed: {str(e)}")
                state["llm_response_trans"] = ""

        # Ensure at least one answer generated
        if not state.get("llm_response_sec") and not state.get("llm_response_trans"):
            logger.warning("No answers generated")
            state["analyst_fail"] = True

        return state