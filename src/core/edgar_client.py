import logging
from typing import Optional
from edgar import set_identity, Filing, use_local_storage
from edgar.files.html_documents import TextBlock, TableBlock
from src.core.logger import configure_logging

logger = configure_logging(logging.INFO)



def initialize_edgar(sec_id: Optional[str], cache_path: Optional[str]) -> None:
    """
    Initialize SEC Edgar client.

    - Sets SEC identity (required by API)
    - Configures local file cache if path provided
    """

    if not sec_id:
        logger.warning("SEC_ID not provided. edgar.set_identity will still be called with None.")
    set_identity(sec_id)
    if cache_path:
        use_local_storage(cache_path)
        logger.info("edgar local storage configured: %s", cache_path)
    else:
        logger.info("No edgar cache path provided; using default edgar storage.")