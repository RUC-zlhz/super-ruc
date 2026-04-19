import { get } from '@/utils/request'
import type { ApiEnvelope } from '@/utils/request'
import type { Paginated } from './types'

export interface AcademicModuleGap {
  module_code: string
  module_name: string
  module_type: string
  credits_required: number
  credits_earned: number
  credits_gap: number
  passed_courses: string[]
  note?: string | null
}

export interface AcademicGapResult {
  student_no: string
  student_name: string
  grade_code?: string | null
  major_code?: string | null
  plan_id?: number | null
  plan_name?: string | null
  total_credits_required?: number | null
  total_credits_earned: number
  modules: AcademicModuleGap[]
  suggested_courses: Record<string, unknown>[]
  disclaimer: string
  data_warnings: string[]
  generated_at: string
}

export interface AcademicGapAggregateItem {
  student_id: number
  student_no: string
  student_name: string
  grade_code?: string | null
  major_code?: string | null
  total_credits_required?: number | null
  total_credits_earned: number
  credits_gap?: number | null
  data_warnings: string[]
  generated_at: string
}

export interface AcademicGapAggregateParams {
  keyword?: string
  grade_code?: string
  major_code?: string
  risk_level?: 'HIGH' | 'MEDIUM' | 'LOW'
  page?: number
  page_size?: number
}

export interface OverviewMetric {
  key: string
  label: string
  value: number
  sub_label?: string | null
}

export interface OverviewRequestSummary {
  type_code: string
  type_name: string
  draft: number
  submitted: number
  in_review: number
  approved: number
  rejected: number
  withdrawn: number
  total: number
}

export interface OverviewNoticeSummary {
  total_notices: number
  published_notices: number
  total_batches: number
  total_deliveries: number
  sent: number
  failed: number
  skipped: number
  read: number
}

export interface OverviewWorkflowSummary {
  template_code: string
  template_name: string
  kind: string
  total_students: number
  nodes_pending: number
  nodes_overdue: number
  nodes_done: number
}

export interface OverviewResult {
  metrics: OverviewMetric[]
  requests: OverviewRequestSummary[]
  notices?: OverviewNoticeSummary | null
  workflows: OverviewWorkflowSummary[]
  generated_at: string
  disclaimer: string
}

export interface DashboardMetricCard {
  key: string
  label: string
  value: number
  sub_label?: string | null
}

export interface DashboardBarDatum {
  key: string
  label: string
  value: number
  percent: number
  helper: string
}

export interface DashboardNoticeDatum {
  key: string
  label: string
  value: number
  helper: string
}

export interface DashboardAcademicGapItem {
  key: string
  title: string
  description: string
  count?: number | null
}

export interface DashboardAcademicGapSection {
  title: string
  description: string
  source: 'reserved-overview-only' | 'aggregated-query'
  items: DashboardAcademicGapItem[]
}

export interface DashboardViewModel {
  metrics: DashboardMetricCard[]
  requestDistribution: DashboardBarDatum[]
  workflowLoad: DashboardBarDatum[]
  noticeDelivery: DashboardNoticeDatum[]
  academicGap: DashboardAcademicGapSection
  disclaimer: string
  generatedAt?: string | null
  warnings: string[]
  hasData: boolean
}

export const DEFAULT_DASHBOARD_DISCLAIMER =
  '本页仅展示运营概览与弱提示，不构成个人学业风险、审批结论或正式管理决定；请结合业务台账与正式审核流程复核。'

function pickMetric(metrics: OverviewMetric[], key: string) {
  return metrics.find((metric) => metric.key === key)
}

function clampPercent(value: number, total: number) {
  if (total <= 0) return 0
  return Math.max(0, Math.min(100, Math.round((value / total) * 100)))
}

export function formatCredits(value?: number | null) {
  if (value == null) return '-'
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

function withPercent<T extends { value: number }>(
  items: T[],
  getMaxValue?: (rows: T[]) => number,
): Array<T & { percent: number }> {
  const maxValue = getMaxValue ? getMaxValue(items) : Math.max(...items.map((item) => item.value), 0)
  return items.map((item) => ({
    ...item,
    percent: clampPercent(item.value, maxValue),
  }))
}

export function adaptOverviewMetrics(overview: OverviewResult): DashboardMetricCard[] {
  const students = pickMetric(overview.metrics, 'students')
  const requests = pickMetric(overview.metrics, 'requests')
  const pendingApprovals = pickMetric(overview.metrics, 'pending_approvals')
  const notices = pickMetric(overview.metrics, 'notices')
  const deliveries = pickMetric(overview.metrics, 'deliveries')
  const overdueNodes = overview.workflows.reduce(
    (total, workflow) => total + workflow.nodes_overdue,
    0,
  )

  return [
    {
      key: 'students',
      label: students?.label ?? '在籍学生',
      value: Number(students?.value ?? 0),
      sub_label: students?.sub_label ?? null,
    },
    {
      key: 'requests',
      label: requests?.label ?? '申请总量',
      value: Number(requests?.value ?? 0),
      sub_label: requests?.sub_label ?? null,
    },
    {
      key: 'pending_approvals',
      label: pendingApprovals?.label ?? '待审批',
      value: Number(pendingApprovals?.value ?? 0),
      sub_label: pendingApprovals?.sub_label ?? null,
    },
    {
      key: 'notices',
      label: notices?.label ?? '通知条数',
      value: Number(notices?.value ?? 0),
      sub_label: notices?.sub_label ?? null,
    },
    {
      key: 'deliveries',
      label: deliveries?.label ?? '投递条数',
      value: Number(deliveries?.value ?? 0),
      sub_label: deliveries?.sub_label ?? null,
    },
    {
      key: 'overdue_nodes',
      label: '逾期流程节点',
      value: overdueNodes,
      sub_label: overview.workflows.length
        ? `共 ${overview.workflows.length} 个流程模板`
        : null,
    },
  ]
}

export function defaultDashboardMetrics(): DashboardMetricCard[] {
  return [
    { key: 'students', label: '在籍学生', value: 0 },
    { key: 'requests', label: '申请总量', value: 0 },
    { key: 'pending_approvals', label: '待审批', value: 0 },
    { key: 'notices', label: '通知条数', value: 0 },
    { key: 'deliveries', label: '投递条数', value: 0 },
    { key: 'overdue_nodes', label: '逾期流程节点', value: 0 },
  ]
}

export function adaptRequestDistribution(overview: OverviewResult): DashboardBarDatum[] {
  const rows = overview.requests.map((item) => ({
    key: item.type_code,
    label: item.type_name,
    value: item.total,
    helper: `待处理 ${item.submitted + item.in_review} / 已通过 ${item.approved} / 已驳回 ${item.rejected}`,
  }))
  return withPercent(rows)
}

export function adaptWorkflowLoad(overview: OverviewResult): DashboardBarDatum[] {
  const rows = overview.workflows.map((item) => ({
    key: item.template_code,
    label: item.template_name,
    value: item.nodes_pending + item.nodes_overdue,
    helper: `待处理 ${item.nodes_pending} / 逾期 ${item.nodes_overdue} / 已完成 ${item.nodes_done}`,
  }))
  return withPercent(rows)
}

export function adaptNoticeDelivery(overview: OverviewResult): DashboardNoticeDatum[] {
  const notices = overview.notices
  if (!notices) return []

  return [
    {
      key: 'sent',
      label: '成功送达',
      value: notices.sent,
      helper: `总投递 ${notices.total_deliveries}`,
    },
    {
      key: 'read',
      label: '已读回执',
      value: notices.read,
      helper: notices.sent > 0
        ? `送达已读率 ${clampPercent(notices.read, notices.sent)}%`
        : '暂无送达记录',
    },
    {
      key: 'failed',
      label: '失败或跳过',
      value: notices.failed + notices.skipped,
      helper: `失败 ${notices.failed} / 跳过 ${notices.skipped}`,
    },
  ]
}

export function buildAcademicGapReservedSection(): DashboardAcademicGapSection {
  return {
    title: '学业缺口聚合',
    description: '当前看板仍只消费 overview。后续接入 academic-gap 聚合查询后，本区块将承载聚合列表而不改变页面结构。',
    source: 'reserved-overview-only',
    items: [],
  }
}

export function deriveAcademicRiskLevel(item: AcademicGapAggregateItem): 'HIGH' | 'MEDIUM' | 'LOW' {
  if (item.total_credits_required == null) {
    return item.data_warnings.length ? 'HIGH' : 'MEDIUM'
  }
  const gap = Number(item.credits_gap ?? Math.max(item.total_credits_required - item.total_credits_earned, 0))
  if (gap <= 0 && !item.data_warnings.length) return 'LOW'
  const ratio = item.total_credits_required > 0 ? gap / item.total_credits_required : (gap > 0 ? 1 : 0)
  if (gap >= 6 || ratio >= 0.3) return 'HIGH'
  return 'MEDIUM'
}

export function adaptAcademicGapSection(items: AcademicGapAggregateItem[]): DashboardAcademicGapSection {
  if (!items.length) {
    return {
      title: '学业缺口聚合',
      description: '当前筛选条件下没有待关注的学业缺口记录。',
      source: 'aggregated-query',
      items: [],
    }
  }

  const counts = items.reduce(
    (result, item) => {
      const risk = deriveAcademicRiskLevel(item)
      result[risk] += 1
      return result
    },
    { HIGH: 0, MEDIUM: 0, LOW: 0 },
  )

  return {
    title: '学业缺口聚合',
    description: '当前列表基于管理侧 academic-gap 聚合查询，保持弱结论口径，只用于定位需要进一步核验的学生。',
    source: 'aggregated-query',
    items: [
      {
        key: 'high',
        title: '高关注',
        description: '培养方案缺失，或总差额较大，需要优先人工核验。',
        count: counts.HIGH,
      },
      {
        key: 'medium',
        title: '待跟进',
        description: '存在学分差额或数据 warning，建议继续跟进。',
        count: counts.MEDIUM,
      },
      {
        key: 'low',
        title: '低关注',
        description: '当前无明显差额，但仍需以正式审核结果为准。',
        count: counts.LOW,
      },
    ],
  }
}

export function buildDashboardViewModel(
  overview?: OverviewResult | null,
  academicGapItems: AcademicGapAggregateItem[] = [],
): DashboardViewModel {
  if (!overview) {
    return {
      metrics: defaultDashboardMetrics(),
      requestDistribution: [],
      workflowLoad: [],
      noticeDelivery: [],
      academicGap: academicGapItems.length
        ? adaptAcademicGapSection(academicGapItems)
        : buildAcademicGapReservedSection(),
      disclaimer: DEFAULT_DASHBOARD_DISCLAIMER,
      generatedAt: null,
      warnings: ['当前未获取到 overview 数据，请稍后刷新或检查接口连通性。'],
      hasData: false,
    }
  }

  const requestDistribution = adaptRequestDistribution(overview)
  const workflowLoad = adaptWorkflowLoad(overview)
  const noticeDelivery = adaptNoticeDelivery(overview)
  const metrics = adaptOverviewMetrics(overview)
  const warnings: string[] = []
  const totalMetricValue = metrics.reduce((sum, item) => sum + item.value, 0)
  const hasData =
    totalMetricValue > 0 ||
    requestDistribution.some((item) => item.value > 0) ||
    workflowLoad.some((item) => item.value > 0) ||
    noticeDelivery.some((item) => item.value > 0)

  if (!requestDistribution.length) {
    warnings.push('overview 暂未返回事务申请分布，当前仅展示摘要卡。')
  }
  if (!workflowLoad.length) {
    warnings.push('overview 暂未返回流程节点负载，无法形成流程图表。')
  }
  if (!noticeDelivery.length) {
    warnings.push('overview 暂未返回通知送达汇总，通知模块仅保留空态说明。')
  }
  if (!hasData) {
    warnings.push('当前 overview 已返回，但有效指标均为空或为 0，请结合业务台账核对是否仍在准备数据。')
  }

  return {
    metrics,
    requestDistribution,
    workflowLoad,
    noticeDelivery,
    academicGap: academicGapItems.length
      ? adaptAcademicGapSection(academicGapItems)
      : buildAcademicGapReservedSection(),
    disclaimer: overview.disclaimer || DEFAULT_DASHBOARD_DISCLAIMER,
    generatedAt: overview.generated_at,
    warnings,
    hasData,
  }
}

export function fetchOverview() {
  return get<ApiEnvelope<OverviewResult>>('/admin/report/overview')
}

export function fetchAcademicGapList(params: AcademicGapAggregateParams) {
  return get<ApiEnvelope<Paginated<AcademicGapAggregateItem>>>('/admin/report/academic-gap', {
    params,
  })
}

export function fetchAcademicGap(studentId: number) {
  return get<ApiEnvelope<AcademicGapResult>>(`/admin/report/academic-gap/${studentId}`)
}
