import { get, patch, post } from '@/utils/request'
import type { ApiEnvelope } from '@/utils/request'
import type { Paginated } from './types'
import { downloadFile } from '@/utils/download'

export type HonorStatus = 'ACTIVE' | 'ARCHIVED' | 'REVOKED'
export type HonorLevel = 'NATIONAL' | 'PROVINCIAL' | 'MINISTERIAL' | 'SCHOOL'

export interface HonorCategoryOut {
  id: number
  code: string
  name: string
  description?: string | null
  sort_order: number
  is_active: boolean
}

export interface HonorCategoryIn {
  id?: number | null
  code: string
  name: string
  description?: string | null
  sort_order?: number
  is_active?: boolean
}

export interface HonorRecordBrief {
  id: number
  category_code: string
  category_name?: string | null
  title: string
  level: HonorLevel
  awarded_by: string
  announced_at: string
  status: HonorStatus
  is_collective: boolean
  cover_image_url?: string | null
  summary?: string | null
  effective_to?: string | null
  is_historical?: boolean | null
  history_reason?: string | null
  updated_by_name?: string | null
  updated_at?: string | null
  recipient_names: string[]
}

export interface HonorRecipientOut {
  id: number
  student_id?: number | null
  student_no_snapshot?: string | null
  display_name: string
  major_snapshot?: string | null
  grade_snapshot?: string | null
  class_snapshot?: string | null
  role_in_collective?: string | null
}

export interface HonorRecipientIn {
  student_id?: number | null
  student_no_snapshot?: string | null
  display_name: string
  major_snapshot?: string | null
  grade_snapshot?: string | null
  class_snapshot?: string | null
  role_in_collective?: string | null
}

export interface HonorRecordDetail extends HonorRecordBrief {
  document_no?: string | null
  effective_from?: string | null
  story_md?: string | null
  acceptance_speech?: string | null
  media?: Record<string, unknown> | null
  consent_flag: boolean
  view_count: number
  archived_at?: string | null
  archive_reason?: string | null
  recipients: HonorRecipientOut[]
}

export interface HonorRecordIn {
  category_code: string
  title: string
  level: HonorLevel
  awarded_by: string
  document_no?: string | null
  announced_at: string
  effective_from?: string | null
  effective_to?: string | null
  is_collective?: boolean
  summary?: string | null
  story_md?: string | null
  acceptance_speech?: string | null
  cover_image_url?: string | null
  media?: Record<string, unknown> | null
  consent_flag?: boolean
  recipients?: HonorRecipientIn[]
}

export interface HonorImportBatchBrief {
  id: number
  batch_no: string
  filename: string
  status: string
  total_rows: number
  ok_rows: number
  warn_rows: number
  fatal_rows: number
  started_at: string
  finished_at?: string | null
}

export interface HonorImportBatchRowOut {
  id: number
  row_no: number
  severity: 'INFO' | 'WARN' | 'FATAL'
  result: string
  field_name?: string | null
  message?: string | null
  raw_data?: Record<string, unknown> | null
}

export interface HonorImportPreviewResult {
  batch: HonorImportBatchBrief
  rows: HonorImportBatchRowOut[]
}

export function listCategories() {
  return get<ApiEnvelope<HonorCategoryOut[]>>('/honors/categories')
}

export function adminListCategories() {
  return get<ApiEnvelope<HonorCategoryOut[]>>('/admin/honors/categories')
}

export function adminUpsertCategory(payload: HonorCategoryIn) {
  return post<ApiEnvelope<HonorCategoryOut>>('/admin/honors/categories', payload)
}

export function adminListRecords(params: {
  category_code?: string
  level?: HonorLevel
  status?: HonorStatus
  year?: number
  q?: string
  page?: number
  size?: number
}) {
  return get<ApiEnvelope<Paginated<HonorRecordBrief>>>('/admin/honors', { params })
}

export function adminGetRecord(id: number) {
  return get<ApiEnvelope<HonorRecordDetail>>(`/admin/honors/${id}`)
}

export function adminCreateRecord(payload: HonorRecordIn) {
  return post<ApiEnvelope<HonorRecordDetail>>('/admin/honors', payload)
}

export function adminUpdateRecord(id: number, payload: HonorRecordIn) {
  return patch<ApiEnvelope<HonorRecordDetail>>(`/admin/honors/${id}`, payload)
}

export function adminArchiveRecord(id: number, reason?: string, new_status: HonorStatus = 'ARCHIVED') {
  return post<ApiEnvelope<HonorRecordDetail>>(`/admin/honors/${id}/archive`, {
    reason,
    new_status,
  })
}

export function uploadHonorImport(file: File) {
  const fd = new FormData()
  fd.append('file', file)
  return post<ApiEnvelope<HonorImportPreviewResult>>(
    '/admin/exchange/imports/honor',
    fd,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
}

export function commitHonorImport(batchId: number, note?: string) {
  return post<ApiEnvelope<HonorImportBatchBrief>>(
    `/admin/exchange/imports/${batchId}/commit`,
    { note },
  )
}

export function listHonorImports(params: {
  status?: string
  page?: number
  size?: number
}) {
  return get<ApiEnvelope<Paginated<HonorImportBatchBrief>>>('/admin/exchange/imports', {
    params: { ...params, import_type: 'HONOR' },
  })
}

export function getHonorImport(batchId: number, severity?: string) {
  return get<ApiEnvelope<HonorImportPreviewResult>>(
    `/admin/exchange/imports/${batchId}`,
    { params: { severity } },
  )
}

export function downloadHonorImportErrorReport(batchId: number, filename?: string) {
  return downloadFile(
    `/admin/exchange/imports/${batchId}/error-report`,
    filename || `honor-import-errors-${batchId}.xlsx`,
  )
}
