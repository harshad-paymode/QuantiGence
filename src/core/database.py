import os
from neo4j import GraphDatabase
from src.core.logger import configure_logging

logger = configure_logging()

def connect_neo4j():
    """Initializes and verifies the Neo4j connection."""
    uri = os.getenv('NEO4J_URI')
    user = os.getenv('NEO4J_USERNAME')
    password = os.getenv('NEO4J_PASSWORD')

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        logger.info("Successfully connected to the Neo4j database.")
        return driver
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}", exc_info=True)
        raise