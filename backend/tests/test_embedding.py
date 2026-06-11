from unittest.mock import AsyncMock, patch

import pytest

from app.services.embedding import (
    DASHSCOPE_MAX_BATCH_SIZE,
    embed_texts,
    prepare_embed_text,
)


def test_prepare_embed_text_strips_control_chars():
    raw = "hello\x00world\r\n\t!"
    assert "\x00" not in prepare_embed_text(raw)
    assert prepare_embed_text(raw).startswith("hello world")


@pytest.mark.asyncio
async def test_embed_texts_batches_remote_requests():
    from app.services.runtime_ai_config import RuntimeAiConfig

    texts = [f"chunk-{i}" for i in range(25)]
    call_sizes: list[int] = []

    async def fake_batch(batch, *, api_key, client):
        call_sizes.append(len(batch))
        return [[float(i), float(len(batch))] for i in range(len(batch))]

    fake_cfg = RuntimeAiConfig(
        llm_model="qwen3.6-flash",
        llm_base_url="https://example.com/v1",
        llm_api_key="",
        embedding_model="text-embedding-v4",
        embedding_base_url="https://example.com/v1",
        embedding_api_key="test-key",
        llm_daily_limit=100,
        llm_api_key_configured=False,
        embedding_api_key_configured=True,
        source="env",
    )

    with patch("app.services.embedding._embed_remote_batch", new=AsyncMock(side_effect=fake_batch)):
        with patch(
            "app.services.embedding.get_cached_runtime_ai_config",
            return_value=fake_cfg,
        ):
            vectors = await embed_texts(texts)

    assert len(vectors) == 25
    assert call_sizes == [10, 10, 5]
    assert all(len(v) == 2 for v in vectors)


@pytest.mark.asyncio
async def test_embed_texts_empty_input():
    assert await embed_texts([]) == []


def test_dashscope_batch_limit():
    assert DASHSCOPE_MAX_BATCH_SIZE == 10
