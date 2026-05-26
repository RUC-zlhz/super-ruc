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

export const TRANSCRIPT_PDF_REVIEW_IMPORT_TYPE = 'TRANSCRIPT_PDF_REVIEW'

export interface DefaultImportResult {
  import_type: string
  total_rows: number
  created_count: number
  updated_count: number
  skipped_count: number
  warning_count: number
  warnings: string[]
}

export interface DefaultImportAllResult {
  students: DefaultImportResult
  curriculum: DefaultImportResult
}

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
  summary?: Record<string, any> | null
  note?: string | null
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

export interface TranscriptPdfCourseRecommendation {
  course_code: string
  course_name: string
  credits?: number | null
  match_score: number
  match_reason: string
  major_codes: string[]
  module_names: string[]
}

export interface TranscriptPdfParsedCandidate {
  line_no?: number | null
  raw_text?: string
  course_code?: string | null
  course_name?: string | null
  credits?: number | null
  term_code?: string | null
  score?: number | null
  grade_letter?: string | null
  pass_flag?: boolean | null
  confidence?: string
  note?: string | null
  course_recommendations?: TranscriptPdfCourseRecommendation[]
}

export interface TranscriptPdfReviewRecord {
  line_no?: number | null
  course_code: string
  course_name: string
  credits?: number
  term_code: string
  score?: number | null
  grade_letter?: string | null
  pass_flag: boolean
  note?: string | null
}

export interface TranscriptPdfReviewCommitResult {
  batch_id: number
  batch_no: string
  status: string
  student_id: number
  student_no: string
  formal_records_written: number
  committed_at: string
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

export function importDefaultStudents() {
  return post<ApiEnvelope<DefaultImportResult>>('/admin/default-imports/students')
}

export function importDefaultCurriculum() {
  return post<ApiEnvelope<DefaultImportResult>>('/admin/default-imports/curriculum')
}

export function importAllDefaults() {
  return post<ApiEnvelope<DefaultImportAllResult>>('/admin/default-imports/all')
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

export function commitTranscriptPdfReview(
  batchId: number,
  payload: {
    records: TranscriptPdfReviewRecord[]
    note?: string | null
  },
) {
  return post<ApiEnvelope<TranscriptPdfReviewCommitResult>>(
    `/admin/report/transcript-pdf-reviews/${batchId}/commit`,
    payload,
  )
}
