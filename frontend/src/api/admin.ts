import request from './request'

export interface AdminUser {
  id: number
  username: string
  role: 'student' | 'teacher'
  status: 'active' | 'disabled'
  created_at: string
  updated_at: string
}

export interface PageResult<T> {
  list: T[]
  total: number
  page_num: number
  page_size: number
}

export interface RoleCountSummary {
  total: number
  active: number
  disabled: number
}

export interface AdminOverview {
  students: RoleCountSummary
  teachers: RoleCountSummary
  courses: { total: number; published: number }
  enrollment_total: number
  login_events_7d: number
  recent_logs: OperationLogItem[]
}

export interface OperationLogItem {
  id: number
  user_id: number | null
  username: string | null
  action: string
  action_label: string
  ip: string | null
  detail: string | null
  created_at: string
}

export interface AdminUserSearch {
  role: 'student' | 'teacher'
  username?: string
  status?: 'active' | 'disabled'
  page_num?: number
  page_size?: number
}

export interface AdminUserCreatePayload {
  username: string
  password: string
  role: 'student' | 'teacher'
}

export interface AdminUserUpdatePayload {
  status?: 'active' | 'disabled'
  password?: string
}

export interface AdminLogSearch {
  action?: string
  username?: string
  page_num?: number
  page_size?: number
}

export const STATUS_LABELS: Record<string, string> = {
  active: '正常',
  disabled: '已禁用',
}

export const LOG_ACTION_LABELS: Record<string, string> = {
  login: '用户登录',
  user_create: '创建账号',
  user_update: '更新账号',
  user_delete: '删除账号',
  ai_config_update: '更新 AI 配置',
}

export function getAdminOverview(): Promise<AdminOverview> {
  return request.get('/api/v1/admin/overview')
}

export function listAdminLogs(params?: AdminLogSearch): Promise<PageResult<OperationLogItem>> {
  return request.get('/api/v1/admin/logs', { params })
}

export function listAdminUsers(params: AdminUserSearch): Promise<PageResult<AdminUser>> {
  return request.get('/api/v1/admin/users', { params })
}

export function createAdminUser(data: AdminUserCreatePayload): Promise<AdminUser> {
  return request.post('/api/v1/admin/users', data)
}

export function updateAdminUser(
  id: number,
  data: AdminUserUpdatePayload,
  role: 'student' | 'teacher',
): Promise<AdminUser> {
  return request.put(`/api/v1/admin/users/${id}`, data, { params: { role } })
}

export function deleteAdminUser(id: number, role: 'student' | 'teacher'): Promise<void> {
  return request.delete(`/api/v1/admin/users/${id}`, { params: { role } })
}

export interface AiModelItem {
  id: string
  name: string
  provider: string
  category: string
  tier?: string
  context_k?: number
  dimensions?: number
  description: string
  recommended?: boolean
  custom?: boolean
}

export interface AiModelCatalog {
  provider: string
  console_url: string
  docs_url: string
  api_key_url: string
  default_llm_base_url: string
  default_embedding_base_url: string
  chat_models: AiModelItem[]
  embedding_models: AiModelItem[]
  custom_chat_models: AiModelItem[]
}

export interface AiConfig {
  llm_model: string
  llm_base_url: string
  llm_api_key_masked: string
  llm_api_key_configured: boolean
  embedding_model: string
  embedding_base_url: string
  embedding_api_key_masked: string
  embedding_api_key_configured: boolean
  llm_daily_limit: number
  config_source: string
}

export interface AiConfigUpdatePayload {
  llm_model?: string
  llm_base_url?: string
  llm_api_key?: string
  embedding_model?: string
  embedding_base_url?: string
  embedding_api_key?: string
  llm_daily_limit?: number
  clear_llm_api_key?: boolean
  clear_embedding_api_key?: boolean
}

export interface AiUsage {
  tokens_total: number
  calls_total: number
  tokens_today: number
  calls_today: number
  daily_limit_per_user: number
  active_llm_model: string
  active_llm_model_name: string
  daily_tokens_7d: { date: string; tokens: number }[]
  daily_calls_7d: { date: string; calls: number }[]
}

export function getAiModels(): Promise<AiModelCatalog> {
  return request.get('/api/v1/admin/ai/models')
}

export function getAiConfig(): Promise<AiConfig> {
  return request.get('/api/v1/admin/ai/config')
}

export function updateAiConfig(data: AiConfigUpdatePayload): Promise<AiConfig> {
  return request.put('/api/v1/admin/ai/config', data)
}

export function getAiUsage(): Promise<AiUsage> {
  return request.get('/api/v1/admin/ai/usage')
}

export interface CustomChatModelPayload {
  id: string
  name?: string
  description?: string
}

export interface ModelUsageBreakdown {
  model_id: string
  model_name: string
  model_tier: string
  model_category: string
  custom: boolean
  tokens: number
  calls: number
}

export interface SceneUsageBreakdown {
  scene: string
  scene_label: string
  tokens: number
  calls: number
}

export interface StudentTokenUsage {
  user_id: number
  username: string
  tokens_today: number
  tokens_total: number
  calls_today: number
  quota_used_today: number
  daily_limit?: number
  models_today: ModelUsageBreakdown[]
  scenes_today: SceneUsageBreakdown[]
  last_model_id?: string | null
  last_model_name?: string | null
  last_model_tier?: string | null
  last_model_category?: string | null
  last_scene?: string | null
  last_scene_label?: string | null
  last_tokens?: number
  last_invoke_at?: string | null
}

export interface StudentUsageSearch {
  username?: string
  page_num?: number
  page_size?: number
}

export function addCustomChatModel(data: CustomChatModelPayload): Promise<AiModelItem> {
  return request.post('/api/v1/admin/ai/models/custom', data)
}

export function deleteCustomChatModel(modelId: string): Promise<void> {
  return request.delete(`/api/v1/admin/ai/models/custom/${encodeURIComponent(modelId)}`)
}

export function getStudentAiUsage(
  params?: StudentUsageSearch,
): Promise<PageResult<StudentTokenUsage>> {
  return request.get('/api/v1/admin/ai/usage/students', { params })
}
