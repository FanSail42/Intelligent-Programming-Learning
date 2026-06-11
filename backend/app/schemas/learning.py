from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class LearningEventCreate(BaseModel):
    event_type: str
    course_id: int | None = None
    kp_id: int | None = None
    payload: dict[str, Any] | None = None


class DashboardSummary(BaseModel):
    total_events_7d: int = 0
    wrong_count: int = 0
    mastered_count: int = 0


class WeakKpItem(BaseModel):
    kp_id: int
    name: str
    score: int
    course_id: int


class RecentEventItem(BaseModel):
    event_type: str
    course_id: int | None = None
    course_name: str | None = None
    kp_id: int | None = None
    kp_name: str | None = None
    title: str | None = None
    detail: str | None = None
    icon: str | None = None
    tone: str | None = None
    created_at: datetime


class DashboardOut(BaseModel):
    summary: DashboardSummary
    weak_kps: list[WeakKpItem] = Field(default_factory=list)
    recent_events: list[RecentEventItem] = Field(default_factory=list)


class WrongBookItem(BaseModel):
    id: int
    source_type: str
    ref_id: int
    course_id: int | None = None
    kp_id: int | None = None
    kp_name: str | None = None
    language: str | None = None
    summary: str | None = None
    category: str | None = None
    category_label: str | None = None
    issues: list[dict[str, Any]] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    review_tip: str | None = None
    has_fixed_code: bool = False
    mastered: bool
    created_at: datetime


class WrongBookCategoryStat(BaseModel):
    category: str
    label: str
    total: int
    unmastered: int
    analysis: str = ""
    sample_issues: list[str] = Field(default_factory=list)


class WrongBookStatsOut(BaseModel):
    summary: dict[str, Any]
    by_category: list[WrongBookCategoryStat] = Field(default_factory=list)
    by_source: list[dict[str, Any]] = Field(default_factory=list)
    by_language: list[dict[str, Any]] = Field(default_factory=list)
    by_kp: list[dict[str, Any]] = Field(default_factory=list)
    trend: list[dict[str, Any]] = Field(default_factory=list)
    mastered_pie: list[dict[str, Any]] = Field(default_factory=list)


class WrongBookMasteredUpdate(BaseModel):
    mastered: bool


class RecommendationItem(BaseModel):
    kp_id: int | None = None
    kp_name: str | None = None
    score: int = 100
    wrong_count: int = 0
    action_type: str
    priority: str
    material_id: int | None = None
    material_name: str | None = None
    reason: str
