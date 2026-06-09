from sqlalchemy.orm import Session

from app.core.exceptions import ERR_FORBIDDEN, ERR_NOT_FOUND, BusinessException
from app.models.course import Course, CourseStudent
from app.models.user import User, UserRole


def get_course_or_404(db: Session, course_id: int) -> Course:
    course = db.query(Course).filter(Course.id == course_id, Course.deleted == 0).first()
    if not course:
        raise BusinessException(ERR_NOT_FOUND, "课程不存在")
    return course


def ensure_teacher_course_access(db: Session, user: User, course_id: int) -> Course:
    course = get_course_or_404(db, course_id)
    if user.role == UserRole.admin:
        return course
    if user.role == UserRole.teacher and course.teacher_id == user.id:
        return course
    raise BusinessException(ERR_FORBIDDEN, "无权限访问该课程")


def ensure_student_enrolled(db: Session, user: User, course_id: int) -> Course:
    course = get_course_or_404(db, course_id)
    if user.role == UserRole.admin:
        return course
    enrolled = (
        db.query(CourseStudent)
        .filter(
            CourseStudent.course_id == course_id,
            CourseStudent.user_id == user.id,
            CourseStudent.deleted == 0,
        )
        .first()
    )
    if not enrolled:
        raise BusinessException(ERR_FORBIDDEN, "未选该课程，无法访问")
    return course


def ensure_chat_access(db: Session, user: User, course_id: int) -> Course:
    if user.role == UserRole.student:
        return ensure_student_enrolled(db, user, course_id)
    if user.role in (UserRole.teacher, UserRole.admin):
        return ensure_teacher_course_access(db, user, course_id)
    raise BusinessException(ERR_FORBIDDEN, "无权限访问")
