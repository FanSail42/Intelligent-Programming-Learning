"""Seed demo users and a sample course."""
import os
import sys
from datetime import datetime

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

import bcrypt

from app.core.database import SessionLocal
from app.models.course import (
    Course,
    CourseCreateApproval,
    CoursePublishApproval,
    CourseStatus,
    CourseStudent,
    CourseTeacher,
)
from app.models.material import MaterialType
from app.models.user import User, UserRole, UserStatus
from app.models.warehouse import CourseSubject, MaterialWarehouse, WarehouseKind

DEMO_USERS = [
    ("admin", "Admin123!", UserRole.admin),
    ("teacher", "Teacher123!", UserRole.teacher),
    ("student", "Student123!", UserRole.student),
    ("adm", "123123", UserRole.admin),
    ("tea", "123123", UserRole.teacher),
    ("stu", "123123", UserRole.student),
    ("tea1", "123123", UserRole.teacher),
    ("tea2", "123123", UserRole.teacher),
    ("tea3", "123123", UserRole.teacher),
]


def seed() -> None:
    db = SessionLocal()
    try:
        user_map: dict[str, User] = {}
        for username, password, role in DEMO_USERS:
            existing = db.query(User).filter(User.username == username).first()
            if existing:
                user_map[username] = existing
                continue
            user = User(
                username=username,
                password_hash=bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
                role=role,
                status=UserStatus.active,
            )
            db.add(user)
            db.flush()
            user_map[username] = user

        teacher = user_map["teacher"]
        course = (
            db.query(Course).filter(Course.name == "Python Programming Demo").first()
        )
        if not course:
            course = Course(
                name="Python Programming Demo",
                description="Phase 1 demo course for Huibian system.",
                teacher_id=teacher.id,
                status=CourseStatus.published,
                create_approval=CourseCreateApproval.approved,
                publish_approval=CoursePublishApproval.approved,
                published_at=datetime.now(),
            )
            db.add(course)
            db.flush()
            db.add(CourseTeacher(course_id=course.id, user_id=teacher.id))

        student = user_map["student"]
        enrolled = (
            db.query(CourseStudent)
            .filter(
                CourseStudent.course_id == course.id,
                CourseStudent.user_id == student.id,
            )
            .first()
        )
        if not enrolled:
            db.add(CourseStudent(course_id=course.id, user_id=student.id))

        for name, desc, mtype, icon, color, sort_order in [
            ("PDF 文献库", "存放 PDF 格式课程资料", MaterialType.pdf, "📕", "#e74c3c", 1),
            ("TXT 文本库", "存放 TXT 格式课程资料", MaterialType.txt, "📄", "#3498db", 2),
            ("MD 笔记库", "存放 Markdown 格式课程资料", MaterialType.md, "📝", "#2ecc71", 3),
            ("PPTX 演示库", "存放 PPT/PPTX 格式课程资料", MaterialType.pptx, "📊", "#9b59b6", 4),
        ]:
            wh = (
                db.query(MaterialWarehouse)
                .filter(
                    MaterialWarehouse.warehouse_kind == WarehouseKind.file_type,
                    MaterialWarehouse.material_type == mtype,
                    MaterialWarehouse.deleted == 0,
                )
                .first()
            )
            if not wh:
                db.add(
                    MaterialWarehouse(
                        name=name,
                        description=desc,
                        warehouse_kind=WarehouseKind.file_type,
                        material_type=mtype,
                        icon=icon,
                        color=color,
                        sort_order=sort_order,
                    )
                )

        for name, desc, subject, icon, color, sort_order in [
            ("Python 课程仓库", "Python 课程资料，管理员手动分派", CourseSubject.python, "🐍", "#3776ab", 10),
            ("Java 课程仓库", "Java 课程资料，管理员手动分派", CourseSubject.java, "☕", "#f89820", 11),
            ("C/C++ 课程仓库", "C/C++ 课程资料，管理员手动分派", CourseSubject.cpp, "⚙️", "#00599c", 12),
        ]:
            wh = (
                db.query(MaterialWarehouse)
                .filter(
                    MaterialWarehouse.warehouse_kind == WarehouseKind.course,
                    MaterialWarehouse.course_subject == subject,
                    MaterialWarehouse.deleted == 0,
                )
                .first()
            )
            if not wh:
                db.add(
                    MaterialWarehouse(
                        name=name,
                        description=desc,
                        warehouse_kind=WarehouseKind.course,
                        course_subject=subject,
                        material_type=MaterialType.pdf,
                        icon=icon,
                        color=color,
                        sort_order=sort_order,
                    )
                )

        db.commit()
        print(
            "Seed completed: admin/teacher/student + adm/tea/stu (123123) + demo course "
            f"(id={course.id})"
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
