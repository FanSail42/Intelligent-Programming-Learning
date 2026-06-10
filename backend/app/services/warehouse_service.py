from sqlalchemy.orm import Session

from app.core.exceptions import ERR_NOT_FOUND, BusinessException
from app.models.material import CourseMaterial, MaterialType
from app.models.warehouse import MaterialWarehouse, WarehouseKind

_WAREHOUSE_BY_TYPE: dict[MaterialType, int] = {}


def clear_warehouse_cache() -> None:
    _WAREHOUSE_BY_TYPE.clear()


def resolve_warehouse_for_type(db: Session, material_type: MaterialType) -> int:
    cached = _WAREHOUSE_BY_TYPE.get(material_type)
    if cached is not None:
        return cached
    warehouse = (
        db.query(MaterialWarehouse)
        .filter(
            MaterialWarehouse.warehouse_kind == WarehouseKind.file_type,
            MaterialWarehouse.material_type == material_type,
            MaterialWarehouse.deleted == 0,
        )
        .order_by(MaterialWarehouse.sort_order.asc(), MaterialWarehouse.id.asc())
        .first()
    )
    if not warehouse:
        raise BusinessException(40001, f"未配置 {material_type.value} 类型资料仓库，请联系管理员")
    _WAREHOUSE_BY_TYPE[material_type] = warehouse.id
    return warehouse.id


def get_warehouse_or_404(db: Session, warehouse_id: int) -> MaterialWarehouse:
    warehouse = (
        db.query(MaterialWarehouse)
        .filter(MaterialWarehouse.id == warehouse_id, MaterialWarehouse.deleted == 0)
        .first()
    )
    if not warehouse:
        raise BusinessException(ERR_NOT_FOUND, "资料仓库不存在")
    return warehouse


def count_warehouse_materials(db: Session, warehouse_id: int) -> int:
    return (
        db.query(CourseMaterial)
        .filter(CourseMaterial.warehouse_id == warehouse_id, CourseMaterial.deleted == 0)
        .count()
    )


def ensure_course_warehouse(db: Session, warehouse: MaterialWarehouse) -> None:
    if warehouse.warehouse_kind != WarehouseKind.course:
        raise BusinessException(40001, "仅课程资料仓库支持手动分派")


def is_in_course_warehouse(db: Session, warehouse_id: int | None) -> bool:
    if not warehouse_id:
        return False
    wh = (
        db.query(MaterialWarehouse)
        .filter(MaterialWarehouse.id == warehouse_id, MaterialWarehouse.deleted == 0)
        .first()
    )
    return wh is not None and wh.warehouse_kind == WarehouseKind.course
