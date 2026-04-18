import { get, post } from '@/utils/request'

export interface ProfileSelfView {
  student: {
    student_no: string
    full_name: string
    gender?: string | null
    grade_code?: string | null
    major_code?: string | null
    class_code?: string | null
    political_status?: string | null
    enrollment_status: string
  }
  facts: any[]
  fact_counts: Record<string, number>
  corrections_pending: number
}

export function getMyProfile() {
  return get<ProfileSelfView>('/profile/me')
}

export function submitCorrection(payload: {
  field_name: string
  current_value?: string | null
  proposed_value?: string | null
  reason?: string | null
}) {
  return post<any>('/profile/me/corrections', payload)
}

export function getMyCorrections(params?: { status?: string; page?: number; size?: number }) {
  return get<{ items: any[]; meta: any }>('/profile/me/corrections', params)
}
