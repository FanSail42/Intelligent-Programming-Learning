import request from './request'
import type { UserInfo } from './auth'

export interface ProfileAiUsage {
  tokens_today: number
  tokens_total: number
  calls_today: number
  daily_limit: number
  quota_used_today: number
  last_model_name: string | null
  last_scene_label: string | null
  last_invoke_at: string | null
}

export interface ProfileSummary {
  id: number
  username: string
  role: string
  status: string
  created_at: string
  login_count: number
  last_login_at: string | null
  last_login_ip: string | null
  ai_usage: ProfileAiUsage | null
}

export function getProfileSummary(): Promise<ProfileSummary> {
  return request.get('/api/v1/auth/profile/summary')
}

export function updateUsername(newUsername: string, currentPassword: string): Promise<UserInfo> {
  return request.patch('/api/v1/auth/profile/username', {
    new_username: newUsername,
    current_password: currentPassword,
  })
}

export function changePassword(currentPassword: string, newPassword: string) {
  return request.patch('/api/v1/auth/profile/password', {
    current_password: currentPassword,
    new_password: newPassword,
  })
}
