import { get, post } from '@/utils/request'

export interface StudentNoticeItem {
  id: number
  title: string
  summary?: string | null
  category?: string | null
  is_pinned: boolean
  published_at?: string | null
  read_at?: string | null
  delivery_id?: number | null
}

export interface NoticeDetail {
  id: number
  title: string
  body_md: string
  summary?: string | null
  category?: string | null
  status: string
  source_type: string
  source_url?: string | null
  channels: string
  target_rule?: Record<string, any> | null
  target_summary?: string | null
  effective_start?: string | null
  effective_end?: string | null
  is_pinned: boolean
  published_at?: string | null
  updated_at: string
  tags: string[]
}

export interface WechatSubscribeTemplate {
  scene: string
  template_id: string
}

export interface WechatSubscribeConfig {
  enabled: boolean
  templates: WechatSubscribeTemplate[]
}

export interface WechatSubscribeAuthorizationResult {
  template_id: string
  status: 'accept' | 'reject' | 'ban' | 'filter'
}

export function getMyNotices(params?: { page?: number; size?: number; unread_only?: boolean }) {
  return get<{ items: StudentNoticeItem[]; meta: any }>('/notices/inbox', params)
}

export function markRead(deliveryId: number) {
  return post<any>(`/notices/read/${deliveryId}`)
}

export function getNoticeDetail(noticeId: number) {
  return get<NoticeDetail>(`/notices/${noticeId}`)
}

export function getSubscribeConfig() {
  return get<WechatSubscribeConfig>('/notices/subscribe-config')
}

export function saveSubscribeAuthorizations(results: WechatSubscribeAuthorizationResult[]) {
  return post<WechatSubscribeAuthorizationResult[]>('/notices/subscribe-authorizations', { results })
}
