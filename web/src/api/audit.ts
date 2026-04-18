import { get, post } from '@/utils/request'
import type { ApiEnvelope } from '@/utils/request'
import type { Paginated } from './types'

export interface AuditLogOut {
  id: number
  event_type: string
  entity_code: string
  entity_id?: number | null
  actor_user_id?: number | null
  actor_role?: string | null
  action: string
  result_code: string
  ip_address?: string | null
  detail?: Record<string, any> | null
  message?: string | null
  occurred_at: string
}

export function listAuditLogs(params: {
  page?: number
  size?: number
  event_type?: string
  entity_code?: string
  actor_user_id?: number
  since?: string
  until?: string
}) {
  return get<ApiEnvelope<Paginated<AuditLogOut>>>('/admin/audit-logs', { params })
}

// v1.5 触发归档
export function archiveAuditLogs(retention_days = 180, batch_size = 1000) {
  return post<ApiEnvelope<{ moved: number; retention_days: number }>>(
    '/admin/audit-logs/archive',
    null,
    { params: { retention_days, batch_size } },
  )
}
