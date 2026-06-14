"""Self-service profile: username, password, summary."""

from __future__ import annotations

from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import ERR_UNAUTHORIZED, ERR_VALIDATION, BusinessException
from app.core.security import hash_password, verify_password
from app.models.system import OperationLog
from app.models.user import User, UserRole
from app.services.ai_usage import _build_model_lookup, _student_stats
from app.services.runtime_ai_config import load_runtime_ai_config


def _login_stats(db: Session, user_id: int) -> tuple[int, str | None, str | None]:
    from datetime import datetime

    count = (
        db.query(func.count(OperationLog.id))
        .filter(OperationLog.user_id == user_id, OperationLog.action == "login")
        .scalar()
        or 0
    )
    last = (
        db.query(OperationLog)
        .filter(OperationLog.user_id == user_id, OperationLog.action == "login")
        .order_by(OperationLog.created_at.desc())
        .first()
    )
    last_at: datetime | None = last.created_at if last else None
    last_ip = last.ip if last else None
    return int(count), last_at, last_ip


def build_profile_summary(db: Session, user: User) -> dict:
    login_count, last_login_at, last_login_ip = _login_stats(db, user.id)
    payload: dict = {
        "id": user.id,
        "username": user.username,
        "role": user.role.value,
        "status": user.status.value,
        "created_at": user.created_at,
        "login_count": login_count,
        "last_login_at": last_login_at,
        "last_login_ip": last_login_ip,
        "ai_usage": None,
    }

    if user.role == UserRole.student:
        cfg = load_runtime_ai_config(db)
        model_lookup = _build_model_lookup(db)
        stats = _student_stats(user, today=date.today(), model_lookup=model_lookup)
        payload["ai_usage"] = {
            "tokens_today": stats["tokens_today"],
            "tokens_total": stats["tokens_total"],
            "calls_today": stats["calls_today"],
            "daily_limit": cfg.llm_daily_limit,
            "quota_used_today": stats["quota_used_today"],
            "last_model_name": stats["last_model_name"],
            "last_scene_label": stats["last_scene_label"],
            "last_invoke_at": stats["last_invoke_at"],
        }

    return payload


def update_username(
    db: Session,
    *,
    user: User,
    new_username: str,
    current_password: str,
) -> User:
    if not verify_password(current_password, user.password_hash):
        raise BusinessException(ERR_UNAUTHORIZED, "当前密码不正确")

    username = new_username.strip()
    if username == user.username:
        raise BusinessException(ERR_VALIDATION, "新用户名与当前相同")

    exists = (
        db.query(User)
        .filter(User.username == username, User.deleted == 0, User.id != user.id)
        .first()
    )
    if exists:
        raise BusinessException(ERR_VALIDATION, "用户名已被占用")

    user.username = username
    db.flush()
    return user


def change_password(
    db: Session,
    *,
    user: User,
    current_password: str,
    new_password: str,
) -> None:
    if not verify_password(current_password, user.password_hash):
        raise BusinessException(ERR_UNAUTHORIZED, "当前密码不正确")
    if current_password == new_password:
        raise BusinessException(ERR_VALIDATION, "新密码不能与当前密码相同")

    user.password_hash = hash_password(new_password)
    db.flush()
