import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.deps import DbSession, require_roles
from app.core.exceptions import ERR_INTERNAL, ERR_NOT_FOUND, BusinessException
from app.core.security import get_redis
from app.models.material import CourseMaterial, MaterialChunk, MaterialStatus, MaterialType
from app.models.user import User, UserRole
from app.schemas.material import MaterialOut, MaterialStatusOut
from app.schemas.response import success
from app.services.course_access import ensure_teacher_course_access
from app.services.material_dispatch import dispatch_material_processing
from app.services.material_upload import (
    check_duplicate_or_linkable,
    normalize_original_name,
    remove_upload_file,
    validate_upload_content,
)
from app.services.vector_store import get_vector_store
from app.services.warehouse_service import resolve_warehouse_for_type

router = APIRouter(prefix="/materials", tags=["materials"])
settings = get_settings()

TeacherOrAdmin = Depends(require_roles(UserRole.teacher, UserRole.admin))

ALLOWED_EXT = {
    ".pdf": MaterialType.pdf,
    ".txt": MaterialType.txt,
    ".md": MaterialType.md,
    ".pptx": MaterialType.pptx,
}

MEDIA_TYPES = {
    MaterialType.pdf: "application/pdf",
    MaterialType.txt: "text/plain; charset=utf-8",
    MaterialType.md: "text/markdown; charset=utf-8",
    MaterialType.pptx: (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    ),
}


def _get_material_or_404(db: DbSession, material_id: int) -> CourseMaterial:
    material = (
        db.query(CourseMaterial)
        .filter(CourseMaterial.id == material_id, CourseMaterial.deleted == 0)
        .first()
    )
    if not material:
        raise BusinessException(ERR_NOT_FOUND, "资料不存在")
    return material


def _resolve_material_file(material: CourseMaterial) -> Path:
    file_path = Path(material.file_path)
    if not file_path.is_file():
        raise BusinessException(ERR_NOT_FOUND, "文件不存在或已被移除")
    upload_root = Path(settings.upload_dir).resolve()
    resolved = file_path.resolve()
    try:
        resolved.relative_to(upload_root)
    except ValueError as exc:
        raise BusinessException(40301, "非法文件路径") from exc
    return resolved


def _dispatch_process(material_id: int, background_tasks: BackgroundTasks) -> None:
    background_tasks.add_task(dispatch_material_processing, material_id)


def _create_material_record(
    db: DbSession,
    *,
    course_id: int,
    user_id: int,
    mat_type: MaterialType,
    file_path: str,
    original_name: str,
) -> CourseMaterial:
    warehouse_id = resolve_warehouse_for_type(db, mat_type)
    material = CourseMaterial(
        course_id=course_id,
        warehouse_id=warehouse_id,
        uploaded_by=user_id,
        type=mat_type,
        file_path=file_path,
        original_name=original_name,
        status=MaterialStatus.uploaded,
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    try:
        get_redis().set(
            f"material:status:{material.id}",
            MaterialStatus.uploaded.value,
            ex=86400,
        )
    except Exception:
        pass
    return material


@router.post("/upload")
async def upload_material(
    background_tasks: BackgroundTasks,
    db: DbSession,
    user: User = TeacherOrAdmin,
    course_id: int = Form(...),
    file: UploadFile = File(...),
):
    ensure_teacher_course_access(db, user, course_id)

    original_name = normalize_original_name(file.filename or "")
    suffix = Path(original_name).suffix.lower()
    if suffix not in ALLOWED_EXT:
        raise BusinessException(
            40001,
            "仅支持 pdf、txt、md、pptx 文件；PPT 请另存为 .pptx 或直接上传 .pptx",
        )

    content = await file.read()
    mat_type = ALLOWED_EXT[suffix]
    max_bytes = settings.max_upload_size_mb * 1024 * 1024

    try:
        validate_upload_content(content, mat_type, max_bytes)
    except BusinessException:
        raise
    except Exception as exc:
        raise BusinessException(40001, f"文件校验失败：{exc}") from exc

    link_source = check_duplicate_or_linkable(db, original_name, course_id)
    if link_source:
        material = _create_material_record(
            db,
            course_id=course_id,
            user_id=user.id,
            mat_type=link_source.type,
            file_path=link_source.file_path,
            original_name=original_name,
        )
        _dispatch_process(material.id, background_tasks)
        return success(
            {"material_id": material.id, "linked": True},
            message="检测到同名资料已存在，已关联到本课程，无需重复上传文件",
        )

    upload_root = Path(settings.upload_dir)
    upload_root.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    file_path = upload_root / stored_name

    try:
        file_path.write_bytes(content)
        material = _create_material_record(
            db,
            course_id=course_id,
            user_id=user.id,
            mat_type=mat_type,
            file_path=str(file_path),
            original_name=original_name,
        )
    except BusinessException:
        remove_upload_file(file_path)
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        remove_upload_file(file_path)
        raise BusinessException(ERR_INTERNAL, f"上传失败：数据库保存异常，请重新上传") from exc
    except Exception as exc:
        db.rollback()
        remove_upload_file(file_path)
        raise BusinessException(ERR_INTERNAL, f"上传失败：{exc}，请重新上传") from exc

    _dispatch_process(material.id, background_tasks)
    return success({"material_id": material.id, "linked": False})


@router.get("/{material_id}/download")
def download_material(material_id: int, db: DbSession, user: User = TeacherOrAdmin):
    """教师/管理员下载资料原文件；不对学生开放。"""
    material = _get_material_or_404(db, material_id)
    ensure_teacher_course_access(db, user, material.course_id)
    resolved = _resolve_material_file(material)
    return FileResponse(
        path=resolved,
        filename=material.original_name,
        media_type=MEDIA_TYPES.get(material.type, "application/octet-stream"),
    )


@router.get("/{material_id}/status")
def material_status(material_id: int, db: DbSession, user: User = TeacherOrAdmin):
    material = _get_material_or_404(db, material_id)
    ensure_teacher_course_access(db, user, material.course_id)

    cached = get_redis().get(f"material:status:{material_id}")
    status = cached or material.status.value
    return success(
        MaterialStatusOut(
            id=material.id, status=status, error_message=material.error_message
        ).model_dump()
    )


@router.get("")
def list_materials(
    db: DbSession,
    user: User = TeacherOrAdmin,
    course_id: int = Query(...),
):
    ensure_teacher_course_access(db, user, course_id)
    rows = (
        db.query(CourseMaterial)
        .filter(CourseMaterial.course_id == course_id, CourseMaterial.deleted == 0)
        .order_by(CourseMaterial.id.desc())
        .all()
    )
    return success(
        [MaterialOut.model_validate(r).model_dump(mode="json") for r in rows]
    )


@router.post("/{material_id}/retry")
def retry_material(
    material_id: int,
    background_tasks: BackgroundTasks,
    db: DbSession,
    user: User = TeacherOrAdmin,
):
    material = _get_material_or_404(db, material_id)
    ensure_teacher_course_access(db, user, material.course_id)
    if material.status != MaterialStatus.failed:
        raise BusinessException(40001, "仅 FAILED 状态可重试")

    material.status = MaterialStatus.uploaded
    material.error_message = None
    db.commit()
    get_redis().set(f"material:status:{material.id}", MaterialStatus.uploaded.value, ex=86400)
    _dispatch_process(material.id, background_tasks)
    return success({"material_id": material.id})


@router.delete("/{material_id}")
def delete_material(material_id: int, db: DbSession, user: User = TeacherOrAdmin):
    material = _get_material_or_404(db, material_id)
    ensure_teacher_course_access(db, user, material.course_id)

    material.deleted = 1
    db.query(MaterialChunk).filter(MaterialChunk.material_id == material.id).update(
        {"deleted": 1}
    )
    get_vector_store().delete_by_material(material.id)
    get_redis().delete(f"material:status:{material_id}")
    db.commit()
    return success(None, message="已删除")
