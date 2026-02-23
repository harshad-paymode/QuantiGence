"""
Supervisor Agent: Orchestrator & State Manager
Routes traffic, manages state, and formats final output.
"""
import logging
from typing import Any, Dict

from langchain_core.messages import AIMessage
from services.memory import persist_conversation_turn
from src.core.logger import configure_logging
from src.core.state import QueryResState

logger = configure_logging(logging.INFO)


def supervisor(state: Dict[str, Any]) -> Dict[str, Any]:
    logger.debug("SUPERVISOR: enter node with keys: %s", list(state.keys()))

    # ---------------------------
    # 1. FAILURE HANDLING
    # ---------------------------
    final_text = None
    if state.get("query_harmful") and state.get("auditor_fail"):
        final_text = (
            "I apologize, but your request appears to be outside my specialized "
            "financial knowledge base or violates my safety policies."
        )
        logger.info("SUPERVISOR: query_harmful & auditor_fail -> final_text set")

    elif state.get("response_harmful") and state.get("auditor_fail"):
        final_text = (
            "I apologize, but there seems to be some error from our side. "
            "Please try again with a rephrased query."
        )
        logger.info("SUPERVISOR: response_harmful & auditor_fail -> final_text set")

    elif state.get("parsed_query") and not state["parsed_query"].get("companies"):
        final_text = (
            "I am currently unable to locate the requested company in our knowledge base. "
            "Please ensure the company name or ticker is correct."
        )
        logger.info("SUPERVISOR: parsed_query missing companies -> final_text set")


    elif state.get("researcher_fail"):
        final_text = (
            "I encountered difficulty retrieving specific data points for this query. "
            "Please rephrase your request or provide more details."
        )
        logger.info("SUPERVISOR: researcher_fail -> final_text set")

    # ---------------------------
    # 2. SUCCESS PATH
    # ---------------------------
    else:
        sec_out = state.get("llm_response_sec")
        trans_out = state.get("llm_response_trans")

        if sec_out or trans_out:
            logger.info("SUPERVISOR: success path - aggregating insights")
            sections = []
            if sec_out:
                sections.append(f"## SEC Filing Analysis\n\n{sec_out}")
            if trans_out:
                sections.append(f"## Management Commentary (Earnings Calls)\n\n{trans_out}")
            final_text = "\n\n---\n\n".join(sections)

            # Persist conversation turn and save to DB (helper provided elsewhere)
            try:
                persist_conversation_turn(state)
                logger.debug("SUPERVISOR: persisted conversation turn")
            except Exception as e:
                logger.exception("SUPERVISOR: failed to persist conversation turn: %s", e)
        else:
            # Still processing -> return state to continue pipeline
            logger.debug("SUPERVISOR: no outputs yet, returning state to continue processing")
            return state  # IMPORTANT: never return empty dict

    # ---------------------------
    # 3. Append AI Message (Multi-turn)
    # ---------------------------
    updated_messages = state.get("messages", []) + [
        AIMessage(content=final_text, additional_kwargs={"turn_id": state.get("turn_id")})
    ]
    logger.debug("SUPERVISOR: appended AIMessage; total messages=%d", len(updated_messages))

    return {
        "final_response": final_text,
        "audit_score": state['audit_score'],
        "messages": updated_messages,
    }