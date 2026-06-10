"""Dedicated thread pool for material processing when Celery is unavailable."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
_executor: ThreadPoolExecutor | None = None


def _get_executor() -> ThreadPoolExecutor:
    global _executor
    if _executor is None:
        workers = max(1, get_settings().material_process_workers)
        _executor = ThreadPoolExecutor(
            max_workers=workers,
            thread_name_prefix="material",
        )
        logger.info("material_worker_started", workers=workers)
    return _executor


def dispatch_material_process(material_id: int) -> None:
    """Queue material processing; runs concurrently up to material_process_workers."""
    _get_executor().submit(_run_process, material_id)


def _run_process(material_id: int) -> None:
    from app.services.material_pipeline import process_material

    try:
        process_material(material_id)
    except Exception:
        logger.exception("material_process_failed", material_id=material_id)
