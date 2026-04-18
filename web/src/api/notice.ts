import { get, post } from '@/utils/request'
import type { ApiEnvelope } from '@/utils/request'
import type { Paginated } from './types'

export interface NoticeOut {
  id: number
  title: string
  body?: string
  source_type: string
  tags?: string[] | null
  status: string
  published_at?: string | null
  archived_at?: string | null
}

export function listNotices(params: { status?: string; q?: string; page?: number; size?: number }) {
  return get<ApiEnvelope<Paginated<NoticeOut>>>('/admin/notices', { params })
}

export function createNotice(payload: Partial<NoticeOut>) {
  return post<ApiEnvelope<NoticeOut>>('/admin/notices', payload)
}

export function publishNotice(id: number) {
  return post<ApiEnvelope<NoticeOut>>(`/admin/notices/${id}/publish`)
}

export function archiveNotice(id: number) {
  return post<ApiEnvelope<NoticeOut>>(`/admin/notices/${id}/archive`)
}
