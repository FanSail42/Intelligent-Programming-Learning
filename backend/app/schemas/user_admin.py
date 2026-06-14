from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AdminUserOut(BaseModel):
    id: int
    username: str
    role: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AdminUserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    role: Literal["student", "teacher"]


class AdminUserUpdate(BaseModel):
    status: Literal["active", "disabled"] | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)

    @field_validator("password")
    @classmethod
    def strip_empty_password(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            return None
        return value


class RoleCountSummary(BaseModel):
    total: int = 0
    active: int = 0
    disabled: int = 0


class CourseCountSummary(BaseModel):
    total: int = 0
    published: int = 0


class OperationLogItem(BaseModel):
    id: int
    user_id: int | None = None
    username: str | None = None
    action: str
    action_label: str
    ip: str | None = None
    detail: str | None = None
    created_at: datetime


class AdminOverviewOut(BaseModel):
    students: RoleCountSummary
    teachers: RoleCountSummary
    courses: CourseCountSummary
    enrollment_total: int = 0
    login_events_7d: int = 0
    recent_logs: list[OperationLogItem] = Field(default_factory=list)
