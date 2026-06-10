from datetime import datetime

from pydantic import BaseModel, Field


class WarehouseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    description: str | None = None
    warehouse_kind: str = Field(default="file_type", pattern="^(file_type|course)$")
    course_subject: str | None = Field(default=None, pattern="^(python|java|cpp)$")
    material_type: str = Field(default="pdf", pattern="^(pdf|txt|md|pptx)$")
    icon: str = Field(default="📦", max_length=32)
    color: str = Field(default="#409eff", max_length=16)
    sort_order: int = Field(default=0, ge=0)


class WarehouseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = None
    material_type: str | None = Field(default=None, pattern="^(pdf|txt|md|pptx)$")
    icon: str | None = Field(default=None, max_length=32)
    color: str | None = Field(default=None, max_length=16)
    sort_order: int | None = Field(default=None, ge=0)


class WarehouseOut(BaseModel):
    id: int
    name: str
    description: str | None
    warehouse_kind: str
    course_subject: str | None
    material_type: str
    icon: str
    color: str
    sort_order: int
    material_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WarehouseMaterialOut(BaseModel):
    id: int
    course_id: int
    course_name: str
    warehouse_id: int | None
    type: str
    original_name: str
    status: str
    uploaded_by: int | None
    uploader_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WarehouseAssignBody(BaseModel):
    material_ids: list[int] = Field(min_length=1)
