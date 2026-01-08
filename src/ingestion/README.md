# SEC Chunking Package

SEC filings are noisy as PDFs and inconsistently structured as raw HTML.
QuantiGence uses edgartools to extract logical document sections, then performs semantic chunking aligned to headings instead of arbitrary token windows. This preserves context while avoiding vector dilution.

Quick overview:
- src/chunking/config.py: paths and processing settings.
- src/chunking/edgar_client.py: thin wrapper to initialize edgar client (SEC_ID, SEC_CACHE).
- src/chunking/toc.py: heuristics to find table-of-contents table.
- src/chunking/postprocess.py: create child chunks using SentenceSplitter (llama_index).
- src/chunking/tenk_chunker.py / tenq_chunker.py: chunking logic adapted from your notebook.
- scripts/run_chunking.py: entrypoint to run the pipeline and persist JSON outputs.

Usage:
1. Install dependencies (edgar, llama_index, pandas, python-dotenv, etc.)
2. Ensure environment variables are set:
   - SEC_ID, SEC_CACHE (optional)
   - or edit src/chunking/config.py to change paths
3. Run:
   python scripts/run_chunking.py

Notes:
- All external dependency imports are wrapped with helpful log messages; installing the packages will remove those warnings.
- Logging is configured to stdout. Edit src/chunking/logger.py to change behavior.
- You can integrate these modules into a larger pipeline (vector store, retrieval) easily.
