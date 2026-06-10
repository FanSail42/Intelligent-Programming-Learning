import json
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_token(
    *,
    user_id: int,
    role: str,
    token_type: str,
    expires_delta: timedelta,
) -> tuple[str, str, int]:
    jti = str(uuid4())
    expire = _utcnow() + expires_delta
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": token_type,
        "jti": jti,
        "exp": expire,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, jti, int(expires_delta.total_seconds())


def create_access_token(user_id: int, role: str) -> tuple[str, str, int]:
    delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    return create_token(
        user_id=user_id, role=role, token_type=TOKEN_TYPE_ACCESS, expires_delta=delta
    )


def create_refresh_token(user_id: int, role: str) -> tuple[str, str, int]:
    delta = timedelta(days=settings.jwt_refresh_token_expire_days)
    return create_token(
        user_id=user_id, role=role, token_type=TOKEN_TYPE_REFRESH, expires_delta=delta
    )


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def get_token_jti(payload: dict[str, Any]) -> str:
    return payload["jti"]


def get_token_exp_ts(payload: dict[str, Any]) -> int:
    exp = payload.get("exp")
    if isinstance(exp, datetime):
        return int(exp.timestamp())
    return int(exp)


class InMemoryRedis:
    """Fallback for tests or when Redis is unavailable."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[str, float | None]] = {}
        self._lists: dict[str, list[str]] = {}
        self._lock = threading.Lock()
        self._list_ready = threading.Condition(self._lock)

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        expire_at = time.time() + ex if ex else None
        with self._lock:
            self._store[key] = (value, expire_at)

    def get(self, key: str) -> str | None:
        with self._lock:
            item = self._store.get(key)
            if not item:
                return None
            value, expire_at = item
            if expire_at and time.time() > expire_at:
                del self._store[key]
                return None
            return value

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)
            self._lists.pop(key, None)

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def ping(self) -> bool:
        return True

    def lpush(self, key: str, *values: str) -> int:
        with self._list_ready:
            bucket = self._lists.setdefault(key, [])
            for value in reversed(values):
                bucket.insert(0, value)
            self._list_ready.notify_all()
            return len(bucket)

    def brpop(self, keys: str | list[str], timeout: int = 0) -> tuple[str, str] | None:
        key_list = [keys] if isinstance(keys, str) else list(keys)
        deadline = time.time() + timeout if timeout else None
        with self._list_ready:
            while True:
                for key in key_list:
                    bucket = self._lists.get(key, [])
                    if bucket:
                        return key, bucket.pop()
                if timeout == 0:
                    return None
                remaining = (deadline or 0) - time.time()
                if remaining <= 0:
                    return None
                self._list_ready.wait(timeout=remaining)


def redis_supports_queue(client: Any) -> bool:
    return callable(getattr(client, "lpush", None)) and callable(getattr(client, "brpop", None))


_redis_client: Any = None


def set_redis_client(client: Any | None) -> None:
    global _redis_client
    _redis_client = client


def get_redis() -> Any:
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    try:
        import redis

        client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            protocol=2,
        )
        client.ping()
        _redis_client = client
    except Exception:
        _redis_client = InMemoryRedis()
    return _redis_client


def store_refresh_token(jti: str, user_id: int) -> None:
    key = f"refresh:token:{jti}"
    ttl = settings.jwt_refresh_token_expire_days * 86400
    get_redis().set(key, str(user_id), ex=ttl)


def validate_refresh_token(jti: str) -> int | None:
    key = f"refresh:token:{jti}"
    value = get_redis().get(key)
    if value is None:
        return None
    return int(value)


def revoke_refresh_token(jti: str) -> None:
    get_redis().delete(f"refresh:token:{jti}")


def blacklist_access_token(jti: str, exp_ts: int) -> None:
    ttl = max(exp_ts - int(_utcnow().timestamp()), 1)
    get_redis().set(f"jwt:blacklist:{jti}", "1", ex=ttl)


def is_token_blacklisted(jti: str) -> bool:
    return bool(get_redis().exists(f"jwt:blacklist:{jti}"))
