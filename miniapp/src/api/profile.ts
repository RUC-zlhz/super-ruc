import { get, post, setToken, type ApiEnvelope } from '@/utils/request'

const BASE_URL = 'http://localhost:8080/api/v1'
const TOKEN_KEY = 'sip.access_token'

export interface ProfileStudent {
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

export interface ProfileFactStudentView {
  id: number
  fact_type: string
  title: string
  description?: string | null
  role_in_activity?: string | null
  started_on?: string | null
  ended_on?: string | null
  hours?: number | null
  rank_label?: string | null
  attachments?: Record<string, any> | null
  approval_status: string
  updated_at: string
}

export interface ProfileFactSubmissionOut {
  id: number
  student_id?: number | null
  fact_type: string
  title: string
  description?: string | null
  role_in_activity?: string | null
  started_on?: string | null
  ended_on?: string | null
  hours?: number | null
  rank_label?: string | null
  attachments?: Record<string, any> | null
  approval_status: string
  source?: string
  source_label?: string | null
  review_comment?: string | null
  created_at?: string | null
  updated_at: string
}

export interface ProfileFactSubmissionIn {
  fact_type: string
  title: string
  description?: string | null
  role_in_activity?: string | null
  started_on?: string | null
  ended_on?: string | null
  hours?: number | null
  rank_label?: string | null
  attachments?: Record<string, any> | null
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

export interface ProfileSelfView {
  student: ProfileStudent
  facts: ProfileFactStudentView[]
  research_count: number
  competition_count: number
  practice_count: number
  volunteer_hours: number
  leadership_count: number
  generated_at: string
}

type ProfileStudentRaw = Omit<ProfileStudent, 'status' | 'enrollment_status'> & {
  status?: string | null
  enrollment_status?: string | null
}

type ProfileSelfViewRaw = Omit<ProfileSelfView, 'student'> & {
  student: ProfileStudentRaw
}

function withEnrollmentAlias(student: ProfileStudentRaw): ProfileStudent {
  const enrollmentStatus = student.enrollment_status || student.status || 'UNKNOWN'
  return {
    ...student,
    status: student.status || enrollmentStatus,
    enrollment_status: enrollmentStatus,
  }
}

function getToken() {
  return uni.getStorageSync(TOKEN_KEY) || null
}

function buildUrl(url: string, params?: Record<string, any>) {
  const query = params
    ? Object.entries(params)
      .filter(([, value]) => value != null && value !== '')
      .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
      .join('&')
    : ''
  return `${BASE_URL}${url}${query ? `?${query}` : ''}`
}

function optionalRequest<T>(
  url: string,
  method: 'GET' | 'POST' = 'GET',
  data?: any,
  params?: Record<string, any>,
) {
  return new Promise<T | null>((resolve, reject) => {
    const token = getToken()
    uni.request({
      url: buildUrl(url, params),
      method,
      data,
      header: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      success(res) {
        const payload = res.data as ApiEnvelope<T>
        if (res.statusCode === 401) {
          setToken(null)
          uni.reLaunch({ url: '/pages/profile/index' })
          reject(new Error('登录已失效'))
          return
        }
        if (res.statusCode === 404 || res.statusCode === 405 || res.statusCode === 501) {
          resolve(null)
          return
        }
        if (res.statusCode >= 200 && res.statusCode < 300 && payload?.code === 0) {
          resolve(payload.data)
          return
        }
        reject(new Error(payload?.message || '请求失败'))
      },
      fail(err) {
        reject(err)
      },
    })
  })
}

export async function getMyProfile() {
  const resp = await get<ProfileSelfViewRaw>('/profile/me')
  return {
    ...resp,
    data: {
      ...resp.data,
      student: withEnrollmentAlias(resp.data.student),
    },
  }
}

export function submitCorrection(payload: {
  fact_id?: number | null
  field_name: string
  proposed_value?: string | null
  reason?: string | null
}) {
  return post<CorrectionOut>('/profile/me/corrections', payload)
}

export function getMyCorrections(params?: { status?: string; page?: number; size?: number }) {
  return get<{ items: CorrectionOut[]; meta: any }>('/profile/me/corrections', params)
}

export async function getMyFactSubmissions(params?: { status?: string; page?: number; size?: number }) {
  const data = await optionalRequest<{ items: ProfileFactSubmissionOut[]; meta: any }>(
    '/profile/me/fact-submissions',
    'GET',
    undefined,
    params,
  )
  if (!data) return null
  return {
    code: 0,
    message: 'ok',
    data,
  }
}

export async function submitMyFact(payload: ProfileFactSubmissionIn) {
  const data = await optionalRequest<ProfileFactSubmissionOut>(
    '/profile/me/facts',
    'POST',
    {
      ...payload,
      source: 'STUDENT_SELF',
    },
  )
  if (!data) {
    throw new Error('当前版本暂未开放成长补录')
  }
  return {
    code: 0,
    message: 'ok',
    data,
  }
}
