"""Cross-encoder reranking service"""
import logging
from copy import deepcopy
from typing import List, Dict, Any
from sentence_transformers import CrossEncoder
from core.logger import configure_logging
from src.core.logger import configure_logging

logger = configure_logging(logging.INFO)

class Reranker:
    """Cross-encoder based reranking"""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name)
    
    def rerank(
        self,
        query: str,
        items: List[Dict[str, Any]],
        top_k: int,
        text_field: str = "child_text"
    ) -> List[Dict[str, Any]]:
        """Rerank items based on query relevance"""
        if not items:
            return []
        
        try:
            pairs = [(query, item.get(text_field, "")) for item in items]
            scores = self.model.predict(pairs)
            
            scored = []
            for item, score in zip(items, scores):
                item_copy = deepcopy(item)
                item_copy["rerank_score"] = float(score)
                scored.append(item_copy)
            
            scored.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
            return scored[:top_k]
            
        except Exception as e:
            logger.error(f"Reranking error: {str(e)}")
            return items[:top_k]

reranker = Reranker()