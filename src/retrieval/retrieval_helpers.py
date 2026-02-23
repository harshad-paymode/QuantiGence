from typing import List, Dict, Any, Tuple, Set
from src.core.logger import configure_logging
from src.services.query_processor import query_processor

logger = configure_logging()

# --- Helper Functions ---

def parse_record_content_and_graph_ui(
    record_items: List[Dict[str, Any]], 
    query_type: str = "SIMPLE"
) -> Tuple[List[Dict], List[Dict]]:
    """Parses and deduplicates raw Neo4j records into content and UI components."""
    logger.info(f"Parsing {len(record_items)} records with mode: {query_type}")
    
    print(f"Show me the sec results")
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

def build_retrieval_jobs(user_query: str, query_type: str):
    """
    Returns list of retrieval jobs:
    [
       { "sub_q": "...sub query...",
        "company": "Apple Inc.",
        "periods": ["Q1 2024", ...],
        "forms": ["10-Q", ...],
        "headings": ["risk factors", ...]
      }, ...
    }]
    """
  

    # always parse the original query (SIMPLE also)
    base = query_processor.parse_query(user_query)

    # decompose only if needed
    if query_type in ["BROAD", "COMPARISON"]:
        sub_queries = query_processor.decompose_query(user_query, query_type).get("sub_queries", []) or [user_query]
    else:
        sub_queries = [user_query]

    # helper: periods from years+quarters
    def make_periods(years, quarters):
        if years and quarters:
            return [f"{q}_{y}" for y in years for q in quarters]
        if years:
            return [f"FY_{str(y)}" for y in years]
        return []

    # global defaults from original parse
    base_company = base["companies"][0]["name"] if base.get("companies") else None
    base_periods = make_periods(base.get("years", []), base.get("quarters", []))
    base_headings = base.get("section_hints", [])
    base_forms = ["10-Q"] if base.get("filing_type_hint") == "10-Q" else ["10-K"] if base.get("filing_type_hint") == "10-K" else ["10-Q", "10-K"]

    jobs = []
    for sq in sub_queries:
        # parse each subquery to bind filters correctly
        p = query_processor.parse_query(sq)

        company = p["companies"][0]["name"] if p.get("companies") else base_company
        periods = make_periods(p.get("years", []), p.get("quarters", [])) or base_periods
        headings = p.get("section_hints", []) or base_headings

        if p.get("filing_type_hint") == "10-Q":
            forms = ["10-Q"]
        elif p.get("filing_type_hint") == "10-K":
            forms = ["10-K"]
        else:
            forms = base_forms

        jobs.append(
            {
                "q": sq,
                "company": company,
                "periods": periods,
                "forms": forms,
                "headings": headings,
            }
        )
    
    return jobs
