import os
from typing import List, Dict
from src.core.logger import configure_logging
from src.cypher.ingestion_queries import *
from src.ingestion.mapper import map_sec_chunk, map_transcript_chunk

logger = configure_logging()

class GraphIngestionPipeline:
    def __init__(self, driver):
        self.driver = driver
        self.db_name = os.getenv("NEO4J_DATABASE", "neo4j")

    def _execute_write_query(self, query: str, batch: List[Dict] = None, log_msg: str = ""):
        """Centralized execution wrapper with logging."""
        try:
            with self.driver.session(database=self.db_name) as session:
                if batch:
                    summary = session.execute_write(lambda tx: tx.run(query, batch=batch).consume())
                    logger.info(f"{log_msg} | Nodes: {summary.counters.nodes_created} | Rels: {summary.counters.relationships_created} | Time: {summary.result_available_after}ms")
                else:
                    summary = session.execute_write(lambda tx: tx.run(query).consume())
                    logger.info(f"{log_msg} completed successfully.")
        except Exception as e:
            logger.error(f"Error executing query ({log_msg}): {e}", exc_info=True)

    def ingest_sec_data(self, raw_chunks: List[Dict], embed_df, batch_size: int = 10):
        logger.info("Starting SEC Data Ingestion...")
        self._execute_write_query(SEC_INIT_VECTOR_INDEX, log_msg="Initializing SEC Vector Index")

        buffer = []
        batch_id = 0

        for file in raw_chunks:
            for chunk_obj in file["file_chunks"]:
                buffer.append(map_sec_chunk(chunk_obj, embed_df))

                if len(buffer) == batch_size:
                    self._execute_write_query(SEC_INGESTION_BATCH, buffer, log_msg=f"SEC Batch {batch_id}")
                    batch_id += 1
                    buffer.clear()
            logger.info(f"Finished parsing SEC File: {file.get('ticker')} - {file.get('filing_date')}")

        if buffer:
            self._execute_write_query(SEC_INGESTION_BATCH, buffer, log_msg=f"SEC Final Batch {batch_id}")

        logger.info("SEC Database Creation Successful. Running post-processing...")
        self._execute_write_query(SEC_10Q_PERIOD, log_msg="Post-processing: 10-Q Periods")
        self._execute_write_query(SEC_10K_PERIOD, log_msg="Post-processing: 10-K Periods")
        self._execute_write_query(SEC_NEXT_REL, log_msg="Post-processing: SEC NEXT relationships")

    def ingest_transcript_data(self, transcript_chunks: List[Dict], embed_df, batch_size: int = 10):
        logger.info("Starting Transcript Data Ingestion...")
        self._execute_write_query(TRANSCRIPT_INIT_VECTOR_INDEX, log_msg="Initializing Transcript Vector Index")

        buffer = []
        batch_id = 0

        for file in transcript_chunks:
            for chunk_obj in file["transcript"]:
                buffer.append(map_transcript_chunk(chunk_obj, embed_df))

                if len(buffer) == batch_size:
                    self._execute_write_query(TRANSCRIPT_INGESTION_BATCH, buffer, log_msg=f"Transcript Batch {batch_id}")
                    batch_id += 1
                    buffer.clear()
            logger.info(f"Finished parsing Transcript File: {file.get('ticker')} - Q{file.get('quarter')} {file.get('year')}")

        if buffer:
            self._execute_write_query(TRANSCRIPT_INGESTION_BATCH, buffer, log_msg=f"Transcript Final Batch {batch_id}")

        logger.info("Transcript Database Creation Successful. Running post-processing...")
        self._execute_write_query(TRANSCRIPT_NEXT_REL, log_msg="Post-processing: Transcript NEXT relationships")