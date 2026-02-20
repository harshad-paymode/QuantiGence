import os
import json
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
import io

from src.core.database import connect_neo4j
from src.core.logger import configure_logging
from src.services.ingestion_service import GraphIngestionPipeline
from azure.storage.blob import BlobServiceClient


# Initialize environment and logger
load_dotenv()
logger = configure_logging()

class AzureBlobManager:
    def __init__(self):
        conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not conn_str:
            logger.error("Azure Storage Connection String not found in .env")
            raise ValueError("Missing AZURE_STORAGE_CONNECTION_STRING")
        
        self.blob_service_client = BlobServiceClient.from_connection_string(conn_str)
        self.container_name = "data"

    def load_parquet_from_blob(self, blob_name: str) -> pd.DataFrame:
        """Downloads a blob and loads it directly into a Pandas DataFrame."""
        try:
            logger.info(f"Fetching blob from Azure: {blob_name}")
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, 
                blob=blob_name
            )
            
            # Download as bytes and read into pandas
            downloader = blob_client.download_blob()
            stream = io.BytesIO(downloader.readall())
            df = pd.read_parquet(stream)
            
            logger.info(f"Successfully loaded {blob_name} ({len(df)} rows)")
            return df
        except Exception as e:
            logger.error(f"Failed to load blob {blob_name}: {e}")
            raise

def load_json(filepath: Path):
    logger.info(f"Loading JSON data from {filepath}")
    with open(filepath, 'r') as file:
        return json.load(file)

def main():
    # --- Configuration ---
    # JSON files are still local (as per your previous setup)
    sec_data_path = Path(os.getenv("OUT_ALL"))
    trans_data_path = Path(os.getenv("ALL_TRANSCRIPTS_PATH"))

    # Azure Blob Names
    sec_blob_name =  os.getenv("EMBEDDING_OPENAI_SEC")
    trans_blob_name =  os.getenv("EMBEDDING_OPENAI_TRANS")

    # --- Initialize Services ---
    blob_manager = AzureBlobManager()
    driver = connect_neo4j()

    try:
        # --- Load Data ---
        # 1. Load Local JSONs
        sec_chunks = load_json(sec_data_path)
        trans_chunks = load_json(trans_data_path)

        # 2. Fetch Parquets from Azure
        sec_embed_df = blob_manager.load_parquet_from_blob(sec_blob_name)
        trans_embed_df = blob_manager.load_parquet_from_blob(trans_blob_name)

        # --- Execute Pipeline ---
        pipeline = GraphIngestionPipeline(driver)
        
        logger.info("--- PHASE 1: INGESTING SEC DATA ---")
        pipeline.ingest_sec_data(sec_chunks, sec_embed_df, batch_size=10)
        
        logger.info("--- PHASE 2: INGESTING TRANSCRIPT DATA ---")
        pipeline.ingest_transcript_data(trans_chunks, trans_embed_df, batch_size=10)
        
        logger.info("All ingestion pipelines completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
    finally:
        driver.close()
        logger.info("Neo4j connection closed.")

if __name__ == "__main__":
    main()