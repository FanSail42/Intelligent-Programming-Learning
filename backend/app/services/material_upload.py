"""Course material upload helpers: validation, dedup, file cleanup."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.core.exceptions import ERR_MATERIAL_DUPLICATE, BusinessException
from app.models.material import CourseMaterial, MaterialType

MAX_UPLOAD_BYTES = 10 * 1024 * 1024

PDF_INVALID_MSG = (
    "文件不是有效的 PDF。"
    "若由 PPT 转换而来，请勿直接修改扩展名；"
    "请使用 PowerPoint「文件→导出→PDF」或「另存为 PDF」，"
    "也可直接上传 .pptx 文件。"
)

PPT_DISGUISED_MSG = (
    "该文件实为 PPT/PPTX 格式但使用了 .pdf 扩展名。"
    "请直接上传 .pptx 文件，或使用 PowerPoint 正确导出为 PDF。"
)


def normalize_original_name(filename: str) -> str:
    name = (filename or "").strip()
    if not name:
        raise BusinessException(40001, "文件名不能为空")
    return name


def validate_file_size(content: bytes, max_bytes: int = MAX_UPLOAD_BYTES) -> None:
    if len(content) > max_bytes:
        raise BusinessException(40001, f"文件大小不能超过 {max_bytes // (1024 * 1024)}MB")


def validate_pdf_content(content: bytes) -> None:
    if len(content) < 5 or not content.startswith(b"%PDF-"):
        if content[:2] == b"PK":
            raise BusinessException(40001, PPT_DISGUISED_MSG)
        if content[:4] == b"\xd0\xcf\x11\xe0":
            raise BusinessException(40001, PPT_DISGUISED_MSG)
        raise BusinessException(40001, PDF_INVALID_MSG)


def validate_upload_content(
    content: bytes,
    mat_type: MaterialType,
    max_bytes: int = MAX_UPLOAD_BYTES,
) -> None:
    validate_file_size(content, max_bytes)
    if mat_type == MaterialType.pdf:
        validate_pdf_content(content)


def find_materials_by_name(db: Session, original_name: str) -> list[CourseMaterial]:
    return (
        db.query(CourseMaterial)
        .filter(
            CourseMaterial.original_name == original_name,
            CourseMaterial.deleted == 0,
        )
        .order_by(CourseMaterial.id.asc())
        .all()
    )


def check_duplicate_or_linkable(
    db: Session,
    original_name: str,
    course_id: int,
) -> CourseMaterial | None:
    """
    Return an existing material to link (same name, other course).
    Raise if the same name already exists in the target course.
    """
    existing = find_materials_by_name(db, original_name)
    if not existing:
        return None

    for row in existing:
        if row.course_id == course_id:
            raise BusinessException(
                ERR_MATERIAL_DUPLICATE,
                f"资料「{original_name}」已存在于本课程，"
                f"请修改上传文件名，或先删除同名资料后再上传。",
                data={"original_name": original_name, "material_id": row.id},
            )

    return existing[0]


def remove_upload_file(file_path: Path | str | None) -> None:
    if not file_path:
        return
    path = Path(file_path)
    if path.is_file():
        path.unlink(missing_ok=True)
