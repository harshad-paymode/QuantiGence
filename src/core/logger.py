import logging
import sys
from typing import Optional
from dotenv import load_dotenv
from opencensus.ext.azure.log_exporter import AzureLogHandler
import os

load_dotenv()


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """Configures and returns the logger with Azure and Stream handlers."""
    fmt = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
    formatter = logging.Formatter(fmt)
    
    logger = logging.getLogger(__name__)
    
    # Avoid duplicate handlers if the logger is reused
    if not logger.handlers:
        # Azure Insights Handler
        azure_key = os.getenv("AZURE_INSIGHTS_KEY")
        if azure_key:
            logger.addHandler(AzureLogHandler(connection_string=azure_key))
        
        # Stream Handler
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    logger.setLevel(level)
    return logger
