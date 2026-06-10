"""Redis-backed material processing queue with in-process consumer."""

from __future__ import annotations

import threading
import time

import structlog

from app.core.config import get_settings
from app.core.security import get_redis
from app.services.material_dispatch import QUEUE_KEY
from app.services.material_worker import dispatch_material_process

logger = structlog.get_logger(__name__)

_consumer_started = False
_consumer_lock = threading.Lock()


def ensure_queue_consumer() -> None:
    global _consumer_started
    if get_settings().material_dispatch_mode.lower() != "redis":
        return
    from app.core.security import get_redis, redis_supports_queue

    if not redis_supports_queue(get_redis()):
        return
    with _consumer_lock:
        if _consumer_started:
            return
        _consumer_started = True
        thread = threading.Thread(
            target=_consume_loop,
            daemon=True,
            name="material-queue",
        )
        thread.start()
        logger.info("material_queue_consumer_started")


def _consume_loop() -> None:
    from app.core.security import get_redis, redis_supports_queue

    redis = get_redis()
    if not redis_supports_queue(redis):
        logger.error("material_queue_consumer_unsupported_redis_client")
        return
    while True:
        try:
            item = redis.brpop(QUEUE_KEY, timeout=5)
            if not item:
                continue
            material_id = int(item[1])
            dispatch_material_process(material_id)
        except Exception:
            logger.exception("material_queue_consume_error")
            time.sleep(1)
