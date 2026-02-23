"""
Auditor Agent: Quality & Safety Controller
Validates input/output and evaluates response quality.
"""
import logging
from typing import List


from services.safety import safety_checker
from services.evaluation import evaluator
from src.core.state import QueryResState

from src.core.logger import configure_logging

logger = configure_logging(logging.INFO)


def auditor(state: QueryResState) -> QueryResState:
    """
    ROLE: Quality & Safety Controller
    Performs simple input/output audits and computes faithfulness/relevancy for outputs.
    """
    logger.debug("AUDITOR: running audit; input_state=%s", state.get("input_state"))

    # ---------- INPUT AUDIT ----------
    if state.get("input_state"):
        level_1_check = safety_checker.check_harm(state.get("org_query", ""))
        logger.debug("AUDITOR: input level_1_check=%s", level_1_check)
        if level_1_check.get("category") == "harmful":
            logger.info("AUDITOR: input harmful detected (level 1)")
            return {
                "query_harmful": True,
                "auditor_fail": True,
                "final_response": level_1_check.get("reason"),
                "input_state": False,
            }

        level_2_check = safety_checker.filter_input(state.get("org_query", ""))
        logger.debug("AUDITOR: input level_2_check=%s", level_2_check)
        if level_2_check.get("classification") != "FINANCE_RESEARCH_OK":
            logger.info("AUDITOR: input harmful detected (level 2)")
            return {
                "query_harmful": True,
                "auditor_fail": True,
                "final_response": level_2_check.get("reason"),
                "input_state": False,
            }

        # Input passed
        logger.debug("AUDITOR: input passed")
        return {"auditor_fail": False, "input_state": False}

    # ---------- OUTPUT AUDIT ----------
    level_1_check = safety_checker.check_harm(state.get("llm_response_sec", ""))
    logger.debug("AUDITOR: output level_1_check=%s", level_1_check)
    if level_1_check.get("category") == "harmful":
        logger.info("AUDITOR: output harmful detected (level 1)")
        return {"response_harmful": True, "auditor_fail": True, "analysis_ok": False}

    level_2_check = safety_checker.filter_output(state.get("llm_response_sec", ""))
    logger.debug("AUDITOR: output level_2_check=%s", level_2_check)
    if level_2_check.get("has_financial_advice"):
        logger.info("AUDITOR: output contains financial advice -> blocked")
        return {"response_harmful": True, "auditor_fail": True, "analysis_ok": False}

    # Evaluation: compute faithfulness & relevancy
    query = state.get("modif_query") if state.get("query_modified") else state.get("last_user_message", "")
    parent_chunks: List[str] = []
    for chunk in state.get("sec_context", []):
        parent_chunks.append(chunk.get("parent_text", ""))

    logger.debug("AUDITOR: evaluating faithfulness & relevancy")
    faithfulness, relevancy = evaluator.evaluate(query, state.get("llm_response_sec", ""), parent_chunks)
    logger.debug("AUDITOR: results faithfulness=%.2f relevancy=%.2f", faithfulness, relevancy)

    passed = (faithfulness >= 0.50) and (relevancy >= 0.50)
    logger.info("AUDITOR: passed=%s", passed)

    return {
        "auditor_fail": False,
        "analysis_ok": passed,
        "analysis_retry_count": state.get("analysis_retry_count", 0) + (0 if passed else 1),
        "audit_score": {"faithfulness": faithfulness, "answer_relevancy": relevancy},
    }