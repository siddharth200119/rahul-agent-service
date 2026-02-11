import os
from RAW.llms import GroqLLM
from src.utils import logger

def get_primary_llm() -> GroqLLM:
    """
    Returns the primary LLM instance (Groq).
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        logger.error("GROQ_API_KEY not found in environment.")
    
    model_name = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
    return GroqLLM(api_key=api_key, logger=logger, model=model_name)
