from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_

from app.core.deps import DbSession, require_roles
from app.core.exceptions import ERR_NOT_FOUND, ERR_VALIDATION, BusinessException
from app.models.course import Course
from app.models.material import CourseMaterial, MaterialType
from app.models.user import User, UserRole
from app.models.warehouse import CourseSubject, MaterialWarehouse, WarehouseKind
from app.schemas.response import PageResult, success
from app.schemas.warehouse import (
    WarehouseAssignBody,
    WarehouseCreate,
    WarehouseMaterialOut,
    WarehouseOut,
    WarehouseUpdate,
)
from app.services.warehouse_service import (
    count_warehouse_materials,
    ensure_course_warehouse,
    get_warehouse_or_404,
    is_in_course_warehouse,
    resolve_warehouse_for_type,
)

router = APIRouter(prefix="/warehouses", tags=["warehouses"])

TeacherOrAdmin = Depends(require_roles(UserRole.teacher, UserRole.admin))
AdminOnly = Depends(require_roles(UserRole.admin))


def _parse_datetime_param(value: str, end_of_day: bool = False) -> datetime:
    value = value.strip()
    for fmt in ("%Y/%m/%d %H-%M-%S", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value, fmt)
            if fmt in ("%Y/%m/%d", "%Y-%m-%d") and end_of_day:
                return dt.replace(hour=23, minute=59, second=59)
            return dt
        except ValueError:
            continue
    raise BusinessException(ERR_VALIDATION, "时间格式无效，请使用 yyyy/mm/dd 或 yyyy-mm-dd")


def _warehouse_to_out(db: DbSession, warehouse) -> dict:
    out = WarehouseOut(
        id=warehouse.id,
        name=warehouse.name,
        description=warehouse.description,
        warehouse_kind=warehouse.warehouse_kind.value,
        course_subject=warehouse.course_subject.value if warehouse.course_subject else None,
        material_type=warehouse.material_type.value,
        icon=warehouse.icon,
        color=warehouse.color,
        sort_order=warehouse.sort_order,
        material_count=count_warehouse_materials(db, warehouse.id),
        created_at=warehouse.created_at,
        updated_at=warehouse.updated_at,
    )
    return out.model_dump(mode="json")


def _build_material_query(db: DbSession, warehouse_id: int):
    return (
        db.query(CourseMaterial, Course, User)
        .join(Course, Course.id == CourseMaterial.course_id)
        .outerjoin(User, User.id == CourseMaterial.uploaded_by)
        .filter(
            CourseMaterial.warehouse_id == warehouse_id,
            CourseMaterial.deleted == 0,
            Course.deleted == 0,
        )
    )


def _apply_material_filters(
    query,
    *,
    material_name: str | None,
    course_name: str | None,
    teacher_name: str | None,
    created_from: str | None,
    created_to: str | None,
):
    if material_name:
        query = query.filter(CourseMaterial.original_name.like(f"%{material_name.strip()}%"))
    if course_name:
        query = query.filter(Course.name.like(f"%{course_name.strip()}%"))
    if teacher_name:
        query = query.filter(User.username.like(f"%{teacher_name.strip()}%"))
    if created_from:
        query = query.filter(CourseMaterial.created_at >= _parse_datetime_param(created_from))
    if created_to:
        query = query.filter(
            CourseMaterial.created_at <= _parse_datetime_param(created_to, end_of_day=True)
        )
    return query


def _rows_to_material_items(rows) -> list[dict]:
    items = []
    for material, course, uploader in rows:
        items.append(
            WarehouseMaterialOut(
                id=material.id,
                course_id=material.course_id,
                course_name=course.name,
                warehouse_id=material.warehouse_id,
                type=material.type.value,
                original_name=material.original_name,
                status=material.status.value,
                uploaded_by=material.uploaded_by,
                uploader_name=uploader.username if uploader else "",
                created_at=material.created_at,
            ).model_dump(mode="json")
        )
    return items


@router.get("")
def list_warehouses(db: DbSession, user: User = TeacherOrAdmin):
    rows = (
        db.query(MaterialWarehouse)
        .filter(MaterialWarehouse.deleted == 0)
        .order_by(MaterialWarehouse.sort_order.asc(), MaterialWarehouse.id.asc())
        .all()
    )
    return success([_warehouse_to_out(db, row) for row in rows])


@router.post("")
def create_warehouse(body: WarehouseCreate, db: DbSession, user: User = AdminOnly):
    kind = WarehouseKind(body.warehouse_kind)
    course_subject = None
    if kind == WarehouseKind.course:
        if not body.course_subject:
            raise BusinessException(40001, "课程资料仓库须指定 course_subject")
        course_subject = CourseSubject(body.course_subject)

    warehouse = MaterialWarehouse(
        name=body.name,
        description=body.description,
        warehouse_kind=kind,
        course_subject=course_subject,
        material_type=MaterialType(body.material_type),
        icon=body.icon,
        color=body.color,
        sort_order=body.sort_order,
    )
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    return success(_warehouse_to_out(db, warehouse))


@router.get("/{warehouse_id}")
def get_warehouse(warehouse_id: int, db: DbSession, user: User = TeacherOrAdmin):
    warehouse = get_warehouse_or_404(db, warehouse_id)
    return success(_warehouse_to_out(db, warehouse))


@router.put("/{warehouse_id}")
def update_warehouse(
    warehouse_id: int,
    body: WarehouseUpdate,
    db: DbSession,
    user: User = AdminOnly,
):
    warehouse = get_warehouse_or_404(db, warehouse_id)
    if body.name is not None:
        warehouse.name = body.name
    if body.description is not None:
        warehouse.description = body.description
    if body.material_type is not None and warehouse.warehouse_kind == WarehouseKind.file_type:
        warehouse.material_type = MaterialType(body.material_type)
    if body.icon is not None:
        warehouse.icon = body.icon
    if body.color is not None:
        warehouse.color = body.color
    if body.sort_order is not None:
        warehouse.sort_order = body.sort_order
    db.commit()
    db.refresh(warehouse)
    return success(_warehouse_to_out(db, warehouse))


@router.delete("/{warehouse_id}")
def delete_warehouse(warehouse_id: int, db: DbSession, user: User = AdminOnly):
    warehouse = get_warehouse_or_404(db, warehouse_id)
    material_count = count_warehouse_materials(db, warehouse_id)
    if material_count > 0:
        raise BusinessException(40001, f"仓库内仍有 {material_count} 份资料，无法删除")
    warehouse.deleted = 1
    db.commit()
    return success(None, message="已删除")


@router.get("/{warehouse_id}/materials")
def list_warehouse_materials(
    warehouse_id: int,
    db: DbSession,
    user: User = TeacherOrAdmin,
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    material_name: str | None = Query(None),
    course_name: str | None = Query(None),
    teacher_name: str | None = Query(None),
    created_from: str | None = Query(None),
    created_to: str | None = Query(None),
):
    get_warehouse_or_404(db, warehouse_id)

    query = _apply_material_filters(
        _build_material_query(db, warehouse_id),
        material_name=material_name,
        course_name=course_name,
        teacher_name=teacher_name,
        created_from=created_from,
        created_to=created_to,
    )

    total = query.count()
    rows = (
        query.order_by(CourseMaterial.id.desc())
        .offset((page_num - 1) * page_size)
        .limit(page_size)
        .all()
    )

    page = PageResult(
        list=_rows_to_material_items(rows),
        total=total,
        page_num=page_num,
        page_size=page_size,
    )
    return success(page.model_dump(mode="json"))


@router.get("/{warehouse_id}/assignable-materials")
def list_assignable_materials(
    warehouse_id: int,
    db: DbSession,
    user: User = AdminOnly,
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    material_name: str | None = Query(None),
    course_name: str | None = Query(None),
):
    warehouse = get_warehouse_or_404(db, warehouse_id)
    ensure_course_warehouse(db, warehouse)

    query = (
        db.query(CourseMaterial, Course, User)
        .join(Course, Course.id == CourseMaterial.course_id)
        .outerjoin(User, User.id == CourseMaterial.uploaded_by)
        .outerjoin(MaterialWarehouse, MaterialWarehouse.id == CourseMaterial.warehouse_id)
        .filter(
            CourseMaterial.deleted == 0,
            Course.deleted == 0,
            or_(
                CourseMaterial.warehouse_id.is_(None),
                MaterialWarehouse.warehouse_kind == WarehouseKind.file_type,
                MaterialWarehouse.id.is_(None),
            ),
        )
    )

    query = _apply_material_filters(
        query,
        material_name=material_name,
        course_name=course_name,
        teacher_name=None,
        created_from=None,
        created_to=None,
    )

    total = query.count()
    rows = (
        query.order_by(CourseMaterial.id.desc())
        .offset((page_num - 1) * page_size)
        .limit(page_size)
        .all()
    )

    page = PageResult(
        list=_rows_to_material_items(rows),
        total=total,
        page_num=page_num,
        page_size=page_size,
    )
    return success(page.model_dump(mode="json"))


@router.post("/{warehouse_id}/assign")
def assign_materials(
    warehouse_id: int,
    body: WarehouseAssignBody,
    db: DbSession,
    user: User = AdminOnly,
):
    warehouse = get_warehouse_or_404(db, warehouse_id)
    ensure_course_warehouse(db, warehouse)

    materials = (
        db.query(CourseMaterial)
        .filter(CourseMaterial.id.in_(body.material_ids), CourseMaterial.deleted == 0)
        .all()
    )
    if len(materials) != len(body.material_ids):
        raise BusinessException(ERR_NOT_FOUND, "部分资料不存在")

    for material in materials:
        if is_in_course_warehouse(db, material.warehouse_id):
            raise BusinessException(
                40001,
                f"资料「{material.original_name}」已在其他课程仓库中，请先移出",
            )
        material.warehouse_id = warehouse.id

    db.commit()
    return success({"assigned_count": len(materials)})


@router.post("/{warehouse_id}/unassign")
def unassign_materials(
    warehouse_id: int,
    body: WarehouseAssignBody,
    db: DbSession,
    user: User = AdminOnly,
):
    warehouse = get_warehouse_or_404(db, warehouse_id)
    ensure_course_warehouse(db, warehouse)

    materials = (
        db.query(CourseMaterial)
        .filter(
            CourseMaterial.id.in_(body.material_ids),
            CourseMaterial.warehouse_id == warehouse_id,
            CourseMaterial.deleted == 0,
        )
        .all()
    )
    if len(materials) != len(body.material_ids):
        raise BusinessException(ERR_NOT_FOUND, "部分资料不在本仓库中")

    for material in materials:
        material.warehouse_id = resolve_warehouse_for_type(db, material.type)

    db.commit()
    return success({"unassigned_count": len(materials)})
