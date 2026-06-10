import request from './request'
import { useAuthStore } from '@/stores/auth'

export interface Material {
  id: number
  course_id: number
  type: string
  original_name: string
  status: string
  version: number
  error_message: string | null
  created_at: string
}

export class MaterialUploadError extends Error {
  code: number
  data?: unknown

  constructor(message: string, code: number, data?: unknown) {
    super(message)
    this.name = 'MaterialUploadError'
    this.code = code
    this.data = data
  }
}

export const MATERIAL_DUPLICATE_CODE = 40002
export const MAX_UPLOAD_BYTES = 10 * 1024 * 1024

export function listMaterials(courseId: number): Promise<Material[]> {
  return request.get('/api/v1/materials', { params: { course_id: courseId } })
}

export function getMaterialStatus(materialId: number): Promise<{ id: number; status: string; error_message: string | null }> {
  return request.get(`/api/v1/materials/${materialId}/status`)
}

export function retryMaterial(materialId: number): Promise<{ material_id: number }> {
  return request.post(`/api/v1/materials/${materialId}/retry`)
}

export function deleteMaterial(materialId: number): Promise<null> {
  return request.delete(`/api/v1/materials/${materialId}`)
}

/** 教师/管理员下载资料到本地（学生无权限） */
export async function downloadMaterial(materialId: number, filename: string): Promise<void> {
  const auth = useAuthStore()
  const resp = await fetch(
    `${import.meta.env.VITE_API_BASE}/api/v1/materials/${materialId}/download`,
    {
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    },
  )
  const contentType = resp.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    const data = await resp.json()
    throw new Error(data.message || '下载失败')
  }
  if (!resp.ok) {
    throw new Error('下载失败')
  }
  const blob = await resp.blob()
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}

export async function uploadMaterial(
  courseId: number,
  file: File,
): Promise<{ material_id: number; linked?: boolean }> {
  const form = new FormData()
  form.append('course_id', String(courseId))
  form.append('file', file)
  const auth = useAuthStore()
  const resp = await fetch(`${import.meta.env.VITE_API_BASE}/api/v1/materials/upload`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${auth.accessToken}`,
    },
    body: form,
  })
  const data = await resp.json()
  if (data.code !== 0) {
    throw new MaterialUploadError(data.message || '上传失败', data.code, data.data)
  }
  return data.data
}
