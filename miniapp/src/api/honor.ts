import { get } from '@/utils/request'

export interface HonorRecordBrief {
  id: number
  title: string
  level: string
  awarded_by: string
  announced_at: string
  status: string
  cover_image_url?: string | null
  summary?: string | null
  recipient_names: string[]
}

export function listPublicHonors(params?: { level?: string; q?: string; page?: number; size?: number }) {
  return get<{ items: HonorRecordBrief[]; meta: any }>('/honors', params)
}

export function getHonorDetail(id: number) {
  return get<any>(`/honors/${id}`)
}
