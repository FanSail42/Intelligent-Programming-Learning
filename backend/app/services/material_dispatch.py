"""Dispatch material processing via Redis queue, thread pool, or Celery."""

from __future__ import annotations

import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
QUEUE_KEY = "material:process:queue"


def dispatch_material_processing(material_id: int) -> None:
    mode = get_settings().material_dispatch_mode.lower()
    if mode == "celery":
        _dispatch_celery(material_id)
        return
    if mode == "redis":
        _dispatch_redis(material_id)
        return
    _dispatch_thread(material_id)


def _dispatch_celery(material_id: int) -> None:
    try:
        from app.tasks.material_tasks import process_material_task

        process_material_task.delay(material_id)
        logger.debug("material_dispatched_celery", material_id=material_id)
    except Exception:
        logger.warning("material_celery_unavailable_fallback_redis", material_id=material_id)
        _dispatch_redis(material_id)


def _dispatch_redis(material_id: int) -> None:
    from app.core.security import get_redis, redis_supports_queue
    from app.services.material_queue import ensure_queue_consumer

    redis = get_redis()
    if not redis_supports_queue(redis):
        logger.warning("redis_queue_unavailable_fallback_thread", material_id=material_id)
        _dispatch_thread(material_id)
        return

    redis.lpush(QUEUE_KEY, str(material_id))
    ensure_queue_consumer()
    logger.debug("material_dispatched_redis", material_id=material_id)


def _dispatch_thread(material_id: int) -> None:
    from app.services.material_worker import dispatch_material_process

    dispatch_material_process(material_id)
    logger.debug("material_dispatched_thread", material_id=material_id)
