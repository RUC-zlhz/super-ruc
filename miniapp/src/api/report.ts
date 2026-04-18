import { get } from '@/utils/request'

export interface AcademicGapResult {
  plan_name: string
  total_required_credits: number
  total_earned_credits: number
  gap_credits: number
  modules: {
    module_name: string
    module_type: string
    min_credits: number
    earned_credits: number
    gap: number
    is_required: boolean
  }[]
}

export function getMyAcademicGap() {
  return get<AcademicGapResult>('/report/academic-gap')
}
