"""Redis-backed LLM token and call statistics."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.security import get_redis
from app.models.user import User, UserRole, UserStatus

TOTAL_TOKENS_KEY = "stats:llm:tokens:total"
TOTAL_CALLS_KEY = "stats:llm:calls:total"

SCENE_LABELS: dict[str, str] = {
    "chat_rag": "AI 对话",
    "code_analysis": "代码讲解",
}


def _day_tokens_key(day: date) -> str:
    return f"stats:llm:tokens:day:{day.isoformat()}"


def _day_calls_key(day: date) -> str:
    return f"stats:llm:calls:day:{day.isoformat()}"


def _user_day_calls_key(user_id: int, day: date) -> str:
    return f"stats:llm:user_calls:{user_id}:{day.isoformat()}"


def _user_day_tokens_key(user_id: int, day: date) -> str:
    return f"stats:llm:tokens:user:{user_id}:day:{day.isoformat()}"


def _user_total_tokens_key(user_id: int) -> str:
    return f"stats:llm:tokens:user:{user_id}:total"


def _user_day_detail_key(user_id: int, day: date) -> str:
    return f"stats:llm:user:{user_id}:day:{day.isoformat()}:detail"


def _user_last_key(user_id: int) -> str:
    return f"stats:llm:user:{user_id}:last"


def _model_tokens_field(model_id: str) -> str:
    return f"model:{model_id}:tokens"


def _model_calls_field(model_id: str) -> str:
    return f"model:{model_id}:calls"


def _scene_tokens_field(scene: str) -> str:
    return f"scene:{scene}:tokens"


def _scene_calls_field(scene: str) -> str:
    return f"scene:{scene}:calls"


def record_llm_usage(*, user_id: int, tokens: int, scene: str, model: str) -> None:
    redis = get_redis()
    today = date.today()
    detail_key = _user_day_detail_key(user_id, today)

    if tokens > 0:
        redis.incrby(TOTAL_TOKENS_KEY, tokens)
        redis.incrby(_day_tokens_key(today), tokens)
        redis.incrby(_user_day_tokens_key(user_id, today), tokens)
        redis.incrby(_user_total_tokens_key(user_id), tokens)
        redis.hincrby(detail_key, _model_tokens_field(model), tokens)
        redis.hincrby(detail_key, _scene_tokens_field(scene), tokens)

    redis.incr(TOTAL_CALLS_KEY)
    redis.incr(_day_calls_key(today))
    redis.incr(_user_day_calls_key(user_id, today))
    redis.hincrby(detail_key, _model_calls_field(model), 1)
    redis.hincrby(detail_key, _scene_calls_field(scene), 1)

    redis.set(
        _user_last_key(user_id),
        json.dumps(
            {
                "model": model,
                "scene": scene,
                "tokens": tokens,
                "at": datetime.now().isoformat(timespec="seconds"),
            },
            ensure_ascii=False,
        ),
    )

    redis.expire(_day_tokens_key(today), 86400 * 45)
    redis.expire(_day_calls_key(today), 86400 * 45)
    redis.expire(_user_day_calls_key(user_id, today), 86400 * 45)
    redis.expire(_user_day_tokens_key(user_id, today), 86400 * 45)
    redis.expire(detail_key, 86400 * 45)
    redis.expire(_user_last_key(user_id), 86400 * 45)


def _int_val(raw: str | None) -> int:
    if not raw:
        return 0
    try:
        return int(raw)
    except ValueError:
        return 0


def _build_model_lookup(db: Session) -> dict[str, dict]:
    from app.services.ai_model_catalog import list_models_payload

    lookup: dict[str, dict] = {}
    for item in list_models_payload(db)["chat_models"]:
        lookup[item["id"]] = {
            "model_name": item["name"],
            "model_tier": item.get("tier") or "standard",
            "model_category": item.get("category") or "chat",
            "custom": bool(item.get("custom")),
        }
    return lookup


def _resolve_model_meta(model_id: str, lookup: dict[str, dict]) -> dict:
    meta = lookup.get(model_id)
    if meta:
        return {"model_id": model_id, **meta}
    return {
        "model_id": model_id,
        "model_name": model_id,
        "model_tier": "custom",
        "model_category": "chat",
        "custom": True,
    }


def _parse_day_detail(raw: dict[str, str]) -> tuple[dict[str, dict], dict[str, dict]]:
    models: dict[str, dict] = {}
    scenes: dict[str, dict] = {}
    for field, value in raw.items():
        count = _int_val(value)
        if field.startswith("model:") and field.endswith(":tokens"):
            model_id = field[6:-7]
            models.setdefault(model_id, {"tokens": 0, "calls": 0})
            models[model_id]["tokens"] = count
        elif field.startswith("model:") and field.endswith(":calls"):
            model_id = field[6:-6]
            models.setdefault(model_id, {"tokens": 0, "calls": 0})
            models[model_id]["calls"] = count
        elif field.startswith("scene:") and field.endswith(":tokens"):
            scene = field[6:-7]
            scenes.setdefault(scene, {"tokens": 0, "calls": 0})
            scenes[scene]["tokens"] = count
        elif field.startswith("scene:") and field.endswith(":calls"):
            scene = field[6:-6]
            scenes.setdefault(scene, {"tokens": 0, "calls": 0})
            scenes[scene]["calls"] = count
    return models, scenes


def build_usage_summary(*, daily_limit: int, active_llm_model: str, active_llm_model_name: str) -> dict:
    redis = get_redis()
    today = date.today()
    daily_tokens: list[dict] = []
    daily_calls: list[dict] = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        daily_tokens.append(
            {
                "date": day.isoformat(),
                "tokens": _int_val(redis.get(_day_tokens_key(day))),
            }
        )
        daily_calls.append(
            {
                "date": day.isoformat(),
                "calls": _int_val(redis.get(_day_calls_key(day))),
            }
        )

    return {
        "tokens_total": _int_val(redis.get(TOTAL_TOKENS_KEY)),
        "calls_total": _int_val(redis.get(TOTAL_CALLS_KEY)),
        "tokens_today": _int_val(redis.get(_day_tokens_key(today))),
        "calls_today": _int_val(redis.get(_day_calls_key(today))),
        "daily_limit_per_user": daily_limit,
        "active_llm_model": active_llm_model,
        "active_llm_model_name": active_llm_model_name,
        "daily_tokens_7d": daily_tokens,
        "daily_calls_7d": daily_calls,
    }


def _student_stats(user: User, *, today: date, model_lookup: dict[str, dict]) -> dict:
    redis = get_redis()
    calls_today = _int_val(redis.get(_user_day_calls_key(user.id, today)))
    detail_raw = redis.hgetall(_user_day_detail_key(user.id, today))
    model_map, scene_map = _parse_day_detail(detail_raw)

    models_today = []
    for model_id, stats in model_map.items():
        meta = _resolve_model_meta(model_id, model_lookup)
        models_today.append(
            {
                **meta,
                "tokens": stats["tokens"],
                "calls": stats["calls"],
            }
        )
    models_today.sort(key=lambda x: x["tokens"], reverse=True)

    scenes_today = []
    for scene, stats in scene_map.items():
        scenes_today.append(
            {
                "scene": scene,
                "scene_label": SCENE_LABELS.get(scene, scene),
                "tokens": stats["tokens"],
                "calls": stats["calls"],
            }
        )
    scenes_today.sort(key=lambda x: x["tokens"], reverse=True)

    last_raw = redis.get(_user_last_key(user.id))
    last_invoke: dict | None = None
    if last_raw:
        try:
            last_invoke = json.loads(last_raw)
        except json.JSONDecodeError:
            last_invoke = None

    last_model_id = last_invoke.get("model") if last_invoke else None
    last_meta = _resolve_model_meta(last_model_id, model_lookup) if last_model_id else None

    return {
        "user_id": user.id,
        "username": user.username,
        "tokens_today": _int_val(redis.get(_user_day_tokens_key(user.id, today))),
        "tokens_total": _int_val(redis.get(_user_total_tokens_key(user.id))),
        "calls_today": calls_today,
        "quota_used_today": calls_today,
        "models_today": models_today,
        "scenes_today": scenes_today,
        "last_model_id": last_model_id,
        "last_model_name": last_meta["model_name"] if last_meta else None,
        "last_model_tier": last_meta["model_tier"] if last_meta else None,
        "last_model_category": last_meta["model_category"] if last_meta else None,
        "last_scene": last_invoke.get("scene") if last_invoke else None,
        "last_scene_label": SCENE_LABELS.get(last_invoke.get("scene", ""), last_invoke.get("scene"))
        if last_invoke and last_invoke.get("scene")
        else None,
        "last_tokens": last_invoke.get("tokens") if last_invoke else 0,
        "last_invoke_at": last_invoke.get("at") if last_invoke else None,
    }


def list_student_usage(
    db: Session,
    *,
    username: str | None = None,
    page_num: int = 1,
    page_size: int = 10,
) -> tuple[list[dict], int]:
    today = date.today()
    model_lookup = _build_model_lookup(db)
    query = db.query(User).filter(
        User.deleted == 0,
        User.role == UserRole.student,
        User.status == UserStatus.active,
    )
    if username:
        query = query.filter(User.username.like(f"%{username.strip()}%"))

    students = query.order_by(User.id.asc()).all()
    rows = [_student_stats(u, today=today, model_lookup=model_lookup) for u in students]
    rows.sort(key=lambda r: (r["tokens_today"], r["tokens_total"]), reverse=True)

    total = len(rows)
    start = (page_num - 1) * page_size
    end = start + page_size
    return rows[start:end], total
