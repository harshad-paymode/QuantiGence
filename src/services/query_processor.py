"""Query processing pipeline"""
import json
import logging
from typing import Dict, Any, List
from src.tools.query_decomposer_helpers import _validate_sub_queries
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
        msg = mistral_client.call_with_tool(
            model=self.classifier_model,
            system_prompt=SYSTEM_PROMPT_CLASSIFIER,
            user_message=query,
            tools=QUERY_CLASSIFIER_FN,
            tool_choice={"type": "function", "function": {"name": "return_query_type"}},
            temperature=0.0,
        )

        tool_calls = getattr(msg, "tool_calls", None)

        if not tool_calls:
            return {"query_type": "SIMPLE", "reason": "Defaulted due to tool call failure."}

        args = json.loads(tool_calls[0].function.arguments) if isinstance(tool_calls[0].function.arguments, str) else tool_calls[0].function.arguments

        return {
            "query_type": args.get("query_type", "SIMPLE"),
            "reason": args.get("reason", "No reason provided.")
        }

    
    def classify_source(self, query: str) -> Dict[str, Any]:
        """Classify data source (SEC or TRANSCRIPT)"""
        msg = mistral_client.call_with_tool(
            model=self.classifier_model,
            system_prompt=SYSTEM_PROMPT_SOURCE_CLASSIFIER,
            user_message=query,
            tools=SOURCE_CLASSIFIER_FN,
            tool_choice= {"type": "function", "function": {"name": "return_source_type"}},
            temperature=0.0,
        )
        tool_calls = getattr(msg, "tool_calls", None)

        if not tool_calls:
            return {"source_type": "SEC", "reason": "Defaulted due to tool call failure."}

        args = (
            json.loads(tool_calls[0].function.arguments)
            if isinstance(tool_calls[0].function.arguments, str)
            else tool_calls[0].function.arguments
        )

        return {
            "source_type": args.get("source_type", "SEC"),
            "reason": args.get("reason", "No reason provided."),
        }
    
    def parse_query(self, query: str) -> Dict[str, Any]:
        """Parse query for companies, years, quarters, sections"""
        msg = mistral_client.call_with_tool(
            model=self.parser_model,
            system_prompt=SYSTEM_PROMPT_QUERY_PARSER,
            user_message=query,
            tools=QUERY_PARSER_FN,
            tool_choice={"type": "function", "function": {"name": "return_parsed_query"}},
            temperature=0.0,
            max_tokens=250,
        )

        tool_calls = getattr(msg, "tool_calls", None)

        # safe fallback
        if not tool_calls:
            return {
                "companies": [],
                "years": [],
                "quarters": [],
                "filing_type_hint": "UNKNOWN",
                "section_hints": [],
            }

        args = tool_calls[0].function.arguments
        if isinstance(args, str):
            args = json.loads(args)

        # normalize / dedupe (important)
        args["years"] = sorted(set(int(y) for y in args.get("years", []) if isinstance(y, int) or str(y).isdigit()))
        args["quarters"] = sorted(set(args.get("quarters", [])))
        args["section_hints"] = list(dict.fromkeys([s.strip().lower() for s in args.get("section_hints", []) if isinstance(s, str)]))

        # dedupe companies by ticker
        seen = set()
        companies_clean = []
        for c in args.get("companies", []):
            t = c.get("ticker")
            if t and t not in seen:
                seen.add(t)
                companies_clean.append({"ticker": t, "name": c.get("name", "")})
        args["companies"] = companies_clean

        
        return args
    
    def decompose_query(self, query: str, query_type: str) -> Dict[str, Any]:
        """Decompose complex queries into sub-queries"""
        if query_type not in ["BROAD", "COMPARISON"]:
            return {"sub_queries": [query]}
        
        msg = mistral_client.call_with_tool(
            model=self.decomposer_model,
            system_prompt=SYSTEM_PROMPT_DECOMPOSE,
            user_message=query,
            tools= DECOMPOSE_FN,
            tool_choice={"type": "function", "function": {"name": "return_sub_queries"}},
            temperature=0.0,
            max_tokens=300,
        )

        tool_calls = getattr(msg, "tool_calls", None)

        if not tool_calls:
            return {"sub_queries": [query]}

        args = tool_calls[0].function.arguments
        if isinstance(args, str):
            args = json.loads(args)

        raw_sub_queries = args.get("sub_queries", [])
        sub_queries = _validate_sub_queries(raw_sub_queries, fallback_query=query)

        return {"sub_queries": sub_queries}

    
    def normalize_query_with_history(self, query: str, chat_history: List[Dict]) -> Dict[str, Any]:
        """Refine query using chat history"""
        history = chat_history[-3:] if chat_history else []
        payload = json.dumps({
            "input_query": query,
            "chat_history": history,
        }, ensure_ascii=False)
        
        msg =  mistral_client.call_with_tool(
            model=self.modifier_model,
            system_prompt=SYSTEM_PROMPT_QUERY_MODIFIER,
            user_message=payload,
            tools=QUERY_MODIFIER_FN,
            tool_choice={"type": "function", "function": {"name": "return_modified_query"}},
            temperature=0.0,
            max_tokens=200,
        )
        tool_calls = getattr(msg, "tool_calls", None)

        if not tool_calls:
            return {
                "original_query": query,
                "corrected_query": query,
                "explanation": "No changes applied; tool call missing.",
            }

        args = tool_calls[0].function.arguments
        if isinstance(args, str):
            args = json.loads(args)

        return {
            "original_query": args.get("original_query", query),
            "corrected_query": args.get("corrected_query", query),
            "explanation": args.get("explanation", "No explanation provided."),
        }
    
    def get_transcript_query(self, query: str) -> Dict[str, Any]:
        """Transform query into transcript-focused question"""
        msg = mistral_client.call_with_tool(
            model=self.tone_model,
            system_prompt=SYSTEM_PROMPT_TONE_REWRITER,
            user_message=query,
            tools=TONE_REWRITER_FN,
            tool_choice={"type": "function", "function": {"name": "return_tone_query"}},
            temperature=0.0,
            max_tokens=160,
        )

        tool_calls = getattr(msg, "tool_calls", None)

        # fallback
        if not tool_calls:
            return {
                "focus": "GENERAL",
                "tone_query": "What was management's tone and outlook related to this topic?"
            }

        args = tool_calls[0].function.arguments
        if isinstance(args, str):
            args = json.loads(args)

        focus = args.get("focus", "GENERAL")
        if focus not in ["METRICS", "RISKS", "GUIDANCE", "GENERAL"]:
            focus = "GENERAL"

        tone_query = args.get("tone_query", "").strip()
        if not tone_query:
            tone_query = "What was management's tone and outlook related to this topic?"

        return {"focus": focus, "tone_query": tone_query}

query_processor = QueryProcessor()