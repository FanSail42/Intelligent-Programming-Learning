"""Seed knowledge points for demo course."""
import os
import sys

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.course import Course
from app.models.learning import KnowledgePoint, UserKpMastery
from app.models.user import User, UserRole

KP_NAMES = [
    ("变量与数据类型", 1),
    ("控制流与循环", 2),
    ("函数与模块", 3),
    ("代码基础", 0),
]


def seed() -> None:
    db = SessionLocal()
    try:
        course = db.query(Course).filter(Course.name == "Python Programming Demo").first()
        if not course:
            print("Demo course not found. Run seed_demo.py first.")
            return

        kp_map: dict[str, KnowledgePoint] = {}
        for name, order in KP_NAMES:
            existing = (
                db.query(KnowledgePoint)
                .filter(
                    KnowledgePoint.course_id == course.id,
                    KnowledgePoint.name == name,
                    KnowledgePoint.deleted == 0,
                )
                .first()
            )
            if existing:
                kp_map[name] = existing
                continue
            kp = KnowledgePoint(course_id=course.id, name=name, sort_order=order)
            db.add(kp)
            db.flush()
            kp_map[name] = kp

        students = db.query(User).filter(User.role == UserRole.student, User.deleted == 0).all()
        for student in students:
            for kp in kp_map.values():
                exists = (
                    db.query(UserKpMastery)
                    .filter(
                        UserKpMastery.user_id == student.id,
                        UserKpMastery.kp_id == kp.id,
                        UserKpMastery.deleted == 0,
                    )
                    .first()
                )
                if not exists:
                    db.add(UserKpMastery(user_id=student.id, kp_id=kp.id, score=100))

        db.commit()
        print(f"Knowledge points seeded for course id={course.id}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
