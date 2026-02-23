"""Mistral API client wrapper"""
import json
import logging
from typing import Dict, Any, List
from mistralai import Mistral
from dotenv import load_dotenv
from core.logger import configure_logging
import os 

load_dotenv()
from src.core.logger import configure_logging

logger = configure_logging(logging.INFO)

class MistralClient:
    """Wrapper for Mistral API calls with tool use"""
    
    def __init__(self, api_key: str = os.getenv("MISTRAL_API")):
        self.client = Mistral(api_key=api_key)
    
    def call_with_tool(
        self,
        model: str,
        system_prompt: str,
        user_message: str,
        tools: List[Dict[str, Any]],
        tool_choice: str,
        temperature: float = 0.0,
        max_tokens: int = 300
    ) -> Dict[str, Any]:
        """
        Call Mistral API with tool use and extract function arguments
        
        Args:
            model: Model name to use
            system_prompt: System prompt text
            user_message: User message text
            tools: List of tool definitions
            tool_function_name: Name of function to force call
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Parsed function arguments as dictionary
        """
        try:
            response = self.client.chat.complete(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                tools=tools,
                tool_choice=tool_choice,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            return response.choices[0].message
            
        except Exception as e:
            logger.error(f"Error calling Mistral: {str(e)}")
            return {}

# Global client instance
mistral_client = MistralClient()