import enum

from sqlalchemy import BigInteger, Enum, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class CodeLanguage(str, enum.Enum):
    c = "c"
    cpp = "cpp"
    python = "python"
    java = "java"


class AnalysisStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"


class CodeSubmission(BaseModel):
    __tablename__ = "code_submission"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    course_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    assignment_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    language: Mapped[CodeLanguage] = mapped_column(
        Enum(CodeLanguage, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    source_code: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class AnalysisResult(BaseModel):
    __tablename__ = "analysis_result"

    submission_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)
    status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=AnalysisStatus.pending,
    )
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
