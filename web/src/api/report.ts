import { get } from '@/utils/request'
import type { ApiEnvelope } from '@/utils/request'

export interface DashboardMetrics {
  pending_requests: number
  overdue_nodes: number
  active_students: number
  knowledge_entries: number
  recent_notices: number
}

export function fetchDashboard() {
  return get<ApiEnvelope<DashboardMetrics>>('/admin/report/dashboard')
}

export function fetchAcademicGap(studentId: number) {
  return get<ApiEnvelope<any>>(`/admin/report/academic-gap/${studentId}`)
}
