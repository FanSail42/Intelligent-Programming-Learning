import request from './request'

export interface HealthData {
  status: string
  app: string
  env: string
}

export function healthCheck(): Promise<HealthData> {
  return request.get('/health')
}
