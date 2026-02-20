"""Query processing pipeline"""
import json
import logging
from typing import Dict, Any, List
from prompts.retrieval_prompts import (
    SYSTEM_PROMPT_CLASSIFIER,
    SYSTEM_PROMPT_SOURCE_CLASSIFIER,
    SYSTEM_PROMPT_DECOMPOSE,
    SYSTEM_PROMPT_QUERY_PARSER,
    SYSTEM_PROMPT_QUERY_MODIFIER,
    SYSTEM_PROMPT_TONE_REWRITER,
)
from tools.mistral_functions import (
    QUERY_CLASSIFIER_FN,
    SOURCE_CLASSIFIER_FN,
    DECOMPOSE_FN,
    QUERY_PARSER_FN,
    QUERY_MODIFIER_FN,
    TONE_REWRITER_FN,
)
from tools.mistral_client import mistral_client
from core.constants import COMPANY_SYNONYMS
from dotenv import load_dotenv
import os

load_dotenv()
from src.core.logger import configure_logging

logger = configure_logging(logging.INFO)

class QueryProcessor:
    """Query classification, parsing, decomposition"""
    
    def __init__(self):
        self.classifier_model = os.getenv("MISTRAL_CLASSIFIER_MODEL")
        self.parser_model = os.getenv("MISTRAL_PARSER_MODEL")
        self.decomposer_model = os.getenv("MISTRAL_DECOMPOSER_MODEL")
        self.tone_model = os.getenv("MISTRAL_TONE_REWRITER_MODEL")
        self.modifier_model = os.getenv("MISTRAL_MODIFIER_MODEL")
    
    def classify_query(self, query: str) -> Dict[str, Any]:
        """Classify query type (SIMPLE, BROAD, etc)"""
        return mistral_client.call_with_tool(
            model=self.classifier_model,
            system_prompt=SYSTEM_PROMPT_CLASSIFIER,
            user_message=query,
            tools=[{"type": "function", "function": QUERY_CLASSIFIER_FN}],
            tool_function_name="return_query_type",
            temperature=0.0,
        )
    
    def classify_source(self, query: str) -> Dict[str, Any]:
        """Classify data source (SEC or TRANSCRIPT)"""
        return mistral_client.call_with_tool(
            model=self.classifier_model,
            system_prompt=SYSTEM_PROMPT_SOURCE_CLASSIFIER,
            user_message=query,
            tools=[{"type": "function", "function": SOURCE_CLASSIFIER_FN}],
            tool_function_name="return_source_type",
            temperature=0.0,
        )
    
    def parse_query(self, query: str) -> Dict[str, Any]:
        """Parse query for companies, years, quarters, sections"""
        return mistral_client.call_with_tool(
            model=self.parser_model,
            system_prompt=SYSTEM_PROMPT_QUERY_PARSER,
            user_message=query,
            tools=[{"type": "function", "function": QUERY_PARSER_FN}],
            tool_function_name="return_parsed_query",
            temperature=0.0,
            max_tokens=250,
        )
    
    def decompose_query(self, query: str, query_type: str) -> Dict[str, Any]:
        """Decompose complex queries into sub-queries"""
        if query_type not in ["BROAD", "COMPARISON"]:
            return {"sub_queries": [query]}
        
        return mistral_client.call_with_tool(
            model=self.decomposer_model,
            system_prompt=SYSTEM_PROMPT_DECOMPOSE,
            user_message=query,
            tools=[{"type": "function", "function": DECOMPOSE_FN}],
            tool_function_name="return_sub_queries",
            temperature=0.0,
            max_tokens=300,
        )
    
    def normalize_query_with_history(self, query: str, chat_history: List[Dict]) -> Dict[str, Any]:
        """Refine query using chat history"""
        history = chat_history[-3:] if chat_history else []
        payload = json.dumps({
            "input_query": query,
            "chat_history": history,
        }, ensure_ascii=False)
        
        return mistral_client.call_with_tool(
            model=self.modifier_model,
            system_prompt=SYSTEM_PROMPT_QUERY_MODIFIER,
            user_message=payload,
            tools=[{"type": "function", "function": QUERY_MODIFIER_FN}],
            tool_function_name="return_modified_query",
            temperature=0.0,
            max_tokens=200,
        )
    
    def get_transcript_query(self, query: str) -> Dict[str, Any]:
        """Transform query into transcript-focused question"""
        return mistral_client.call_with_tool(
            model=self.tone_model,
            system_prompt=SYSTEM_PROMPT_TONE_REWRITER,
            user_message=query,
            tools=[{"type": "function", "function": TONE_REWRITER_FN}],
            tool_function_name="return_tone_query",
            temperature=0.0,
            max_tokens=160,
        )

query_processor = QueryProcessor()