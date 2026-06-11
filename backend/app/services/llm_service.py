import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path

import httpx
import structlog
import yaml

from app.core.config import get_settings
from app.services.runtime_ai_config import get_cached_runtime_ai_config
from app.services.vector_store import VectorHit

settings = get_settings()
logger = structlog.get_logger(__name__)

DANGEROUS_PATTERNS = ("eval(", "exec(", "__import__", "os.system")


@dataclass(frozen=True)
class LlmStreamChunk:
    kind: str  # "reasoning" | "content"
    text: str


def load_system_prompt() -> str:
    prompt_path = Path(__file__).resolve().parents[2] / "prompts" / "chat_rag.yaml"
    if prompt_path.exists():
        data = yaml.safe_load(prompt_path.read_text(encoding="utf-8"))
        return data.get("system", "")
    return "你是慧编学伴 AI 助教，请基于课程资料回答学生问题。"


def validate_user_input(content: str) -> None:
    lowered = content.lower()
    for pattern in DANGEROUS_PATTERNS:
        if pattern in lowered:
            raise ValueError("输入包含不允许的内容")


def _chunks_from_stream_payload(chunk: dict) -> list[LlmStreamChunk]:
    """Parse one OpenAI-compatible SSE JSON chunk; skip heartbeat / empty choices."""
    choices = chunk.get("choices")
    if not choices:
        return []
    first = choices[0]
    if not isinstance(first, dict):
        return []
    delta = first.get("delta")
    if not isinstance(delta, dict):
        return []
    out: list[LlmStreamChunk] = []
    reasoning = delta.get("reasoning_content")
    content = delta.get("content")
    if reasoning:
        out.append(LlmStreamChunk("reasoning", reasoning))
    if content:
        out.append(LlmStreamChunk("content", content))
    return out


def _append_code_language_instruction(system: str, code_language: str, fence_tag: str) -> str:
    return (
        f"{system.rstrip()}\n\n"
        f"## 课程编程语言（必须遵守）\n"
        f"当前课程代码示例语言为 **{code_language}**。\n"
        f"- 所有代码示例必须使用 {code_language} 编写\n"
        f"- Markdown 代码块必须标注为 ```{fence_tag}\n"
        f"- 禁止改用 Python / Java / C++ 等其他语言，除非学生明确要求对比多种语言"
    )


def build_rag_prompt(
    context_blocks: list[VectorHit],
    question: str,
    history: list[dict] | None = None,
    *,
    code_language: str = "Python",
    code_fence_tag: str = "python",
) -> list[dict]:
    system = _append_code_language_instruction(
        load_system_prompt(), code_language, code_fence_tag
    )
    if context_blocks:
        context = "\n\n".join(
            f"[资料：{h.material_name or '课程资料'}"
            f"{f'，第{h.page}页' if h.page else ''}，chunk_id={h.chunk_id}]\n{h.text}"
            for h in context_blocks
        )
        user_content = f"课程资料：\n{context}\n\n学生问题：{question}"
    else:
        user_content = (
            f"当前课程暂无相关资料。\n\n学生问题：{question}\n"
            "请礼貌说明资料不足，并给出通用学习建议。"
        )

    messages: list[dict] = [{"role": "system", "content": system}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_content})
    return messages


async def stream_llm(messages: list[dict]) -> AsyncIterator[LlmStreamChunk]:
    cfg = get_cached_runtime_ai_config()
    api_key = cfg.llm_api_key
    if not api_key:
        fallback = (
            "（演示模式：未配置 LLM_API_KEY）\n"
            "根据检索到的资料，建议你结合课件复习相关章节。"
        )
        for ch in fallback:
            yield LlmStreamChunk("content", ch)
        return

    url = f"{cfg.llm_base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": cfg.llm_model,
        "messages": messages,
        "stream": True,
        "enable_thinking": True,
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data = line[6:].strip()
                if not data or data == "[DONE]":
                    if data == "[DONE]":
                        break
                    continue
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    logger.warning("llm_stream_invalid_json", line=data[:120])
                    continue
                for part in _chunks_from_stream_payload(chunk):
                    yield part


async def invoke_llm(messages: list[dict]) -> str:
    """Non-streaming completion; returns assistant text or empty when unconfigured."""
    cfg = get_cached_runtime_ai_config()
    api_key = cfg.llm_api_key
    if not api_key:
        return ""

    url = f"{cfg.llm_base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": cfg.llm_model,
        "messages": messages,
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices") or []
        if not choices:
            return ""
        message = choices[0].get("message") or {}
        return message.get("content") or ""


async def log_llm_invoke(*, user_id: int, scene: str, model: str, tokens: int = 0) -> None:
    from app.services.ai_usage import record_llm_usage

    record_llm_usage(user_id=user_id, tokens=tokens, scene=scene, model=model)
    logger.info(
        "llm_invoke",
        user_id=user_id,
        scene=scene,
        model=model,
        tokens=tokens,
    )
