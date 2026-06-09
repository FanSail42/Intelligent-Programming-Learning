from datetime import datetime

from pydantic import BaseModel, Field


class MaterialOut(BaseModel):
    id: int
    course_id: int
    warehouse_id: int | None = None
    uploaded_by: int | None = None
    type: str
    original_name: str
    status: str
    version: int
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MaterialStatusOut(BaseModel):
    id: int
    status: str
    error_message: str | None = None
