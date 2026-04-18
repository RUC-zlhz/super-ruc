import { get, post, patch } from '@/utils/request'
import type { ApiEnvelope } from '@/utils/request'
import type { Paginated } from './types'

export type RequestStatus =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'IN_REVIEW'
  | 'APPROVED'
  | 'REJECTED'
  | 'WITHDRAWN'
  | 'OFFLINE_HANDLED'

export interface RequestBrief {
  id: number
  request_no: string
  type_code: string
  title: string
  status: RequestStatus
  applicant_user_id: number
  submitted_at?: string | null
  decided_at?: string | null
  revision: number
  updated_at: string
}

export interface RequestDetail extends RequestBrief {
  form_data: Record<string, any>
  summary?: string | null
  decided_by?: number | null
  decision_comment?: string | null
  attachments: any[]
  approval_records: any[]
}

export function listAdminRequests(params: {
  q?: string
  type_code?: string
  status?: RequestStatus
  in_review_only?: boolean
  page?: number
  size?: number
}) {
  return get<ApiEnvelope<Paginated<RequestBrief>>>('/admin/requests', { params })
}

export function getMyRequests(params: { status?: RequestStatus; page?: number; size?: number }) {
  return get<ApiEnvelope<Paginated<RequestBrief>>>('/requests/my', { params })
}

export function getRequestDetail(id: number) {
  return get<ApiEnvelope<RequestDetail>>(`/requests/${id}`)
}

export function claimRequest(id: number) {
  return post<ApiEnvelope<RequestDetail>>(`/admin/requests/${id}/claim`)
}

export function approveRequest(id: number, comment?: string) {
  return post<ApiEnvelope<RequestDetail>>(`/admin/requests/${id}/approve`, { comment })
}

export function rejectRequest(id: number, comment?: string) {
  return post<ApiEnvelope<RequestDetail>>(`/admin/requests/${id}/reject`, { comment })
}

// v1.5 转线下
export function markRequestOffline(id: number, contact_info: string, note?: string) {
  return post<ApiEnvelope<RequestDetail>>(`/admin/requests/${id}/offline`, {
    contact_info,
    note,
  })
}
