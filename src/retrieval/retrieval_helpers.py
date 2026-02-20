import logging
from typing import List, Dict, Any, Tuple, Set
from src.core.logger import configure_logging

logger = configure_logging()

# --- Helper Functions ---

def parse_record_content_and_graph_ui(
    record_items: List[Dict[str, Any]], 
    query_type: str = "SIMPLE"
) -> Tuple[List[Dict], List[Dict]]:
    """Parses and deduplicates raw Neo4j records into content and UI components."""
    logger.info(f"Parsing {len(record_items)} records with mode: {query_type}")
    
    content_dict_list = []
    graph_ui_list = []
    seen_chunk_ids: Set[str] = set()

    chunk_id_key = "parent_chunk_id" if query_type == "CHANGE_DETECTION" else "child_chunk_id"

    for item in record_items:
        record = item.get('content', {})
        graph_ui = item.get('graph_ui', {})
        cid = record.get(chunk_id_key)

        if cid and cid not in seen_chunk_ids:
            seen_chunk_ids.add(cid)
            content_dict_list.append(record)
            graph_ui_list.append(graph_ui)
        elif not cid:
            logger.warning(f"Record found missing identifier key: {chunk_id_key}")

    logger.info(f"Parsing complete. Retained {len(content_dict_list)} unique chunks.")
    return graph_ui_list, content_dict_list


def build_sec_context(sec_chunks: List[Dict[str, Any]]) -> str:
    """Formats SEC filing chunks into a structured string for LLM context."""
    if not sec_chunks:
        logger.warning("build_sec_context called with empty chunk list.")
        return "No SEC context available."

    logger.info(f"Building SEC context for {len(sec_chunks)} chunks.")
    parts = []
    for chunk in sec_chunks:
        entry = (
            f"--- EVIDENCE ID: {chunk.get('filing_id', 'N/A')} ---\n"
            f"Company: {chunk.get('company', 'N/A')}\n"
            f"Period: {chunk.get('period', 'N/A')}\n"
            f"Form: {chunk.get('form', 'N/A')}\n"
            f"Section: {chunk.get('heading', 'N/A')}\n"
            f"Sub-sections: {chunk.get('sub_heading', 'N/A')}\n"
            f"Content: {chunk.get('parent_text', '').strip()}\n"
        )
        parts.append(entry)

    return "\n\n---\n\n".join(parts)


def build_transcript_context(transcript_chunks: List[Dict[str, Any]]) -> str:
    """Formats earnings call transcript chunks into a dialogue-style context."""
    if not transcript_chunks:
        logger.warning("build_transcript_context called with empty chunk list.")
        return "No transcript context available."

    logger.info(f"Building Transcript context for {len(transcript_chunks)} chunks.")
    parts = []
    for chunk in transcript_chunks:
        entry = (
            f"Company: {chunk.get('company', 'N/A')}\n"
            f"Period: {chunk.get('period', 'N/A')}\n"
            f"Speaker: {chunk.get('speaker', 'N/A')}\n"
            f"Content: {chunk.get('parent_text', '').strip()}\n"
        )
        parts.append(entry)

    return "\n\n---\n\n".join(parts)
