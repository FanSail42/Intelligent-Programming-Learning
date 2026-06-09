import request from './request'

export interface Course {
  id: number
  name: string
  description: string | null
  teacher_id: number
  teacher_name: string
  status: string
  create_approval: string
  publish_approval: string
  published_at: string | null
  created_at: string
  updated_at: string
}

export interface PageResult<T> {
  list: T[]
  total: number
  page_num: number
  page_size: number
}

export interface MyCourseSearch {
  name?: string
  teacher_name?: string
  status?: string
  published_from?: string
  published_to?: string
  page_num?: number
  page_size?: number
}

export interface BrowseCourseSearch extends MyCourseSearch {
  course_id?: string
}

export interface BrowseCourse extends Course {
  enrolled: boolean
}

export function getMyCourses(params?: MyCourseSearch): Promise<PageResult<Course>> {
  return request.get('/api/v1/courses/my', { params })
}

export function browseCourses(params?: BrowseCourseSearch): Promise<PageResult<BrowseCourse>> {
  return request.get('/api/v1/courses/browse', { params })
}

export interface CourseListSearch {
  course_id?: string
  name?: string
  teacher_name?: string
  status?: string
  published_from?: string
  published_to?: string
  page_num?: number
  page_size?: number
  pending_only?: boolean
}

export function getCourses(params?: CourseListSearch): Promise<PageResult<Course>> {
  return request.get('/api/v1/courses', { params })
}

export interface TeacherOption {
  id: number
  username: string
}

export function getTeachers(): Promise<TeacherOption[]> {
  return request.get('/api/v1/courses/teachers')
}

export function createCourse(data: {
  name: string
  description?: string
  status?: string
  teacher_id?: number
}): Promise<Course> {
  return request.post('/api/v1/courses', data)
}

export function updateCourse(
  id: number,
  data: { name?: string; description?: string; status?: string },
): Promise<Course> {
  return request.put(`/api/v1/courses/${id}`, data)
}

export function requestPublishCourse(id: number): Promise<Course> {
  return request.post(`/api/v1/courses/${id}/request-publish`)
}

export function approveCreateCourse(id: number, approved: boolean): Promise<Course> {
  return request.post(`/api/v1/courses/${id}/approve-create`, { approved })
}

export function approvePublishCourse(id: number, approved: boolean): Promise<Course> {
  return request.post(`/api/v1/courses/${id}/approve-publish`, { approved })
}

export function deleteCourse(id: number): Promise<null> {
  return request.delete(`/api/v1/courses/${id}`)
}

export function joinCourse(id: number): Promise<null> {
  return request.post(`/api/v1/courses/${id}/join`)
}

export function leaveCourse(id: number): Promise<null> {
  return request.post(`/api/v1/courses/${id}/leave`)
}

export const STATUS_LABELS: Record<string, string> = {
  draft: '草稿',
  published: '已发布',
  archived: '已归档',
}

export const CREATE_APPROVAL_LABELS: Record<string, string> = {
  pending: '待审核',
  approved: '已通过',
  rejected: '已驳回',
}

export const PUBLISH_APPROVAL_LABELS: Record<string, string> = {
  none: '-',
  pending: '待审核',
  approved: '已通过',
  rejected: '已驳回',
}
