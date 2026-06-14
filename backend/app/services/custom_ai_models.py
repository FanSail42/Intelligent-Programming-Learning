"""Admin-defined custom chat models (stored in sys_config)."""

from __future__ import annotations

import json
import re

from sqlalchemy.orm import Session

from app.core.exceptions import ERR_VALIDATION, BusinessException
from app.models.system import SysConfig

CUSTOM_CHAT_MODELS_KEY = "ai.custom_chat_models"
MODEL_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}$")


def _normalize_entry(raw: dict) -> dict:
    model_id = str(raw.get("id", "")).strip()
    name = str(raw.get("name", "")).strip() or model_id
    description = str(raw.get("description", "")).strip() or "管理员添加的自定义百炼模型"
    return {
        "id": model_id,
        "name": name,
        "provider": "custom",
        "category": "chat",
        "tier": "custom",
        "description": description,
        "custom": True,
    }


def load_custom_chat_models(db: Session) -> list[dict]:
    row = db.query(SysConfig).filter(SysConfig.config_key == CUSTOM_CHAT_MODELS_KEY).first()
    if not row or not row.config_value:
        return []
    try:
        data = json.loads(row.config_value)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    out: list[dict] = []
    seen: set[str] = set()
    for item in data:
        if not isinstance(item, dict):
            continue
        entry = _normalize_entry(item)
        if not entry["id"] or entry["id"] in seen:
            continue
        seen.add(entry["id"])
        out.append(entry)
    return out


def _save_custom_chat_models(db: Session, models: list[dict]) -> None:
    payload = json.dumps(models, ensure_ascii=False)
    row = db.query(SysConfig).filter(SysConfig.config_key == CUSTOM_CHAT_MODELS_KEY).first()
    if row:
        row.config_value = payload
        row.remark = "自定义对话模型列表"
    else:
        db.add(
            SysConfig(
                config_key=CUSTOM_CHAT_MODELS_KEY,
                config_value=payload,
                remark="自定义对话模型列表",
            )
        )


def validate_model_id(model_id: str) -> str:
    cleaned = model_id.strip()
    if not cleaned or not MODEL_ID_PATTERN.match(cleaned):
        raise BusinessException(
            ERR_VALIDATION,
            "模型 ID 仅允许字母、数字、点、横线、下划线，且以字母或数字开头",
        )
    return cleaned


def add_custom_chat_model(
    db: Session,
    *,
    model_id: str,
    name: str | None = None,
    description: str | None = None,
) -> dict:
    cleaned_id = validate_model_id(model_id)
    models = load_custom_chat_models(db)
    if any(m["id"] == cleaned_id for m in models):
        raise BusinessException(ERR_VALIDATION, f"模型 {cleaned_id} 已存在")
    entry = _normalize_entry(
        {"id": cleaned_id, "name": name or cleaned_id, "description": description or ""}
    )
    models.append(entry)
    _save_custom_chat_models(db, models)
    return entry


def remove_custom_chat_model(db: Session, model_id: str) -> None:
    cleaned_id = validate_model_id(model_id)
    models = load_custom_chat_models(db)
    filtered = [m for m in models if m["id"] != cleaned_id]
    if len(filtered) == len(models):
        raise BusinessException(ERR_VALIDATION, f"未找到自定义模型 {cleaned_id}")
    _save_custom_chat_models(db, filtered)


def custom_chat_model_ids(db: Session) -> set[str]:
    return {m["id"] for m in load_custom_chat_models(db)}


def is_allowed_chat_model(db: Session, model_id: str) -> bool:
    from app.services.ai_model_catalog import CHAT_MODEL_IDS

    return model_id in CHAT_MODEL_IDS or model_id in custom_chat_model_ids(db)
