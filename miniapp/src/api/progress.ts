import { get } from '@/utils/request'

export interface ProgressItem {
  id: string
  source_type: string
  source_id: number
  title: string
  category?: string | null
  status: string
  status_label: string
  current_step?: string | null
  due_date?: string | null
  updated_at: string
  detail_url: string
}

export interface ProgressMyResult {
  items: ProgressItem[]
  generated_at: string
}

export function getMyProgress() {
  return get<ProgressMyResult>('/progress/my')
}
