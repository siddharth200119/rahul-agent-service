import os
from .vllm import VLLM
from src.utils import logger

def get_vision_llm():
    """
    Returns the vision LLM instance (using VLLM class connected to Ollama/Host).
    """
    # Checking both names to be safe
    vision_llm_host = os.environ.get("VISION_LLM_HOST") or os.environ.get("VISION_VLLM_HOST", "http://127.0.0.1:11434")
    model_name = os.environ.get("VISION_LLM_MODEL", "Qwen/Qwen2.5-VL-7B-Instruct")
    
    logger.info(f"Initializing Vision LLM with model: {model_name} at {vision_llm_host}")
    return VLLM(model=model_name, base_url=vision_llm_host, logger=logger)
