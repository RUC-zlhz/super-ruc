import { get, post } from '@/utils/request'

export interface StudentNoticeItem {
  id: number
  title: string
  body?: string | null
  source_type: string
  published_at: string
  is_read: boolean
}

export function getMyNotices(params?: { page?: number; size?: number }) {
  return get<{ items: StudentNoticeItem[]; meta: any }>('/notices/inbox', params)
}

export function markRead(deliveryId: number) {
  return post<any>(`/notices/${deliveryId}/read`)
}

export function getNoticeDetail(deliveryId: number) {
  return get<StudentNoticeItem>(`/notices/${deliveryId}`)
}
