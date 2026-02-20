import json
import pandas as pd
from typing import Dict, Any, List
from src.core.logger import configure_logging

logger = configure_logging()

def extract_embeddings(child_chunks: Dict, embed_df: pd.DataFrame) -> Dict[str, List[float]]:
    """Helper to fetch embeddings from the loaded Parquet dataframe."""
    embeddings = {}
    for child_id in child_chunks.keys():
        row = embed_df.loc[embed_df['id'] == child_id, "openai_embedding"]
        if row.empty:
            raise ValueError(f"Missing embedding for {child_id}")
        vec = row.values[0]
        embeddings[child_id] = [float(x) for x in vec]
        logger.info(f"Fetched embedding from dataframe")
    return embeddings

def map_sec_chunk(chunk_obj: Dict, embed_df: pd.DataFrame) -> Dict[str, Any]:
    """Maps SEC JSON chunk into the required Cypher dictionary format."""
    metadata = chunk_obj["Metadata"]
    chunks = chunk_obj["Chunks"]
    
    return {
        "parent_chunk_content": chunks["parent_chunk"],
        "parent_chunk_id": chunk_obj["ID"],
        "child_chunks": chunks["child_chunks"],
        "filing_date": metadata["filing_date"],
        "heading_name": metadata.get("item_heading", "Not Found"),
        "form_type": metadata["form"],
        "company_name": metadata["company"],
        "is_table": metadata["is_table"],
        "accession_no": metadata["accession_no"],
        "sub_headings": json.dumps(metadata.get("sub_headings", {})),
        "embeddings": extract_embeddings(chunks["child_chunks"], embed_df)
    }

def map_transcript_chunk(chunk_obj: Dict, embed_df: pd.DataFrame) -> Dict[str, Any]:
    """Maps Transcript JSON chunk into the required Cypher dictionary format."""
    metadata = chunk_obj["Metadata"]
    parent_chunk = chunk_obj["ParentChunk"]
    
    return {
        "parent_chunk_content": parent_chunk["chunk"],
        "parent_chunk_id": parent_chunk['ID'],
        "child_chunks": chunk_obj["ChildChunks"],
        "period": f"{metadata['quarter']}_{metadata['year']}",
        "company_name": metadata["company"],
        "speaker_name": metadata["speaker"],
        "speaker_title": metadata["title"],
        "embeddings": extract_embeddings(chunk_obj["ChildChunks"], embed_df)
    }