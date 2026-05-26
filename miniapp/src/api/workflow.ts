import {
  AuthRequiredError,
  buildApiUrl,
  download,
  get,
  getAuthHeader,
  handleUnauthorized,
  hasToken,
  post,
  request,
  type ApiEnvelope,
} from '@/utils/request'

export interface StudentWorkflowNode {
  id: number
  node_id: number
  node_code: string
  node_name: string
  sort_order: number
  stage_group?: string | null
  required_task?: string | null
  student_material_required?: boolean
  status: string
  triggered_at?: string | null
  due_date?: string | null
  completed_at?: string | null
  evidence?: string | null
  note?: string | null
}

export interface StudentWorkflow {
  id: number
  template_code: string
  template_name: string
  kind: string
  status: string
  started_at: string
  completed_at?: string | null
  current_node_id?: number | null
  current_node_name?: string | null
  next_action_hint?: string | null
  nodes: StudentWorkflowNode[]
}

export function getMyWorkflows() {
  return get<StudentWorkflow[]>('/workflow/my')
}

export function getWorkflowDetail(id: number) {
  return get<StudentWorkflow>(`/workflow/${id}`)
}

export function submitWorkflowNodeMaterial(
  stateId: number,
  payload: { evidence: string; note?: string | null },
) {
  return post<StudentWorkflow>(`/workflow/node-states/${stateId}/submit`, payload)
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
  submitted_at?: string | null
  updated_at: string
}

export interface RequestType {
  id: number
  code: string
  name: string
  category: string
  description?: string | null
  form_schema?: Record<string, any> | null
  attachment_required: boolean
  allow_withdraw: boolean
  withdraw_hours_limit?: number | null
  approver_roles: string
  is_active: boolean
}

export type RequestCategory =
  | 'LEAVE'
  | 'CERTIFICATE'
  | 'STAMP'
  | 'REGISTRATION'
  | 'MATERIAL'
  | 'OTHER'

export type RequestStatus =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'IN_REVIEW'
  | 'APPROVED'
  | 'REJECTED'
  | 'WITHDRAWN'
  | 'OFFLINE_HANDLED'

export type RequestAction =
  | 'CLAIM'
  | 'SUBMIT'
  | 'RESUBMIT'
  | 'APPROVE'
  | 'REJECT'
  | 'WITHDRAW'
  | 'REOPEN'
  | 'OFFLINE_HANDLE'

export const REQUEST_CATEGORY_LABELS: Record<string, string> = {
  LEAVE: '请假',
  CERTIFICATE: '证明',
  STAMP: '盖章',
  REGISTRATION: '报名',
  MATERIAL: '材料提交',
  OTHER: '其他',
}

export const REQUEST_STATUS_LABELS: Record<string, string> = {
  DRAFT: '草稿',
  SUBMITTED: '待受理',
  IN_REVIEW: '审核中',
  APPROVED: '已通过',
  REJECTED: '已驳回',
  WITHDRAWN: '已撤回',
  OFFLINE_HANDLED: '转线下办理',
}

export const REQUEST_ACTION_LABELS: Record<string, string> = {
  CLAIM: '受理',
  SUBMIT: '提交申请',
  RESUBMIT: '重新提交申请',
  APPROVE: '审批通过',
  REJECT: '驳回申请',
  WITHDRAW: '撤回申请',
  REOPEN: '重开审批',
  OFFLINE_HANDLE: '转线下办理',
}

type RequestBadgeInput = {
  code?: string | null
  category?: string | null
}

const REQUEST_CATEGORY_BADGES: Record<string, string> = {
  LEAVE: '假',
  CERTIFICATE: '证',
  STAMP: '章',
  REGISTRATION: '报',
  MATERIAL: '材',
  OTHER: '事',
}

export function getRequestCategoryLabel(category: string) {
  return REQUEST_CATEGORY_LABELS[category] || category
}

export function getRequestCategoryBadge(category?: string | null) {
  const normalized = (category || '').toUpperCase()
  return REQUEST_CATEGORY_BADGES[normalized] || '事'
}

export function getRequestTypeBadge(
  input?: string | null | RequestBadgeInput,
  fallbackCategory?: string | null,
) {
  const code = typeof input === 'object' ? input?.code : input
  const category = typeof input === 'object' ? input?.category : fallbackCategory
  const normalizedCategory = (category || '').toUpperCase()
  if (normalizedCategory && normalizedCategory !== 'OTHER') {
    return getRequestCategoryBadge(normalizedCategory)
  }

  const normalizedCode = (code || '').toUpperCase()
  if (normalizedCode.includes('CERT')) return '证'
  if (normalizedCode.includes('LEAVE') || normalizedCode.includes('SICK')) return '假'
  if (normalizedCode.includes('STAMP') || normalizedCode.includes('SEAL')) return '章'
  if (
    normalizedCode.includes('REGISTRATION') ||
    normalizedCode.includes('REG_') ||
    normalizedCode.includes('ACTIVITY') ||
    normalizedCode.includes('EVENT')
  ) {
    return '报'
  }
  if (normalizedCode.includes('MATERIAL') || normalizedCode.includes('DOCUMENT')) return '材'
  if (normalizedCode.includes('GRADE') || normalizedCode.includes('SCORE')) return '绩'
  if (normalizedCode.includes('SCHOLAR') || normalizedCode.includes('HONOR')) return '奖'
  return '事'
}

export function getRequestStatusLabel(status: string) {
  return REQUEST_STATUS_LABELS[status] || status
}

export function getRequestActionLabel(action: string) {
  return REQUEST_ACTION_LABELS[action] || action
}

export function isEditableRequestStatus(status?: string | null) {
  return status === 'DRAFT' || status === 'REJECTED'
}

export interface ApprovalRecord {
  id: number
  revision: number
  action: RequestAction | string
  status_before?: string | null
  status_after?: string | null
  operator_id?: number | null
  operator_role?: string | null
  comment?: string | null
  occurred_at: string
}

export interface RequestAttachment {
  id: number
  filename: string
  file_size?: number | null
  mime_type?: string | null
  uploaded_at: string
}

export interface RequestDetail extends RequestBrief {
  type_name: string
  category: RequestCategory | string
  summary?: string | null
  form_data: Record<string, any>
  decided_at?: string | null
  decided_by?: number | null
  decision_comment?: string | null
  withdrawn_at?: string | null
  revision: number
  approval_records: ApprovalRecord[]
  attachments: RequestAttachment[]
}

export function listRequestTypes() {
  return get<RequestType[]>('/requests/types')
}

export function getMyRequests(params?: { status?: string; page?: number; size?: number }) {
  return get<{ items: RequestBrief[]; meta: any }>('/requests/my', params)
}

export function createRequest(payload: {
  type_code: string
  title: string
  form_data: Record<string, any>
  summary?: string
  attachment_ids?: number[]
}) {
  return post<RequestDetail>('/requests', payload)
}

export function updateRequest(id: number, payload: {
  title?: string
  form_data?: Record<string, any>
  summary?: string
}) {
  return request<RequestDetail>(`/requests/${id}`, 'PATCH', payload)
}

export function submitRequest(id: number) {
  return post<RequestDetail>(`/requests/${id}/submit`)
}

export function withdrawRequest(id: number, comment?: string) {
  return post<RequestDetail>(`/requests/${id}/withdraw`, { comment })
}

export function getRequestDetail(id: number) {
  return get<RequestDetail>(`/requests/${id}`)
}

export function uploadRequestAttachment(requestId: number, filePath: string) {
  return new Promise<RequestAttachment>((resolve, reject) => {
    if (!hasToken()) {
      handleUnauthorized(true)
      reject(new AuthRequiredError())
      return
    }
    uni.uploadFile({
      url: buildApiUrl(`/requests/${requestId}/attachments`),
      filePath,
      name: 'file',
      header: getAuthHeader(),
      success(res) {
        let payload: ApiEnvelope<RequestAttachment> | null = null
        try {
          payload = typeof res.data === 'string'
            ? JSON.parse(res.data)
            : (res.data as ApiEnvelope<RequestAttachment>)
        } catch {
          uni.showToast({ title: '附件上传失败', icon: 'none' })
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
        uni.showToast({ title: payload?.message || '附件上传失败', icon: 'none' })
        reject(payload || res)
      },
      fail(err) {
        uni.showToast({ title: '网络异常', icon: 'none' })
        reject(err)
      },
    })
  })
}

export function previewProof(id: number) {
  return download(`/workflow/proof-preview/${id}`)
}

// =====================================================================
// 理论自测 — FR-005
// =====================================================================
export type QuizType = 'SINGLE' | 'MULTI' | 'JUDGE'

export interface QuizOption {
  key: string
  text: string
}

export interface QuizQuestionStudent {
  id: number
  topic: string
  qtype: QuizType
  stem: string
  options_json: QuizOption[] | null
  difficulty?: string | null
}

export interface QuizDrawResult {
  batch_id: string
  questions: QuizQuestionStudent[]
}

export interface QuizItemResult {
  question_id: number
  is_correct: boolean
  correct_key: string
  explanation?: string | null
}

export interface QuizSubmitResult {
  batch_id: string
  total: number
  correct: number
  score: number
  items: QuizItemResult[]
}

export interface QuizRecord {
  id: number
  student_id: number
  question_id: number
  batch_id?: string | null
  answer: string
  is_correct: boolean
  score: number
  submitted_at: string
}

export function drawQuiz(params: { topic?: string; qtype?: QuizType; limit?: number }) {
  return get<QuizDrawResult>('/quiz/draw', params)
}

export function submitQuiz(payload: {
  batch_id: string
  answers: { question_id: number; answer: string }[]
}) {
  return post<QuizSubmitResult>('/quiz/submit', payload)
}

export function listMyQuizRecords(params?: { batch_id?: string; limit?: number }) {
  return get<QuizRecord[]>('/quiz/my/records', params)
}
