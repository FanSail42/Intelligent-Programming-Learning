from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.deps import DbSession, require_roles
from app.models.user import User, UserRole
from app.schemas.teacher import TeacherCourseOverviewOut
from app.schemas.response import success
from app.services.course_access import ensure_teacher_course_access
from app.services.teacher_stats import build_teacher_course_overview

router = APIRouter(prefix="/teacher", tags=["teacher"])

TeacherUser = Annotated[User, Depends(require_roles(UserRole.teacher, UserRole.admin))]


@router.get("/courses/{course_id}/overview")
def get_course_overview(
    course_id: int,
    db: DbSession,
    user: TeacherUser,
    days: int = Query(7, ge=7, le=30),
) -> dict:
    course = ensure_teacher_course_access(db, user, course_id)
    raw = build_teacher_course_overview(db, course, days=days)
    out = TeacherCourseOverviewOut.model_validate(raw)
    return success(out.model_dump(mode="json"))
