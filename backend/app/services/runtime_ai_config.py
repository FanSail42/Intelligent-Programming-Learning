"""Runtime AI settings: sys_config overrides with .env fallback."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.secret_crypto import decrypt_secret, encrypt_secret
from app.models.system import SysConfig

CONFIG_KEYS = {
    "llm_model": "ai.llm_model",
    "llm_base_url": "ai.llm_base_url",
    "llm_api_key": "ai.llm_api_key",
    "embedding_model": "ai.embedding_model",
    "embedding_base_url": "ai.embedding_base_url",
    "embedding_api_key": "ai.embedding_api_key",
    "llm_daily_limit": "ai.llm_daily_limit",
}

_cache: "RuntimeAiConfig | None" = None


@dataclass
class RuntimeAiConfig:
    llm_model: str
    llm_base_url: str
    llm_api_key: str
    embedding_model: str
    embedding_base_url: str
    embedding_api_key: str
    llm_daily_limit: int
    llm_api_key_configured: bool
    embedding_api_key_configured: bool
    source: str  # env | db | mixed


def _read_config_map(db: Session) -> dict[str, str]:
    rows = db.query(SysConfig).filter(SysConfig.config_key.in_(CONFIG_KEYS.values())).all()
    return {row.config_key: row.config_value for row in rows}


def _from_settings(settings: Settings) -> RuntimeAiConfig:
    llm_key = settings.llm_api_key or ""
    emb_key = settings.embedding_api_key or llm_key
    return RuntimeAiConfig(
        llm_model=settings.llm_model,
        llm_base_url=settings.llm_base_url,
        llm_api_key=llm_key,
        embedding_model=settings.embedding_model,
        embedding_base_url=settings.embedding_base_url,
        embedding_api_key=emb_key,
        llm_daily_limit=settings.llm_daily_limit,
        llm_api_key_configured=bool(llm_key),
        embedding_api_key_configured=bool(emb_key),
        source="env",
    )


def load_runtime_ai_config(db: Session | None = None) -> RuntimeAiConfig:
    settings = get_settings()
    if db is None:
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            return _load_runtime_ai_config(db, settings)
        finally:
            db.close()
    return _load_runtime_ai_config(db, settings)


def _load_runtime_ai_config(db: Session, settings: Settings) -> RuntimeAiConfig:
    cfg = _from_settings(settings)
    stored = _read_config_map(db)
    if not stored:
        return cfg

    source = "env"
    if stored.get(CONFIG_KEYS["llm_model"]):
        cfg.llm_model = stored[CONFIG_KEYS["llm_model"]]
        source = "db"
    if stored.get(CONFIG_KEYS["llm_base_url"]):
        cfg.llm_base_url = stored[CONFIG_KEYS["llm_base_url"]]
        source = "db"
    if stored.get(CONFIG_KEYS["embedding_model"]):
        cfg.embedding_model = stored[CONFIG_KEYS["embedding_model"]]
        source = "db"
    if stored.get(CONFIG_KEYS["embedding_base_url"]):
        cfg.embedding_base_url = stored[CONFIG_KEYS["embedding_base_url"]]
        source = "db"
    if stored.get(CONFIG_KEYS["llm_daily_limit"]):
        try:
            cfg.llm_daily_limit = int(stored[CONFIG_KEYS["llm_daily_limit"]])
            source = "db"
        except ValueError:
            pass

    if stored.get(CONFIG_KEYS["llm_api_key"]):
        cfg.llm_api_key = decrypt_secret(stored[CONFIG_KEYS["llm_api_key"]])
        cfg.llm_api_key_configured = bool(cfg.llm_api_key)
        source = "mixed" if source == "env" else "db"
    if stored.get(CONFIG_KEYS["embedding_api_key"]):
        cfg.embedding_api_key = decrypt_secret(stored[CONFIG_KEYS["embedding_api_key"]])
        cfg.embedding_api_key_configured = bool(cfg.embedding_api_key)
        source = "mixed" if source == "env" else "db"
    elif cfg.llm_api_key:
        cfg.embedding_api_key = cfg.llm_api_key
        cfg.embedding_api_key_configured = cfg.llm_api_key_configured

    cfg.source = source
    return cfg


def get_cached_runtime_ai_config() -> RuntimeAiConfig:
    global _cache
    if _cache is None:
        _cache = load_runtime_ai_config()
    return _cache


def refresh_runtime_ai_config(db: Session | None = None) -> RuntimeAiConfig:
    global _cache
    _cache = load_runtime_ai_config(db)
    return _cache


def clear_runtime_ai_config_cache() -> None:
    global _cache
    _cache = None


def mask_api_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return f"{key[:3]}****{key[-4:]}"


def _upsert(db: Session, key: str, value: str, remark: str) -> None:
    row = db.query(SysConfig).filter(SysConfig.config_key == key).first()
    if row:
        row.config_value = value
        row.remark = remark
    else:
        db.add(SysConfig(config_key=key, config_value=value, remark=remark))


def save_ai_config(
    db: Session,
    *,
    llm_model: str | None = None,
    llm_base_url: str | None = None,
    llm_api_key: str | None = None,
    embedding_model: str | None = None,
    embedding_base_url: str | None = None,
    embedding_api_key: str | None = None,
    llm_daily_limit: int | None = None,
    clear_llm_api_key: bool = False,
    clear_embedding_api_key: bool = False,
) -> RuntimeAiConfig:
    if llm_model is not None:
        _upsert(db, CONFIG_KEYS["llm_model"], llm_model, "LLM 对话模型")
    if llm_base_url is not None:
        _upsert(db, CONFIG_KEYS["llm_base_url"], llm_base_url.rstrip("/"), "LLM API Base URL")
    if llm_api_key is not None and llm_api_key.strip():
        _upsert(
            db,
            CONFIG_KEYS["llm_api_key"],
            encrypt_secret(llm_api_key.strip()),
            "LLM API Key（加密存储）",
        )
    elif clear_llm_api_key:
        row = db.query(SysConfig).filter(SysConfig.config_key == CONFIG_KEYS["llm_api_key"]).first()
        if row:
            db.delete(row)
    if embedding_model is not None:
        _upsert(db, CONFIG_KEYS["embedding_model"], embedding_model, "Embedding 模型")
    if embedding_base_url is not None:
        _upsert(
            db,
            CONFIG_KEYS["embedding_base_url"],
            embedding_base_url.rstrip("/"),
            "Embedding API Base URL",
        )
    if embedding_api_key is not None and embedding_api_key.strip():
        _upsert(
            db,
            CONFIG_KEYS["embedding_api_key"],
            encrypt_secret(embedding_api_key.strip()),
            "Embedding API Key（加密存储）",
        )
    elif clear_embedding_api_key:
        row = db.query(SysConfig).filter(
            SysConfig.config_key == CONFIG_KEYS["embedding_api_key"]
        ).first()
        if row:
            db.delete(row)
    if llm_daily_limit is not None:
        _upsert(db, CONFIG_KEYS["llm_daily_limit"], str(llm_daily_limit), "每用户每日 AI 调用上限")

    db.flush()
    return refresh_runtime_ai_config(db)


def build_admin_config_view(cfg: RuntimeAiConfig) -> dict:
    return {
        "llm_model": cfg.llm_model,
        "llm_base_url": cfg.llm_base_url,
        "llm_api_key_masked": mask_api_key(cfg.llm_api_key),
        "llm_api_key_configured": cfg.llm_api_key_configured,
        "embedding_model": cfg.embedding_model,
        "embedding_base_url": cfg.embedding_base_url,
        "embedding_api_key_masked": mask_api_key(cfg.embedding_api_key),
        "embedding_api_key_configured": cfg.embedding_api_key_configured,
        "llm_daily_limit": cfg.llm_daily_limit,
        "config_source": cfg.source,
    }
