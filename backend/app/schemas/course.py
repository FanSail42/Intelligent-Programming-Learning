from datetime import datetime

from pydantic import BaseModel, Field

from app.models.course import CourseStatus


class CourseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    teacher_id: int | None = None
    status: CourseStatus = CourseStatus.draft


class CourseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = None
    status: CourseStatus | None = None


class CourseApprovalAction(BaseModel):
    approved: bool
    remark: str | None = None


class CourseOut(BaseModel):
    id: int
    name: str
    description: str | None
    teacher_id: int
    teacher_name: str
    status: str
    create_approval: str
    publish_approval: str
    published_at: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
