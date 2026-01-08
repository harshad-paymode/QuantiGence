#!/usr/bin/env python3
"""
CLI script to run 10-K and 10-Q chunking and save outputs.
This script uses configuration from src/chunking/config.py and will call the chunker modules.
"""
import logging
import os
from typing import List
from pathlib import Path

from src.core.logger import configure_logging
from src.core.config import Paths, Processing
from src.core.edgar_client import initialize_edgar
from src.chunking.postprocess import PostProcessor
from src.core.io import save_json
from src.core.config import SecFilingConfig

# chunkers
from src.chunking.tenk_chunker import get_chunks as get_chunks_10k
from src.chunking.tenq_chunker import get_chunks as get_chunks_10q

import pandas as pd

logger = logging.getLogger(__name__)



def process_files(kind: str, meta_base: str, out_path: str, get_chunks_fn, processing_cfg: Processing, config: SecFilingConfig) -> List[dict]:
    results = []
    for (cik, ticker), company in zip(config.TICKERS.items(), config.COMPANY_NAMES):
        meta_df_path = os.path.join(meta_base, ticker, f"{kind}.csv")
        if not os.path.exists(meta_df_path):
            logger.warning("Metadata file missing: %s", meta_df_path)
            continue
        try:
            meta_df = pd.read_csv(meta_df_path)
            meta_df = meta_df[pd.to_datetime(meta_df["filing_date"]).dt.year > processing_cfg.min_year]
        except Exception:
            logger.exception("Failed to read metadata csv: %s", meta_df_path)
            continue

        for _, row in meta_df.iterrows():
            filing_date = row.get("filing_date")
            accession_no = row.get("accession_number")
            try:
                all_chunks = get_chunks_fn(
                    filing_date=filing_date, ticker=ticker, company=company, cik=cik, accession_no=accession_no
                )
                # post-process
                pp = PostProcessor(chunk_size=processing_cfg.sentence_split_chunk_size, chunk_overlap=processing_cfg.sentence_split_overlap)
                all_chunks_processed = pp.post_processing_chunks(all_chunks)
                chunk_det = {"filing_date": filing_date, "ticker": ticker, "file_chunks": all_chunks_processed}
                results.append(chunk_det)
            except Exception:
                logger.exception("Failed to process filing %s %s %s", ticker, filing_date, accession_no)
    # try to persist
    try:
        save_json(out_path, results)
    except Exception:
        logger.exception("Failed to save results to %s", out_path)
    return results


def main():
    configure_logging()
    paths = Paths()
    proc = Processing()
    CONFIG = SecFilingConfig()

    sec_id = os.getenv("SEC_ID")
    sec_cache = os.getenv("SEC_CACHE")
    try:
        initialize_edgar(sec_id, sec_cache)
    except Exception:
        logger.exception("Failed to initialize edgar client. Aborting.")
        return

    results_10k = process_files("10-K", paths.base_metadata_10k, paths.out_10k, get_chunks_10k, proc, CONFIG)
    results_10q = process_files("10-Q", paths.base_metadata_10q, paths.out_10q, get_chunks_10q, proc, CONFIG)

    # combine and save combined
    try:
        combined = results_10k + results_10q
        save_json(paths.out_all, combined)
    except Exception:
        logger.exception("Failed to save combined file.")


if __name__ == "__main__":
    main()