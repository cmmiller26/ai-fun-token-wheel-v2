#!/usr/bin/env python3
"""
Pre-download HuggingFace models for Docker image.
This script runs during Docker build to cache models.
"""
import os
from transformers import AutoModelForCausalLM, AutoTokenizer

# Model configurations
MODELS = {
    "gpt2": "openai-community/gpt2",
    "gpt2-medium": "openai-community/gpt2-medium",
}

# Cache directory (will be copied to Docker image)
CACHE_DIR = os.getenv("TRANSFORMERS_CACHE", "/models")


def download_model(model_id: str, model_name: str):
    """Download and cache a model."""
    print(f"Downloading {model_name} ({model_id})...")

    # Download model
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        cache_dir=CACHE_DIR,
        local_files_only=False,  # Allow downloads during build
    )
    print(f"  Model downloaded: {model.config.model_type}")

    # Download tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_id,
        cache_dir=CACHE_DIR,
        local_files_only=False,
    )
    print(f"  Tokenizer downloaded: {len(tokenizer)} tokens\n")

    # Clean up memory
    del model
    del tokenizer


if __name__ == "__main__":
    print("=" * 60)
    print("Pre-downloading HuggingFace models...")
    print("=" * 60)

    for name, model_id in MODELS.items():
        download_model(model_id, name)

    print("=" * 60)
    print("All models downloaded successfully!")
    print(f"Cache directory: {CACHE_DIR}")
    print("=" * 60)
