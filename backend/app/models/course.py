import enum
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class CourseStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class CourseCreateApproval(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class CoursePublishApproval(str, enum.Enum):
    none = "none"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Course(BaseModel):
    __tablename__ = "course"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    teacher_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    status: Mapped[CourseStatus] = mapped_column(
        Enum(CourseStatus, values_callable=lambda x: [e.value for e in x]),
        default=CourseStatus.draft,
        nullable=False,
    )
    create_approval: Mapped[CourseCreateApproval] = mapped_column(
        Enum(CourseCreateApproval, values_callable=lambda x: [e.value for e in x]),
        default=CourseCreateApproval.approved,
        nullable=False,
    )
    publish_approval: Mapped[CoursePublishApproval] = mapped_column(
        Enum(CoursePublishApproval, values_callable=lambda x: [e.value for e in x]),
        default=CoursePublishApproval.none,
        nullable=False,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class CourseStudent(BaseModel):
    __tablename__ = "course_student"

    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class CourseTeacher(BaseModel):
    __tablename__ = "course_teacher"

    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
