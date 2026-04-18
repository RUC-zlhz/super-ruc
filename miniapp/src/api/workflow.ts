import { get, post } from '@/utils/request'

export interface StudentWorkflow {
  id: number
  template_code: string
  template_name: string
  current_node_name?: string | null
  status: string
  started_at: string
}

export interface StudentWorkflowNode {
  id: number
  node_code: string
  node_name: string
  status: string
  completed_at?: string | null
}

export function getMyWorkflows() {
  return get<StudentWorkflow[]>('/workflow/my')
}

export function getWorkflowDetail(id: number) {
  return get<{ workflow: StudentWorkflow; nodes: StudentWorkflowNode[] }>(`/workflow/${id}`)
}

export interface RequestBrief {
  id: number
  request_no: string
  type_code: string
  title: string
  status: string
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
}

export interface ApprovalRecord {
  id: number
  action: string
  operator_user_id: number
  comment?: string | null
  operated_at: string
}

export interface RequestDetail extends RequestBrief {
  type_name: string
  category: string
  summary?: string | null
  form_data: Record<string, any>
  decision_comment?: string | null
  revision: number
  approval_records?: ApprovalRecord[]
  attachments?: { id: number; file_name: string; file_size: number }[]
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
}) {
  return post<RequestDetail>('/requests', payload)
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
