"""LangGraph state definitions"""
from typing import TypedDict, List, Literal, Union, Dict, Any
from langchain_core.messages import BaseMessage

class QueryParserState(TypedDict, total=False):
    """Parsed query metadata"""
    companies: List[Dict[str, str]]
    years: List[int]
    quarters: List[str]
    filing_type_hint: str
    section_hints: List[str]

class QueryResState(TypedDict):
    """Main orchestration state"""
    # Conversation
    conversation_id: str
    turn_id: int
    messages: List[BaseMessage]
    last_user_message: str
    conversation_memory: Dict[str, Any]
    
    # Query processing
    org_query: str
    modif_query: str
    query_classification: str
    data_source_classification: str
    sub_queries: List[Dict[str, Any]]
    transcript_query: str
    query_embedding: List[float]
    query_embedding_trans: List[float]
    parsed_query: QueryParserState
    query_modified: bool
    
    # Retrieval
    sec_context: List[Dict[str, Any]]
    trans_context: List[Dict[str, Any]]
    sec_graph_ui: List[Dict[str, Any]]
    transcript_graph_ui: List[Dict[str, Any]]
    reuse_context: bool
    
    # Generation
    llm_response_sec: str
    llm_response_trans: str
    final_response: Union[str, List[Dict]]
    
    # Evaluation
    audit_score: Dict[str, float]
    analysis_retry_count: int
    research_retry_count: int
    analysis_ok: bool
    context_sufficient: bool
    
    # Safety
    input_state: bool
    auditor_fail: bool
    query_harmful: bool
    response_harmful: bool
    
    # Flow control
    needs_refinement: bool
    researcher_fail: bool
    company_present: bool
    period_present: bool

def init_query_state(user_query: str, conversation_id: str) -> QueryResState:
    """Initialize empty state for new query"""
    return {
        "conversation_id": conversation_id,
        "turn_id": 0,
        "messages": [],
        "last_user_message": user_query,
        "conversation_memory": {},
        "org_query": user_query,
        "modif_query": "",
        "query_classification": "SIMPLE",
        "data_source_classification": "SEC",
        "sub_queries": [],
        "transcript_query": "",
        "query_embedding": [],
        "query_embedding_trans": [],
        "parsed_query": {},
        "query_modified": False,
        "sec_context": [],
        "trans_context": [],
        "sec_graph_ui": [],
        "transcript_graph_ui": [],
        "reuse_context": False,
        "llm_response_sec": "",
        "llm_response_trans": "",
        "final_response": "",
        "audit_score": {},
        "analysis_retry_count": 0,
        "research_retry_count": 0,
        "analysis_ok": False,
        "context_sufficient": True,
        "input_state": True,
        "auditor_fail": False,
        "query_harmful": False,
        "response_harmful": False,
        "needs_refinement": False,
        "researcher_fail": False,
        "company_present": True,
        "period_present": True,
    }