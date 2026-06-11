import request from './request'

export interface DashboardSummary {
  total_events_7d: number
  wrong_count: number
  mastered_count: number
}

export interface WeakKpItem {
  kp_id: number
  name: string
  score: number
  course_id: number
}

export interface RecentEventItem {
  event_type: string
  course_id: number | null
  course_name?: string | null
  kp_id?: number | null
  kp_name?: string | null
  title?: string | null
  detail?: string | null
  icon?: string | null
  tone?: string | null
  created_at: string
}

export interface DashboardData {
  summary: DashboardSummary
  weak_kps: WeakKpItem[]
  recent_events: RecentEventItem[]
}

export interface WrongBookItem {
  id: number
  source_type: string
  ref_id: number
  course_id: number | null
  kp_id: number | null
  kp_name: string | null
  language: string | null
  summary: string | null
  category: string | null
  category_label: string | null
  issues: Array<{ level: string; line?: number | null; message: string; explanation?: string | null }>
  suggestions: string[]
  review_tip: string | null
  has_fixed_code: boolean
  mastered: boolean
  created_at: string
}

export interface WrongBookCategoryStat {
  category: string
  label: string
  total: number
  unmastered: number
  analysis: string
  sample_issues: string[]
}

export interface WrongBookStats {
  summary: {
    total: number
    mastered: number
    unmastered: number
    mastery_rate: number
  }
  by_category: WrongBookCategoryStat[]
  by_source: Array<{ source_type: string; label: string; count: number }>
  by_language: Array<{ language: string; count: number }>
  by_kp: Array<{ kp_id: number; kp_name: string; total: number; unmastered: number }>
  trend: Array<{ date: string; count: number }>
  mastered_pie: Array<{ name: string; value: number }>
}

export type RecommendationActionType = 'review_wrong_book' | 'review_material' | 'practice_code'
export type RecommendationPriority = 'high' | 'medium' | 'low'

export interface RecommendationItem {
  kp_id: number | null
  kp_name: string | null
  score: number
  wrong_count: number
  action_type: RecommendationActionType
  priority: RecommendationPriority
  material_id: number | null
  material_name: string | null
  reason: string
}

export interface PageResult<T> {
  list: T[]
  total: number
  page_num: number
  page_size: number
}

export function getDashboard(courseId?: number): Promise<DashboardData> {
  return request.get('/api/v1/learning/dashboard', {
    params: courseId ? { course_id: courseId } : undefined,
  })
}

export function listWrongBook(params?: {
  course_id?: number
  mastered?: boolean
  category?: string
  page_num?: number
  page_size?: number
}): Promise<PageResult<WrongBookItem>> {
  return request.get('/api/v1/learning/wrong-book', { params })
}

export function getWrongBookStats(params?: {
  course_id?: number
  days?: number
}): Promise<WrongBookStats> {
  return request.get('/api/v1/learning/wrong-book/stats', { params })
}

export function updateWrongBookMastered(
  id: number,
  mastered: boolean,
): Promise<{ id: number; mastered: boolean }> {
  return request.put(`/api/v1/learning/wrong-book/${id}/mastered`, { mastered })
}

export function getRecommendations(courseId: number): Promise<RecommendationItem[]> {
  return request.get('/api/v1/learning/recommendations', {
    params: { course_id: courseId },
  })
}
