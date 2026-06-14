from datetime import datetime

from pydantic import BaseModel, Field


class UpdateUsernameRequest(BaseModel):
    new_username: str = Field(min_length=3, max_length=64)
    current_password: str = Field(min_length=6, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=6, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


class ProfileAiUsage(BaseModel):
    tokens_today: int
    tokens_total: int
    calls_today: int
    daily_limit: int
    quota_used_today: int
    last_model_name: str | None = None
    last_scene_label: str | None = None
    last_invoke_at: str | None = None


class ProfileSummary(BaseModel):
    id: int
    username: str
    role: str
    status: str
    created_at: datetime
    login_count: int
    last_login_at: datetime | None = None
    last_login_ip: str | None = None
    ai_usage: ProfileAiUsage | None = None
