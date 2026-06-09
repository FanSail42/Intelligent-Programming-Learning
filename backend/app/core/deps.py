from typing import Annotated, Callable

from fastapi import Depends, Header
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import (
    ERR_FORBIDDEN,
    ERR_UNAUTHORIZED,
    BusinessException,
)
from app.core.security import (
    TOKEN_TYPE_ACCESS,
    decode_token,
    is_token_blacklisted,
)
from app.models.user import User, UserRole, UserStatus

DbSession = Annotated[Session, Depends(get_db)]


async def get_current_user(
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise BusinessException(ERR_UNAUTHORIZED, "未登录或 Token 无效")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_token(token)
    except JWTError as exc:
        raise BusinessException(ERR_UNAUTHORIZED, "未登录或 Token 无效") from exc

    if payload.get("type") != TOKEN_TYPE_ACCESS:
        raise BusinessException(ERR_UNAUTHORIZED, "Token 类型无效")

    jti = payload.get("jti")
    if jti and is_token_blacklisted(jti):
        raise BusinessException(ERR_UNAUTHORIZED, "Token 已失效")

    user_id = int(payload.get("sub", 0))
    user = db.query(User).filter(User.id == user_id, User.deleted == 0).first()
    if not user:
        raise BusinessException(ERR_UNAUTHORIZED, "用户不存在")
    if user.status != UserStatus.active:
        raise BusinessException(ERR_UNAUTHORIZED, "账号已禁用")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole) -> Callable:
    allowed = set(roles)

    async def _checker(user: CurrentUser) -> User:
        if user.role not in allowed:
            raise BusinessException(ERR_FORBIDDEN, "无权限访问")
        return user

    return _checker
