"""OpenAI-compatible embeddings API (vectors persisted as JSON in MySQL)."""

import os

from openai import OpenAI

from app.core.config import settings


def _embedding_client() -> OpenAI:
    api_key = (
        settings.EMBEDDING_API_KEY
        or settings.DEEPSEEK_API_KEY
        or settings.QWEN_API_KEY
    )
    if not api_key:
        raise RuntimeError(
            "No embedding API key: set EMBEDDING_API_KEY or LLM provider keys (DEEPSEEK_API_KEY / QWEN_API_KEY)."
        )
    base_url = settings.EMBEDDING_BASE_URL
    if not base_url:
        provider = settings.LLM_PROVIDER.lower()
        base_url = (
            settings.QWEN_BASE_URL if provider == "qwen" else settings.DEEPSEEK_BASE_URL
        )
    return OpenAI(api_key=api_key, base_url=base_url, timeout=settings.EMBEDDING_TIMEOUT)


def create_embedding(text: str) -> list[float]:
    """
    Embed a single text chunk. Returns a vector of length settings.EMBEDDING_DIM
    (truncated if the model returns a larger dimension).
    """
    raw = (text or "").strip()
    if not raw:
        raise ValueError("Embedding input text is empty")

    max_chars = int(os.getenv("EMBEDDING_MAX_CHARS", "24000"))
    if len(raw) > max_chars:
        raw = raw[:max_chars]

    client = _embedding_client()
    response = client.embeddings.create(model=settings.EMBEDDING_MODEL, input=raw)
    vec = list(response.data[0].embedding)
    dim = settings.EMBEDDING_DIM
    if len(vec) > dim:
        vec = vec[:dim]
    elif len(vec) < dim:
        raise RuntimeError(
            f"Embedding length {len(vec)} < EMBEDDING_DIM {dim}; change EMBEDDING_DIM or model."
        )
    return vec
