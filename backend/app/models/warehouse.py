import enum

from sqlalchemy import Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.models.material import MaterialType


class WarehouseKind(str, enum.Enum):
    file_type = "file_type"
    course = "course"


class CourseSubject(str, enum.Enum):
    python = "python"
    java = "java"
    cpp = "cpp"


class MaterialWarehouse(BaseModel):
    __tablename__ = "material_warehouse"

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    warehouse_kind: Mapped[WarehouseKind] = mapped_column(
        Enum(WarehouseKind, values_callable=lambda x: [e.value for e in x]),
        default=WarehouseKind.file_type,
        nullable=False,
        index=True,
    )
    course_subject: Mapped[CourseSubject | None] = mapped_column(
        Enum(CourseSubject, values_callable=lambda x: [e.value for e in x]),
        nullable=True,
        index=True,
    )
    material_type: Mapped[MaterialType] = mapped_column(
        Enum(MaterialType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    icon: Mapped[str] = mapped_column(String(32), default="📦", nullable=False)
    color: Mapped[str] = mapped_column(String(16), default="#409eff", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
