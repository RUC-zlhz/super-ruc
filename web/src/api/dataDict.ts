import { get, post, del } from '@/utils/request'
import type { ApiEnvelope } from '@/utils/request'

export interface DataDictItem {
  id: number
  dict_type: string
  label: string
  value: string
  sort_order: number
  is_active: boolean
}

export interface DataDictIn {
  dict_type: string
  label: string
  value: string
  sort_order?: number
}

/** 按字典类型查询选项列表 */
export function listDataDict(dict_type: string) {
  return get<ApiEnvelope<DataDictItem[]>>('/data-dicts', { params: { dict_type } })
}

/** 新增字典选项（管理端） */
export function createDataDict(payload: DataDictIn) {
  return post<ApiEnvelope<DataDictItem>>('/admin/data-dicts', payload)
}

/** 删除字典选项（管理端） */
export function deleteDataDict(id: number) {
  return del<ApiEnvelope<{ deleted: boolean }>>(`/admin/data-dicts/${id}`)
}
