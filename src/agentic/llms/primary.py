import os
from RAW.llms import GeminiLLM
from src.utils import logger

def get_primary_llm() -> GeminiLLM:
    """
    Returns the primary LLM instance (Groq).
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not found in environment.")
    
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    return GeminiLLM(api_key=api_key, logger=logger, model=model_name)
