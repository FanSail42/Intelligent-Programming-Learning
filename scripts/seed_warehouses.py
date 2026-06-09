"""Seed default material warehouses (file-type + course subjects)."""
import os
import sys

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.material import MaterialType
from app.models.warehouse import CourseSubject, MaterialWarehouse, WarehouseKind

FILE_TYPE_WAREHOUSES = [
    ("PDF 文献库", "存放 PDF 格式课程资料", MaterialType.pdf, "📕", "#e74c3c", 1),
    ("TXT 文本库", "存放 TXT 格式课程资料", MaterialType.txt, "📄", "#3498db", 2),
    ("MD 笔记库", "存放 Markdown 格式课程资料", MaterialType.md, "📝", "#2ecc71", 3),
]

COURSE_WAREHOUSES = [
    (
        "Python 课程仓库",
        "存放 Python 课程相关资料，由管理员手动分派",
        CourseSubject.python,
        "🐍",
        "#3776ab",
        10,
    ),
    (
        "Java 课程仓库",
        "存放 Java 课程相关资料，由管理员手动分派",
        CourseSubject.java,
        "☕",
        "#f89820",
        11,
    ),
    (
        "C/C++ 课程仓库",
        "存放 C/C++ 课程相关资料，由管理员手动分派",
        CourseSubject.cpp,
        "⚙️",
        "#00599c",
        12,
    ),
]


def seed() -> None:
    db = SessionLocal()
    try:
        for name, desc, mtype, icon, color, sort_order in FILE_TYPE_WAREHOUSES:
            existing = (
                db.query(MaterialWarehouse)
                .filter(MaterialWarehouse.name == name, MaterialWarehouse.deleted == 0)
                .first()
            )
            if existing:
                continue
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

        for name, desc, subject, icon, color, sort_order in COURSE_WAREHOUSES:
            existing = (
                db.query(MaterialWarehouse)
                .filter(
                    MaterialWarehouse.warehouse_kind == WarehouseKind.course,
                    MaterialWarehouse.course_subject == subject,
                    MaterialWarehouse.deleted == 0,
                )
                .first()
            )
            if existing:
                continue
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
        print("Seed warehouses completed: PDF/TXT/MD + Python/Java/C++ course warehouses")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
