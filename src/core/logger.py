import logging
import sys
from typing import Optional


def configure_logging(level: int = logging.INFO, stream: Optional = None) -> None:
    """Configure root logger for the chunking package."""
    if stream is None:
        stream = sys.stdout

    fmt = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter(fmt))

    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(handler)

    # basic config (no forced overwrite)
    logging.basicConfig(level=level, handlers=[handler], force=False)

    root.setLevel(level)

