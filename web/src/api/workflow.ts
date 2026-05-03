import { del, get, patch, post } from '@/utils/request'
import type { ApiEnvelope } from '@/utils/request'
import type { Paginated } from './types'

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
}

export interface QuizQuestionPatch extends Partial<QuizQuestionPayload> {
  is_active?: boolean
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
