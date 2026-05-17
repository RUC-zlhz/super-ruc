import type { RequestBrief, RequestDetail } from '@/api/workflow'

export const LEAVE_WORKBENCH_ALERT = {
  message: '请假类申请仅用于院内协同与留痕',
  description:
    '涉及 LEAVE 类申请时，本平台仅承载院内提醒、补件和审批留痕；正式请假仍以微人大等校级正式系统为准。',
}

export const LEAVE_DETAIL_ALERT = {
  message: '正式请假仍以校级正式系统为准',
  description:
    '当前页面中的请假申请仅用于院内协同、补件和审批留痕；如需形成正式请假结果，请继续通过微人大等校级正式系统办理。',
}

export const PREVIEW_CADRE_ROLES = [
  { code: 'PARTY_BRANCH_SECRETARY', label: '党支部书记' },
  { code: 'YOUTH_LEAGUE_SECRETARY', label: '团支书' },
  { code: 'CLASS_MONITOR', label: '班长' },
] as const

export const PREVIEW_HIDDEN_MENU_LABELS = [
  '运营看板',
  '导入导出中心',
  '培养方案管理',
  '用户管理',
  '审计日志',
]

export const PREVIEW_LEAVE_REQUEST_BRIEF: RequestBrief = {
  id: 900001,
  request_no: 'PREVIEW-LEAVE-001',
  type_code: 'LEAVE_PERSONAL',
  title: '开发预览：个人请假',
  status: 'SUBMITTED',
  revision: 1,
  applicant_user_id: 20001,
  applicant_student_id: 20260001,
  submitted_at: '2026-05-17T09:30:00+08:00',
  updated_at: '2026-05-17T10:00:00+08:00',
}

export const PREVIEW_LEAVE_REQUEST_DETAIL: RequestDetail = {
  ...PREVIEW_LEAVE_REQUEST_BRIEF,
  type_name: '个人请假',
  category: 'LEAVE',
  summary: '用于直接预览前端中的请假边界提示',
  form_data: {
    reason: '开发预览：测试请假边界提示',
    start_date: '2026-05-18',
    end_date: '2026-05-18',
    leave_type: '事假',
  },
  decided_at: null,
  decided_by: null,
  decision_comment: '当前为开发预览样例，不会提交到后端。',
  withdrawn_at: null,
  attachments: [],
  approval_records: [
    {
      id: 1,
      revision: 1,
      action: 'SUBMIT',
      status_before: 'DRAFT',
      status_after: 'SUBMITTED',
      operator_id: 20001,
      operator_role: 'STUDENT',
      comment: '开发预览样例已提交',
      occurred_at: '2026-05-17T09:30:00+08:00',
    },
  ],
}

export function isLeaveRequestPreview(
  request: Pick<RequestDetail, 'category' | 'type_code'> | null | undefined,
) {
  if (!request) return false
  const typeCode = (request.type_code || '').toUpperCase()
  return request.category === 'LEAVE' || typeCode.startsWith('LEAVE')
}
