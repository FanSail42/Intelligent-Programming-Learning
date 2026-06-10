import re

from sqlalchemy.orm import Session

from app.models.course import CourseStudent
from app.models.learning import KnowledgePoint, WrongQuestionBook
from app.models.material import CourseMaterial, MaterialStatus
from app.models.user import User
from app.services.course_access import ensure_student_enrolled
from app.services.mastery import get_weak_kps_for_user


def _priority_for_score(score: int) -> str:
    if score < 60:
        return "high"
    if score < 80:
        return "medium"
    return "low"


def _kp_keywords(name: str) -> list[str]:
    tokens = re.split(r"[\s与及、,，/]+", name.strip())
    keywords = [t for t in tokens if len(t) >= 2]
    if not keywords:
        keywords = [name]
    return keywords


def _material_match_score(kp_name: str, material_name: str) -> int:
    score = 0
    lowered_material = material_name.lower()
    for token in _kp_keywords(kp_name):
        if token in material_name or token.lower() in lowered_material:
            score += 10
    if kp_name in material_name:
        score += 15
    return score


def _pick_material_for_kp(
    materials: list[CourseMaterial],
    kp_name: str,
    used_ids: set[int],
) -> CourseMaterial | None:
    candidates = [m for m in materials if m.id not in used_ids]
    if not candidates:
        candidates = materials
    if not candidates:
        return None

    ranked = sorted(
        candidates,
        key=lambda m: (_material_match_score(kp_name, m.original_name), m.id),
        reverse=True,
    )
    return ranked[0]


def _wrong_count_for_kp(db: Session, user_id: int, kp_id: int) -> int:
    return (
        db.query(WrongQuestionBook)
        .filter(
            WrongQuestionBook.user_id == user_id,
            WrongQuestionBook.kp_id == kp_id,
            WrongQuestionBook.mastered == False,
            WrongQuestionBook.deleted == 0,
        )
        .count()
    )


def _fallback_weak_kps(
    db: Session,
    course_id: int,
    limit: int,
) -> list[tuple[int, str, int, int]]:
    kp_rows = (
        db.query(KnowledgePoint)
        .filter(KnowledgePoint.course_id == course_id, KnowledgePoint.deleted == 0)
        .order_by(KnowledgePoint.sort_order.asc())
        .limit(limit)
        .all()
    )
    return [(kp.id, kp.name, 100, kp.course_id) for kp in kp_rows]


def build_recommendations(
    db: Session,
    user: User,
    course_id: int,
    limit: int = 3,
) -> list[dict]:
    ensure_student_enrolled(db, user, course_id)

    weak = get_weak_kps_for_user(db, user.id, limit=limit, course_id=course_id)
    if not weak:
        weak = _fallback_weak_kps(db, course_id, limit)

    ready_materials = (
        db.query(CourseMaterial)
        .filter(
            CourseMaterial.course_id == course_id,
            CourseMaterial.status == MaterialStatus.ready,
            CourseMaterial.deleted == 0,
        )
        .order_by(CourseMaterial.id.desc())
        .all()
    )

    used_material_ids: set[int] = set()
    results: list[dict] = []

    for kp_id, kp_name, score, _course_id in weak:
        wrong_count = _wrong_count_for_kp(db, user.id, kp_id)
        priority = _priority_for_score(score)
        material = _pick_material_for_kp(ready_materials, kp_name, used_material_ids)

        if wrong_count > 0 and score < 80:
            results.append(
                {
                    "kp_id": kp_id,
                    "kp_name": kp_name,
                    "score": score,
                    "wrong_count": wrong_count,
                    "action_type": "review_wrong_book",
                    "priority": priority,
                    "material_id": None,
                    "material_name": None,
                    "reason": (
                        f"「{kp_name}」掌握度 {score}，仍有 {wrong_count} 道未掌握错题，建议优先复习错题本"
                    ),
                }
            )
            continue

        if material:
            used_material_ids.add(material.id)
            match_hint = (
                "资料名称与知识点相关"
                if _material_match_score(kp_name, material.original_name) > 0
                else "课程最新可用资料"
            )
            results.append(
                {
                    "kp_id": kp_id,
                    "kp_name": kp_name,
                    "score": score,
                    "wrong_count": wrong_count,
                    "action_type": "review_material",
                    "priority": priority,
                    "material_id": material.id,
                    "material_name": material.original_name,
                    "reason": f"「{kp_name}」掌握度 {score}，{match_hint}：{material.original_name}",
                }
            )
            continue

        results.append(
            {
                "kp_id": kp_id,
                "kp_name": kp_name,
                "score": score,
                "wrong_count": wrong_count,
                "action_type": "practice_code",
                "priority": priority,
                "material_id": None,
                "material_name": None,
                "reason": f"「{kp_name}」掌握度 {score}，建议通过代码讲解针对性练习",
            }
        )

    return results


def list_enrolled_course_ids(db: Session, user_id: int) -> list[int]:
    rows = (
        db.query(CourseStudent.course_id)
        .filter(CourseStudent.user_id == user_id, CourseStudent.deleted == 0)
        .all()
    )
    return [row.course_id for row in rows]
