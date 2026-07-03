"""
Shared LLM client. Supports NVIDIA NIM, OpenRouter, and Hugging Face
(all OpenAI-compatible endpoints) - controlled by LLM_PROVIDER in .env.
Hugging Face is the default since real paid credits mean dedicated,
non-rate-limited inference - much more reliable than free tiers.
Switch providers any time via .env - no code changes needed.
"""
from langchain_openai import ChatOpenAI
from app.config import (
    NVIDIA_API_KEY, NVIDIA_MODEL, NVIDIA_BASE_URL,
    OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_BASE_URL,
    HF_API_KEY, HF_MODEL, HF_BASE_URL,
    LLM_PROVIDER,
)


def get_llm(temperature: float = 0.3):
    if LLM_PROVIDER == "nvidia":
        return ChatOpenAI(
            model=NVIDIA_MODEL, api_key=NVIDIA_API_KEY, base_url=NVIDIA_BASE_URL,
            temperature=temperature, timeout=60, max_retries=0,
        )
    if LLM_PROVIDER == "huggingface":
        return ChatOpenAI(
            model=HF_MODEL, api_key=HF_API_KEY, base_url=HF_BASE_URL,
            temperature=temperature, timeout=60, max_retries=0,
        )
    return ChatOpenAI(
        model=OPENROUTER_MODEL, api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL,
        temperature=temperature, timeout=60, max_retries=0,
    )
