from typing import Annotated

from fastapi import APIRouter, Header, Request

from app.core.deps import CurrentUser, DbSession
from app.core.exceptions import ERR_UNAUTHORIZED, BusinessException
from app.core.security import (
    blacklist_access_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_exp_ts,
    get_token_jti,
    revoke_refresh_token,
    store_refresh_token,
    validate_refresh_token,
    verify_password,
)
from app.models.system import OperationLog
from app.models.user import User, UserStatus
from app.schemas.auth import LoginRequest, RefreshRequest, TokenData, UserOut
from app.schemas.profile import ChangePasswordRequest, ProfileSummary, UpdateUsernameRequest
from app.schemas.response import success
from app.services.profile import build_profile_summary, change_password, update_username

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(user: User) -> TokenData:
    access_token, _, expires_in = create_access_token(user.id, user.role.value)
    refresh_token, refresh_jti, _ = create_refresh_token(user.id, user.role.value)
    store_refresh_token(refresh_jti, user.id)
    return TokenData(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


@router.post("/login")
def login(body: LoginRequest, db: DbSession, request: Request):
    user = (
        db.query(User)
        .filter(User.username == body.username, User.deleted == 0)
        .first()
    )
    if not user or not verify_password(body.password, user.password_hash):
        raise BusinessException(ERR_UNAUTHORIZED, "你的账号或密码错误！")
    if user.status != UserStatus.active:
        raise BusinessException(ERR_UNAUTHORIZED, "你的账号或密码错误！")

    log = OperationLog(
        user_id=user.id,
        action="login",
        ip=request.client.host if request.client else None,
        detail=f"user={user.username}",
    )
    db.add(log)
    db.commit()

    return success(_issue_tokens(user).model_dump())


@router.post("/refresh")
def refresh(body: RefreshRequest, db: DbSession):
    try:
        payload = decode_token(body.refresh_token)
    except Exception as exc:
        raise BusinessException(ERR_UNAUTHORIZED, "Refresh Token 无效") from exc

    if payload.get("type") != "refresh":
        raise BusinessException(ERR_UNAUTHORIZED, "Refresh Token 无效")

    jti = get_token_jti(payload)
    user_id = validate_refresh_token(jti)
    if user_id is None:
        raise BusinessException(ERR_UNAUTHORIZED, "Refresh Token 已失效")

    user = db.query(User).filter(User.id == user_id, User.deleted == 0).first()
    if not user or user.status != UserStatus.active:
        raise BusinessException(ERR_UNAUTHORIZED, "用户不可用")

    revoke_refresh_token(jti)
    access_token, _, expires_in = create_access_token(user.id, user.role.value)
    refresh_token, new_jti, _ = create_refresh_token(user.id, user.role.value)
    store_refresh_token(new_jti, user.id)

    return success(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in,
        }
    )


@router.post("/logout")
def logout(
    user: CurrentUser,
    authorization: Annotated[str | None, Header()] = None,
):
    token = ""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
    if token:
        try:
            payload = decode_token(token)
            jti = get_token_jti(payload)
            blacklist_access_token(jti, get_token_exp_ts(payload))
        except Exception:
            pass
    return success(None, message="已登出")


@router.get("/me")
def me(user: CurrentUser):
    return success(UserOut.model_validate(user).model_dump(mode="json"))


@router.get("/profile/summary")
def profile_summary(user: CurrentUser, db: DbSession):
    data = build_profile_summary(db, user)
    return success(ProfileSummary.model_validate(data).model_dump(mode="json"))


@router.patch("/profile/username")
def profile_update_username(body: UpdateUsernameRequest, user: CurrentUser, db: DbSession, request: Request):
    update_username(
        db,
        user=user,
        new_username=body.new_username,
        current_password=body.current_password,
    )
    log = OperationLog(
        user_id=user.id,
        action="profile_update",
        ip=request.client.host if request.client else None,
        detail=f"username={body.new_username.strip()}",
    )
    db.add(log)
    db.commit()
    db.refresh(user)
    return success(UserOut.model_validate(user).model_dump(mode="json"), message="用户名已更新")


@router.patch("/profile/password")
def profile_change_password(body: ChangePasswordRequest, user: CurrentUser, db: DbSession, request: Request):
    change_password(
        db,
        user=user,
        current_password=body.current_password,
        new_password=body.new_password,
    )
    log = OperationLog(
        user_id=user.id,
        action="password_change",
        ip=request.client.host if request.client else None,
        detail=f"user={user.username}",
    )
    db.add(log)
    db.commit()
    return success(None, message="密码已修改，请使用新密码登录")
