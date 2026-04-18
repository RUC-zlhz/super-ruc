import { get, post, patch } from '@/utils/request'
import type { ApiEnvelope } from '@/utils/request'
import type { Paginated } from './types'

export interface HonorCategoryOut {
  id: number
  code: string
  name: string
  description?: string | null
  sort_order: number
  is_active: boolean
}

export interface HonorRecordBrief {
  id: number
  category_code: string
  title: string
  level: string
  awarded_by: string
  announced_at: string
  status: string
  is_collective: boolean
  cover_image_url?: string | null
  summary?: string | null
  effective_to?: string | null
  recipient_names: string[]
}

export interface HonorRecordDetail extends HonorRecordBrief {
  document_no?: string | null
  effective_from?: string | null
  story_md?: string | null
  acceptance_speech?: string | null
  media?: Record<string, any> | null
  consent_flag: boolean
  view_count: number
  archived_at?: string | null
  archive_reason?: string | null
  recipients: HonorRecipientOut[]
  updated_at: string
}

export interface HonorRecipientOut {
  id: number
  student_id?: number | null
  student_no_snapshot?: string | null
  display_name: string
  major_snapshot?: string | null
  grade_snapshot?: string | null
  class_snapshot?: string | null
  role_in_collective?: string | null
}

export interface HonorRecordIn {
  category_code: string
  title: string
  level: string
  awarded_by: string
  document_no?: string | null
  announced_at: string
  effective_from?: string | null
  effective_to?: string | null
  is_collective?: boolean
  summary?: string | null
  story_md?: string | null
  acceptance_speech?: string | null
  cover_image_url?: string | null
  media?: Record<string, any> | null
  consent_flag?: boolean
  recipients?: {
    student_id?: number | null
    student_no_snapshot?: string | null
    display_name: string
    major_snapshot?: string | null
    grade_snapshot?: string | null
    class_snapshot?: string | null
    role_in_collective?: string | null
  }[]
}

export function listCategories() {
  return get<ApiEnvelope<HonorCategoryOut[]>>('/honors/categories')
}

export function adminListCategories() {
  return get<ApiEnvelope<HonorCategoryOut[]>>('/admin/honors/categories')
}

export function adminUpsertCategory(payload: Partial<HonorCategoryOut>) {
  return post<ApiEnvelope<HonorCategoryOut>>('/admin/honors/categories', payload)
}

export function adminListRecords(params: {
  category_code?: string
  level?: string
  status?: string
  year?: number
  q?: string
  page?: number
  size?: number
}) {
  return get<ApiEnvelope<Paginated<HonorRecordBrief>>>('/admin/honors', { params })
}

export function adminGetRecord(id: number) {
  return get<ApiEnvelope<HonorRecordDetail>>(`/admin/honors/${id}`)
}

export function adminCreateRecord(payload: HonorRecordIn) {
  return post<ApiEnvelope<HonorRecordDetail>>('/admin/honors', payload)
}

export function adminUpdateRecord(id: number, payload: HonorRecordIn) {
  return patch<ApiEnvelope<HonorRecordDetail>>(`/admin/honors/${id}`, payload)
}

export function adminArchiveRecord(id: number, reason?: string, new_status = 'ARCHIVED') {
  return post<ApiEnvelope<HonorRecordDetail>>(`/admin/honors/${id}/archive`, {
    reason,
    new_status,
  })
}
