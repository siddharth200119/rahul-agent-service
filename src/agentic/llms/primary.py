import os
from .vllm import VLLM
from src.utils import logger

def get_primary_llm() -> VLLM:
    """
    Returns the primary LLM instance (VLLM).
    """
    vllm_host = os.environ.get("VLLM_HOST", "http://127.0.0.1:11434")
    model_name = os.environ.get("VLLM_MODEL", "Qwen/Qwen2.5-32B-Instruct-AWQ")
    
    logger.info(f"Initializing VLLM with model: {model_name} at {vllm_host}")
    return VLLM(model=model_name, base_url=vllm_host, logger=logger)
