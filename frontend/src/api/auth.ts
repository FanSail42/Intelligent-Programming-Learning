import request from './request'

export interface TokenResult {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface UserInfo {
  id: number
  username: string
  role: string
  status: string
  created_at: string
}

export function login(username: string, password: string): Promise<TokenResult> {
  return request.post('/api/v1/auth/login', { username, password })
}

export function getMe(): Promise<UserInfo> {
  return request.get('/api/v1/auth/me')
}

export function logoutApi(): Promise<null> {
  return request.post('/api/v1/auth/logout')
}
