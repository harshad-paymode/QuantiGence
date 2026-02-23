"""Evaluation using DeepEval"""
import logging
from typing import Tuple
from langchain_openai import AzureChatOpenAI
from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric
from deepeval.models.base_model import DeepEvalBaseLLM
from dotenv import load_dotenv
from core.logger import configure_logging
import os

load_dotenv()
from src.core.logger import configure_logging

logger = configure_logging(logging.INFO)

class AzureOpenAIEvaluator(DeepEvalBaseLLM):
    """Azure OpenAI wrapper for DeepEval"""
    
    def __init__(self, model):
        self.model = model
    
    def load_model(self):
        return self.model
    
    def generate(self, prompt: str) -> str:
        return self.load_model().invoke(prompt).content
    
    async def a_generate(self, prompt: str) -> str:
        return (await self.load_model().ainvoke(prompt)).content
    
    def get_model_name(self): 
        return "gpt-4-mini"

class Evaluator:
    """RAG output evaluation"""
    
    def __init__(self):
        self.model = AzureChatOpenAI(
            openai_api_version=os.getenv("OPENAI_EVAL_API_VERSION"),
            azure_deployment=os.getenv("OPENAI_EVAL_MODEL_NAME"),
            azure_endpoint=os.getenv("OPENAI_EVAL_END_POINT"),
            openai_api_key=os.getenv("OPENAI_EVAL_API_KEY"),
        )
        self.evaluator = AzureOpenAIEvaluator(self.model)
    
    def evaluate(
        self,
        query: str,
        output: str,
        context: list
    ) -> Tuple[float, float]:
        """Evaluate faithfulness and relevancy"""
        try:
            test_case = LLMTestCase(
                input=query,
                actual_output=output,
                retrieval_context= context
            )
            
            metrics = [
                FaithfulnessMetric(threshold=0.5, model=self.evaluator),
                AnswerRelevancyMetric(threshold=0.5, model=self.evaluator),
            ]
            
            results = evaluate(test_cases=[test_case], metrics=metrics)
            scores = {}
            
            for _, test_results in results:
                if test_results:
                    for t in test_results:
                        for m in t.metrics_data:
                            scores[m.name] = m.score
            
            return (
                scores.get("Faithfulness", 0.0),
                scores.get("Answer Relevancy", 0.0)
            )
        except Exception as e:
            logger.error(f"Evaluation error: {str(e)}")
            return (0.0, 0.0)

evaluator = Evaluator()
