"""
Model loading utilities for production.
Uses pre-downloaded models from Docker image.
"""
import os
from typing import Dict, Tuple
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Use pre-downloaded models (set during Docker build)
CACHE_DIR = os.getenv("TRANSFORMERS_CACHE", "/models")

# Global model cache (loaded once at startup)
_model_cache: Dict[str, Tuple] = {}

# Map friendly names to HuggingFace IDs
MODEL_IDS = {
    "gpt2": "openai-community/gpt2",
    "gpt2-medium": "openai-community/gpt2-medium",
}


def load_model(model_name: str = "gpt2"):
    """
    Load a pre-downloaded model from cache.
    Models are loaded once and cached in memory.
    """
    if model_name in _model_cache:
        return _model_cache[model_name]

    model_id = MODEL_IDS.get(model_name)
    if not model_id:
        raise ValueError(f"Unknown model: {model_name}")

    print(f"Loading {model_name} from cache...")

    # Load from pre-downloaded cache (no network access)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        cache_dir=CACHE_DIR,
        local_files_only=True,  # Critical: no downloads in production
        torch_dtype=torch.float32,
    )
    model.eval()  # Set to evaluation mode

    tokenizer = AutoTokenizer.from_pretrained(
        model_id,
        cache_dir=CACHE_DIR,
        local_files_only=True,
    )

    # Cache for future requests
    _model_cache[model_name] = (model, tokenizer)

    print(f"  Model loaded successfully!")
    return model, tokenizer


def get_available_models() -> list:
    """Return list of available pre-loaded models."""
    return [
        {
            "id": "gpt2",
            "name": "GPT-2 (124M)",
            "description": "Base GPT-2 model with 124M parameters",
            "parameters": "124M",
            "default": True,
        },
        {
            "id": "gpt2-medium",
            "name": "GPT-2 Medium (355M)",
            "description": "Medium-sized GPT-2 model",
            "parameters": "355M",
            "default": False,
        },
    ]


def is_model_loaded(model_name: str) -> bool:
    """Check if a model is loaded in cache."""
    return model_name in _model_cache
