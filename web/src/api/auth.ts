import { get, post, patch } from '@/utils/request'
import type { ApiEnvelope } from '@/utils/request'
import type { TokenResponse, UserInfo } from './types'

export function loginByWorkNo(work_no: string, password: string) {
  return post<ApiEnvelope<TokenResponse>>('/auth/login', { work_no, password })
}

export function refreshToken(refresh_token: string) {
  return post<ApiEnvelope<TokenResponse>>('/auth/refresh', { refresh_token })
}

export function logoutSession(refresh_token?: string | null, access_token?: string | null) {
  return post<ApiEnvelope<{ revoked: boolean }>>(
    '/auth/logout',
    { refresh_token: refresh_token || undefined },
    access_token ? { headers: { Authorization: `Bearer ${access_token}` } } : undefined,
  )
}

export function getMe() {
  return get<ApiEnvelope<UserInfo>>('/auth/me')
}

export function changePassword(old_password: string, new_password: string) {
  return post<ApiEnvelope<UserInfo>>('/auth/change-password', {
    old_password,
    new_password,
  })
}

// v1.5 学籍状态变更
export interface EnrollmentStatusUpdate {
  status: 'ACTIVE' | 'SUSPENDED' | 'TRANSFERRED' | 'GRADUATED' | 'ARCHIVED'
  reason?: string | null
}
export function updateEnrollmentStatus(studentId: number, payload: EnrollmentStatusUpdate) {
  return patch<ApiEnvelope<{ student_id: number; status: string }>>(
    `/admin/auth/students/${studentId}/enrollment-status`,
    payload,
  )
}
