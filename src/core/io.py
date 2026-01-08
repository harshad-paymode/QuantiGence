import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def save_json(path: Path, data: Any, indent: int = 4) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=indent)
        logger.info("Saved JSON to %s", path)
    except Exception:
        logger.exception("Failed to save JSON to %s", path)
        raise

