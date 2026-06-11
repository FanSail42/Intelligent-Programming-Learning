from app.core.config import get_settings
from app.core.exceptions import ERR_RATE_LIMIT, BusinessException
from app.core.security import get_redis
from app.services.runtime_ai_config import get_cached_runtime_ai_config

settings = get_settings()


def check_llm_rate_limit(user_id: int) -> None:
    cfg = get_cached_runtime_ai_config()
    key = f"rate:llm:{user_id}"
    redis = get_redis()
    count = redis.get(key)
    current = int(count) if count else 0
    if current >= cfg.llm_daily_limit:
        raise BusinessException(ERR_RATE_LIMIT, "今日 AI 调用次数已达上限")
    redis.set(key, str(current + 1), ex=86400)
