"""Curated Alibaba Cloud Bailian (百炼) models for admin selection."""

from __future__ import annotations

BAILIAN_CONSOLE_URL = (
    "https://bailian.console.aliyun.com/cn-beijing/?tab=model#/model-market/all"
)
BAILIAN_DOCS_URL = "https://help.aliyun.com/zh/model-studio/getting-started/models"
BAILIAN_API_KEY_URL = "https://help.aliyun.com/zh/model-studio/get-api-key"

DEFAULT_LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_EMBEDDING_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

CHAT_MODELS: list[dict] = [
    {
        "id": "qwen3.6-flash",
        "name": "通义千问 3.6 Flash",
        "provider": "bailian",
        "category": "chat",
        "tier": "fast",
        "context_k": 128,
        "description": "默认推荐：响应快、成本低，适合 AI 对话与代码讲解。",
        "recommended": True,
    },
    {
        "id": "qwen-max",
        "name": "通义千问 Max",
        "provider": "bailian",
        "category": "chat",
        "tier": "premium",
        "context_k": 128,
        "description": "复杂推理与长文理解，适合高难度问答。",
    },
    {
        "id": "qwen-plus",
        "name": "通义千问 Plus",
        "provider": "bailian",
        "category": "chat",
        "tier": "balanced",
        "context_k": 128,
        "description": "性能与成本均衡，通用对话场景。",
    },
    {
        "id": "qwen-turbo",
        "name": "通义千问 Turbo",
        "provider": "bailian",
        "category": "chat",
        "tier": "fast",
        "context_k": 128,
        "description": "轻量高速，适合高并发辅导。",
    },
    {
        "id": "qwen-long",
        "name": "通义千问 Long",
        "provider": "bailian",
        "category": "chat",
        "tier": "long_context",
        "context_k": 1000,
        "description": "超长上下文，适合整章资料问答。",
    },
    {
        "id": "qwen2.5-coder-32b-instruct",
        "name": "Qwen2.5 Coder 32B",
        "provider": "bailian",
        "category": "code",
        "tier": "code",
        "context_k": 128,
        "description": "代码生成与讲解优化，适合 M05 代码分析。",
    },
    {
        "id": "deepseek-v3",
        "name": "DeepSeek V3",
        "provider": "bailian",
        "category": "chat",
        "tier": "premium",
        "context_k": 64,
        "description": "百炼模型广场接入的 DeepSeek 系列。",
    },
    {
        "id": "deepseek-r1",
        "name": "DeepSeek R1",
        "provider": "bailian",
        "category": "reasoning",
        "tier": "reasoning",
        "context_k": 64,
        "description": "深度推理模型，响应较慢但逻辑更强。",
    },
]

EMBEDDING_MODELS: list[dict] = [
    {
        "id": "text-embedding-v4",
        "name": "Text Embedding V4",
        "provider": "bailian",
        "category": "embedding",
        "dimensions": 1024,
        "description": "默认向量模型，与 Chroma 维度 1024 对齐。",
        "recommended": True,
    },
    {
        "id": "text-embedding-v3",
        "name": "Text Embedding V3",
        "provider": "bailian",
        "category": "embedding",
        "dimensions": 1024,
        "description": "上一代 embedding，兼容 OpenAI 接口。",
    },
]

CHAT_MODEL_IDS = {m["id"] for m in CHAT_MODELS}
EMBEDDING_MODEL_IDS = {m["id"] for m in EMBEDDING_MODELS}


def list_models_payload(db=None) -> dict:
    from app.services.custom_ai_models import load_custom_chat_models

    custom_models: list[dict] = []
    if db is not None:
        custom_models = load_custom_chat_models(db)

    builtin_ids = {m["id"] for m in CHAT_MODELS}
    merged_chat = list(CHAT_MODELS) + [m for m in custom_models if m["id"] not in builtin_ids]

    return {
        "provider": "阿里云百炼",
        "console_url": BAILIAN_CONSOLE_URL,
        "docs_url": BAILIAN_DOCS_URL,
        "api_key_url": BAILIAN_API_KEY_URL,
        "default_llm_base_url": DEFAULT_LLM_BASE_URL,
        "default_embedding_base_url": DEFAULT_EMBEDDING_BASE_URL,
        "chat_models": merged_chat,
        "embedding_models": EMBEDDING_MODELS,
        "custom_chat_models": custom_models,
    }


def list_models_payload_static() -> dict:
    """Backward-compatible helper when DB session is unavailable."""
    return list_models_payload(None)
