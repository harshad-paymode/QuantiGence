"""Function call schemas for LLM tools"""


INPUT_OUTPUT_POLICY_FN = {
    "name": "classify_harm",
    "description": "Classify whether the given text is harmful or not",
    "parameters": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": ["harmful", "unharmful"]
            },
            "reason": {
                "type": "string"
            }
        },
        "required": ["category", "reason"]
    }
}

INPUT_FILTER_FN = {
    "name": "route_user_input",
    "description": "Classify the user query for safe routing",
    "parameters": {
        "type": "object",
        "properties": {
            "classification": {
                "type": "string",
                "enum": [
                    "SMALL_TALK",
                    "OUT_OF_SCOPE",
                    "INVESTMENT_ADVICE_REQUEST",
                    "PERSONAL_INFO",
                    "FINANCE_RESEARCH_OK"
                ]
            },
            "reason": {
                "type": "string"
            }
        },
        "required": ["classification", "reason"]
    }
}

OUTPUT_FILTER_FN = {
    "name": "check_financial_advice",
    "description": "Check whether the assistant response contains financial advice",
    "parameters": {
        "type": "object",
        "properties": {
            "has_financial_advice": {
                "type": "boolean"
            },
            "reason": {
                "type": "string"
            },
            "suggested_fix": {
                "type": "string"
            }
        },
        "required": ["has_financial_advice", "reason", "suggested_fix"]
    }
}


QUERY_MODIFIER_FN = [
    {
        "type": "function",
        "function": {
            "name": "return_modified_query",
            "description": (
                "Return the original query, a corrected/completed query using chat history, "
                "and a short explanation of what was changed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "original_query": {
                        "type": "string",
                        "description": "The user's raw input query.",
                    },
                    "corrected_query": {
                        "type": "string",
                        "description": "The completed/corrected query using chat history context.",
                    },
                    "explanation": {
                        "type": "string",
                        "description": "Brief explanation of the correction or completion.",
                    },
                },
                "required": ["original_query", "corrected_query", "explanation"],
            },
        },
    }
]


SOURCE_CLASSIFIER_FN = [
    {
        "type": "function",
        "function": {
            "name": "return_source_type",
            "description": "Classify whether the financial query is about SEC filings or Earnings Call transcripts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_type": {
                        "type": "string",
                        "enum": ["SEC", "TRANSCRIPT"],
                        "description": "SEC for filings like 10-K, 10-Q. TRANSCRIPT for earnings call / management commentary."
                    },
                    "reason": {
                        "type": "string",
                        "description": "Brief explanation for classification."
                    }
                },
                "required": ["source_type", "reason"]
            }
        }
    }
]

QUERY_CLASSIFIER_FN = [
    {
        "type": "function",
        "function": {
            "name": "return_query_type",
            "description": "Classify the financial query into exactly one of four categories based on intent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_type": {
                        "type": "string",
                        "enum": ["GENERAL", "SIMPLE", "BROAD", "COMPARISON", "CHANGE_DETECTION"],
                        "description": "The specific category the query falls into."
                    },
                    "reason": {
                        "type": "string",
                        "description": "Brief explanation for the chosen classification."
                    }
                },
                "required": ["query_type", "reason"]
            }
        }
    }
]

DECOMPOSE_FN = [
    {
        "type": "function",
        "function": {
            "name": "return_sub_queries",
            "description": "Return 2-5 atomic retrieval sub-queries for SEC filing QA.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sub_queries": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["sub_queries"],
            },
        },
    }
]

QUERY_PARSER_FN = [
    {
        "type": "function",
        "function": {
            "name": "return_parsed_query",
            "description": "Parse query into company, time period, and section hints for retrieval filtering.",
            "parameters": {
                "type": "object",
                "properties": {
                    "companies": {
                        "type": "array",
                        "description": "List of matched companies in the query.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ticker": {"type": "string"},
                                "name": {"type": "string"},
                            },
                            "required": ["ticker", "name"],
                        },
                    },
                    "years": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Years mentioned in the query (e.g., 2021, 2023).",
                    },
                    "quarters": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["Q1", "Q2", "Q3", "Q4"]},
                        "description": "Quarters mentioned in the query.",
                    },
                    "filing_type_hint": {
                        "type": "string",
                        "enum": ["10-K", "10-Q", "UNKNOWN"],
                        "description": "Infer whether the query is annual/quarterly. Use UNKNOWN if unclear.",
                    },
                    "section_hints": {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 4,
                        "items": {"type": "string"},
                        "description": "Matched section/heading hints from canonical 10-K/10-Q heading sets.",
                    },
                },
                "required": ["companies", "years", "quarters", "filing_type_hint", "section_hints"],
            },
        },
    }
]


TONE_REWRITER_FN = [
    {
        "type": "function",
        "function": {
            "name": "return_tone_query",
            "description": "Rewrite query into ONE transcript-focused management tone retrieval query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "focus": {
                        "type": "string",
                        "enum": ["METRICS", "RISKS", "GUIDANCE", "GENERAL"],
                        "description": "Main intent of the query for transcript tone extraction."
                    },
                    "tone_query": {
                        "type": "string",
                        "description": "Single rewritten query optimized to retrieve management tone from earnings call transcripts."
                    }
                },
                "required": ["focus", "tone_query"]
            }
        }
    }
]
