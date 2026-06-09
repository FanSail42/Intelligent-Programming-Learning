import request from './request'
import type { PageResult } from './course'

export interface Warehouse {
  id: number
  name: string
  description: string | null
  warehouse_kind: 'file_type' | 'course'
  course_subject: string | null
  material_type: string
  icon: string
  color: string
  sort_order: number
  material_count: number
  created_at: string
  updated_at: string
}

export interface WarehouseMaterial {
  id: number
  course_id: number
  course_name: string
  warehouse_id: number | null
  type: string
  original_name: string
  status: string
  uploaded_by: number | null
  uploader_name: string
  created_at: string
}

export interface WarehouseCreate {
  name: string
  description?: string
  warehouse_kind?: 'file_type' | 'course'
  course_subject?: string
  material_type?: string
  icon?: string
  color?: string
  sort_order?: number
}

export interface WarehouseMaterialSearch {
  page_num?: number
  page_size?: number
  material_name?: string
  course_name?: string
  teacher_name?: string
  created_from?: string
  created_to?: string
}

export function listWarehouses(): Promise<Warehouse[]> {
  return request.get('/api/v1/warehouses')
}

export function getWarehouse(id: number): Promise<Warehouse> {
  return request.get(`/api/v1/warehouses/${id}`)
}

export function createWarehouse(data: WarehouseCreate): Promise<Warehouse> {
  return request.post('/api/v1/warehouses', data)
}

export function updateWarehouse(id: number, data: Partial<WarehouseCreate>): Promise<Warehouse> {
  return request.put(`/api/v1/warehouses/${id}`, data)
}

export function deleteWarehouse(id: number): Promise<null> {
  return request.delete(`/api/v1/warehouses/${id}`)
}

export function listWarehouseMaterials(
  warehouseId: number,
  params: WarehouseMaterialSearch,
): Promise<PageResult<WarehouseMaterial>> {
  return request.get(`/api/v1/warehouses/${warehouseId}/materials`, { params })
}

export function listAssignableMaterials(
  warehouseId: number,
  params: WarehouseMaterialSearch,
): Promise<PageResult<WarehouseMaterial>> {
  return request.get(`/api/v1/warehouses/${warehouseId}/assignable-materials`, { params })
}

export function assignMaterials(warehouseId: number, materialIds: number[]): Promise<{ assigned_count: number }> {
  return request.post(`/api/v1/warehouses/${warehouseId}/assign`, { material_ids: materialIds })
}

export function unassignMaterials(warehouseId: number, materialIds: number[]): Promise<{ unassigned_count: number }> {
  return request.post(`/api/v1/warehouses/${warehouseId}/unassign`, { material_ids: materialIds })
}

export const COURSE_SUBJECT_LABEL: Record<string, string> = {
  python: 'Python',
  java: 'Java',
  cpp: 'C/C++',
}
