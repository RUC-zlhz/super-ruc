import { get } from '@/utils/request'

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
  suggested_courses: Record<string, any>[]
  disclaimer: string
  data_warnings: string[]
  generated_at: string
}

export function getMyAcademicGap() {
  return get<AcademicGapResult>('/report/academic-gap')
}
