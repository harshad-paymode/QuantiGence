import os
from dataclasses import dataclass
from dotenv import load_dotenv
from typing import Optional
from typing import Iterable, Mapping
from frozendict import frozendict
import Path

load_dotenv()  # load .env if present

def require_env(name: str) -> str:
    """
    Fetch a required environment variable or raise a clear error.

    This prevents cryptic runtime crashes like int(None).
    """
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"Missing required environment variable: {name}")
    return value

# ---------------- Configuration & Constants ---------------- #


@dataclass(frozen=True)
class SecFilingConfig:
    tech_tickers: frozendict[int, str] = frozendict({
    320193: "AAPL",
    789019: "MSFT",
    1652044: "GOOGL",
    1018724: "AMZN",
    1326801: "META",
    1045810: "NVDA",
    1318605: "TSLA",
    1341439: "ORCL",
    1108524: "CRM",
    1065280: "NFLX",
    796343: "ADBE",
    })
    
    # 2. Using tuple for the "frozen list" of company names
    company_names: tuple[str, ...] = (
        "Apple Inc.",
        "MICROSOFT CORP",
        "Alphabet Inc.",
        "AMAZON COM INC.",
        "Meta Platforms, Inc.",
        "NVIDIA CORP",
        "Tesla, Inc.",
        "ORACLE CORP",
        "Salesforce, Inc.",
        "NETFLIX INC",
        "ADOBE INC.",
    )
    
    forms: tuple[str, ...] = ("10-K", "10-Q")



@dataclass
class Paths:
    base_metadata_10k: str = require_env(
        "BASE_PATH_TENK"
    )
    base_metadata_10q: str = require_env(
        "BASE_PATH_TENQ"
    )
    out_10k: str = require_env(
        "OUT_10K"
    )
    out_10q: str = require_env(
        "OUT_10Q"
    )
    out_all: str = require_env(
        "OUT_ALL"
    )
    base_save_path = require_env(
        "BASE_PATH_SAVE"
    )


@dataclass
class Processing:
    min_year: int = int(os.getenv("MIN_YEAR", 2023))
    sentence_split_chunk_size: int = int(os.getenv("SENT_SPLIT_CHUNK_SIZE", 512))
    sentence_split_overlap: int = int(os.getenv("SENT_SPLIT_OVERLAP",100))
    min_words_for_chunk: int = int(os.getenv("MIN_WORDS_FOR_CHUNK",20))
    table_match_pct: float = float(os.getenv("TABLE_MATCH_PCT",0.3))