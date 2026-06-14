from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.core.deps import DbSession, require_roles
from app.core.exceptions import ERR_VALIDATION, BusinessException
from app.models.system import OperationLog
from app.models.user import User, UserRole
from app.schemas.ai_config import (
    AiConfigOut,
    AiConfigUpdate,
    AiUsageOut,
    CustomChatModelCreate,
    StudentTokenUsageItem,
)
from app.schemas.response import PageResult, success
from app.services.ai_model_catalog import EMBEDDING_MODEL_IDS, list_models_payload
from app.services.ai_usage import build_usage_summary, list_student_usage
from app.services.custom_ai_models import (
    add_custom_chat_model,
    is_allowed_chat_model,
    remove_custom_chat_model,
)
from app.services.runtime_ai_config import (
    build_admin_config_view,
    get_cached_runtime_ai_config,
    load_runtime_ai_config,
    save_ai_config,
)

router = APIRouter(prefix="/admin/ai", tags=["admin-ai"])

AdminUser = Annotated[User, Depends(require_roles(UserRole.admin))]


def _log_ai_config(db, operator: User, request: Request, detail: str) -> None:
    db.add(
        OperationLog(
            user_id=operator.id,
            action="ai_config_update",
            ip=request.client.host if request.client else None,
            detail=detail,
        )
    )


@router.get("/models")
def list_ai_models(db: DbSession, user: AdminUser) -> dict:
    return success(list_models_payload(db))


@router.post("/models/custom")
def create_custom_chat_model(
    body: CustomChatModelCreate,
    db: DbSession,
    user: AdminUser,
    request: Request,
) -> dict:
    entry = add_custom_chat_model(
        db,
        model_id=body.id,
        name=body.name,
        description=body.description,
    )
    _log_ai_config(db, user, request, f"custom_model_add id={entry['id']}")
    db.commit()
    return success(entry, message="自定义模型已添加")


@router.delete("/models/custom/{model_id}")
def delete_custom_chat_model(
    model_id: str,
    db: DbSession,
    user: AdminUser,
    request: Request,
) -> dict:
    remove_custom_chat_model(db, model_id)
    _log_ai_config(db, user, request, f"custom_model_delete id={model_id}")
    db.commit()
    return success(None, message="已删除自定义模型")


@router.get("/config")
def get_ai_config(db: DbSession, user: AdminUser) -> dict:
    cfg = load_runtime_ai_config(db)
    out = AiConfigOut.model_validate(build_admin_config_view(cfg))
    return success(out.model_dump(mode="json"))


@router.put("/config")
def update_ai_config(
    body: AiConfigUpdate,
    db: DbSession,
    user: AdminUser,
    request: Request,
) -> dict:
    if body.llm_model is not None and not is_allowed_chat_model(db, body.llm_model):
        raise BusinessException(
            ERR_VALIDATION,
            f"不支持的对话模型：{body.llm_model}，请从列表选择或先添加自定义模型",
        )
    if body.embedding_model is not None and body.embedding_model not in EMBEDDING_MODEL_IDS:
        raise BusinessException(ERR_VALIDATION, f"不支持的向量模型：{body.embedding_model}")

    has_change = any(
        [
            body.llm_model is not None,
            body.llm_base_url is not None,
            body.llm_api_key,
            body.embedding_model is not None,
            body.embedding_base_url is not None,
            body.embedding_api_key,
            body.llm_daily_limit is not None,
            body.clear_llm_api_key,
            body.clear_embedding_api_key,
        ]
    )
    if not has_change:
        raise BusinessException(ERR_VALIDATION, "请至少修改一项配置")

    cfg = save_ai_config(
        db,
        llm_model=body.llm_model,
        llm_base_url=body.llm_base_url,
        llm_api_key=body.llm_api_key,
        embedding_model=body.embedding_model,
        embedding_base_url=body.embedding_base_url,
        embedding_api_key=body.embedding_api_key,
        llm_daily_limit=body.llm_daily_limit,
        clear_llm_api_key=body.clear_llm_api_key,
        clear_embedding_api_key=body.clear_embedding_api_key,
    )

    parts = []
    if body.llm_model is not None:
        parts.append(f"llm_model={body.llm_model}")
    if body.llm_daily_limit is not None:
        parts.append(f"daily_limit={body.llm_daily_limit}")
    if body.llm_api_key:
        parts.append("llm_key=updated")
    if body.embedding_api_key:
        parts.append("embedding_key=updated")
    if body.clear_llm_api_key:
        parts.append("llm_key=cleared")
    if body.clear_embedding_api_key:
        parts.append("embedding_key=cleared")

    _log_ai_config(db, user, request, " ".join(parts) or "ai config updated")
    db.commit()

    out = AiConfigOut.model_validate(build_admin_config_view(cfg))
    return success(out.model_dump(mode="json"), message="AI 配置已更新")


@router.get("/usage")
def get_ai_usage(db: DbSession, user: AdminUser) -> dict:
    cfg = get_cached_runtime_ai_config()
    lookup = {}
    for item in list_models_payload(db)["chat_models"]:
        if item["id"] == cfg.llm_model:
            lookup = item
            break
    raw = build_usage_summary(
        daily_limit=cfg.llm_daily_limit,
        active_llm_model=cfg.llm_model,
        active_llm_model_name=lookup.get("name", cfg.llm_model),
    )
    out = AiUsageOut.model_validate(raw)
    return success(out.model_dump(mode="json"))


@router.get("/usage/students")
def get_student_ai_usage(
    db: DbSession,
    user: AdminUser,
    username: str | None = Query(None, description="学生用户名模糊匹配"),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
) -> dict:
    cfg = get_cached_runtime_ai_config()
    items, total = list_student_usage(
        db,
        username=username,
        page_num=page_num,
        page_size=page_size,
    )
    for item in items:
        item["daily_limit"] = cfg.llm_daily_limit
    page = PageResult(
        list=[StudentTokenUsageItem.model_validate(item) for item in items],
        total=total,
        page_num=page_num,
        page_size=page_size,
    )
    return success(page.model_dump(mode="json"))
