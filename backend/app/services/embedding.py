import hashlib
import math

import httpx

from app.core.config import get_settings

settings = get_settings()
LOCAL_EMBED_DIM = 384


def _local_embed(text: str) -> list[float]:
    """Deterministic local embedding when API key is not configured."""
    vec = [0.0] * LOCAL_EMBED_DIM
    for i, ch in enumerate(text):
        vec[i % LOCAL_EMBED_DIM] += ord(ch) / 255.0
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    for i, b in enumerate(digest):
        vec[i % LOCAL_EMBED_DIM] += b / 255.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    api_key = settings.embedding_api_key or settings.llm_api_key
    if not api_key:
        return [_local_embed(t) for t in texts]

    url = f"{settings.embedding_base_url.rstrip('/')}/embeddings"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"model": settings.embedding_model, "input": texts}
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()["data"]
        return [item["embedding"] for item in sorted(data, key=lambda x: x["index"])]
