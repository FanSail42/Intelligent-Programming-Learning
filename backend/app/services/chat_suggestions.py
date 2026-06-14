from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.learning import KnowledgePoint
from app.services.course_track import course_track_key

TRACK_SUGGESTIONS: dict[str, list[str]] = {
    "java": [
        "面向对象三大特性是什么？",
        "接口和抽象类有什么区别？",
        "HashMap 的底层实现原理是什么？",
    ],
    "python": [
        "Pandas 如何做数据清洗？",
        "NumPy 数组和 Python 列表有什么区别？",
        "如何用 Matplotlib 绘制折线图？",
    ],
    "cpp": [
        "快排的时间复杂度是多少？",
        "二叉树的前序遍历怎么实现？",
        "动态规划的基本思路是什么？",
    ],
}

DEFAULT_SUGGESTIONS = [
    "这门课的核心知识点有哪些？",
    "能给我一个学习路径建议吗？",
    "帮我解释一下课程中的重点概念",
]


def get_chat_suggestions(db: Session, course_id: int) -> list[str]:
    course = (
        db.query(Course)
        .filter(Course.id == course_id, Course.deleted == 0)
        .first()
    )
    if not course:
        return DEFAULT_SUGGESTIONS[:3]

    track = course_track_key(course.name)
    if track and track in TRACK_SUGGESTIONS:
        return TRACK_SUGGESTIONS[track][:3]

    kps = (
        db.query(KnowledgePoint)
        .filter(KnowledgePoint.course_id == course_id, KnowledgePoint.deleted == 0)
        .order_by(KnowledgePoint.sort_order.asc(), KnowledgePoint.id.asc())
        .all()
    )
    named = [kp for kp in kps if kp.name != "代码基础"]
    if len(named) >= 3:
        return [f"请讲解一下「{kp.name}」" for kp in named[:3]]
    if named:
        questions = [f"请讲解一下「{kp.name}」" for kp in named]
        while len(questions) < 3:
            questions.append(DEFAULT_SUGGESTIONS[len(questions)])
        return questions[:3]
    return DEFAULT_SUGGESTIONS[:3]
