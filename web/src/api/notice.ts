import { get, patch, post } from '@/utils/request'
import type { ApiEnvelope } from '@/utils/request'
import type { Paginated } from './types'

export type NoticeStatus = 'DRAFT' | 'PUBLISHED' | 'ARCHIVED'
export type NoticeChannel = 'IN_APP' | 'EMAIL' | 'SMS'
export type NoticeBatchStatus = 'PENDING' | 'COMPLETED' | 'FAILED' | 'PARTIAL'
export type NoticeDeliveryStatus = 'SENT' | 'FAILED' | 'SKIPPED' | 'READ'

export interface NoticeTargetRule {
  grade_codes?: string[] | null
  major_codes?: string[] | null
  class_codes?: string[] | null
  political_status?: string[] | null
  role_codes?: string[] | null
  exclude_graduated?: boolean
}

export interface NoticeBrief {
  id: number
  title: string
  summary?: string | null
  category?: string | null
  status: NoticeStatus
  is_pinned: boolean
  published_at?: string | null
  updated_at: string
  tags: string[]
}

export interface NoticeOut extends NoticeBrief {
  body_md: string
  source_type: string
  source_url?: string | null
  channels: string
  target_rule?: NoticeTargetRule | null
  target_summary?: string | null
  effective_start?: string | null
  effective_end?: string | null
}

export interface NoticeInput {
  title: string
  body_md: string
  summary?: string | null
  category?: string | null
  tags?: string[]
  target_rule?: NoticeTargetRule | null
  target_summary?: string | null
  channels?: string[]
  effective_start?: string | null
  effective_end?: string | null
  is_pinned?: boolean
  source_type?: string
  source_url?: string | null
}

export interface NoticeListParams {
  status?: NoticeStatus
  q?: string
  category?: string
  page?: number
  size?: number
}

export interface NoticeTargetPreviewPayload {
  target_rule?: NoticeTargetRule | null
}

export interface NoticeTargetPreviewResult {
  target_count: number
  sample_student_nos: string[]
}

export interface NoticeDispatchInput {
  channels?: NoticeChannel[] | null
  note?: string | null
}

export interface NoticeBatch {
  id: number
  notice_id: number
  batch_no: string
  channels: string
  target_count: number
  success_count: number
  failed_count: number
  status: NoticeBatchStatus
  note?: string | null
  started_at: string
  finished_at?: string | null
}

export interface NoticeDelivery {
  id: number
  student_id: number
  user_id?: number | null
  channel: NoticeChannel
  status: NoticeDeliveryStatus
  sent_at?: string | null
  read_at?: string | null
  error_code?: string | null
  error_message?: string | null
}

export interface NoticeDeliveryListParams {
  status?: NoticeDeliveryStatus
  channel?: NoticeChannel
  page?: number
  size?: number
}

export function listNotices(params: NoticeListParams) {
  return get<ApiEnvelope<Paginated<NoticeBrief>>>('/admin/notices', { params })
}

export function getNoticeDetail(id: number) {
  return get<ApiEnvelope<NoticeOut>>(`/notices/${id}`)
}

export function previewNoticeTarget(payload: NoticeTargetPreviewPayload) {
  return post<ApiEnvelope<NoticeTargetPreviewResult>>('/admin/notices/target-preview', payload)
}

export function createNotice(payload: NoticeInput) {
  return post<ApiEnvelope<NoticeOut>>('/admin/notices', payload)
}

export function updateNotice(id: number, payload: NoticeInput) {
  return patch<ApiEnvelope<NoticeOut>>(`/admin/notices/${id}`, payload)
}

export function publishNotice(id: number) {
  return post<ApiEnvelope<NoticeOut>>(`/admin/notices/${id}/publish`)
}

export function dispatchNotice(id: number, payload: NoticeDispatchInput) {
  return post<ApiEnvelope<NoticeBatch>>(`/admin/notices/${id}/dispatch`, payload)
}

export function listNoticeBatches(id: number) {
  return get<ApiEnvelope<NoticeBatch[]>>(`/admin/notices/${id}/batches`)
}

export function listBatchDeliveries(batchId: number, params: NoticeDeliveryListParams) {
  return get<ApiEnvelope<Paginated<NoticeDelivery>>>(`/admin/notices/batches/${batchId}/deliveries`, {
    params,
  })
}

export function archiveNotice(id: number) {
  return post<ApiEnvelope<NoticeOut>>(`/admin/notices/${id}/archive`)
}
