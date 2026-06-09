from datetime import datetime

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    course_id: int
    title: str = Field(default="新对话", max_length=128)


class SessionOut(BaseModel):
    id: int
    course_id: int
    title: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=8000)


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    citations: list[dict] = []
    no_context: bool | None = None

    model_config = {"from_attributes": True}
