from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from sqlalchemy.orm import Session

from app.core.deps import DbSession, require_roles
from app.models.system import OperationLog
from app.models.user import User, UserRole, UserStatus
from app.schemas.response import PageResult, success
from app.schemas.user_admin import (
    AdminOverviewOut,
    AdminUserCreate,
    AdminUserOut,
    AdminUserUpdate,
    OperationLogItem,
)
from app.services.admin_overview import build_admin_overview, list_operation_logs
from app.services.user_admin import (
    create_managed_user,
    delete_managed_user,
    get_user_or_404,
    list_managed_users,
    update_managed_user,
)

router = APIRouter(prefix="/admin", tags=["admin"])

AdminUser = Annotated[User, Depends(require_roles(UserRole.admin))]


def _parse_role_param(role: str | None) -> UserRole | None:
    if not role:
        return None
    if role == UserRole.admin.value:
        return None
    return UserRole(role)


@router.get("/overview")
def get_overview(db: DbSession, user: AdminUser) -> dict:
    raw = build_admin_overview(db)
    out = AdminOverviewOut.model_validate(raw)
    return success(out.model_dump(mode="json"))


@router.get("/logs")
def list_logs(
    db: DbSession,
    user: AdminUser,
    action: str | None = Query(None, description="login / user_create / user_update / user_delete"),
    username: str | None = Query(None, description="操作者用户名模糊匹配"),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
) -> dict:
    items, total = list_operation_logs(
        db,
        action=action,
        username=username,
        page_num=page_num,
        page_size=page_size,
    )
    page = PageResult(
        list=[OperationLogItem.model_validate(item) for item in items],
        total=total,
        page_num=page_num,
        page_size=page_size,
    )
    return success(page.model_dump(mode="json"))


def _log_action(
    db: Session,
    *,
    operator: User,
    action: str,
    detail: str,
    request: Request,
) -> None:
    db.add(
        OperationLog(
            user_id=operator.id,
            action=action,
            ip=request.client.host if request.client else None,
            detail=detail,
        )
    )


@router.get("/users")
def list_users(
    db: DbSession,
    user: AdminUser,
    role: UserRole | None = Query(None, description="student / teacher（必填其一以分模块管理）"),
    username: str | None = Query(None, description="用户名模糊匹配"),
    status: UserStatus | None = Query(None, description="active / disabled"),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
) -> dict:
    if role is None or role == UserRole.admin:
        from app.core.exceptions import ERR_VALIDATION, BusinessException

        raise BusinessException(ERR_VALIDATION, "请指定 role=student 或 role=teacher")
    items, total = list_managed_users(
        db,
        role=role,
        username=username,
        status=status,
        page_num=page_num,
        page_size=page_size,
    )
    page = PageResult(
        list=[AdminUserOut.model_validate(item) for item in items],
        total=total,
        page_num=page_num,
        page_size=page_size,
    )
    return success(page.model_dump(mode="json"))


@router.post("/users")
def create_user(
    body: AdminUserCreate,
    db: DbSession,
    user: AdminUser,
    request: Request,
) -> dict:
    created = create_managed_user(
        db,
        username=body.username.strip(),
        password=body.password,
        role=body.role,
    )
    _log_action(
        db,
        operator=user,
        action="user_create",
        detail=f"target={created['username']} role={created['role']}",
        request=request,
    )
    db.commit()
    return success(AdminUserOut.model_validate(created).model_dump(mode="json"))


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    body: AdminUserUpdate,
    db: DbSession,
    user: AdminUser,
    request: Request,
    role: UserRole | None = Query(None, description="student / teacher，与分模块页面对应"),
) -> dict:
    if body.status is None and not body.password:
        from app.core.exceptions import ERR_VALIDATION, BusinessException

        raise BusinessException(ERR_VALIDATION, "请至少提供 status 或 password")
    if role is None or role == UserRole.admin:
        from app.core.exceptions import ERR_VALIDATION, BusinessException

        raise BusinessException(ERR_VALIDATION, "请指定 role=student 或 role=teacher")

    updated = update_managed_user(
        db,
        user_id=user_id,
        operator_id=user.id,
        status=body.status,
        password=body.password,
        expected_role=role,
    )
    parts = [f"target={updated['username']}"]
    if body.status is not None:
        parts.append(f"status={body.status}")
    if body.password:
        parts.append("password=reset")
    _log_action(
        db,
        operator=user,
        action="user_update",
        detail=" ".join(parts),
        request=request,
    )
    db.commit()
    return success(AdminUserOut.model_validate(updated).model_dump(mode="json"))


@router.delete("/users/{user_id}")
def remove_user(
    user_id: int,
    db: DbSession,
    user: AdminUser,
    request: Request,
    role: UserRole | None = Query(None, description="student / teacher，与分模块页面对应"),
) -> dict:
    if role is None or role == UserRole.admin:
        from app.core.exceptions import ERR_VALIDATION, BusinessException

        raise BusinessException(ERR_VALIDATION, "请指定 role=student 或 role=teacher")

    target = get_user_or_404(db, user_id)
    delete_managed_user(db, user_id=user_id, operator_id=user.id, expected_role=role)
    _log_action(
        db,
        operator=user,
        action="user_delete",
        detail=f"target={target.username}",
        request=request,
    )
    db.commit()
    return success(None, message="已删除")
