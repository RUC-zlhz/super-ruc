import { del, get, getAccessToken, patch, post, setAccessToken } from '@/utils/request'
import type { ApiEnvelope } from '@/utils/request'
import type { Paginated } from './types'

export interface StudentBasic {
  id: number
  student_no: string
  full_name: string
  gender?: string | null
  grade_code?: string | null
  major_code?: string | null
  class_code?: string | null
  political_status?: string | null
  enrollment_year?: number | null
  expected_graduation_year?: number | null
  status: string
  enrollment_status: string
  enrollment_status_reason?: string | null
  enrollment_status_updated_at?: string | null
}

export interface ProfileFactOut {
  id: number
  student_id: number
  fact_type: string
  title: string
  description?: string | null
  role_in_activity?: string | null
  started_on?: string | null
  ended_on?: string | null
  hours?: number | null
  rank_label?: string | null
  attachments?: Record<string, unknown> | null
  extra?: Record<string, unknown> | null
  source: string
  source_ref?: string | null
  approval_status: string
  is_sensitive: boolean
  created_by?: number | null
  updated_by?: number | null
  created_at?: string | null
  updated_at: string
  source_label?: string | null
  created_by_name?: string | null
  updated_by_name?: string | null
  review_comment?: string | null
}

export interface ProfileFactIn {
  fact_type: string
  title: string
  description?: string | null
  role_in_activity?: string | null
  started_on?: string | null
  ended_on?: string | null
  hours?: number | null
  rank_label?: string | null
  attachments?: Record<string, unknown> | null
  extra?: Record<string, unknown> | null
  source?: string
  source_ref?: string | null
  is_sensitive?: boolean
}

export interface CorrectionOut {
  id: number
  student_id: number
  fact_id?: number | null
  field_name: string
  current_value?: string | null
  proposed_value?: string | null
  reason?: string | null
  status: string
  handled_by?: number | null
  handled_at?: string | null
  handler_comment?: string | null
  created_at: string
}

export interface CorrectionIn {
  fact_id?: number | null
  field_name: string
  proposed_value?: string | null
  reason?: string | null
}

export interface CorrectionDecisionIn {
  decision: 'APPROVED' | 'REJECTED'
  comment?: string | null
  apply_to_fact?: boolean
}

export interface FactDecisionIn {
  decision: 'APPROVED' | 'REJECTED'
  comment?: string | null
}

export interface ProfileSummary {
  student: StudentBasic
  facts: ProfileFactOut[]
  research_count: number
  competition_count: number
  practice_count: number
  volunteer_hours: number
  leadership_count: number
  masked_fields?: string[]
  hidden_sensitive_fact_count?: number
  full_view_approved_fields?: string[]
  full_view_sensitive_facts_approved?: boolean
  generated_at: string
}

export interface StudentAcademicInfoPatch {
  full_name?: string | null
  gender?: string | null
  grade_code?: string | null
  major_code?: string | null
  class_code?: string | null
  political_status?: string | null
  enrollment_year?: number | null
  expected_graduation_year?: number | null
}

export interface ProfileFullViewRequestOut {
  id: number
  student_id: number
  requester_user_id?: number | null
  requester_name?: string | null
  target_type: 'STUDENT_FIELD' | 'PROFILE_FACTS' | string
  field_name?: string | null
  reason?: string | null
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | string
  handled_by?: number | null
  handled_at?: string | null
  handler_comment?: string | null
  created_at: string
}

export interface ProfileFullViewRequestIn {
  target_type: 'STUDENT_FIELD' | 'PROFILE_FACTS'
  field_name?: string | null
  reason?: string | null
}

export interface ProfileFullViewDecisionIn {
  decision: 'APPROVED' | 'REJECTED'
  comment?: string | null
}

type StudentBasicRaw = Omit<StudentBasic, 'status' | 'enrollment_status'> & {
  status?: string | null
  enrollment_status?: string | null
}

function withEnrollmentAlias(student: StudentBasicRaw): StudentBasic {
  const enrollmentStatus = student.enrollment_status || student.status || 'UNKNOWN'
  return {
    ...student,
    status: student.status || enrollmentStatus,
    enrollment_status: enrollmentStatus,
  }
}

export async function adminSearchStudents(params: {
  q?: string
  grade_code?: string
  major_code?: string
  class_code?: string
  include_non_active?: boolean
  enrollment_status?: string
  page?: number
  size?: number
}) {
  const resp = await get<ApiEnvelope<Paginated<StudentBasic>>>('/admin/profile/students', { params })
  return {
    ...resp,
    data: {
      ...resp.data,
      items: resp.data.items.map(withEnrollmentAlias),
    },
  }
}

export async function adminGetProfile(studentId: number) {
  const resp = await get<ApiEnvelope<Omit<ProfileSummary, 'student'> & { student: StudentBasicRaw }>>(`/admin/profile/${studentId}`)
  return {
    ...resp,
    data: {
      ...resp.data,
      student: withEnrollmentAlias(resp.data.student),
    },
  }
}

export function adminAddFact(studentId: number, payload: ProfileFactIn) {
  return post<ApiEnvelope<ProfileFactOut>>(`/admin/profile/${studentId}/facts`, payload)
}

export function adminUpdateFact(factId: number, payload: ProfileFactIn) {
  return patch<ApiEnvelope<ProfileFactOut>>(`/admin/profile/facts/${factId}`, payload)
}

export function adminDeleteFact(factId: number) {
  return del<ApiEnvelope<{ id: number; deleted: boolean }>>(`/admin/profile/facts/${factId}`)
}

export async function adminUpdateStudentAcademicInfo(studentId: number, payload: StudentAcademicInfoPatch) {
  const resp = await patch<ApiEnvelope<StudentBasicRaw>>(`/admin/students/${studentId}/academic-info`, payload)
  return {
    ...resp,
    data: withEnrollmentAlias(resp.data),
  }
}

function buildUrl(url: string, params?: Record<string, unknown>) {
  const base = import.meta.env.VITE_API_BASE || '/api/v1'
  const requestUrl = new URL(`${base}${url}`, window.location.origin)
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value != null && value !== '') {
      requestUrl.searchParams.set(key, String(value))
    }
  })
  return requestUrl.toString()
}

async function optionalAdminGet<T>(url: string, params?: Record<string, unknown>): Promise<T | null> {
  const token = getAccessToken()
  const resp = await fetch(buildUrl(url, params), {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    credentials: 'same-origin',
  })
  if (resp.status === 401) {
    setAccessToken(null)
    if (location.pathname !== '/login') {
      location.replace('/login')
    }
    throw new Error('登录已失效')
  }
  if (resp.status === 404 || resp.status === 405 || resp.status === 501) {
    return null
  }
  const payload = await resp.json().catch(() => null) as ApiEnvelope<T> | null
  if (!resp.ok) {
    throw new Error(payload?.message || '请求失败')
  }
  if (!payload || payload.code !== 0) {
    throw new Error(payload?.message || '请求失败')
  }
  return payload.data
}

export function adminListPendingFacts(params?: {
  student_id?: number
  page?: number
  size?: number
}) {
  return optionalAdminGet<Paginated<ProfileFactOut>>('/admin/profile/facts/pending', params)
}

export function adminDecideFact(factId: number, payload: FactDecisionIn) {
  return post<ApiEnvelope<ProfileFactOut>>(`/admin/profile/facts/${factId}/decision`, payload)
}

export function adminSubmitFullViewRequest(studentId: number, payload: ProfileFullViewRequestIn) {
  return post<ApiEnvelope<ProfileFullViewRequestOut>>(`/admin/profile/${studentId}/full-view-requests`, payload)
}

export function adminListFullViewRequests(params?: {
  student_id?: number
  status?: string
  page?: number
  size?: number
}) {
  return get<ApiEnvelope<Paginated<ProfileFullViewRequestOut>>>('/admin/profile/full-view-requests', { params })
}

export function adminDecideFullViewRequest(id: number, payload: ProfileFullViewDecisionIn) {
  return post<ApiEnvelope<ProfileFullViewRequestOut>>(`/admin/profile/full-view-requests/${id}/decision`, payload)
}

export async function downloadStudentProfileSnapshot(studentId: number, format: 'pdf' | 'xlsx') {
  const token = getAccessToken()
  const resp = await fetch(buildUrl(`/admin/profile/${studentId}/snapshot.${format}`), {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    credentials: 'same-origin',
  })
  if (resp.status === 401) {
    setAccessToken(null)
    if (location.pathname !== '/login') {
      location.replace('/login')
    }
    throw new Error('登录已失效')
  }
  if (resp.status === 404 || resp.status === 405 || resp.status === 501) {
    return false
  }
  if (!resp.ok) {
    throw new Error('画像快照下载失败')
  }
  const blob = await resp.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `student-profile-${studentId}.${format}`
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
  return true
}

export function adminListCorrections(params: {
  student_id?: number
  status?: string
  page?: number
  size?: number
}) {
  return get<ApiEnvelope<Paginated<CorrectionOut>>>('/admin/profile/corrections', { params })
}

export function adminDecideCorrection(id: number, payload: CorrectionDecisionIn) {
  return post<ApiEnvelope<CorrectionOut>>(`/admin/profile/corrections/${id}/decision`, payload)
}
