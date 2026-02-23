# src/agents/ingest_user_turn.py
from src.core.logger import configure_logging
from typing import Any, Dict
from src.core.state import QueryResState
from langchain_core.messages import HumanMessage

logger = configure_logging()


def ingest_user_turn(state: QueryResState) -> QueryResState:
    """
    Simple ingestion node: append the user's raw/original query as a HumanMessage
    into the conversation messages list.
    """
    logger.debug("INGEST: starting ingest_user_turn")
    messages = state.get("messages", [])
    org_query = state.get("org_query", "")
    human_msg = HumanMessage(content=org_query)
    updated_messages = messages + [human_msg]
    logger.debug("INGEST: appended HumanMessage; total messages=%d", len(updated_messages))
    return {"messages": updated_messages}