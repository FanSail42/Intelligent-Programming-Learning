from app.services.rag_relevance import filter_relevant_hits, keyword_overlap
from app.services.vector_store import VectorHit


def _hit(text: str, material: str, score: float) -> VectorHit:
    return VectorHit(
        chunk_id=1,
        course_id=1,
        text=text,
        page=1,
        score=score,
        material_id=1,
        material_name=material,
    )


def test_keyword_overlap_oop_question_vs_cpp_material():
    hit = _hit("双指针与滑动窗口模板", "05_双指针与滑动窗口", 0.58)
    overlap = keyword_overlap("面向对象三大特性是什么？", hit)
    assert overlap < 0.12


def test_filter_rejects_weak_irrelevant_hits():
    hits = [
        _hit("双指针与滑动窗口", "05_双指针与滑动窗口", 0.58),
        _hit("动态规划状态转移", "09_动态规划", 0.55),
    ]
    assert filter_relevant_hits("面向对象三大特性是什么？", hits) == []


def test_filter_keeps_strong_match():
    hit = _hit("封装继承多态是面向对象三大特性", "03_面向对象基础", 0.75)
    result = filter_relevant_hits("面向对象三大特性是什么？", [hit])
    assert len(result) == 1


def test_filter_keeps_moderate_score_with_overlap():
    hit = _hit("快排平均时间复杂度 O(n log n)", "04_排序算法", 0.6)
    result = filter_relevant_hits("快排的时间复杂度是多少？", [hit])
    assert len(result) == 1
