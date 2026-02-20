"""
Auditor Agent: Quality & Safety Controller
Validates input/output and evaluates response quality.
"""
import logging
from typing import Any, Dict

from .base_agent import BaseAgent
from services.safety import safety_checker
from services.evaluation import evaluator
from src.core.state import QueryResState

from src.core.logger import configure_logging

logger = configure_logging(logging.INFO)


class AuditorAgent(BaseAgent):
    """
    Auditor Agent: Responsible for input/output validation and quality assessment.
    - Input: Checks for harmful content, routing classification
    - Output: Checks for financial advice, evaluates faithfulness & relevancy
    """

    def __init__(self):
        super().__init__("Auditor")

    def execute(self, state: QueryResState) -> Dict[str, Any]:
        """Execute auditor logic based on current state."""
        # Input audit phase
        if state.get("input_state", True):
            return self._audit_input(state)
        
        # Output audit phase
        return self._audit_output(state)

    def _audit_input(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Audit user input for safety and validity."""
        self._log_execution("INPUT_AUDIT", f"Checking: {state['org_query'][:50]}...")

        # Level 1: Harm classification
        harm_check = safety_checker.check_harm(state["org_query"])
        if harm_check["category"] == "harmful":
            logger.warning(f"Harmful input detected: {harm_check['reason']}")
            return {
                "query_harmful": True,
                "auditor_fail": True,
                "final_response": harm_check["reason"],
                "input_state": False,
            }

        # Level 2: Routing classification
        route_check = safety_checker.filter_input(state["org_query"])
        if route_check["classification"] != "FINANCE_RESEARCH_OK":
            logger.info(f"Query routed: {route_check['classification']}")
            return {
                "query_harmful": True,
                "auditor_fail": True,
                "final_response": route_check["reason"],
                "input_state": False,
            }

        logger.info("Input audit passed")
        return {
            "auditor_fail": False,
            "input_state": False,
        }

    def _audit_output(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Audit LLM output for safety and quality."""
        self._log_execution(
            "OUTPUT_AUDIT", f"Evaluating response: {state['llm_response_sec'][:50]}..."
        )

        # Level 1: Harm classification
        harm_check = safety_checker.check_harm(state["llm_response_sec"])
        if harm_check["category"] == "harmful":
            logger.warning("Harmful output detected")
            return {
                "response_harmful": True,
                "auditor_fail": True,
                "analysis_ok": False,
            }

        # Level 2: Financial advice check
        advice_check = safety_checker.filter_output(state["llm_response_sec"])
        if advice_check["has_financial_advice"]:
            logger.warning("Financial advice detected in output")
            return {
                "response_harmful": True,
                "auditor_fail": True,
                "analysis_ok": False,
            }

        # Quality evaluation
        query = state.get("modif_query") or state.get("last_user_message", "")
        parent_chunks = [chunk.get("parent_text", "") for chunk in state.get("sec_context", [])]

        if not parent_chunks:
            logger.warning("No context chunks for evaluation")
            return {
                "auditor_fail": False,
                "analysis_ok": False,
                "analysis_retry_count": state.get("analysis_retry_count", 0) + 1,
            }

        try:
            faithfulness, relevancy = evaluator.evaluate(
                query,
                state["llm_response_sec"],
                parent_chunks,
            )

            passed = faithfulness >= 0.60 and relevancy >= 0.60
            retry_count = state.get("analysis_retry_count", 0)
            if not passed:
                retry_count += 1

            logger.info(
                f"Evaluation scores - Faithfulness: {faithfulness:.2f}, Relevancy: {relevancy:.2f}"
            )

            return {
                "auditor_fail": False,
                "analysis_ok": passed,
                "analysis_retry_count": retry_count,
                "audit_score": {
                    "faithfulness": faithfulness,
                    "answer_relevancy": relevancy,
                },
            }
        except Exception as e:
            logger.error(f"Evaluation failed: {str(e)}")
            return {
                "auditor_fail": False,
                "analysis_ok": False,
                "analysis_retry_count": state.get("analysis_retry_count", 0) + 1,
            }