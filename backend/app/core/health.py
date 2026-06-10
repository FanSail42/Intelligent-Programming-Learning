from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import engine
from app.core.security import get_redis


def check_mysql() -> str:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "ok"
    except Exception as exc:
        return f"error: {exc}"


def check_redis() -> str:
    try:
        client = get_redis()
        if hasattr(client, "ping"):
            client.ping()
        else:
            client.get("__health_probe__")
        return "ok"
    except Exception as exc:
        return f"error: {exc}"


def check_chroma() -> str:
    try:
        from app.services.vector_store import get_vector_store

        store = get_vector_store()
        store._collection.count()
        return "ok"
    except Exception as exc:
        return f"error: {exc}"


def check_pptx_parser() -> str:
    try:
        import pptx  # noqa: F401

        return "ok"
    except ImportError as exc:
        return f"error: python-pptx not installed ({exc})"


def collect_health_status() -> dict:
    settings = get_settings()
    components = {
        "mysql": check_mysql(),
        "redis": check_redis(),
        "chroma": check_chroma(),
        "pptx_parser": check_pptx_parser(),
    }
    all_ok = all(status == "ok" for status in components.values())
    return {
        "status": "healthy" if all_ok else "degraded",
        "app": settings.app_name,
        "env": settings.app_env,
        "components": components,
    }
