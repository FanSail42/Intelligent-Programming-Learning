import asyncio
import hashlib
import math
import re

import httpx

from app.core.config import get_settings

settings = get_settings()
LOCAL_EMBED_DIM = 384
DASHSCOPE_MAX_BATCH_SIZE = 10
# text-embedding-v4: 8192 tokens; use a conservative char cap.
MAX_EMBED_CHARS = 12_000


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


def prepare_embed_text(text: str) -> str:
    """Normalize text before sending to embedding API."""
    cleaned = text.replace("\x00", " ")
    cleaned = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f]", " ", cleaned)
    cleaned = cleaned.strip()
    if len(cleaned) > MAX_EMBED_CHARS:
        cleaned = cleaned[:MAX_EMBED_CHARS]
    return cleaned


async def _embed_remote_batch(
    texts: list[str],
    *,
    api_key: str,
    client: httpx.AsyncClient,
) -> list[list[float]]:
    url = f"{settings.embedding_base_url.rstrip('/')}/embeddings"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload: dict = {
        "model": settings.embedding_model,
        "input": texts,
        "encoding_format": "float",
    }
    if settings.embedding_model.startswith("text-embedding-v"):
        payload["dimensions"] = settings.embedding_dimensions

    resp = await client.post(url, json=payload, headers=headers)
    if resp.status_code >= 400:
        detail = resp.text[:500]
        raise RuntimeError(
            f"Embedding API 错误 ({resp.status_code})：{detail}。"
            f"请检查 EMBEDDING_API_KEY 与模型配置。"
        )
    data = resp.json()["data"]
    return [item["embedding"] for item in sorted(data, key=lambda x: x["index"])]


def _build_remote_batches(
    prepared: list[str],
) -> tuple[list[list[float] | None], list[tuple[list[int], list[str]]]]:
    results: list[list[float] | None] = [None] * len(prepared)
    remote_batches: list[tuple[list[int], list[str]]] = []
    batch_indices: list[int] = []
    batch_texts: list[str] = []

    for idx, text in enumerate(prepared):
        if not text:
            results[idx] = _local_embed(" ")
            continue
        batch_indices.append(idx)
        batch_texts.append(text)
        if len(batch_texts) >= DASHSCOPE_MAX_BATCH_SIZE:
            remote_batches.append((batch_indices, batch_texts))
            batch_indices = []
            batch_texts = []

    if batch_texts:
        remote_batches.append((batch_indices, batch_texts))

    return results, remote_batches


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    prepared = [prepare_embed_text(t) for t in texts]
    api_key = settings.embedding_api_key or settings.llm_api_key
    if not api_key:
        return [_local_embed(t or " ") for t in prepared]

    results, remote_batches = _build_remote_batches(prepared)
    if not remote_batches:
        return [r if r is not None else _local_embed(" ") for r in results]

    concurrency = max(1, settings.embedding_concurrent_batches)
    semaphore = asyncio.Semaphore(concurrency)

    async with httpx.AsyncClient(timeout=60.0) as client:

        async def run_batch(
            indices: list[int], batch_texts: list[str]
        ) -> list[tuple[int, list[float]]]:
            async with semaphore:
                vectors = await _embed_remote_batch(
                    batch_texts, api_key=api_key, client=client
                )
                return list(zip(indices, vectors))

        batch_results = await asyncio.gather(
            *(run_batch(indices, batch_texts) for indices, batch_texts in remote_batches)
        )

    for pairs in batch_results:
        for idx, vec in pairs:
            results[idx] = vec

    return [r if r is not None else _local_embed(" ") for r in results]
