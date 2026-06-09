import enum

from sqlalchemy import BigInteger, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class ChatSession(BaseModel):
    __tablename__ = "chat_session"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False, default="新对话")


class ChatMessage(BaseModel):
    __tablename__ = "chat_message"

    session_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class MessageCitation(BaseModel):
    __tablename__ = "message_citation"

    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    chunk_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
