import { get, post } from '@/utils/request'
import type { ApiEnvelope } from '@/utils/request'
import type { Paginated } from './types'
import { downloadFile } from '@/utils/download'

export type ImportType =
  | 'student'
  | 'transcript'
  | 'curriculum-module'
  | 'course-equiv'
  | 'course-offering'

export interface ImportBatchBrief {
  id: number
  batch_no: string
  import_type: string
  filename: string
  status: string
  total_rows: number
  ok_rows: number
  warn_rows: number
  fatal_rows: number
  started_at: string
  finished_at?: string | null
}

export interface ImportBatchRowOut {
  id: number
  row_no: number
  severity: 'INFO' | 'WARN' | 'FATAL'
  result: string
  field_name?: string | null
  message?: string | null
  raw_data?: Record<string, any> | null
}

export interface ImportPreviewResult {
  batch: ImportBatchBrief
  rows: ImportBatchRowOut[]
}

export function uploadImport(type: ImportType, file: File) {
  const fd = new FormData()
  fd.append('file', file)
  return post<ApiEnvelope<ImportPreviewResult>>(
    `/admin/exchange/imports/${type}`,
    fd,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
}

export function commitImport(batchId: number, note?: string) {
  return post<ApiEnvelope<ImportBatchBrief>>(
    `/admin/exchange/imports/${batchId}/commit`,
    { note },
  )
}

export function listImports(params: {
  import_type?: string
  status?: string
  page?: number
  size?: number
}) {
  return get<ApiEnvelope<Paginated<ImportBatchBrief>>>('/admin/exchange/imports', { params })
}

export function getImport(batchId: number, severity?: string) {
  return get<ApiEnvelope<ImportPreviewResult>>(
    `/admin/exchange/imports/${batchId}`,
    { params: { severity } },
  )
}

// v1.5 错误报告下载
export function downloadErrorReport(batchId: number, filename?: string) {
  return downloadFile(
    `/admin/exchange/imports/${batchId}/error-report`,
    filename || `import-errors-${batchId}.xlsx`,
  )
}

export function downloadStudents(filename = 'students.xlsx') {
  return downloadFile('/admin/exchange/exports/students', filename)
}
export function downloadTranscripts(filename = 'transcripts.xlsx') {
  return downloadFile('/admin/exchange/exports/transcripts', filename)
}
export function downloadCurriculum(filename = 'curriculum.xlsx') {
  return downloadFile('/admin/exchange/exports/curriculum', filename)
}
