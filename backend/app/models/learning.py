import enum

from sqlalchemy import BigInteger, Boolean, Enum, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class LearningEventType(str, enum.Enum):
    code_submit = "code_submit"
    code_analysis_error = "code_analysis_error"
    chat_message = "chat_message"
    chat_no_context = "chat_no_context"
    material_view = "material_view"


class WrongQuestionSourceType(str, enum.Enum):
    code_submission = "code_submission"
    chat_message = "chat_message"


class KnowledgePoint(BaseModel):
    __tablename__ = "knowledge_point"

    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    parent_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class LearningEvent(BaseModel):
    __tablename__ = "learning_event"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    course_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    event_type: Mapped[LearningEventType] = mapped_column(
        Enum(LearningEventType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    kp_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class WrongQuestionBook(BaseModel):
    __tablename__ = "wrong_question_book"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    course_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    source_type: Mapped[WrongQuestionSourceType] = mapped_column(
        Enum(WrongQuestionSourceType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    kp_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    mastered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class UserKpMastery(BaseModel):
    __tablename__ = "user_kp_mastery"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    kp_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
