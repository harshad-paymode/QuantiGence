"""
Analyst Service: LLM-based answer generation.
Generates SEC analysis, transcript commentary, and change detection analysis.
"""
import logging
from typing import List, Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
import os
from src.core.logger import configure_logging

logger = configure_logging(logging.INFO)


def get_sec_llm() -> AzureChatOpenAI:
    """Get configured Azure OpenAI instance for SEC analysis."""
    return AzureChatOpenAI(
        azure_deployment=os.getenv("OPENAI_SQ_MODEL"),
        api_version=os.getenv("OPENAI_SQ_API_VERSION"),
        api_key=os.getenv("OPENAI_SQ_API"),
        azure_endpoint=os.getenv("OPENAI_SQ_ENDPOINT"),
        temperature=0.0,
    )


def get_broad_llm() -> AzureChatOpenAI:
    """Get configured Azure OpenAI instance for broad/comparison analysis."""
    return AzureChatOpenAI(
        azure_deployment=os.getenv("OPENAI_CB_MODEL"),
        api_version=os.getenv("OPENAI_CB_API_VERSION"),
        api_key=os.getenv("OPENAI_CB_API"),
        azure_endpoint=os.getenv("OPENAI_CB_ENDPOINT"),
        temperature=0.0,
    )


def get_change_llm() -> AzureChatOpenAI:
    """Get configured Azure OpenAI instance for change detection."""
    return AzureChatOpenAI(
        azure_deployment=os.getenv("OPENAI_CD_MODEL"),
        api_version=os.getenv("OPENAI_CD_API_VERSION"),
        api_key=os.getenv("OPENAI_CD_API"),
        azure_endpoint=os.getenv("OPENAI_CD_ENDPOINT"),
        temperature=0.0,
    )


def get_transcript_llm() -> AzureChatOpenAI:
    """Get configured Azure OpenAI instance for transcript analysis."""
    return AzureChatOpenAI(
        azure_deployment=os.getenv("OPENAI_SQ_MODEL"),
        api_version=os.getenv("OPENAI_SQ_API_VERSION"),
        api_key=os.getenv("OPENAI_SQ_API"),
        azure_endpoint=os.getenv("OPENAI_SQ_ENDPOINT"),
        temperature=0.0,
    )


def build_sec_context(sec_chunks: List[Dict[str, Any]]) -> str:
    """Build LLM-ready SEC context with citations metadata."""
    parts = []
    for chunk in sec_chunks:
        part = (
            f"--- EVIDENCE ID: {chunk.get('filing_id', 'N/A')} ---\n"
            f"Company: {chunk.get('company', 'N/A')}\n"
            f"Period: {chunk.get('period', 'N/A')}\n"
            f"Form: {chunk.get('form', 'N/A')}\n"
            f"Section: {chunk.get('heading', 'N/A')}\n"
            f"Sub Sections: {chunk.get('sub_heading', {})}\n"
            f"Content: {chunk.get('parent_text', '').strip()}\n"
        )
        parts.append(part)

    return "\n\n---\n\n".join(parts)


def build_transcript_context(transcript_chunks: List[Dict[str, Any]]) -> str:
    """Build LLM-ready transcript context."""
    parts = []
    for chunk in transcript_chunks:
        part = (
            f"Company: {chunk.get('company', 'N/A')}\n"
            f"Period: {chunk.get('period', 'N/A')}\n"
            f"Speaker: {chunk.get('speaker', 'N/A')}\n"
            f"Title: {chunk.get('title', 'N/A')}\n"
            f"Content: {chunk.get('parent_text', '').strip()}\n"
        )
        parts.append(part)

    return "\n\n---\n\n".join(parts)


def get_simple_prompt() -> ChatPromptTemplate:
    """Get prompt template for simple queries."""
    return ChatPromptTemplate.from_messages([
        (
            "system",
            (
                "You are QuantiGence, a senior financial analyst and SEC reporting expert. "
                "Your goal is to provide a synthesis of SEC evidence. Follow these strict rules:\n\n"
                "1. SOURCE GROUNDING: Answer ONLY using the provided SEC Evidence. If the information "
                "is not present, state: 'Information not found in the provided filings.'\n"
                "2. DEDUPLICATION: If multiple chunks contain identical or nearly identical information "
                "(e.g., repeating risk factors across different years), synthesize them into a single "
                "consolidated point. Do not list the same fact twice.\n"
                "3. FINANCIAL TERMINOLOGY: Use professional financial language (e.g., 'liquidity position', "
                "'capital expenditure', 'market volatility', 'regulatory headwind').\n"
                "4. CITATION FORMAT: Every claim must be followed by a citation in brackets. "
                "Format: [Form, Period, Company, Section > Sub-section].\n"
                "5. HIERARCHY: If sub-sections are provided in the evidence, include them in the citation path. "
                "If not, just use the Heading.\n"
                "6. ANALYTICAL SUMMARY: Do not just list facts. Group related evidence into logical "
                "categories like 'Operational Risks', 'Strategic Shifts', or 'Financial Performance'.\n"
                "7. CONTEXT AWARENESS: Use the recent conversation history for continuity."
            ),
        ),
        (
            "user",
            "RECENT CONVERSATION:\n{chat_history}\n\n"
            "USER QUERY: {query}\n\n"
            "SEC EVIDENCE CHUNKS:\n{context}\n\n"
            "ANALYSIS:",
        ),
    ])


def get_broad_prompt() -> ChatPromptTemplate:
    """Get prompt template for broad/comparison queries."""
    return ChatPromptTemplate.from_messages([
        (
            "system",
            (
                "You are QuantiGence, a senior financial analyst and SEC reporting expert. "
                "Your goal is to provide a synthesis of SEC evidence. Follow these strict rules:\n\n"
                "1. SOURCE GROUNDING: Answer ONLY using the provided SEC Evidence.\n"
                "2. DEDUPLICATION: Synthesize repeating info across years into a single point, but cite all sources.\n"
                "3. FINANCIAL TERMINOLOGY: Use professional terms (e.g., 'revenue tailwinds', 'year-over-year (YoY) variance', 'risk mitigation').\n"
                "4. CITATION FORMAT: Every claim must be followed by [Form, Period, Company, Section > Sub-section].\n"
                "5. HIERARCHY: If sub-sections are absent, use only the Heading in the citation.\n"
                "6. ANALYTICAL SUMMARY: Group evidence into logical thematic categories.\n"
                "7. COMPARATIVE LOGIC: If the query involves multiple companies or periods, explicitly highlight "
                "differences, similarities, and relative performance. Use tables if comparing more than two metrics.\n"
                "8. CONTEXT AWARENESS: Use recent conversation history only for continuity."
            ),
        ),
        (
            "user",
            "RECENT CONVERSATION:\n{chat_history}\n\n"
            "USER QUERY: {query}\n\n"
            "SEC EVIDENCE CHUNKS:\n{context}\n\n"
            "Provide a detailed financial analysis and comparative summary:",
        ),
    ])


def get_change_prompt() -> ChatPromptTemplate:
    """Get prompt template for change detection analysis."""
    return ChatPromptTemplate.from_messages([
        (
            "system",
            (
                "You are QuantiGence, a senior financial auditor. Your specific task is TREND ANALYSIS "
                "and CHANGE DETECTION over multiple periods for the same company. "
                "Follow these rules for temporal auditing:\n\n"
                "1. PERIOD IDENTIFICATION: You must organize your analysis chronologically. "
                "Reference the 'period' key in the metadata to establish the timeline.\n"
                "2. DELTA DETECTION: Explicitly identify what has changed. Categorize findings into: "
                "[NEWLY ADDED], [REMOVED/STALE], or [EVOLVING/UPDATED].\n"
                "3. EVOLUTIONARY NARRATIVE: Describe the 'trend' (e.g., 'Risk factor regarding AI Regulation' "
                "was introduced in Q2 2024 and significantly expanded in Q3 2024 regarding specific EU mandates').\n"
                "4. FINANCIAL INTENSITY: Use terms like 'sequential increase', 'historical variance', "
                "'quarter-over-quarter (QoQ) shift', or 'material pivot'.\n"
                "5. CITATION FORMAT: Use [Form, Period, Company, Section > Sub-section].\n"
                "6. NO HALLUCINATION: If a topic appears in one year but is missing in another, report it as "
                "an omission or removal from the disclosure text.\n"
                "7. CONTEXT AWARENESS: Use conversation history only for continuity."
            ),
        ),
        (
            "user",
            "RECENT CONVERSATION:\n{chat_history}\n\n"
            "USER QUERY: {query}\n\n"
            "SEC EVIDENCE CHUNKS (MULTI-PERIOD):\n{change_context}\n\n"
            "TREND ANALYSIS REPORT:",
        ),
    ])


def get_transcript_prompt() -> ChatPromptTemplate:
    """Get prompt template for transcript analysis."""
    return ChatPromptTemplate.from_messages([
        (
            "system",
            (
                "You are QuantiGence, an expert in Earnings Call Analysis. Your task is to extract, "
                "organize, and summarize executive speeches from transcripts.\n\n"
                "STRICT ARCHITECTURAL RULES:\n"
                "1. CATEGORIZATION: Organize the output first by COMPANY, then chronologically by PERIOD.\n"
                "2. SPEAKER ATTRIBUTION: You must clearly identify who is speaking (e.g., CEO, CFO, Analyst). "
                "Summarize their specific insights, tone, and key takeaways.\n"
                "3. QUERY-DRIVEN MANIPULATION: Analyze the user's intent to determine the focus. If the query asks "
                "for 'strategy,' focus on the CEO's speech. If it asks for 'margins,' focus on the CFO.\n"
                "4. NO CROSS-CONTAMINATION: Do not mix insights from different companies in the same section. "
                "Keep Apple's analysis separate from Microsoft's.\n"
                "5. FINANCIAL CONTEXT: Translate conversational speech into professional financial summaries "
                "(e.g., 'The CEO expressed optimism' becomes 'Management signaled a bullish outlook on pipeline velocity').\n"
                "6. CITATION: Cite every summary block as [Company, Period, Speaker]."
            ),
        ),
        (
            "user",
            "USER INTENT/QUERY: {tquery}\n\n"
            "TRANSCRIPT CHUNKS:\n{tcontext}\n\n"
            "STRUCTURED SPEECH SUMMARY:",
        ),
    ])


def generate_sec_answer(
    query_type: str,
    query: str,
    sec_chunks: List[Dict[str, Any]],
    sec_graph: List[Dict[str, Any]],
    chat_history: str = "",
) -> Dict[str, Any]:
    """Generate SEC filing analysis."""
    context = build_sec_context(sec_chunks)

    if not context.strip():
        return {
            "answer": "No SEC filing information found for your query.",
            "sec_graph_ui": sec_graph,
        }

    try:
        if query_type == "SIMPLE":
            prompt = get_simple_prompt()
            llm = get_sec_llm()
        elif query_type in ["BROAD", "COMPARISON"]:
            prompt = get_broad_prompt()
            llm = get_broad_llm()
        elif query_type == "CHANGE_DETECTION":
            prompt = get_change_prompt()
            llm = get_change_llm()
        else:
            prompt = get_simple_prompt()
            llm = get_sec_llm()

        chain = prompt | llm
        result = chain.invoke({
            "query": query,
            "context": context,
            "change_context": context,
            "chat_history": chat_history,
        })

        logger.info(f"SEC answer generated for {query_type} query")
        return {
            "answer": result.content,
            "sec_graph_ui": sec_graph,
        }

    except Exception as e:
        logger.error(f"SEC answer generation failed: {str(e)}")
        return {
            "answer": "Error generating analysis. Please try again.",
            "sec_graph_ui": sec_graph,
        }


def generate_transcript_commentary(
    transcript_query: str,
    transcript_items: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Generate transcript analysis and commentary."""
    context = build_transcript_context(transcript_items)

    if not context.strip():
        return {
            "transcript_commentary": None,
            "transcript_graph_ui": [],
        }

    try:
        prompt = get_transcript_prompt()
        llm = get_transcript_llm()
        chain = prompt | llm

        result = chain.invoke({
            "tquery": transcript_query,
            "tcontext": context,
        })

        logger.info("Transcript commentary generated")
        return {
            "transcript_commentary": result.content,
            "transcript_graph_ui": [],
        }

    except Exception as e:
        logger.error(f"Transcript commentary generation failed: {str(e)}")
        return {
            "transcript_commentary": None,
            "transcript_graph_ui": [],
        }