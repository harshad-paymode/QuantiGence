import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from opencensus.ext.azure.log_exporter import AzureLogHandler
from src.core.logger import configure_logging
from src.retrieval.retrieval_helpers import parse_record_content_and_graph_ui
from src.services.query_processor import query_processor
from src.retrieval.neo4j_retriever import get_query_embeddings, get_transcript_chunks, retriever
from src.retrieval.reranker import reranker
from src.cypher.queries import SEC_VECTOR_RETRIEVAL_CYPHER
# --- Logging Configuration ---

logger = configure_logging()

# --- Retrieval Logic ---

def _process_transcripts(driver, original_query: str, company: str, periods: List[str]):
    """Helper to handle repetitive transcript retrieval and reranking logic."""
    try:
        transcript_data = query_processor.get_transcript_query(original_query)
        transcript_query = transcript_data["tone_query"]
        
        trans_query_embedding = get_query_embeddings(transcript_query)
        
        transcript_result = get_transcript_chunks(
            driver, transcript_query, company, periods, trans_query_embedding
        )
        
        graph_ui, dict_list = parse_record_content_and_graph_ui(transcript_result)
        reranked_context = reranker.rerank(transcript_query, dict_list, top_k=5)
        
        return {
            "query": transcript_query,
            "embedding": trans_query_embedding,
            "context": reranked_context,
            "graph_ui": graph_ui
        }
    except Exception as e:
        logger.error(f"Error processing transcripts: {e}")
        raise

def retrieve_simple(
    driver,
    original_query: str,
    sub_queries: List[Dict],
    data_type: str,
    query_embedding: List[float],
) -> Dict[str, Any]:
    """Retrieves SEC and Transcript data for a single query context."""
    logger.info(f"Executing simple retrieval for: {original_query[:50]}...")

    # SEC Retrieval
    sec_result = retriever(
        driver=driver,
        cypher=SEC_VECTOR_RETRIEVAL_CYPHER,
        query_text=original_query,
        index_name="childchunks",
        top_k=10,
        query_params=sub_queries[0], # Assuming sub_queries[0] contains filters
        query_embedding=query_embedding
    )

    # Transcript Retrieval
    trans_data = _process_transcripts(
        driver, original_query, sub_queries[0]['company'], sub_queries[0]['periods']
    )

    graph_ui_sec, sec_dict_list = parse_record_content_and_graph_ui(sec_result)
    sec_top = reranker.rerank(original_query, sec_dict_list, top_k=10)

    return {
        "org_query": original_query,
        "data_type": data_type,
        "query_embedding_sec": query_embedding,
        "query_embedding_trans": trans_data["embedding"],
        "sub_queries": sub_queries,
        "transcript_query": trans_data["query"],
        "sec_context": sec_top,
        "trans_context": trans_data["context"],
        "sec_graph_ui": graph_ui_sec,
        "transcript_graph_ui": trans_data["graph_ui"],
    }

def retrieve_multi_query(
    driver,
    original_query: str,
    sub_queries: List[Dict],
    data_type: str,
    query_embedding: List[float]
) -> Dict[str, Any]:
    """Retrieves and aggregates data across multiple sub-queries."""
    logger.info(f"Executing multi-query retrieval for: {original_query[:50]}")

    sec_final, trans_final = [], []
    sec_graphs, trans_graphs = [], []
    
    # Get global transcript info for the original query
    main_trans_info = query_processor.get_transcript_query(original_query)
    trans_query_embedding = get_query_embeddings(main_trans_info["tone_query"])

    for sub_q in sub_queries:
        # SEC Loop
        sec_raw = retriever(
            driver=driver,
            cypher=SEC_VECTOR_RETRIEVAL_CYPHER,
            index_name="childchunks",
            query_text=sub_q['q'],
            top_k=10,
            query_params=sub_q,
            query_embedding=query_embedding
        )

        # Transcript Loop
        t_query = query_processor.get_transcript_query(sub_q["q"])["tone_query"]
        t_embedding = get_query_embeddings(t_query)
        trans_raw = get_transcript_chunks(
            driver, t_query, sub_q['company'], sub_q['periods'], t_embedding
        )

        # Parse & Rerank
        g_sec, d_sec = parse_record_content_and_graph_ui(sec_raw)
        g_trans, d_trans = parse_record_content_and_graph_ui(trans_raw)

        sec_final.extend(reranker.rerank(original_query, d_sec, top_k=3))
        trans_final.extend(reranker.rerank(t_query, d_trans, top_k=2))
        
        sec_graphs.extend(g_sec)
        trans_graphs.extend(g_trans)

    return {
        "org_query": original_query,
        "data_type": data_type,
        "query_embedding": query_embedding,
        "query_embedding_trans": trans_query_embedding,
        "sub_queries": sub_queries,
        "sec_context": sec_final,
        "trans_context": trans_final,
        "sec_graph_ui": sec_graphs,
        "transcript_graph_ui": trans_graphs,
    }

def retrieve_change_detection(
    driver, 
    original_query: str, 
    sub_queries: List, 
    periods: List[str], 
    company: str, 
    headings: List[str], 
    start_period: str, 
    end_period: str, 
    data_type: str, 
    query_embedding: List[float]
) -> Dict[str, Any]:
    """Detects changes over a sequential path of filings in the graph."""
    logger.info(f"Executing change detection for {company} from {start_period} to {end_period}")

    cypher_query = """
    MATCH (c:Company {name:$company})-[:FILED]->(start:Filing)
    WHERE start.period = $start_period
    MATCH path = (start)-[:NEXT*0..]->(end:Filing)
    WHERE end.period = $end_period
    UNWIND nodes(path) AS f
    MATCH hierarchy_path = (f)-[:HAS_SECTION]->(h:Heading)-[:HAS_CONTENT]->(p:ParentChunk)
    WHERE (size($headings)=0 OR any(hint IN $headings WHERE toLower(h.name) CONTAINS toLower(hint)))
    WITH DISTINCT c, f, h, p, 
         (nodes(path) + nodes(hierarchy_path)) AS all_nodes,
         (relationships(path) + relationships(hierarchy_path)) AS all_rels
    RETURN 
    {
        company: c.name, 
        period: f.period,
        filing_id: f.accession,
        form: f.form,
        heading: h.name,
        parent_chunk_id: p.chunk_id, 
        parent_text: p.content, 
        sub_heading: p.sub_heading_dict
    } AS content,
    {
        nodes: [n IN all_nodes | {labels: labels(n), props: properties(n)}],
        rels:  [r IN all_rels | {type: type(r), props: properties(r)}]
    } AS graph_ui
    ORDER BY f.period
    """

    db_name = os.getenv("NEO4J_DATABASE")
    with driver.session(database=db_name) as session:
        raw_sec = session.run(
            cypher_query,
            company=company,
            start_period=start_period,
            end_period=end_period,
            headings=headings,
        ).data()

    # Process Transcripts
    trans_data = _process_transcripts(driver, original_query, company, periods)
    
    graph_ui_sec, sec_dict_list = parse_record_content_and_graph_ui(raw_sec, "CHANGE_DETECTION")

    return {
        "org_query": original_query,
        "data_type": data_type,
        "query_embedding": query_embedding,
        "query_embedding_trans": trans_data["embedding"],
        "sub_queries": sub_queries,
        "sec_context": sec_dict_list, # Note: No reranking for trend analysis
        "trans_context": trans_data["context"],
        "sec_graph_ui": graph_ui_sec,
        "transcript_graph_ui": trans_data["graph_ui"],
    }