"""Safety and content filtering services"""
import logging
from typing import Dict, Any
from prompts.auditor_prompts import (
    INPUT_OUTPUT_POLICY,
    INPUT_FILTER_PROMPT,
    OUTPUT_FILTER_PROMPT,
)
from tools.mistral_functions import (
    INPUT_OUTPUT_POLICY_FN,
    INPUT_FILTER_FN,
    OUTPUT_FILTER_FN,
)
from tools.mistral_client import mistral_client
from dotenv import load_dotenv
from core.logger import configure_logging
import os

load_dotenv()
from src.core.logger import configure_logging

logger = configure_logging(logging.INFO)

class SafetyChecker:
    """Content safety and filtering"""
    
    def __init__(self, safety_model: str = os.getenv("MISTRAL_SAFETY_MODEL")):
        self.safety_model = safety_model
    
    def check_harm(self, text: str) -> Dict[str, Any]:
        """Check if text contains harmful content"""
        return mistral_client.call_with_tool(
            model=self.safety_model,
            system_prompt=INPUT_OUTPUT_POLICY,
            user_message=f"query/response:\n{text}",
            tools=[{"type": "function", "function": INPUT_OUTPUT_POLICY_FN}],
            tool_function_name="classify_harm"
        )
    
    def filter_input(self, user_input: str) -> Dict[str, Any]:
        """Filter and classify user input"""
        return mistral_client.call_with_tool(
            model=self.safety_model,
            system_prompt=INPUT_FILTER_PROMPT,
            user_message=f"query/response:\n{user_input}",
            tools=[{"type": "function", "function": INPUT_FILTER_FN}],
            tool_function_name="route_user_input"
        )
    
    def filter_output(self, bot_response: str) -> Dict[str, Any]:
        """Filter and check bot output for financial advice"""
        return mistral_client.call_with_tool(
            model=self.safety_model,
            system_prompt=OUTPUT_FILTER_PROMPT,
            user_message=f"query/response:\n{bot_response}",
            tools=[{"type": "function", "function": OUTPUT_FILTER_FN}],
            tool_function_name="check_financial_advice"
        )

# Global instance
safety_checker = SafetyChecker()