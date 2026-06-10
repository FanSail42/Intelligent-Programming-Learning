import request from './request'

export interface CodeIssue {
  line?: number | null
  message: string
  hint?: string | null
  explanation?: string | null
}

export interface LevelAnalysis {
  score: 'ok' | 'warning' | 'error'
  issues: CodeIssue[]
  suggestions: string[]
  stderr_hint?: string | null
}

export interface AnalysisResult {
  summary: string
  levels: {
    syntax: LevelAnalysis
    semantic: LevelAnalysis
    runtime: LevelAnalysis
  }
  fixed_code?: string | null
  examples: string[]
  truncated?: boolean
}

export interface CodeSubmission {
  id: number
  course_id?: number | null
  language: string
  source_code: string
  version: number
  created_at: string
}

export interface AnalysisOut {
  status: string
  result: AnalysisResult | null
  error_message?: string | null
}

export interface SubmitResult {
  submission: CodeSubmission
  analysis: AnalysisOut
}

export interface SubmissionListItem {
  id: number
  course_id?: number | null
  language: string
  version: number
  status: string
  summary: string | null
  created_at: string
}

export interface PageResult<T> {
  list: T[]
  total: number
  page_num: number
  page_size: number
}

export function submitCode(payload: {
  language: string
  source_code: string
}): Promise<SubmitResult> {
  return request.post('/api/v1/code/submit', payload, { timeout: 90000 })
}

export function getCodeResult(submissionId: number): Promise<SubmitResult> {
  return request.get(`/api/v1/code/submit/${submissionId}/result`)
}

export function listCodeSubmissions(
  page_num = 1,
  page_size = 10,
): Promise<PageResult<SubmissionListItem>> {
  return request.get('/api/v1/code/submissions', {
    params: { page_num, page_size },
  })
}
