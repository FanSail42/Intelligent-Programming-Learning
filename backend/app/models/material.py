import enum

from sqlalchemy import BigInteger, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class MaterialType(str, enum.Enum):
    pdf = "pdf"
    txt = "txt"
    md = "md"


class MaterialStatus(str, enum.Enum):
    uploaded = "UPLOADED"
    parsing = "PARSING"
    chunking = "CHUNKING"
    embedding = "EMBEDDING"
    ready = "READY"
    failed = "FAILED"


class CourseMaterial(BaseModel):
    __tablename__ = "course_material"

    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    warehouse_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    uploaded_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    type: Mapped[MaterialType] = mapped_column(
        Enum(MaterialType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[MaterialStatus] = mapped_column(
        Enum(MaterialStatus, values_callable=lambda x: [e.value for e in x]),
        default=MaterialStatus.uploaded,
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class MaterialChunk(BaseModel):
    __tablename__ = "material_chunk"

    material_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
