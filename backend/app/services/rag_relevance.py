import re

from app.core.config import get_settings
from app.services.vector_store import VectorHit

settings = get_settings()

_STOPWORDS = frozenset(
    {
        "什么",
        "怎么",
        "如何",
        "为什么",
        "哪些",
        "请问",
        "一下",
        "解释",
        "区别",
        "实现",
        "原理",
        "the",
        "and",
        "for",
        "how",
        "what",
        "why",
    }
)


def _extract_keywords(text: str) -> set[str]:
    tokens: set[str] = set()
    for word in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{1,}", text.lower()):
        if len(word) >= 2:
            tokens.add(word)
    for chunk in re.findall(r"[\u4e00-\u9fff]{2,}", text):
        if chunk in _STOPWORDS:
            continue
        tokens.add(chunk)
        if len(chunk) >= 4:
            for i in range(len(chunk) - 1):
                tokens.add(chunk[i : i + 2])
    return tokens


def keyword_overlap(query: str, hit: VectorHit) -> float:
    query_keys = _extract_keywords(query)
    if not query_keys:
        return 0.0
    corpus = f"{hit.text or ''} {hit.material_name or ''}"
    hit_keys = _extract_keywords(corpus)
    if not hit_keys:
        return 0.0
    return len(query_keys & hit_keys) / len(query_keys)


def filter_relevant_hits(query: str, hits: list[VectorHit]) -> list[VectorHit]:
    if not hits:
        return []

    score_min = settings.rag_relevance_score_min
    score_high = settings.rag_relevance_score_high
    overlap_min = settings.rag_keyword_overlap_min

    relevant: list[VectorHit] = []
    for hit in hits:
        if hit.score >= score_high:
            relevant.append(hit)
            continue
        if hit.score >= score_min and keyword_overlap(query, hit) >= overlap_min:
            relevant.append(hit)
    return relevant
