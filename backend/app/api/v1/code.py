from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.deps import CurrentUser, DbSession, require_roles
from app.core.exceptions import ERR_NOT_FOUND, ERR_VALIDATION, BusinessException
from app.core.rate_limit import check_llm_rate_limit
from app.models.code import AnalysisResult, AnalysisStatus, CodeSubmission
from app.models.learning import KnowledgePoint
from app.models.user import User, UserRole
from app.schemas.code_analysis import (
    AnalysisOut,
    CodeSubmitRequest,
    SubmitResultOut,
    SubmissionListItem,
    SubmissionOut,
)
from app.schemas.response import PageResult, success
from app.services.code_analysis import analyze_source_code, validate_language
from app.services.code_helpers import enum_to_str, extract_summary, validate_result_data
from app.services.learning_events import after_code_submission, resolve_default_kp

router = APIRouter(prefix="/code", tags=["code"])

StudentUser = Annotated[User, Depends(require_roles(UserRole.student))]


def _get_submission_for_user(db: DbSession, submission_id: int, user: User) -> CodeSubmission:
    submission = (
        db.query(CodeSubmission)
        .filter(CodeSubmission.id == submission_id, CodeSubmission.deleted == 0)
        .first()
    )
    if not submission:
        raise BusinessException(ERR_NOT_FOUND, "提交记录不存在")
    if user.role != UserRole.admin and submission.user_id != user.id:
        raise BusinessException(ERR_NOT_FOUND, "提交记录不存在")
    return submission


def _build_analysis_out(analysis: AnalysisResult | None) -> AnalysisOut:
    if not analysis:
        return AnalysisOut(status=AnalysisStatus.pending.value, result=None, error_message=None)
    result_data = validate_result_data(analysis.result_json)
    return AnalysisOut(
        status=enum_to_str(analysis.status),
        result=result_data,
        error_message=analysis.error_message,
    )


def _submission_to_out(submission: CodeSubmission) -> SubmissionOut:
    return SubmissionOut(
        id=submission.id,
        course_id=submission.course_id,
        language=enum_to_str(submission.language),
        source_code=submission.source_code,
        version=submission.version,
        created_at=submission.created_at,
    )


@router.post("/submit")
async def submit_code(
    body: CodeSubmitRequest,
    db: DbSession,
    user: StudentUser,
) -> dict:
    try:
        lang = validate_language(body.language)
    except ValueError as exc:
        raise BusinessException(ERR_VALIDATION, str(exc)) from exc

    check_llm_rate_limit(user.id)

    prev_count = (
        db.query(CodeSubmission)
        .filter(
            CodeSubmission.user_id == user.id,
            CodeSubmission.deleted == 0,
        )
        .count()
    )

    submission = CodeSubmission(
        user_id=user.id,
        course_id=None,
        language=lang,
        source_code=body.source_code,
        version=prev_count + 1,
    )
    db.add(submission)
    db.flush()

    analysis = AnalysisResult(
        submission_id=submission.id,
        status=AnalysisStatus.running,
    )
    db.add(analysis)
    db.flush()

    try:
        result = await analyze_source_code(
            user_id=user.id,
            language=lang.value,
            source_code=body.source_code,
        )
        analysis.status = AnalysisStatus.done
        analysis.result_json = result.model_dump()
        analysis.error_message = None
    except ValueError as exc:
        analysis.status = AnalysisStatus.failed
        analysis.error_message = str(exc)[:512]
        analysis.result_json = None
    except Exception:
        analysis.status = AnalysisStatus.failed
        analysis.error_message = "代码分析服务异常，请稍后重试"
        analysis.result_json = None

    default_kp = resolve_default_kp(db, user.id)
    after_code_submission(
        db,
        user_id=user.id,
        submission=submission,
        analysis=analysis,
        default_kp_id=default_kp.id if default_kp else None,
    )

    db.commit()
    db.refresh(submission)
    db.refresh(analysis)

    payload = SubmitResultOut(
        submission=_submission_to_out(submission),
        analysis=_build_analysis_out(analysis),
    )
    return success(payload.model_dump(mode="json"))


@router.get("/submit/{submission_id}/result")
async def get_submit_result(
    submission_id: int,
    db: DbSession,
    user: CurrentUser,
) -> dict:
    submission = _get_submission_for_user(db, submission_id, user)
    analysis = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.submission_id == submission_id, AnalysisResult.deleted == 0)
        .first()
    )
    payload = SubmitResultOut(
        submission=_submission_to_out(submission),
        analysis=_build_analysis_out(analysis),
    )
    return success(payload.model_dump(mode="json"))


@router.get("/submissions")
async def list_submissions(
    db: DbSession,
    user: StudentUser,
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
) -> dict:
    base_filter = (
        CodeSubmission.user_id == user.id,
        CodeSubmission.deleted == 0,
    )
    total = db.query(CodeSubmission).filter(*base_filter).count()

    submissions = (
        db.query(CodeSubmission)
        .filter(*base_filter)
        .order_by(CodeSubmission.id.desc())
        .offset((page_num - 1) * page_size)
        .limit(page_size)
        .all()
    )

    submission_ids = [s.id for s in submissions]
    analysis_map: dict[int, AnalysisResult] = {}
    if submission_ids:
        analyses = (
            db.query(AnalysisResult)
            .filter(
                AnalysisResult.submission_id.in_(submission_ids),
                AnalysisResult.deleted == 0,
            )
            .all()
        )
        analysis_map = {row.submission_id: row for row in analyses}

    items: list[SubmissionListItem] = []
    for submission in submissions:
        analysis = analysis_map.get(submission.id)
        status = AnalysisStatus.pending.value
        summary = None
        if analysis:
            status = enum_to_str(analysis.status)
            summary = extract_summary(analysis.result_json)
        items.append(
            SubmissionListItem(
                id=submission.id,
                course_id=submission.course_id,
                language=enum_to_str(submission.language),
                version=submission.version,
                status=status,
                summary=summary,
                created_at=submission.created_at,
            )
        )

    page = PageResult(
        list=items,
        total=total,
        page_num=page_num,
        page_size=page_size,
    )
    return success(page.model_dump(mode="json"))
