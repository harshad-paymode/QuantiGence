"""Neo4j retrieval service"""
import logging
from typing import  Any
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings.openai import AzureOpenAIEmbeddings
from dotenv import load_dotenv
from core.logger import configure_logging
import os
from cypher.queries import TRANSCRIPT_VECTOR_RETRIEVAL_CYPHER

load_dotenv()
from src.core.logger import configure_logging

logger = configure_logging(logging.INFO)


#Get Query Embedding Function
def get_query_embeddings(query_text):
    embedder = AzureOpenAIEmbeddings(model=os.getenv("OPENAI_EMBED_MODEL"), azure_endpoint = os.getenv("OPENAI_EMBED_ENDPOINT") , api_version = os.getenv("OPENAI_EMBED_API_VERSION"), api_key=os.getenv("OPENAI_EMBED_API"))
    embedding = embedder.embed_query(query_text)
    logger.info("Query Embedding Done")
    return embedding

#Retriever Function
def retriever(driver,cypher, query_text, index_name, top_k, query_params, query_embedding):

    embedding = query_embedding

    params = dict(query_params)
    params.update({
        "embedding": embedding,
        "top_k": top_k,
        "index_name": index_name,
    })

    try:
        with driver.session(database=os.getenv("NEO4J_DATABASE", "neo4j")) as session:
            return session.run(cypher, params).data()
    except Exception as e:
        logger.error(f"Unable to run the Session! {e}")
        return None
    
def get_transcript_chunks(driver, transcript_query, company, periods, trans_query_embedding):

    transcript_result = retriever(
        driver = driver,
        cypher = TRANSCRIPT_VECTOR_RETRIEVAL_CYPHER,
        query_text=transcript_query,
        index_name = "tc",
        top_k = 5,
        query_params = {
            "company": company,
            "periods": periods,
        },
        query_embedding = trans_query_embedding
    )
    return transcript_result


