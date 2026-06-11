"""
Dashboard demo seed: 3 representative courses, 18 materials, 20–50 wrong-book rows.

Used by scripts/seed_dashboard_demo.py and backend/tests/test_dashboard_integration.py
"""

from __future__ import annotations

import json
import random
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.code import AnalysisResult, AnalysisStatus, CodeLanguage, CodeSubmission
from app.models.course import (
    Course,
    CourseCreateApproval,
    CoursePublishApproval,
    CourseStatus,
    CourseStudent,
    CourseTeacher,
)
from app.models.learning import (
    KnowledgePoint,
    LearningEvent,
    LearningEventType,
    UserKpMastery,
    WrongQuestionBook,
    WrongQuestionSourceType,
)
from app.models.material import CourseMaterial, MaterialStatus, MaterialType
from app.models.user import User, UserRole
from app.models.warehouse import MaterialWarehouse, WarehouseKind
from app.services.mastery import refresh_user_mastery

ROOT = Path(__file__).resolve().parents[1]
MATERIAL_SRC = ROOT / "root_data" / "课程资料" / "_联调演示" / "dashboard_demo"
MANIFEST_PATH = ROOT / "root_data" / "dashboard_demo" / "manifest.json"

TRACK_COURSES: list[dict[str, Any]] = [
    {
        "key": "cpp",
        "name": "C++ 数据结构与算法",
        "description": "竞赛导向的 C++ 数据结构与算法系统课程（仪表盘联调演示）。",
        "language": CodeLanguage.cpp,
        "kps": [
            ("数组与链表", 1),
            ("栈与队列", 2),
            ("树与图", 3),
            ("排序与查找", 4),
            ("动态规划", 5),
            ("代码基础", 0),
        ],
        "wrong_code": 15,
        "wrong_chat": 5,
    },
    {
        "key": "python",
        "name": "Python 数据分析",
        "description": "Pandas/NumPy 数据分析入门到实战（仪表盘联调演示）。",
        "language": CodeLanguage.python,
        "kps": [
            ("NumPy 基础", 1),
            ("Pandas 清洗", 2),
            ("数据可视化", 3),
            ("统计分析", 4),
            ("实战案例", 5),
            ("代码基础", 0),
        ],
        "wrong_code": 12,
        "wrong_chat": 4,
    },
    {
        "key": "java",
        "name": "Java 面向对象编程",
        "description": "封装、继承、多态与设计模式（仪表盘联调演示）。",
        "language": CodeLanguage.java,
        "kps": [
            ("类与对象", 1),
            ("继承与多态", 2),
            ("接口与抽象", 3),
            ("集合框架", 4),
            ("设计模式", 5),
            ("代码基础", 0),
        ],
        "wrong_code": 8,
        "wrong_chat": 3,
    },
]

# (category template via result_json profile)
ERROR_PROFILES: list[dict[str, Any]] = [
    {
        "category": "syntax_error",
        "summary": "语法错误：括号或分号缺失",
        "levels": {
            "syntax": {"score": "error", "issues": [{"message": "缺少分号"}]},
            "semantic": {"score": "ok", "issues": []},
            "runtime": {"score": "ok", "issues": []},
        },
    },
    {
        "category": "semantic_error",
        "summary": "语义错误：循环条件导致死循环",
        "levels": {
            "syntax": {"score": "ok", "issues": []},
            "semantic": {"score": "error", "issues": [{"message": "循环无法终止"}]},
            "runtime": {"score": "ok", "issues": []},
        },
    },
    {
        "category": "runtime_error",
        "summary": "运行错误：数组越界访问",
        "levels": {
            "syntax": {"score": "ok", "issues": []},
            "semantic": {"score": "ok", "issues": []},
            "runtime": {"score": "error", "issues": [{"message": "index out of range"}]},
        },
    },
    {
        "category": "analysis_failed",
        "summary": "分析失败：代码格式异常",
        "failed": True,
    },
]

STUDENT_USERNAMES = ("stu", "student")


def _get_teacher(db: Session) -> User:
    teacher = (
        db.query(User)
        .filter(User.role == UserRole.teacher, User.deleted == 0)
        .order_by(User.id.asc())
        .first()
    )
    if not teacher:
        raise RuntimeError("未找到教师账号，请先运行 seed_demo.py")
    return teacher


def _get_student(db: Session) -> User:
    for name in STUDENT_USERNAMES:
        user = db.query(User).filter(User.username == name, User.deleted == 0).first()
        if user:
            return user
    raise RuntimeError("未找到学生账号 stu/student")


def _ensure_course(db: Session, teacher: User, spec: dict[str, Any]) -> Course:
    course = db.query(Course).filter(Course.name == spec["name"], Course.deleted == 0).first()
    if not course:
        course = Course(
            name=spec["name"],
            description=spec["description"],
            teacher_id=teacher.id,
            status=CourseStatus.published,
            create_approval=CourseCreateApproval.approved,
            publish_approval=CoursePublishApproval.approved,
            published_at=datetime.now(),
        )
        db.add(course)
        db.flush()
        db.add(CourseTeacher(course_id=course.id, user_id=teacher.id))
    return course


def _ensure_kps(db: Session, course: Course, kps: list[tuple[str, int]]) -> dict[str, KnowledgePoint]:
    mapping: dict[str, KnowledgePoint] = {}
    for name, order in kps:
        row = (
            db.query(KnowledgePoint)
            .filter(
                KnowledgePoint.course_id == course.id,
                KnowledgePoint.name == name,
                KnowledgePoint.deleted == 0,
            )
            .first()
        )
        if not row:
            row = KnowledgePoint(course_id=course.id, name=name, sort_order=order)
            db.add(row)
            db.flush()
        mapping[name] = row
    return mapping


def _ensure_enrollment(db: Session, course: Course) -> None:
    students = db.query(User).filter(User.role == UserRole.student, User.deleted == 0).all()
    for student in students:
        exists = (
            db.query(CourseStudent)
            .filter(CourseStudent.course_id == course.id, CourseStudent.user_id == student.id)
            .first()
        )
        if not exists:
            db.add(CourseStudent(course_id=course.id, user_id=student.id))


def _pdf_warehouse(db: Session) -> MaterialWarehouse | None:
    return (
        db.query(MaterialWarehouse)
        .filter(
            MaterialWarehouse.warehouse_kind == WarehouseKind.file_type,
            MaterialWarehouse.material_type == MaterialType.pdf,
            MaterialWarehouse.deleted == 0,
        )
        .first()
    )


def _seed_materials(
    db: Session,
    course: Course,
    course_key: str,
    teacher: User,
    warehouse: MaterialWarehouse | None,
) -> list[CourseMaterial]:
    src_dir = MATERIAL_SRC / course_key
    if not src_dir.is_dir():
        return []

    upload_root = Path(get_settings().upload_dir) / "dashboard_demo" / course_key
    upload_root.mkdir(parents=True, exist_ok=True)
    created: list[CourseMaterial] = []

    for pdf in sorted(src_dir.glob("*.pdf")):
        existing = (
            db.query(CourseMaterial)
            .filter(
                CourseMaterial.course_id == course.id,
                CourseMaterial.original_name == pdf.name,
                CourseMaterial.deleted == 0,
            )
            .first()
        )
        if existing:
            created.append(existing)
            continue

        dest = upload_root / pdf.name
        if not dest.is_file():
            shutil.copy2(pdf, dest)

        material = CourseMaterial(
            course_id=course.id,
            warehouse_id=warehouse.id if warehouse else None,
            uploaded_by=teacher.id,
            type=MaterialType.pdf,
            file_path=str(dest.resolve()),
            original_name=pdf.name,
            status=MaterialStatus.ready,
            version=1,
        )
        db.add(material)
        db.flush()
        created.append(material)
    return created


def _build_analysis(profile: dict[str, Any]) -> tuple[AnalysisStatus, dict | None, str | None]:
    if profile.get("failed"):
        return AnalysisStatus.failed, None, "代码过长或格式无法解析"
    return (
        AnalysisStatus.done,
        {"summary": profile["summary"], "levels": profile["levels"]},
        None,
    )


def _count_wrong_for_course(db: Session, student_id: int, course_id: int) -> int:
    return (
        db.query(WrongQuestionBook)
        .filter(
            WrongQuestionBook.user_id == student_id,
            WrongQuestionBook.course_id == course_id,
            WrongQuestionBook.deleted == 0,
        )
        .count()
    )


def _seed_wrong_books_for_course(
    db: Session,
    *,
    student: User,
    course: Course,
    kp: KnowledgePoint,
    language: CodeLanguage,
    code_count: int,
    chat_count: int,
    rng: random.Random,
    day_offset_start: int,
) -> dict[str, int]:
    target = code_count + chat_count
    if _count_wrong_for_course(db, student.id, course.id) >= target:
        return {"code": 0, "chat": 0, "events": 0, "skipped": True}

    stats: dict[str, int] = {"code": 0, "chat": 0, "events": 0}

    for i in range(code_count):
        profile = ERROR_PROFILES[i % len(ERROR_PROFILES)]
        created_at = datetime.now() - timedelta(days=rng.randint(0, 6), hours=rng.randint(0, 20))
        sub = CodeSubmission(
            user_id=student.id,
            course_id=course.id,
            language=language,
            source_code=f"// demo wrong #{i}\nwhile(true){{}}",
            version=1,
            created_at=created_at,
        )
        db.add(sub)
        db.flush()

        status, result_json, err = _build_analysis(profile)
        db.add(
            AnalysisResult(
                submission_id=sub.id,
                status=status,
                result_json=result_json,
                error_message=err,
            )
        )

        existing = (
            db.query(WrongQuestionBook)
            .filter(
                WrongQuestionBook.user_id == student.id,
                WrongQuestionBook.source_type == WrongQuestionSourceType.code_submission,
                WrongQuestionBook.ref_id == sub.id,
                WrongQuestionBook.deleted == 0,
            )
            .first()
        )
        if not existing:
            db.add(
                WrongQuestionBook(
                    user_id=student.id,
                    course_id=course.id,
                    source_type=WrongQuestionSourceType.code_submission,
                    ref_id=sub.id,
                    kp_id=kp.id,
                    mastered=rng.random() < 0.25,
                    created_at=created_at,
                )
            )
            stats["code"] += 1

        db.add(
            LearningEvent(
                user_id=student.id,
                course_id=course.id,
                event_type=LearningEventType.code_submit,
                kp_id=kp.id,
                created_at=created_at,
            )
        )
        db.add(
            LearningEvent(
                user_id=student.id,
                course_id=course.id,
                event_type=LearningEventType.code_analysis_error,
                kp_id=kp.id,
                payload_json={"submission_id": sub.id},
                created_at=created_at,
            )
        )
        stats["events"] += 2

    for j in range(chat_count):
        created_at = datetime.now() - timedelta(
            days=rng.randint(0, 6),
            hours=rng.randint(0, 20),
        )
        msg_id = day_offset_start * 1000 + j + 1
        existing = (
            db.query(WrongQuestionBook)
            .filter(
                WrongQuestionBook.user_id == student.id,
                WrongQuestionBook.source_type == WrongQuestionSourceType.chat_message,
                WrongQuestionBook.ref_id == msg_id,
                WrongQuestionBook.deleted == 0,
            )
            .first()
        )
        if not existing:
            db.add(
                WrongQuestionBook(
                    user_id=student.id,
                    course_id=course.id,
                    source_type=WrongQuestionSourceType.chat_message,
                    ref_id=msg_id,
                    kp_id=kp.id,
                    mastered=rng.random() < 0.2,
                    created_at=created_at,
                )
            )
            stats["chat"] += 1

        db.add(
            LearningEvent(
                user_id=student.id,
                course_id=course.id,
                event_type=LearningEventType.chat_no_context,
                kp_id=kp.id,
                payload_json={"message_id": msg_id},
                created_at=created_at,
            )
        )
        stats["events"] += 1

    return stats


def seed_dashboard_demo(db: Session, *, seed: int = 20260610) -> dict[str, Any]:
    """Idempotent seed for dashboard integration demo."""
    rng = random.Random(seed)
    teacher = _get_teacher(db)
    student = _get_student(db)
    warehouse = _pdf_warehouse(db)

    report: dict[str, Any] = {
        "student": student.username,
        "courses": [],
        "totals": {"wrong_code": 0, "wrong_chat": 0, "materials": 0, "events": 0},
    }

    day_base = 0
    for spec in TRACK_COURSES:
        course = _ensure_course(db, teacher, spec)
        _ensure_enrollment(db, course)
        kp_map = _ensure_kps(db, course, spec["kps"])
        base_kp = kp_map.get("代码基础") or next(iter(kp_map.values()))

        materials = _seed_materials(db, course, spec["key"], teacher, warehouse)
        wrong_stats = _seed_wrong_books_for_course(
            db,
            student=student,
            course=course,
            kp=base_kp,
            language=spec["language"],
            code_count=spec["wrong_code"],
            chat_count=spec["wrong_chat"],
            rng=rng,
            day_offset_start=day_base,
        )
        day_base += 100

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
                db.add(
                    UserKpMastery(
                        user_id=student.id,
                        kp_id=kp.id,
                        score=rng.randint(42, 95),
                    )
                )

        refresh_user_mastery(db, user_id=student.id, kp_id=None)

        course_info = {
            "id": course.id,
            "name": course.name,
            "key": spec["key"],
            "materials": len(materials),
            "wrong_code": wrong_stats["code"],
            "wrong_chat": wrong_stats["chat"],
            "events": wrong_stats["events"],
        }
        report["courses"].append(course_info)
        report["totals"]["wrong_code"] += wrong_stats["code"]
        report["totals"]["wrong_chat"] += wrong_stats["chat"]
        report["totals"]["materials"] += len(materials)
        report["totals"]["events"] += wrong_stats["events"]

    db.commit()

    from app.services.learning_cache import clear_dashboard_cache

    for u in db.query(User).filter(User.role == UserRole.student, User.deleted == 0).all():
        clear_dashboard_cache(u.id)

    # 汇总库内实际数量（重复执行脚本时仍准确）
    report["totals"] = {"wrong_code": 0, "wrong_chat": 0, "materials": 0, "events": 0}
    for info in report["courses"]:
        cid = info["id"]
        code_n = (
            db.query(WrongQuestionBook)
            .filter(
                WrongQuestionBook.user_id == student.id,
                WrongQuestionBook.course_id == cid,
                WrongQuestionBook.source_type == WrongQuestionSourceType.code_submission,
                WrongQuestionBook.deleted == 0,
            )
            .count()
        )
        chat_n = (
            db.query(WrongQuestionBook)
            .filter(
                WrongQuestionBook.user_id == student.id,
                WrongQuestionBook.course_id == cid,
                WrongQuestionBook.source_type == WrongQuestionSourceType.chat_message,
                WrongQuestionBook.deleted == 0,
            )
            .count()
        )
        mat_n = (
            db.query(CourseMaterial)
            .filter(CourseMaterial.course_id == cid, CourseMaterial.deleted == 0)
            .count()
        )
        evt_n = (
            db.query(LearningEvent)
            .filter(LearningEvent.user_id == student.id, LearningEvent.course_id == cid, LearningEvent.deleted == 0)
            .count()
        )
        info["wrong_code"] = code_n
        info["wrong_chat"] = chat_n
        info["materials"] = mat_n
        info["events"] = evt_n
        report["totals"]["wrong_code"] += code_n
        report["totals"]["wrong_chat"] += chat_n
        report["totals"]["materials"] += mat_n
        report["totals"]["events"] += evt_n

    report["totals"]["wrong_all"] = report["totals"]["wrong_code"] + report["totals"]["wrong_chat"]
    return report


def write_manifest(report: dict[str, Any]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "description": "学习仪表盘三类课程联调演示数据",
        **report,
    }
    MANIFEST_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
