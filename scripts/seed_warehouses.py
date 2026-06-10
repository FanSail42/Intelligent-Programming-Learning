"""Seed default material warehouses (file-type + course subjects)."""
import os
import sys

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

from app.core.database import SessionLocal
from app.models.material import CourseMaterial, MaterialType
from app.models.warehouse import CourseSubject, MaterialWarehouse, WarehouseKind

FILE_TYPE_WAREHOUSES = [
    ("PDF 文献库", "存放 PDF 格式课程资料", MaterialType.pdf, "📕", "#e74c3c", 1),
    ("TXT 文本库", "存放 TXT 格式课程资料", MaterialType.txt, "📄", "#3498db", 2),
    ("MD 笔记库", "存放 Markdown 格式课程资料", MaterialType.md, "📝", "#2ecc71", 3),
    ("PPTX 演示库", "存放 PPT/PPTX 格式课程资料", MaterialType.pptx, "📊", "#9b59b6", 4),
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


def _ensure_file_type_warehouse(db, name, desc, mtype, icon, color, sort_order) -> MaterialWarehouse:
    wh = (
        db.query(MaterialWarehouse)
        .filter(
            MaterialWarehouse.warehouse_kind == WarehouseKind.file_type,
            MaterialWarehouse.material_type == mtype,
            MaterialWarehouse.deleted == 0,
        )
        .first()
    )
    if wh:
        wh.name = name
        wh.description = desc
        wh.icon = icon
        wh.color = color
        wh.sort_order = sort_order
        return wh

    wh = MaterialWarehouse(
        name=name,
        description=desc,
        warehouse_kind=WarehouseKind.file_type,
        material_type=mtype,
        icon=icon,
        color=color,
        sort_order=sort_order,
    )
    db.add(wh)
    db.flush()
    return wh


def _ensure_course_warehouse(db, name, desc, subject, icon, color, sort_order) -> MaterialWarehouse:
    wh = (
        db.query(MaterialWarehouse)
        .filter(
            MaterialWarehouse.warehouse_kind == WarehouseKind.course,
            MaterialWarehouse.course_subject == subject,
            MaterialWarehouse.deleted == 0,
        )
        .first()
    )
    if wh:
        wh.name = name
        wh.description = desc
        wh.icon = icon
        wh.color = color
        wh.sort_order = sort_order
        return wh

    wh = MaterialWarehouse(
        name=name,
        description=desc,
        warehouse_kind=WarehouseKind.course,
        course_subject=subject,
        material_type=MaterialType.pdf,
        icon=icon,
        color=color,
        sort_order=sort_order,
    )
    db.add(wh)
    db.flush()
    return wh


def backfill_material_warehouses(db) -> tuple[int, int]:
    """Assign warehouse_id for materials missing or mismatched with file type."""
    from app.services.warehouse_service import resolve_warehouse_for_type

    fixed = 0
    pptx_reassigned = 0
    rows = (
        db.query(CourseMaterial)
        .filter(CourseMaterial.deleted == 0)
        .all()
    )
    for material in rows:
        target_id = resolve_warehouse_for_type(db, material.type)
        if material.warehouse_id == target_id:
            continue
        if material.type == MaterialType.pptx and material.warehouse_id is not None:
            pptx_reassigned += 1
        material.warehouse_id = target_id
        fixed += 1
    return fixed, pptx_reassigned


def seed() -> None:
    db = SessionLocal()
    try:
        for item in FILE_TYPE_WAREHOUSES:
            _ensure_file_type_warehouse(db, *item)

        for item in COURSE_WAREHOUSES:
            _ensure_course_warehouse(db, *item)

        fixed, pptx_reassigned = backfill_material_warehouses(db)
        db.commit()
        print(
            "Seed warehouses completed: PDF/TXT/MD/PPTX + Python/Java/C++ course warehouses; "
            f"backfilled {fixed} material(s)"
            + (f" ({pptx_reassigned} pptx reassigned)" if pptx_reassigned else "")
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
