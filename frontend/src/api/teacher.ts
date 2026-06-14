import request from './request'
import type { WeakKpItem, WrongBookStats } from './learning'

export interface TeacherOverviewSummary {
  student_count: number
  active_students_7d: number
  total_events_7d: number
  wrong_total: number
  wrong_unmastered: number
  mastery_rate: number
}

export interface EventTrendItem {
  date: string
  count: number
}

export interface EnrolledStudentItem {
  user_id: number
  username: string
  joined_at: string
  wrong_count: number
  unmastered_count: number
}

export interface TeacherCourseOverview {
  course: {
    id: number
    name: string
    teacher_id: number
    teacher_name: string
  }
  summary: TeacherOverviewSummary
  students: EnrolledStudentItem[]
  wrong_book_stats: WrongBookStats
  weak_kps: WeakKpItem[]
  event_trend: EventTrendItem[]
}

export function getTeacherCourseOverview(
  courseId: number,
  days = 7,
): Promise<TeacherCourseOverview> {
  return request.get(`/api/v1/teacher/courses/${courseId}/overview`, {
    params: { days },
  })
}
