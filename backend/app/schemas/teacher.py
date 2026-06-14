from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.learning import WeakKpItem, WrongBookStatsOut


class CourseBrief(BaseModel):
    id: int
    name: str
    teacher_id: int
    teacher_name: str


class EnrolledStudentItem(BaseModel):
    user_id: int
    username: str
    joined_at: datetime
    wrong_count: int = 0
    unmastered_count: int = 0


class TeacherOverviewSummary(BaseModel):
    student_count: int = 0
    active_students_7d: int = 0
    total_events_7d: int = 0
    wrong_total: int = 0
    wrong_unmastered: int = 0
    mastery_rate: float = 0.0


class EventTrendItem(BaseModel):
    date: str
    count: int


class TeacherCourseOverviewOut(BaseModel):
    course: CourseBrief
    summary: TeacherOverviewSummary
    students: list[EnrolledStudentItem] = Field(default_factory=list)
    wrong_book_stats: WrongBookStatsOut
    weak_kps: list[WeakKpItem] = Field(default_factory=list)
    event_trend: list[EventTrendItem] = Field(default_factory=list)
