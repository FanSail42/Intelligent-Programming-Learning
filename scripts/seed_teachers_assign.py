"""Create extra teacher accounts and randomly assign courses to all teachers."""
import os
import random
import sys

import bcrypt

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.course import Course, CourseTeacher
from app.models.user import User, UserRole, UserStatus

PASSWORD = "123123"
NEW_TEACHERS = ["tea1", "tea2", "tea3"]


def seed_teachers_and_assign() -> None:
    password_hash = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt()).decode()
    db = SessionLocal()
    try:
        created: list[str] = []
        for username in NEW_TEACHERS:
            existing = db.query(User).filter(User.username == username).first()
            if existing:
                continue
            db.add(
                User(
                    username=username,
                    password_hash=password_hash,
                    role=UserRole.teacher,
                    status=UserStatus.active,
                )
            )
            created.append(username)
        db.flush()

        teachers = (
            db.query(User)
            .filter(User.role == UserRole.teacher, User.status == UserStatus.active, User.deleted == 0)
            .all()
        )
        if not teachers:
            raise RuntimeError("No teacher accounts found")

        courses = db.query(Course).filter(Course.deleted == 0).all()
        assigned = 0
        for course in courses:
            teacher = random.choice(teachers)
            course.teacher_id = teacher.id

            link = (
                db.query(CourseTeacher)
                .filter(CourseTeacher.course_id == course.id, CourseTeacher.deleted == 0)
                .first()
            )
            if link:
                link.user_id = teacher.id
            else:
                db.add(CourseTeacher(course_id=course.id, user_id=teacher.id))
            assigned += 1

        db.commit()
        teacher_names = ", ".join(t.username for t in teachers)
        print(f"Teachers ({len(teachers)}): {teacher_names}")
        if created:
            print(f"Created: {', '.join(created)} (password: {PASSWORD})")
        print(f"Randomly assigned {assigned} courses")
    finally:
        db.close()


if __name__ == "__main__":
    seed_teachers_and_assign()
