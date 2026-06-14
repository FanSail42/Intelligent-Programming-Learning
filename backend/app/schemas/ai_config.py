from pydantic import BaseModel, Field


class AiConfigOut(BaseModel):
    llm_model: str
    llm_base_url: str
    llm_api_key_masked: str
    llm_api_key_configured: bool
    embedding_model: str
    embedding_base_url: str
    embedding_api_key_masked: str
    embedding_api_key_configured: bool
    llm_daily_limit: int
    config_source: str


class AiConfigUpdate(BaseModel):
    llm_model: str | None = Field(None, max_length=128)
    llm_base_url: str | None = Field(None, max_length=512)
    llm_api_key: str | None = Field(None, max_length=512, description="留空表示不修改")
    embedding_model: str | None = Field(None, max_length=128)
    embedding_base_url: str | None = Field(None, max_length=512)
    embedding_api_key: str | None = Field(None, max_length=512, description="留空表示不修改")
    llm_daily_limit: int | None = Field(None, ge=1, le=10000)
    clear_llm_api_key: bool = False
    clear_embedding_api_key: bool = False


class AiUsageOut(BaseModel):
    tokens_total: int
    calls_total: int
    tokens_today: int
    calls_today: int
    daily_limit_per_user: int
    active_llm_model: str
    active_llm_model_name: str
    daily_tokens_7d: list[dict]
    daily_calls_7d: list[dict]


class CustomChatModelCreate(BaseModel):
    id: str = Field(..., min_length=1, max_length=128, description="百炼模型 ID，如 kimi-k2.6")
    name: str | None = Field(None, max_length=128, description="展示名称")
    description: str | None = Field(None, max_length=512)


class ModelUsageBreakdown(BaseModel):
    model_id: str
    model_name: str
    model_tier: str
    model_category: str
    custom: bool = False
    tokens: int
    calls: int


class SceneUsageBreakdown(BaseModel):
    scene: str
    scene_label: str
    tokens: int
    calls: int


class StudentTokenUsageItem(BaseModel):
    user_id: int
    username: str
    tokens_today: int
    tokens_total: int
    calls_today: int
    quota_used_today: int
    daily_limit: int | None = None
    models_today: list[ModelUsageBreakdown] = []
    scenes_today: list[SceneUsageBreakdown] = []
    last_model_id: str | None = None
    last_model_name: str | None = None
    last_model_tier: str | None = None
    last_model_category: str | None = None
    last_scene: str | None = None
    last_scene_label: str | None = None
    last_tokens: int = 0
    last_invoke_at: str | None = None
