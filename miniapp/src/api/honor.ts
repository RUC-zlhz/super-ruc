import { get } from '@/utils/request'

export interface HonorCategory {
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
  category_name?: string | null
  title: string
  level: string
  awarded_by: string
  announced_at: string
  status: string
  is_collective: boolean
  display_order: number
  cover_image_url?: string | null
  summary?: string | null
  effective_to?: string | null
  is_historical?: boolean | null
  history_reason?: string | null
  recipient_names: string[]
}

export interface HonorRecipient {
  id: number
  student_id?: number | null
  student_no_snapshot?: string | null
  display_name: string
  major_snapshot?: string | null
  grade_snapshot?: string | null
  class_snapshot?: string | null
  role_in_collective?: string | null
}

export interface HonorRecordDetail {
  id: number
  category_code: string
  category_name?: string | null
  title: string
  level: string
  awarded_by: string
  document_no?: string | null
  announced_at: string
  effective_from?: string | null
  effective_to?: string | null
  is_collective: boolean
  display_order: number
  summary?: string | null
  story_md?: string | null
  acceptance_speech?: string | null
  cover_image_url?: string | null
  media?: Record<string, any> | null
  status: string
  consent_flag: boolean
  view_count: number
  archived_at?: string | null
  archive_reason?: string | null
  is_historical?: boolean | null
  history_reason?: string | null
  recipients: HonorRecipient[]
  updated_at?: string | null
}

export function listHonorCategories() {
  return get<HonorCategory[]>('/honors/categories')
}

export function listPublicHonors(params?: {
  category_code?: string
  level?: string
  year?: number
  is_collective?: boolean
  q?: string
  include_archived?: boolean
  page?: number
  size?: number
}) {
  return get<{ items: HonorRecordBrief[]; meta: any }>('/honors', params)
}

export function getHonorDetail(id: number) {
  return get<HonorRecordDetail>(`/honors/${id}`)
}
