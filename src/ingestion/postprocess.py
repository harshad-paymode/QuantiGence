import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Document

logger = logging.getLogger(__name__)


@dataclass
class PostProcessor:
    chunk_size: int = 512
    chunk_overlap: int = 100

    def post_processing_chunks(self, all_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        For each parent chunk, add an 'ID' and compute 'child_chunks' using a sentence splitter.
        If llama_index is not available it will set child_chunks = {} and continue.
        """
        CHUNK_COUNTER = 1
        processed = all_chunks.copy()

        if SentenceSplitter is None or Document is None:
            logger.info("SentenceSplitter not available: returning chunks with empty child_chunks.")
            for chunk in processed:
                chunk["ID"] = CHUNK_COUNTER
                CHUNK_COUNTER += 1
                chunk.setdefault("Chunks", {}).setdefault("child_chunks", {})
            return processed

        splitter = SentenceSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)

        for chunk in processed:
            chunk["ID"] = CHUNK_COUNTER
            CHUNK_COUNTER += 1
            meta = chunk.get("Metadata") or {}
            # tables are kept as-is
            if meta.get("is_table"):
                chunk["Chunks"]["child_chunks"] = {}
                continue

            text = chunk["Chunks"].get("parent_chunk", "")
            chunk["Chunks"]["child_chunks"] = {}
            try:
                documents = [Document(text=text)]
                nodes = splitter.get_nodes_from_documents(documents)
            except Exception:
                logger.exception("Sentence splitting failed; leaving child_chunks empty.")
                continue

            for i, node in enumerate(nodes):
                if text == node.text:
                    break
                if i == 0:
                    if len(text.split()) - len(node.text.split()) > 100:
                        chunk["Chunks"]["child_chunks"][f"{i}"] = node.text
                    else:
                        break
                else:
                    if len(node.text.split()) > 50:
                        chunk["Chunks"]["child_chunks"][f"{i}"] = node.text
                    else:
                        # append to previous
                        if f"{i-1}" in chunk["Chunks"]["child_chunks"]:
                            chunk["Chunks"]["child_chunks"][f"{i-1}"] += node.text
                        else:
                            chunk["Chunks"]["child_chunks"][f"{i}"] = node.text
        return processed