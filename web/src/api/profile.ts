import { get, post, patch, del } from '@/utils/request'
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
  enrollment_status: string
}

export interface ProfileFactOut {
  id: number
  student_id: number
  fact_type: string
  title: string
  description?: string | null
  occurred_at?: string | null
  evidence_url?: string | null
  verified: boolean
  created_at: string
  updated_at: string
}

export interface ProfileFactIn {
  fact_type: string
  title: string
  description?: string | null
  occurred_at?: string | null
  evidence_url?: string | null
  verified?: boolean
}

export interface CorrectionOut {
  id: number
  student_id: number
  field_name: string
  current_value?: string | null
  proposed_value?: string | null
  reason?: string | null
  status: string
  decision_comment?: string | null
  decided_by?: number | null
  created_at: string
  updated_at: string
}

export interface CorrectionIn {
  field_name: string
  current_value?: string | null
  proposed_value?: string | null
  reason?: string | null
}

export interface CorrectionDecisionIn {
  decision: 'APPROVED' | 'REJECTED'
  comment?: string | null
  apply_to_fact?: boolean
}

export interface ProfileSummary {
  student: StudentBasic
  facts: ProfileFactOut[]
  fact_counts: Record<string, number>
  corrections_pending: number
}

export function adminSearchStudents(params: {
  q?: string
  grade_code?: string
  major_code?: string
  class_code?: string
  page?: number
  size?: number
}) {
  return get<ApiEnvelope<Paginated<StudentBasic>>>('/admin/profile/students', { params })
}

export function adminGetProfile(studentId: number) {
  return get<ApiEnvelope<ProfileSummary>>(`/admin/profile/${studentId}`)
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
