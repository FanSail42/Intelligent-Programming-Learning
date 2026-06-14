"""Admin user account management (M09)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import ERR_FORBIDDEN, ERR_NOT_FOUND, ERR_VALIDATION, BusinessException
from app.core.security import hash_password
from app.models.user import User, UserRole, UserStatus


def _user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role.value,
        "status": user.status.value,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


def get_user_or_404(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id, User.deleted == 0).first()
    if not user:
        raise BusinessException(ERR_NOT_FOUND, "用户不存在")
    return user


def list_managed_users(
    db: Session,
    *,
    role: UserRole | None = None,
    username: str | None = None,
    status: UserStatus | None = None,
    page_num: int = 1,
    page_size: int = 10,
) -> tuple[list[dict], int]:
    query = db.query(User).filter(
        User.deleted == 0,
        User.role.in_([UserRole.student, UserRole.teacher]),
    )
    if role is not None:
        query = query.filter(User.role == role)
    if username and username.strip():
        query = query.filter(User.username.like(f"%{username.strip()}%"))
    if status is not None:
        query = query.filter(User.status == status)

    total = query.count()
    rows = (
        query.order_by(User.id.desc())
        .offset((page_num - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return [_user_to_dict(row) for row in rows], total


def create_managed_user(
    db: Session,
    *,
    username: str,
    password: str,
    role: str,
) -> dict:
    if role not in (UserRole.student.value, UserRole.teacher.value):
        raise BusinessException(ERR_VALIDATION, "仅可创建学生或教师账号")

    exists = (
        db.query(User)
        .filter(User.username == username, User.deleted == 0)
        .first()
    )
    if exists:
        raise BusinessException(ERR_VALIDATION, "用户名已存在")

    user = User(
        username=username,
        password_hash=hash_password(password),
        role=UserRole(role),
        status=UserStatus.active,
    )
    db.add(user)
    db.flush()
    return _user_to_dict(user)


def update_managed_user(
    db: Session,
    *,
    user_id: int,
    operator_id: int,
    status: str | None = None,
    password: str | None = None,
    expected_role: UserRole | None = None,
) -> dict:
    user = get_user_or_404(db, user_id)
    if user.role == UserRole.admin:
        raise BusinessException(ERR_FORBIDDEN, "不可修改管理员账号")
    if expected_role is not None and user.role != expected_role:
        raise BusinessException(ERR_FORBIDDEN, "账号角色与当前管理模块不匹配")
    if user.id == operator_id and status == UserStatus.disabled.value:
        raise BusinessException(ERR_FORBIDDEN, "不可禁用当前登录账号")

    if status is not None:
        user.status = UserStatus(status)
    if password:
        user.password_hash = hash_password(password)

    db.flush()
    return _user_to_dict(user)


def delete_managed_user(
    db: Session,
    *,
    user_id: int,
    operator_id: int,
    expected_role: UserRole | None = None,
) -> None:
    if user_id == operator_id:
        raise BusinessException(ERR_FORBIDDEN, "不可删除当前登录账号")
    user = get_user_or_404(db, user_id)
    if user.role == UserRole.admin:
        raise BusinessException(ERR_FORBIDDEN, "不可删除管理员账号")
    if expected_role is not None and user.role != expected_role:
        raise BusinessException(ERR_FORBIDDEN, "账号角色与当前管理模块不匹配")
    user.deleted = 1
    db.flush()
