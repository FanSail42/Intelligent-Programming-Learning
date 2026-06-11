from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "慧编学伴"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    host: str = "0.0.0.0"
    port: int = 8000

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    database_url: str = (
        "mysql+pymysql://huibian:huibian123@localhost:3306/huibian?charset=utf8mb4"
    )
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = "change-me-to-a-random-secret-key-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 4320  # 3 天
    jwt_refresh_token_expire_days: int = 7

    llm_api_key: str = ""
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "qwen3.6-flash"

    embedding_api_key: str = ""
    embedding_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    embedding_model: str = "text-embedding-v4"
    embedding_dimensions: int = 1024

    chroma_persist_dir: str = "./data/chroma"
    upload_dir: str = "./data/uploads"
    max_upload_size_mb: int = 10
    material_dispatch_mode: str = "redis"  # redis | thread | celery
    material_process_workers: int = 4
    embedding_concurrent_batches: int = 5
    material_chunk_size: int = 768
    material_chunk_overlap: int = 64
    llm_daily_limit: int = 100
    config_encryption_key: str = ""
    chat_history_max_turns: int = 10
    rag_relevance_score_min: float = 0.52
    rag_relevance_score_high: float = 0.72
    rag_keyword_overlap_min: float = 0.12
    code_max_source_chars: int = 16384
    celery_broker_url: str = ""

    # Aliyun OSS (optional; empty = local disk storage)
    oss_enabled: bool = False
    oss_access_key_id: str = ""
    oss_access_key_secret: str = ""
    oss_endpoint: str = ""
    oss_bucket: str = ""
    oss_prefix: str = "materials/"

    @property
    def broker_url(self) -> str:
        return self.celery_broker_url or self.redis_url

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | List[str]) -> str:
        if isinstance(value, list):
            return ",".join(value)
        return value

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
