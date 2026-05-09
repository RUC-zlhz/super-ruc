import {
  AuthRequiredError,
  buildApiUrl,
  get,
  getAuthHeader,
  handleUnauthorized,
  hasToken,
  type ApiEnvelope,
} from '@/utils/request'

export interface AcademicModuleGap {
  module_code: string
  module_name: string
  module_type: string
  credits_required: number
  credits_earned: number
  credits_gap: number
  passed_courses: string[]
  note?: string | null
}

export interface SuggestedCourse {
  module_code?: string | null
  module_name?: string | null
  course_code?: string | null
  course_name?: string | null
  credits?: number | null
  course_type?: string | null
  reason?: string | null
}

export interface AcademicGapResult {
  student_no: string
  student_name: string
  grade_code?: string | null
  major_code?: string | null
  plan_id?: number | null
  plan_name?: string | null
  total_credits_required?: number | null
  total_credits_earned: number
  modules: AcademicModuleGap[]
  suggested_courses: SuggestedCourse[]
  disclaimer: string
  data_warnings: string[]
  generated_at: string
}

export interface TranscriptPdfCandidateCourse {
  line_no: number
  raw_text: string
  course_code?: string | null
  course_name?: string | null
  credits?: number | null
  term_code?: string | null
  score?: number | null
  grade_letter?: string | null
  pass_flag?: boolean | null
  confidence: string
}

export interface TranscriptPdfUploadResult {
  upload_id: number
  batch_no: string
  status: string
  student_no: string
  student_name: string
  filename: string
  file_size: number
  mime_type?: string | null
  object_key?: string | null
  parsed_text_chars: number
  parsed_courses_count: number
  parsed_courses: TranscriptPdfCandidateCourse[]
  review_required: boolean
  formal_records_written: number
  data_warnings: string[]
  uploaded_at: string
}

export function getMyAcademicGap() {
  return get<AcademicGapResult>('/report/academic-gap')
}

export function uploadTranscriptPdf(filePath: string) {
  return new Promise<TranscriptPdfUploadResult>((resolve, reject) => {
    if (!hasToken()) {
      handleUnauthorized(true)
      reject(new AuthRequiredError())
      return
    }
    uni.uploadFile({
      url: buildApiUrl('/report/transcript-pdf'),
      filePath,
      name: 'file',
      header: getAuthHeader(),
      success(res) {
        let payload: ApiEnvelope<TranscriptPdfUploadResult> | null = null
        try {
          payload = typeof res.data === 'string'
            ? JSON.parse(res.data)
            : (res.data as ApiEnvelope<TranscriptPdfUploadResult>)
        } catch {
          uni.showToast({ title: '成绩单上传失败', icon: 'none' })
          reject(new Error('invalid upload payload'))
          return
        }
        if (res.statusCode === 401) {
          handleUnauthorized(true)
          reject(new Error('登录已失效'))
          return
        }
        if (res.statusCode >= 200 && res.statusCode < 300 && payload?.code === 0) {
          resolve(payload.data)
          return
        }
        uni.showToast({ title: payload?.message || '成绩单上传失败', icon: 'none' })
        reject(payload || res)
      },
      fail(err) {
        uni.showToast({ title: '网络异常', icon: 'none' })
        reject(err)
      },
    })
  })
}
