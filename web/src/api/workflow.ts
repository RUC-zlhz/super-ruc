import { del, get, patch, post } from '@/utils/request'
import { downloadFile } from '@/utils/download'
import type { ApiEnvelope } from '@/utils/request'
import type { Paginated } from './types'
import type { StudentBasic } from './profile'

export type WorkflowTemplateKind = 'PARTY' | 'YOUTH_LEAGUE' | 'OTHER'
export type WorkflowTriggerRule = 'PREV_DONE' | 'MANUAL' | 'ON_APPLY' | 'ON_DATE'
export type WorkflowNodeStatus =
  | 'PENDING'
  | 'MATERIAL_SUBMITTED'
  | 'DONE'
  | 'OVERDUE'
  | 'DEFERRED'
  | 'MANUAL_FOLLOW_UP'
export type ReminderChannel = 'IN_APP'
export type ReminderStatus = 'PENDING' | 'SENT' | 'CANCELLED' | 'FAILED'
export type ReminderRunStatus = 'RUNNING' | 'COMPLETED' | 'FAILED'

export interface WorkflowNode {
  id: number
  code: string
  name: string
  sort_order: number
  stage_group?: string | null
  required_task?: string | null
  trigger_rule: WorkflowTriggerRule | string
  due_rule_days?: number | null
  reminder_lead_days?: number | null
  reminder_enabled: boolean
  reminder_channel: ReminderChannel | string
  repeat_interval_days?: number | null
  max_reminders?: number | null
  is_terminal: boolean
  is_active: boolean
}

export interface WorkflowNodePayload {
  code: string
  name: string
  sort_order: number
  stage_group?: string | null
  required_task?: string | null
  trigger_rule: WorkflowTriggerRule | string
  due_rule_days?: number | null
  reminder_lead_days?: number | null
  reminder_enabled: boolean
  reminder_channel: ReminderChannel | string
  repeat_interval_days?: number | null
  max_reminders?: number | null
  is_terminal: boolean
  is_active: boolean
}

export interface WorkflowTemplate {
  id: number
  code: string
  name: string
  kind: WorkflowTemplateKind | string
  description?: string | null
  version_label?: string | null
  is_active: boolean
  updated_at?: string
  nodes: WorkflowNode[]
}

export interface WorkflowTemplatePayload {
  code: string
  name: string
  kind: WorkflowTemplateKind | string
  description?: string | null
  version_label?: string | null
  nodes: WorkflowNodePayload[]
}

export interface WorkflowStudentBrief {
  id: number
  student_id: number
  student_no?: string | null
  student_name?: string | null
  template_code: string
  template_name: string
  current_node_state_id?: number | null
  current_node_name?: string | null
  current_node_status?: WorkflowNodeStatus | string | null
  current_node_student_material_required?: boolean
  current_node_evidence?: string | null
  current_node_note?: string | null
  due_date?: string | null
}

export interface WorkflowStudentNodeDetail {
  id: number
  workflow_id: number
  node_id: number
  node_code: string
  node_name: string
  sort_order: number
  status: WorkflowNodeStatus | string
  due_date?: string | null
  triggered_at?: string | null
  completed_at?: string | null
  evidence?: string | null
  note?: string | null
}

export interface WorkflowStudentDetail {
  id: number
  template_code: string
  template_name: string
  kind: WorkflowTemplateKind | string
  status: string
  started_at?: string | null
  completed_at?: string | null
  current_node_id?: number | null
  current_node_name?: string | null
  next_action_hint?: string | null
  nodes: WorkflowStudentNodeDetail[]
}

export interface WorkflowStudentStartPayload {
  student_id: number
  template_code: string
  note?: string
}

export interface WorkflowReminderRecord {
  id: number
  workflow_node_state_id: number
  student_id: number
  student_no?: string | null
  student_name?: string | null
  template_code: string
  template_name: string
  node_code: string
  node_name: string
  node_status: WorkflowNodeStatus | string
  due_date?: string | null
  reminder_date: string
  channel: ReminderChannel | string
  status: ReminderStatus | string
  sent_at?: string | null
  message?: string | null
  cancel_reason?: string | null
  error_message?: string | null
  created_at: string
}

export interface WorkflowReminderRun {
  id: number
  as_of_date: string
  channel: ReminderChannel | string
  trigger_mode: string
  status: ReminderRunStatus | string
  created_count: number
  sent_count: number
  skipped_count: number
  cancelled_count: number
  failed_count: number
  error_message?: string | null
  operator_id?: number | null
  operator_role?: string | null
  started_at: string
  finished_at?: string | null
}

export interface WorkflowReminderListResult {
  supported: boolean
  route: string | null
  items: WorkflowReminderRecord[]
  meta: Paginated<WorkflowReminderRecord>['meta']
}

export interface WorkflowReminderRunListResult {
  supported: boolean
  route: string | null
  items: WorkflowReminderRun[]
  meta: Paginated<WorkflowReminderRun>['meta']
}

export interface WorkflowReminderExecutionResult {
  route: string
  legacy: boolean
  run: WorkflowReminderRun
}

function emptyMeta(page = 1, size = 20) {
  return { page, size, total: 0 }
}

function buildApiUrl(path: string, params?: Record<string, unknown>) {
  const base = (import.meta.env.VITE_API_BASE || '/api/v1').replace(/\/$/, '')
  const url = new URL(`${base}${path}`, window.location.origin)
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return
    url.searchParams.set(key, String(value))
  })
  return url.toString()
}

async function requestOptionalEnvelope<T>(
  method: 'GET' | 'POST',
  path: string,
  options?: { params?: Record<string, unknown>; body?: unknown },
): Promise<{ supported: boolean; data?: T }> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
  }
  const token = localStorage.getItem('sip.access_token')
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  if (method !== 'GET') {
    headers['Content-Type'] = 'application/json'
  }
  const response = await fetch(buildApiUrl(path, options?.params), {
    method,
    headers,
    body: method === 'GET' ? undefined : JSON.stringify(options?.body ?? {}),
  })
  if (response.status === 401) {
    localStorage.removeItem('sip.access_token')
    if (location.pathname !== '/login') {
      const currentPath = location.pathname + location.search + location.hash
      location.replace(`/login?redirect=${encodeURIComponent(currentPath)}`)
    }
    throw new Error('登录已失效')
  }
  if (response.status === 404 || response.status === 405) {
    return { supported: false }
  }
  const payload = (await response.json().catch(() => null)) as ApiEnvelope<T> | null
  if (!response.ok || !payload || payload.code !== 0) {
    throw new Error(payload?.message || `请求失败（${response.status}）`)
  }
  return { supported: true, data: payload.data }
}

async function resolveOptionalEnvelope<T>(
  method: 'GET' | 'POST',
  paths: string[],
  options?: { params?: Record<string, unknown>; body?: unknown },
): Promise<{ supported: boolean; route: string | null; data?: T }> {
  for (const path of paths) {
    const result = await requestOptionalEnvelope<T>(method, path, options)
    if (result.supported) {
      return {
        supported: true,
        route: path,
        data: result.data,
      }
    }
  }
  return {
    supported: false,
    route: null,
  }
}

function normalizeReminderRunRecord(raw: Record<string, any>, fallbackChannel = 'IN_APP'): WorkflowReminderRun {
  return {
    id: Number(raw.id ?? Date.now()),
    as_of_date: String(raw.as_of_date ?? raw.asOfDate ?? new Date().toISOString().slice(0, 10)),
    channel: String(raw.channel ?? fallbackChannel),
    trigger_mode: String(raw.trigger_mode ?? raw.triggerMode ?? 'MANUAL'),
    status: String(raw.status ?? 'COMPLETED'),
    created_count: Number(raw.created_count ?? raw.created ?? 0),
    sent_count: Number(raw.sent_count ?? raw.sent ?? 0),
    skipped_count: Number(raw.skipped_count ?? raw.skipped ?? 0),
    cancelled_count: Number(raw.cancelled_count ?? raw.cancelled ?? 0),
    failed_count: Number(raw.failed_count ?? raw.failed ?? 0),
    error_message: raw.error_message ?? raw.errorMessage ?? null,
    operator_id: raw.operator_id ?? raw.operatorId ?? null,
    operator_role: raw.operator_role ?? raw.operatorRole ?? null,
    started_at: String(raw.started_at ?? raw.startedAt ?? new Date().toISOString()),
    finished_at: raw.finished_at ?? raw.finishedAt ?? null,
  }
}

export function listWorkflowTemplates(params?: { kind?: string }) {
  return get<ApiEnvelope<WorkflowTemplate[]>>('/admin/workflow/templates', { params })
}

export function saveWorkflowTemplate(payload: WorkflowTemplatePayload) {
  return post<ApiEnvelope<WorkflowTemplate>>('/admin/workflow/templates', payload)
}

export function listWorkflowStudents(params: {
  template_code?: string
  student_no?: string
  grade_code?: string
  page?: number
  size?: number
}) {
  return get<ApiEnvelope<Paginated<WorkflowStudentBrief>>>('/admin/workflow/students', { params })
}

export function searchWorkflowStudents(params: {
  q?: string
  grade_code?: string
  major_code?: string
  class_code?: string
  include_non_active?: boolean
  enrollment_status?: string
  page?: number
  size?: number
}) {
  return get<ApiEnvelope<Paginated<StudentBasic>>>('/admin/workflow/students/search', { params })
}

export function startWorkflowStudent(payload: WorkflowStudentStartPayload) {
  return post<ApiEnvelope<WorkflowStudentDetail>>('/admin/workflow/students', payload)
}

export function completeWorkflowNode(
  stateId: number,
  payload: { evidence?: string | null; note?: string | null },
) {
  return post<ApiEnvelope<WorkflowStudentDetail>>(
    `/admin/workflow/node-states/${stateId}/complete`,
    payload,
  )
}

export async function listWorkflowReminderRecords(params: {
  template_code?: string
  student_no?: string
  status?: string
  page?: number
  size?: number
}): Promise<WorkflowReminderListResult> {
  const result = await resolveOptionalEnvelope<Paginated<WorkflowReminderRecord>>(
    'GET',
    ['/admin/workflow/reminders', '/admin/workflow/reminder-records'],
    { params },
  )
  return {
    supported: result.supported,
    route: result.route,
    items: result.data?.items ?? [],
    meta: result.data?.meta ?? emptyMeta(params.page, params.size),
  }
}

export async function listWorkflowReminderRuns(params: {
  page?: number
  size?: number
}): Promise<WorkflowReminderRunListResult> {
  const result = await resolveOptionalEnvelope<Paginated<WorkflowReminderRun>>(
    'GET',
    ['/admin/workflow/reminder-runs', '/admin/workflow/reminders/runs'],
    { params },
  )
  return {
    supported: result.supported,
    route: result.route,
    items: result.data?.items ?? [],
    meta: result.data?.meta ?? emptyMeta(params.page, params.size),
  }
}

export async function executeWorkflowReminderRun(payload: {
  as_of_date?: string
  channel?: ReminderChannel | string
}): Promise<WorkflowReminderExecutionResult> {
  const response = await post<ApiEnvelope<WorkflowReminderRun>>('/admin/workflow/reminders/generate', {
    as_of_date: payload.as_of_date,
    channel: 'IN_APP',
    force_current_nodes: true,
  })
  return {
    route: '/admin/workflow/reminders/generate',
    legacy: false,
    run: normalizeReminderRunRecord(response.data as Record<string, any>, 'IN_APP'),
  }
}

export type RequestStatus =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'IN_REVIEW'
  | 'APPROVED'
  | 'REJECTED'
  | 'WITHDRAWN'
  | 'OFFLINE_HANDLED'

export type ApprovalAction =
  | 'SUBMIT'
  | 'RESUBMIT'
  | 'CLAIM'
  | 'APPROVE'
  | 'REJECT'
  | 'WITHDRAW'
  | 'REOPEN'
  | 'OFFLINE_HANDLE'

export interface RequestStatusMeta {
  label: string
  color: string
  description: string
}

export interface ApprovalActionMeta {
  label: string
  color: string
  description?: string
}

export interface AdminRequestActionMeta {
  label: string
  title: string
  successMessage: string
  color: string
}

export const REQUEST_STATUS_META: Record<RequestStatus, RequestStatusMeta> = {
  DRAFT: {
    label: '草稿',
    color: 'default',
    description: '申请尚未提交，申请人仍可继续编辑内容。',
  },
  SUBMITTED: {
    label: '待受理',
    color: 'blue',
    description: '申请已提交，待审批老师开始受理。',
  },
  IN_REVIEW: {
    label: '审核中',
    color: 'processing',
    description: '审批老师已开始受理，正在审核材料并给出处理意见。',
  },
  APPROVED: {
    label: '已通过',
    color: 'green',
    description: '线上审批已完成，当前申请已通过。',
  },
  REJECTED: {
    label: '已驳回',
    color: 'red',
    description: '申请已退回申请人，可根据驳回意见补充后重新提交。',
  },
  WITHDRAWN: {
    label: '已撤回',
    color: 'default',
    description: '申请人已主动撤回，本次线上申请已结束。',
  },
  OFFLINE_HANDLED: {
    label: '转线下',
    color: 'gold',
    description: '线上流转已终止，请按审批意见中的联系方式线下办理。',
  },
}

export const APPROVAL_ACTION_META: Record<string, ApprovalActionMeta> = {
  SUBMIT: {
    label: '提交',
    color: 'blue',
    description: '申请人将草稿正式提交到审批链路。',
  },
  RESUBMIT: {
    label: '重新提交',
    color: 'blue',
    description: '申请人根据驳回意见补充后重新提交。',
  },
  CLAIM: {
    label: '受理',
    color: 'processing',
    description: '审批老师认领该申请并进入审批中状态。',
  },
  APPROVE: {
    label: '通过',
    color: 'green',
    description: '线上审批通过，当前申请结束。',
  },
  REJECT: {
    label: '驳回',
    color: 'red',
    description: '申请被退回申请人补充或修改。',
  },
  WITHDRAW: {
    label: '申请人撤回',
    color: 'default',
    description: '申请人主动终止当前线上申请。',
  },
  OFFLINE_HANDLE: {
    label: '转线下',
    color: 'gold',
    description: '申请需转为线下核验或办理，线上流转同步终止。',
  },
  REOPEN: {
    label: '重开审批',
    color: 'orange',
    description: '终态申请被审批角色受控重开，重新进入线上审批链路。',
  },
}

export const ADMIN_REQUEST_ACTION_META: Record<'claim' | 'approve' | 'reject' | 'offline' | 'reopen', AdminRequestActionMeta> = {
  claim: {
    label: '受理',
    title: '受理',
    successMessage: '已受理',
    color: 'blue',
  },
  approve: {
    label: '通过',
    title: '通过',
    successMessage: '已通过',
    color: 'green',
  },
  reject: {
    label: '驳回',
    title: '驳回',
    successMessage: '已驳回',
    color: 'red',
  },
  offline: {
    label: '转线下',
    title: '转线下',
    successMessage: '已转线下',
    color: 'gold',
  },
  reopen: {
    label: '重开审批',
    title: '重开审批',
    successMessage: '已重开审批',
    color: 'orange',
  },
}

export function getRequestStatusMeta(status?: string | null): RequestStatusMeta {
  if (!status) {
    return {
      label: '-',
      color: 'default',
      description: '当前状态未知，请以最新流转记录为准。',
    }
  }
  return REQUEST_STATUS_META[status as RequestStatus] ?? {
    label: status,
    color: 'default',
    description: '当前状态未录入前端文案，请以最新流转记录为准。',
  }
}

export function getApprovalActionMeta(action?: string | null): ApprovalActionMeta {
  if (!action) {
    return { label: '-', color: 'default' }
  }
  return APPROVAL_ACTION_META[action] ?? { label: action, color: 'default' }
}

export interface RequestBrief {
  id: number
  request_no: string
  type_code: string
  title: string
  status: RequestStatus
  revision: number
  applicant_user_id: number
  applicant_student_id?: number | null
  applicant_user_name?: string | null
  applicant_student_no?: string | null
  applicant_student_name?: string | null
  submitted_at?: string | null
  updated_at: string
}

export interface RequestAttachment {
  id: number
  filename: string
  file_size?: number | null
  mime_type?: string | null
  uploaded_at: string
}

export interface ApprovalRecord {
  id: number
  revision: number
  action: string
  status_before?: string | null
  status_after?: string | null
  operator_id?: number | null
  operator_role?: string | null
  operator_name?: string | null
  operator_work_no?: string | null
  operator_student_no?: string | null
  operator_student_name?: string | null
  comment?: string | null
  occurred_at: string
}

export interface RequestDetail extends RequestBrief {
  type_name: string
  category: string
  form_data: Record<string, unknown>
  summary?: string | null
  decided_at?: string | null
  decided_by?: number | null
  decided_by_name?: string | null
  decided_by_work_no?: string | null
  decision_comment?: string | null
  withdrawn_at?: string | null
  attachments: RequestAttachment[]
  approval_records: ApprovalRecord[]
}

export function listAdminRequests(params: {
  q?: string
  type_code?: string
  status?: RequestStatus
  in_review_only?: boolean
  page?: number
  size?: number
}) {
  return get<ApiEnvelope<Paginated<RequestBrief>>>('/admin/requests', { params })
}

export function getMyRequests(params: { status?: RequestStatus; page?: number; size?: number }) {
  return get<ApiEnvelope<Paginated<RequestBrief>>>('/requests/my', { params })
}

export function getRequestDetail(id: number) {
  return get<ApiEnvelope<RequestDetail>>(`/requests/${id}`)
}

export function downloadRequestAttachment(
  requestId: number,
  attachmentId: number,
  filename?: string,
) {
  return downloadFile(
    `/requests/${requestId}/attachments/${attachmentId}/download`,
    filename,
  )
}

export function previewRequestProof(id: number) {
  return get<Blob>(`/workflow/proof-preview/${id}`, { responseType: 'blob' })
}

export function claimRequest(id: number) {
  return post<ApiEnvelope<RequestDetail>>(`/admin/requests/${id}/claim`)
}

export function approveRequest(id: number, comment?: string) {
  return post<ApiEnvelope<RequestDetail>>(`/admin/requests/${id}/approve`, { comment })
}

export function rejectRequest(id: number, comment?: string) {
  return post<ApiEnvelope<RequestDetail>>(`/admin/requests/${id}/reject`, { comment })
}

export function markRequestOffline(id: number, contact_info: string, note?: string) {
  return post<ApiEnvelope<RequestDetail>>(`/admin/requests/${id}/offline`, {
    contact_info,
    note,
  })
}

export function reopenRequest(
  id: number,
  comment?: string,
  target_status: 'IN_REVIEW' | 'SUBMITTED' = 'IN_REVIEW',
) {
  return post<ApiEnvelope<RequestDetail>>(`/admin/requests/${id}/reopen`, {
    comment,
    target_status,
  })
}

// =====================================================================
// 理论自测题库 — FR-005
// =====================================================================
export type QuizType = 'SINGLE' | 'MULTI' | 'JUDGE'
export type QuizDifficulty = 'EASY' | 'MEDIUM' | 'HARD'

export interface QuizOption {
  key: string
  text: string
}

export interface QuizQuestion {
  id: number
  topic: string
  qtype: QuizType
  stem: string
  options_json: QuizOption[] | null
  correct_key: string
  explanation?: string | null
  difficulty?: QuizDifficulty | null
  source_name?: string | null
  source_url?: string | null
  source_official?: boolean
  import_batch_id?: number | null
  is_active: boolean
  created_by?: number | null
  created_at: string
  updated_at: string
}

export interface QuizQuestionPayload {
  topic: string
  qtype: QuizType
  stem: string
  options_json?: QuizOption[] | null
  correct_key: string
  explanation?: string | null
  difficulty?: QuizDifficulty | null
  source_name?: string | null
  source_url?: string | null
  source_official?: boolean
}

export interface QuizQuestionPatch extends Partial<QuizQuestionPayload> {
  is_active?: boolean
}

export interface QuizImportBatch {
  id: number
  batch_no: string
  import_type: string
  filename: string
  total_rows: number
  ok_rows: number
  warn_rows: number
  fatal_rows: number
  status: string
  summary?: Record<string, unknown> | null
  started_at: string
  finished_at?: string | null
}

export interface QuizImportRow {
  id: number
  row_no: number
  severity: 'INFO' | 'WARN' | 'FATAL' | string
  result: string
  field_name?: string | null
  message?: string | null
  raw_data?: Record<string, unknown> | null
}

export interface QuizImportPreview {
  batch: QuizImportBatch
  rows: QuizImportRow[]
}

export interface QuizImportCommit {
  batch: QuizImportBatch
  created_count: number
  updated_count: number
  skipped_count: number
}

export function listQuizQuestions(params: {
  topic?: string
  qtype?: QuizType
  is_active?: boolean
  q?: string
  page?: number
  size?: number
}) {
  return get<ApiEnvelope<Paginated<QuizQuestion>>>('/admin/quiz/questions', { params })
}

export function createQuizQuestion(payload: QuizQuestionPayload) {
  return post<ApiEnvelope<QuizQuestion>>('/admin/quiz/questions', payload)
}

export function updateQuizQuestion(id: number, payload: QuizQuestionPatch) {
  return patch<ApiEnvelope<QuizQuestion>>(`/admin/quiz/questions/${id}`, payload)
}

export function deleteQuizQuestion(id: number) {
  return del<ApiEnvelope<{ id: number; is_active: boolean }>>(`/admin/quiz/questions/${id}`)
}

export function previewQuizQuestionImport(file: File) {
  const form = new FormData()
  form.append('file', file)
  return post<ApiEnvelope<QuizImportPreview>>('/admin/quiz/questions/import-preview', form)
}

export function commitQuizQuestionImport(batchId: number) {
  return post<ApiEnvelope<QuizImportCommit>>(`/admin/quiz/questions/import-commit/${batchId}`)
}

export function downloadQuizQuestionImportTemplate(format: 'xlsx' | 'csv' = 'xlsx') {
  return get<Blob>('/admin/quiz/questions/import-template', {
    params: { format },
    responseType: 'blob',
  })
}
