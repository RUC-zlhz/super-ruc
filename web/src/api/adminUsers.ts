import { get, post } from '@/utils/request'
import { downloadFile } from '@/utils/download'
import type { ApiEnvelope } from '@/utils/request'
import type { Paginated } from './types'

export interface AdminUserImportBatch {
  id: number
  batch_no: string
  filename: string
  status: string
  total_rows: number
  ok_rows: number
  warn_rows: number
  fatal_rows: number
  created_rows: number
  existing_rows: number
  role_granted_rows: number
  unchanged_rows: number
  operator_id?: number | null
  operator_role?: string | null
  started_at: string
  finished_at?: string | null
  committed_at?: string | null
  summary?: Record<string, unknown> | null
}

export interface AdminUserImportRow {
  id: number
  row_no: number
  work_no?: string | null
  role_code?: string | null
  scope_code?: string | null
  severity: 'INFO' | 'WARN' | 'FATAL' | string
  result: string
  field_name?: string | null
  message?: string | null
  raw_data?: Record<string, unknown> | null
  normalized_data?: Record<string, unknown> | null
}

export interface AdminUserImportPreviewResult {
  batch: AdminUserImportBatch
  rows: AdminUserImportRow[]
}

export interface AdminUserCredential {
  work_no: string
  display_name: string
  role_code: string
  scope_code?: string | null
  initial_password: string
}

export interface AdminUserImportCommitResult extends AdminUserImportPreviewResult {
  credentials: AdminUserCredential[]
}

export async function downloadAdminUserImportTemplate(format: 'xlsx' | 'csv') {
  await downloadFile(
    '/admin/users/import-template',
    `admin-user-import-template.${format}`,
    { format },
  )
}

export function previewAdminUserImport(file: File) {
  const form = new FormData()
  form.append('file', file)
  return post<ApiEnvelope<AdminUserImportPreviewResult>>('/admin/users/import-preview', form)
}

export function commitAdminUserImport(batchId: number, note?: string) {
  return post<ApiEnvelope<AdminUserImportCommitResult>>('/admin/users/import-commit', {
    batch_id: batchId,
    note,
  })
}

export function listAdminUserImports(params?: { page?: number; size?: number }) {
  return get<ApiEnvelope<Paginated<AdminUserImportBatch>>>('/admin/users/imports', { params })
}

export function getAdminUserImport(batchId: number) {
  return get<ApiEnvelope<AdminUserImportPreviewResult>>(`/admin/users/imports/${batchId}`)
}

export async function downloadAdminUserImportErrorReport(batchId: number, batchNo?: string) {
  await downloadFile(
    `/admin/users/imports/${batchId}/error-report`,
    `admin-user-import-errors-${batchNo || batchId}.xlsx`,
  )
}
