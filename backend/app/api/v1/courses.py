from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import String, cast
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, DbSession, require_roles
from app.core.exceptions import ERR_FORBIDDEN, ERR_NOT_FOUND, ERR_VALIDATION, BusinessException
from app.models.course import (
    Course,
    CourseCreateApproval,
    CoursePublishApproval,
    CourseStatus,
    CourseStudent,
    CourseTeacher,
)
from app.models.user import User, UserRole, UserStatus
from app.schemas.course import CourseApprovalAction, CourseCreate, CourseOut, CourseUpdate
from app.schemas.response import PageResult, success

router = APIRouter(prefix="/courses", tags=["courses"])

TeacherOrAdmin = Depends(require_roles(UserRole.teacher, UserRole.admin))
AdminOnly = Depends(require_roles(UserRole.admin))
StudentOnly = Depends(require_roles(UserRole.student))


def _format_datetime(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.strftime("%Y/%m/%d %H-%M-%S")


def _parse_datetime_param(value: str, end_of_day: bool = False) -> datetime:
    value = value.strip()
    for fmt in ("%Y/%m/%d %H-%M-%S", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value, fmt)
            if fmt in ("%Y/%m/%d", "%Y-%m-%d") and end_of_day:
                return dt.replace(hour=23, minute=59, second=59)
            return dt
        except ValueError:
            continue
    raise BusinessException(ERR_VALIDATION, "时间格式无效，请使用 yyyy/mm/dd 或 yyyy/mm/dd hh-mm-ss")


def _get_teacher_name(db: Session, teacher_id: int) -> str:
    teacher = db.query(User).filter(User.id == teacher_id, User.deleted == 0).first()
    return teacher.username if teacher else ""


def _course_to_out(db: Session, course: Course) -> dict:
    out = CourseOut(
        id=course.id,
        name=course.name,
        description=course.description,
        teacher_id=course.teacher_id,
        teacher_name=_get_teacher_name(db, course.teacher_id),
        status=course.status.value,
        create_approval=course.create_approval.value,
        publish_approval=course.publish_approval.value,
        published_at=_format_datetime(course.published_at),
        created_at=course.created_at,
        updated_at=course.updated_at,
    )
    return out.model_dump(mode="json")


def _get_course_or_404(db: Session, course_id: int) -> Course:
    course = db.query(Course).filter(Course.id == course_id, Course.deleted == 0).first()
    if not course:
        raise BusinessException(ERR_NOT_FOUND, "课程不存在")
    return course


def _can_manage_course(user: User, course: Course) -> bool:
    return user.role == UserRole.admin or course.teacher_id == user.id


def _resolve_teacher_id(db: Session, user: User, body: CourseCreate) -> int:
    if user.role == UserRole.teacher:
        return user.id
    if body.teacher_id is None:
        raise BusinessException(ERR_VALIDATION, "请选择授课教师")
    teacher = (
        db.query(User)
        .filter(
            User.id == body.teacher_id,
            User.role == UserRole.teacher,
            User.status == UserStatus.active,
            User.deleted == 0,
        )
        .first()
    )
    if not teacher:
        raise BusinessException(ERR_VALIDATION, "授课教师不存在或无效")
    return teacher.id


def _apply_admin_publish(course: Course, status: CourseStatus) -> None:
    course.status = status
    if status == CourseStatus.published:
        course.published_at = datetime.now()
        course.publish_approval = CoursePublishApproval.approved
    elif status != CourseStatus.published:
        course.published_at = None
        if course.publish_approval != CoursePublishApproval.pending:
            course.publish_approval = CoursePublishApproval.none


@router.get("")
def list_courses(
    db: DbSession,
    user: User = TeacherOrAdmin,
    course_id: str | None = Query(None, description="课程 ID，模糊匹配"),
    name: str | None = Query(None, description="课程名称，模糊匹配"),
    teacher_name: str | None = Query(None, description="授课教师姓名，模糊匹配"),
    status: CourseStatus | None = Query(None, description="课程状态"),
    published_from: str | None = Query(None, description="发布时间起"),
    published_to: str | None = Query(None, description="发布时间止"),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    pending_only: bool = Query(False),
):
    query = db.query(Course).filter(Course.deleted == 0)
    if user.role == UserRole.teacher:
        query = query.filter(Course.teacher_id == user.id)
    elif pending_only:
        query = query.filter(
            (Course.create_approval == CourseCreateApproval.pending)
            | (Course.publish_approval == CoursePublishApproval.pending)
        )

    query = _apply_course_search_filters(
        query,
        course_id=course_id,
        name=name,
        teacher_name=teacher_name,
        status=status,
        published_from=published_from,
        published_to=published_to,
    )

    total = query.count()
    items = (
        query.order_by(Course.id.desc())
        .offset((page_num - 1) * page_size)
        .limit(page_size)
        .all()
    )
    data = PageResult(
        list=[_course_to_out(db, c) for c in items],
        total=total,
        page_num=page_num,
        page_size=page_size,
    )
    return success(data.model_dump())


@router.get("/teachers")
def list_teachers(db: DbSession, user: User = TeacherOrAdmin):
    teachers = (
        db.query(User)
        .filter(
            User.role == UserRole.teacher,
            User.status == UserStatus.active,
            User.deleted == 0,
        )
        .order_by(User.id)
        .all()
    )
    return success([{"id": t.id, "username": t.username} for t in teachers])


@router.post("")
def create_course(body: CourseCreate, db: DbSession, user: User = TeacherOrAdmin):
    teacher_id = _resolve_teacher_id(db, user, body)
    is_admin = user.role == UserRole.admin

    if is_admin:
        create_approval = CourseCreateApproval.approved
        status = body.status
        published_at = datetime.now() if status == CourseStatus.published else None
        publish_approval = (
            CoursePublishApproval.approved
            if status == CourseStatus.published
            else CoursePublishApproval.none
        )
    else:
        create_approval = CourseCreateApproval.pending
        status = CourseStatus.draft
        published_at = None
        publish_approval = CoursePublishApproval.none

    course = Course(
        name=body.name,
        description=body.description,
        teacher_id=teacher_id,
        status=status,
        create_approval=create_approval,
        publish_approval=publish_approval,
        published_at=published_at,
    )
    db.add(course)
    db.flush()
    db.add(CourseTeacher(course_id=course.id, user_id=teacher_id))
    db.commit()
    db.refresh(course)

    message = None
    if not is_admin:
        message = "已提交审核，请等待管理员批准"
    return success(_course_to_out(db, course), message=message)


def _apply_course_search_filters(
    query,
    *,
    name: str | None,
    teacher_name: str | None,
    status: CourseStatus | None,
    published_from: str | None,
    published_to: str | None,
    course_id: str | None = None,
):
    if course_id and course_id.strip():
        query = query.filter(cast(Course.id, String).like(f"%{course_id.strip()}%"))
    if name:
        query = query.filter(Course.name.like(f"%{name.strip()}%"))
    if teacher_name:
        query = query.join(User, User.id == Course.teacher_id).filter(
            User.deleted == 0,
            User.username.like(f"%{teacher_name.strip()}%"),
        )
    if status:
        query = query.filter(Course.status == status)
    if published_from:
        query = query.filter(Course.published_at >= _parse_datetime_param(published_from))
    if published_to:
        query = query.filter(
            Course.published_at <= _parse_datetime_param(published_to, end_of_day=True)
        )
    return query


def _apply_my_course_filters(
    query,
    *,
    name: str | None,
    teacher_name: str | None,
    status: CourseStatus | None,
    published_from: str | None,
    published_to: str | None,
):
    return _apply_course_search_filters(
        query,
        name=name,
        teacher_name=teacher_name,
        status=status,
        published_from=published_from,
        published_to=published_to,
    )


@router.get("/my")
def my_courses(
    db: DbSession,
    user: CurrentUser,
    name: str | None = Query(None, description="课程名称，模糊匹配"),
    teacher_name: str | None = Query(None, description="授课教师姓名，模糊匹配"),
    status: CourseStatus | None = Query(None, description="课程状态"),
    published_from: str | None = Query(None, description="发布时间起"),
    published_to: str | None = Query(None, description="发布时间止"),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    if user.role == UserRole.student:
        query = (
            db.query(Course)
            .join(CourseStudent, CourseStudent.course_id == Course.id)
            .filter(
                CourseStudent.user_id == user.id,
                CourseStudent.deleted == 0,
                Course.deleted == 0,
            )
        )
    elif user.role == UserRole.teacher:
        query = db.query(Course).filter(Course.teacher_id == user.id, Course.deleted == 0)
    else:
        query = db.query(Course).filter(Course.deleted == 0)

    query = _apply_my_course_filters(
        query,
        name=name,
        teacher_name=teacher_name,
        status=status,
        published_from=published_from,
        published_to=published_to,
    )

    total = query.count()
    rows = (
        query.order_by(Course.id.desc())
        .offset((page_num - 1) * page_size)
        .limit(page_size)
        .all()
    )
    data = PageResult(
        list=[_course_to_out(db, c) for c in rows],
        total=total,
        page_num=page_num,
        page_size=page_size,
    )
    return success(data.model_dump())


@router.get("/browse")
def browse_courses(
    db: DbSession,
    user: User = StudentOnly,
    course_id: str | None = Query(None, description="课程 ID，模糊匹配"),
    name: str | None = Query(None, description="课程名称，模糊匹配"),
    teacher_name: str | None = Query(None, description="授课教师姓名，模糊匹配"),
    published_from: str | None = Query(None, description="发布时间起"),
    published_to: str | None = Query(None, description="发布时间止"),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    query = db.query(Course).filter(
        Course.deleted == 0,
        Course.status == CourseStatus.published,
        Course.create_approval == CourseCreateApproval.approved,
    )
    query = _apply_course_search_filters(
        query,
        course_id=course_id,
        name=name,
        teacher_name=teacher_name,
        status=None,
        published_from=published_from,
        published_to=published_to,
    )

    enrolled_ids = {
        row[0]
        for row in db.query(CourseStudent.course_id)
        .filter(CourseStudent.user_id == user.id, CourseStudent.deleted == 0)
        .all()
    }

    total = query.count()
    items = (
        query.order_by(Course.id.desc())
        .offset((page_num - 1) * page_size)
        .limit(page_size)
        .all()
    )
    course_list = []
    for course in items:
        item = _course_to_out(db, course)
        item["enrolled"] = course.id in enrolled_ids
        course_list.append(item)

    data = PageResult(
        list=course_list,
        total=total,
        page_num=page_num,
        page_size=page_size,
    )
    return success(data.model_dump())


@router.get("/{course_id}")
def get_course(course_id: int, db: DbSession, user: CurrentUser):
    course = _get_course_or_404(db, course_id)
    return success(_course_to_out(db, course))


@router.put("/{course_id}")
def update_course(
    course_id: int,
    body: CourseUpdate,
    db: DbSession,
    user: User = TeacherOrAdmin,
):
    course = _get_course_or_404(db, course_id)
    if not _can_manage_course(user, course):
        raise BusinessException(ERR_FORBIDDEN, "无权限访问")

    if body.name is not None:
        course.name = body.name
    if body.description is not None:
        course.description = body.description
    if body.status is not None:
        if user.role == UserRole.teacher:
            if body.status == CourseStatus.published:
                raise BusinessException(ERR_VALIDATION, "请使用「申请发布」提交审核")
            course.status = body.status
            if body.status != CourseStatus.published:
                course.published_at = None
        else:
            _apply_admin_publish(course, body.status)

    db.commit()
    db.refresh(course)
    return success(_course_to_out(db, course))


@router.post("/{course_id}/request-publish")
def request_publish(course_id: int, db: DbSession, user: User = TeacherOrAdmin):
    course = _get_course_or_404(db, course_id)
    if user.role != UserRole.teacher or course.teacher_id != user.id:
        raise BusinessException(ERR_FORBIDDEN, "无权限访问")
    if course.create_approval != CourseCreateApproval.approved:
        raise BusinessException(ERR_VALIDATION, "课程新建尚未通过审核，无法申请发布")
    if course.status == CourseStatus.published:
        raise BusinessException(ERR_VALIDATION, "课程已发布")
    if course.publish_approval == CoursePublishApproval.pending:
        raise BusinessException(ERR_VALIDATION, "发布申请审核中，请耐心等待")

    course.publish_approval = CoursePublishApproval.pending
    db.commit()
    db.refresh(course)
    return success(_course_to_out(db, course), message="发布申请已提交，请等待管理员审核")


@router.post("/{course_id}/approve-create")
def approve_create(
    course_id: int,
    body: CourseApprovalAction,
    db: DbSession,
    user: User = AdminOnly,
):
    course = _get_course_or_404(db, course_id)
    if course.create_approval != CourseCreateApproval.pending:
        raise BusinessException(ERR_VALIDATION, "该课程不在新建审核中")

    course.create_approval = (
        CourseCreateApproval.approved if body.approved else CourseCreateApproval.rejected
    )
    db.commit()
    db.refresh(course)
    message = "新建审核已通过" if body.approved else "新建审核已驳回"
    return success(_course_to_out(db, course), message=message)


@router.post("/{course_id}/approve-publish")
def approve_publish(
    course_id: int,
    body: CourseApprovalAction,
    db: DbSession,
    user: User = AdminOnly,
):
    course = _get_course_or_404(db, course_id)
    if course.publish_approval != CoursePublishApproval.pending:
        raise BusinessException(ERR_VALIDATION, "该课程不在发布审核中")

    if body.approved:
        course.publish_approval = CoursePublishApproval.approved
        course.status = CourseStatus.published
        course.published_at = datetime.now()
    else:
        course.publish_approval = CoursePublishApproval.rejected

    db.commit()
    db.refresh(course)
    message = "发布审核已通过" if body.approved else "发布审核已驳回"
    return success(_course_to_out(db, course), message=message)


@router.delete("/{course_id}")
def delete_course(course_id: int, db: DbSession, user: User = TeacherOrAdmin):
    course = _get_course_or_404(db, course_id)
    if not _can_manage_course(user, course):
        raise BusinessException(ERR_FORBIDDEN, "无权限访问")

    course.deleted = 1
    db.commit()
    return success(None, message="已删除")


@router.post("/{course_id}/join")
def join_course(course_id: int, db: DbSession, user: User = StudentOnly):
    course = _get_course_or_404(db, course_id)
    if course.create_approval != CourseCreateApproval.approved:
        raise BusinessException(ERR_VALIDATION, "课程未通过审核，无法选课")
    if course.status != CourseStatus.published:
        raise BusinessException(ERR_VALIDATION, "课程未发布，无法选课")

    exists = (
        db.query(CourseStudent)
        .filter(
            CourseStudent.course_id == course_id,
            CourseStudent.user_id == user.id,
            CourseStudent.deleted == 0,
        )
        .first()
    )
    if exists:
        raise BusinessException(ERR_VALIDATION, "已选过该课程")

    enrollment = CourseStudent(course_id=course_id, user_id=user.id)
    db.add(enrollment)
    db.commit()
    return success(None, message="选课成功")


@router.post("/{course_id}/leave")
def leave_course(course_id: int, db: DbSession, user: User = StudentOnly):
    _get_course_or_404(db, course_id)
    enrollment = (
        db.query(CourseStudent)
        .filter(
            CourseStudent.course_id == course_id,
            CourseStudent.user_id == user.id,
            CourseStudent.deleted == 0,
        )
        .first()
    )
    if not enrollment:
        raise BusinessException(ERR_VALIDATION, "未选该课程，无法退课")

    enrollment.deleted = 1
    db.commit()
    return success(None, message="退课成功")
