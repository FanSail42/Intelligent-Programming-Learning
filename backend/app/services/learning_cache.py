import json
from typing import Any

from app.core.security import get_redis

DASHBOARD_TTL = 600


def _dashboard_key(user_id: int) -> str:
    return f"cache:dashboard:{user_id}"


def clear_dashboard_cache(user_id: int) -> None:
    get_redis().delete(_dashboard_key(user_id))


def get_dashboard_cache(user_id: int) -> dict[str, Any] | None:
    raw = get_redis().get(_dashboard_key(user_id))
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def set_dashboard_cache(user_id: int, data: dict[str, Any]) -> None:
    get_redis().set(_dashboard_key(user_id), json.dumps(data, default=str), ex=DASHBOARD_TTL)
