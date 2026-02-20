"""Memory management for conversation persistence."""

import logging
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from azure.cosmos import CosmosClient
from core.state import QueryResState

load_dotenv()
from src.core.logger import configure_logging

logger = configure_logging(logging.INFO)

# Initialize Cosmos DB client
COSMOS_URI = os.getenv("COSMOS_URI")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DB = os.getenv("COSMOS_DB")
COSMOS_CONTAINER = os.getenv("COSMOS_CONTAINER")

_cosmos_client = None
_cosmos_container = None


def _get_cosmos_container():
    """Lazy-load Cosmos container."""
    global _cosmos_client, _cosmos_container
    
    if _cosmos_container is None:
        _cosmos_client = CosmosClient(COSMOS_URI, COSMOS_KEY)
        database = _cosmos_client.get_database_client(COSMOS_DB)
        _cosmos_container = database.get_container_client(COSMOS_CONTAINER)
    
    return _cosmos_container


def persist_conversation_turn(state: QueryResState) -> None:
    """Persist one successful turn into Cosmos DB."""
    container = _get_cosmos_container()
    
    conv_id = state["conversation_id"]
    turn_id = state.get("turn_id", 0)

    document = {
        "id": f"{conv_id}_{turn_id}",
        "conversation_id": conv_id,
        "turn_id": turn_id,
        "modif_query": state.get("modif_query") or state.get("org_query"),
        "transcript_query": state.get("transcript_query", ""),
        "llm_response_sec": state.get("llm_response_sec"),
        "parsed_metadata": state.get("parsed_query", {}),
        "sec_context": state.get("sec_context", []),
        "trans_context": state.get("trans_context", []),
        "query_type": state.get("query_classification"),
        "embedding": state.get("query_embedding"),
        "embedding_trans": state.get("query_embedding_trans"),
    }

    try:
        container.upsert_item(document)
        logger.info(f"Persisted conversation turn {turn_id} for {conv_id}")
    except Exception as e:
        logger.error(f"Failed to persist conversation turn: {e}")


def load_conversation_memory(conversation_id: str) -> List[Dict[str, Any]]:
    """Load all previous turns for a conversation_id."""
    container = _get_cosmos_container()
    
    query = "SELECT * FROM c WHERE c.conversation_id = @cid"
    
    try:
        items = container.query_items(
            query=query,
            parameters=[{"name": "@cid", "value": conversation_id}],
            enable_cross_partition_query=True,
        )

        memory = []
        for item in items:
            key = item.get("modif_query")
            if not key:
                continue

            memory.append({
                "modif_query": key,
                "llm_response_sec": item.get("llm_response_sec", ""),
                "parsed_metadata": item.get("parsed_metadata", {}),
                "turn_id": item.get("turn_id"),
                "sec_context": item.get("sec_context", []),
                "trans_context": item.get("trans_context", []),
                "query_type": item.get("query_type"),
                "embedding": item.get("embedding", []),
                "embedding_trans": item.get("embedding_trans", []),
            })

        logger.info(f"Loaded {len(memory)} previous turns for {conversation_id}")
        return memory
        
    except Exception as e:
        logger.error(f"Failed to load conversation memory: {e}")
        return []