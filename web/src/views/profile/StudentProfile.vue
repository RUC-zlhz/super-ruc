<template>
  <div class="student-profile-page">
    <a-page-header title="学生画像" sub-title="学生成长事实、学籍状态与治理留痕" @back="$router.back()">
      <template #extra>
        <a-space>
          <a-button :loading="snapshotLoading === 'pdf'" @click="onDownloadSnapshot('pdf')">
            <template #icon><FilePdfOutlined /></template>
            导出 PDF 快照
          </a-button>
          <a-button :loading="snapshotLoading === 'xlsx'" @click="onDownloadSnapshot('xlsx')">
            <template #icon><FileExcelOutlined /></template>
            导出 XLSX 快照
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <a-spin :spinning="loading">
      <template v-if="profile">
        <a-alert
          v-if="isReadonlyProfile"
          class="mb16"
          type="warning"
          show-icon
          :message="readonlyMessage"
        />

        <a-card title="学籍信息" :bordered="false" size="small" class="mb16 student-hero-card">
          <a-descriptions :column="3" size="small">
            <a-descriptions-item label="学号">{{ profile.student.student_no }}</a-descriptions-item>
            <a-descriptions-item label="姓名">{{ profile.student.full_name }}</a-descriptions-item>
            <a-descriptions-item label="性别">{{ profile.student.gender || '-' }}</a-descriptions-item>
            <a-descriptions-item label="年级">{{ profile.student.grade_code || '-' }}</a-descriptions-item>
            <a-descriptions-item label="专业">{{ profile.student.major_code || '-' }}</a-descriptions-item>
            <a-descriptions-item label="班级">{{ profile.student.class_code || '-' }}</a-descriptions-item>
            <a-descriptions-item label="政治面貌">{{ profile.student.political_status || '-' }}</a-descriptions-item>
            <a-descriptions-item label="学籍状态">
              <a-tag :color="enrollmentStatusColor(profile.student.enrollment_status)">
                {{ enrollmentStatusLabel(profile.student.enrollment_status) }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="状态说明">
              {{ profile.student.enrollment_status_reason || '-' }}
            </a-descriptions-item>
            <a-descriptions-item label="入学年份">{{ profile.student.enrollment_year || '-' }}</a-descriptions-item>
            <a-descriptions-item label="预计毕业">{{ profile.student.expected_graduation_year || '-' }}</a-descriptions-item>
            <a-descriptions-item label="状态更新时间">
              {{ formatDateTime(profile.student.enrollment_status_updated_at) }}
            </a-descriptions-item>
          </a-descriptions>
        </a-card>

        <div class="metric-grid">
          <div v-for="metric in factMetrics" :key="metric.key" class="metric-tile">
            <span class="metric-icon"><component :is="factMetricIcon(metric.key)" /></span>
            <div class="metric-label">{{ metric.label }}</div>
            <div class="metric-value">{{ metric.value }}</div>
            <div class="metric-sub">成长画像事实</div>
          </div>
          <div class="metric-tile">
            <span class="metric-icon"><ExclamationCircleOutlined /></span>
            <div class="metric-label">待处理申诉</div>
            <div class="metric-value">{{ pendingCorrectionCount }}</div>
            <div class="metric-sub">学生补录/纠错</div>
          </div>
        </div>

        <a-card title="成长事实" :bordered="false" size="small" class="mb16">
          <template #extra>
            <a-space>
              <span v-if="isReadonlyProfile" class="readonly-text">非在读学生画像只读</span>
              <a-button type="primary" size="small" :disabled="isReadonlyProfile" @click="onOpenFactDrawer">
                <template #icon><PlusOutlined /></template>
                新增
              </a-button>
            </a-space>
          </template>
          <a-table
            :columns="factCols"
            :data-source="profile.facts"
            :pagination="false"
            :scroll="{ x: 1320 }"
            row-key="id"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'approval_status'">
                <a-tag :color="approvalStatusColor(record.approval_status)">
                  {{ approvalStatusLabel(record.approval_status) }}
                </a-tag>
              </template>
              <template v-else-if="column.key === 'governance'">
                <div class="meta-stack">
                  <span>来源：{{ factSourceLabel(record) }}</span>
                  <span>录入：{{ operatorLabel(record.created_by_name, record.created_by) }}</span>
                  <span>更新：{{ operatorLabel(record.updated_by_name, record.updated_by) }}</span>
                </div>
              </template>
              <template v-else-if="column.key === 'review_comment'">
                <span>{{ record.review_comment || '-' }}</span>
              </template>
              <template v-else-if="column.key === 'updated_at'">
                <span>{{ formatDateTime(record.updated_at) }}</span>
              </template>
              <template v-else-if="column.key === 'actions'">
                <a-popconfirm
                  title="确定删除？"
                  :disabled="isReadonlyProfile"
                  @confirm="onDeleteFact(record.id)"
                >
                  <a-button type="link" size="small" danger :disabled="isReadonlyProfile">
                    <template #icon><DeleteOutlined /></template>
                    删除
                  </a-button>
                </a-popconfirm>
              </template>
            </template>
          </a-table>
        </a-card>

        <a-card title="学生补录待审核" :bordered="false" size="small" class="mb16">
          <template #extra>
            <a-tag v-if="pendingFactsSupported" color="gold">{{ pendingFacts.length }}</a-tag>
          </template>
          <template v-if="pendingFactsSupported">
            <a-table
              :columns="pendingFactCols"
              :data-source="pendingFacts"
              :pagination="false"
              :scroll="{ x: 1280 }"
              row-key="id"
              size="small"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'approval_status'">
                  <a-tag :color="approvalStatusColor(record.approval_status)">
                    {{ approvalStatusLabel(record.approval_status) }}
                  </a-tag>
                </template>
                <template v-else-if="column.key === 'governance'">
                  <div class="meta-stack">
                    <span>来源：{{ factSourceLabel(record) }}</span>
                    <span>提交：{{ formatDateTime(record.created_at || record.updated_at) }}</span>
                    <span>处理人：{{ operatorLabel(record.updated_by_name, record.updated_by) }}</span>
                  </div>
                </template>
                <template v-else-if="column.key === 'review_comment'">
                  <span>{{ record.review_comment || '-' }}</span>
                </template>
                <template v-else-if="column.key === 'actions'">
                  <a-space>
                    <a-button
                      type="link"
                      size="small"
                      :disabled="isReadonlyProfile"
                      @click="openDecisionModal(record, 'APPROVED')"
                    >
                      <template #icon><CheckOutlined /></template>
                      通过
                    </a-button>
                    <a-button
                      type="link"
                      size="small"
                      danger
                      :disabled="isReadonlyProfile"
                      @click="openDecisionModal(record, 'REJECTED')"
                    >
                      <template #icon><CloseOutlined /></template>
                      驳回
                    </a-button>
                  </a-space>
                </template>
              </template>
              <template #emptyText>
                <a-empty description="当前没有待审核的学生补录事实" />
              </template>
            </a-table>
          </template>
          <a-alert
            v-else
            type="info"
            show-icon
            message="学生补录审核队列将在后端待审核接口上线后自动接通。"
          />
        </a-card>
      </template>
    </a-spin>

    <a-drawer
      :open="showFactDrawer"
      title="新增成长事实"
      width="480"
      @close="closeFactDrawer"
    >
      <a-form layout="vertical" :model="factForm" @finish="onSubmitFact">
        <a-form-item label="类型" :rules="[{ required: true }]">
          <a-select v-model:value="factForm.fact_type">
            <a-select-option value="RESEARCH">科研</a-select-option>
            <a-select-option value="COMPETITION">竞赛</a-select-option>
            <a-select-option value="PRACTICE">实践</a-select-option>
            <a-select-option value="VOLUNTEER">志愿服务</a-select-option>
            <a-select-option value="LEADERSHIP">学生骨干</a-select-option>
            <a-select-option value="CUSTOM">自定义</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="标题" :rules="[{ required: true }]">
          <a-input v-model:value="factForm.title" />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="factForm.description" :rows="3" />
        </a-form-item>
        <a-form-item label="角色/职责">
          <a-input v-model:value="factForm.role_in_activity" />
        </a-form-item>
        <a-form-item label="开始日期">
          <a-date-picker
            v-model:value="factForm.started_on"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="结束日期">
          <a-date-picker
            v-model:value="factForm.ended_on"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="时长/学时">
          <a-input-number v-model:value="factForm.hours" :min="0" :step="0.5" style="width: 100%" />
        </a-form-item>
        <a-form-item label="等级/名次">
          <a-input v-model:value="factForm.rank_label" />
        </a-form-item>
        <a-form-item>
          <a-button type="primary" html-type="submit" :loading="factSubmitting">
            <template #icon><SaveOutlined /></template>
            保存
          </a-button>
        </a-form-item>
      </a-form>
    </a-drawer>

    <a-modal
      v-model:open="decisionModalOpen"
      :title="decisionForm.decision === 'APPROVED' ? '通过学生补录' : '驳回学生补录'"
      :confirm-loading="decisionSubmitting"
      @ok="onSubmitDecision"
      @cancel="closeDecisionModal"
    >
      <a-form layout="vertical">
        <a-form-item label="条目">
          <div>{{ decisionTarget?.title || '-' }}</div>
        </a-form-item>
        <a-form-item label="处理意见">
          <a-textarea
            v-model:value="decisionForm.comment"
            :rows="4"
            :placeholder="decisionForm.decision === 'APPROVED' ? '可选，留空则直接通过' : '建议填写驳回原因'"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  FilePdfOutlined,
  FileExcelOutlined,
  PlusOutlined,
  DeleteOutlined,
  SaveOutlined,
  CheckOutlined,
  CloseOutlined
} from '@ant-design/icons-vue'
import {
  ExperimentOutlined,
  ExclamationCircleOutlined,
  FlagOutlined,
  HeartOutlined,
  TeamOutlined,
  TrophyOutlined,
} from '@ant-design/icons-vue'
import {
  adminAddFact,
  adminDecideFact,
  adminDeleteFact,
  adminGetProfile,
  adminListCorrections,
  adminListPendingFacts,
  downloadStudentProfileSnapshot,
  type ProfileFactOut,
  type ProfileSummary,
} from '@/api/profile'

const route = useRoute()
const studentId = Number(route.params.studentId)

const profile = ref<ProfileSummary | null>(null)
const loading = ref(false)
const pendingCorrectionCount = ref(0)
const pendingFacts = ref<ProfileFactOut[]>([])
const pendingFactsSupported = ref(true)
const snapshotLoading = ref<'pdf' | 'xlsx' | ''>('')

const ACTIVE_ENROLLMENT_STATUSES = new Set(['ACTIVE', 'IN_SCHOOL'])

const ENROLLMENT_STATUS_LABELS: Record<string, string> = {
  ACTIVE: '在读',
  IN_SCHOOL: '在校',
  SUSPENDED: '休学',
  TRANSFERRED: '转出',
  LEAVE: '离校',
  GRADUATED: '毕业',
  ARCHIVED: '归档',
}

const FACT_LABELS: Record<string, string> = {
  RESEARCH: '科研',
  COMPETITION: '竞赛',
  PRACTICE: '实践',
  VOLUNTEER: '志愿服务',
  LEADERSHIP: '学生骨干',
  CUSTOM: '自定义',
}

const FACT_STATUS_LABELS: Record<string, string> = {
  PENDING: '待审核',
  APPROVED: '已通过',
  REJECTED: '已驳回',
}

type FactRecordLike = Partial<ProfileFactOut> & Record<string, any>

function enrollmentStatusLabel(status?: string | null) {
  if (!status) return '-'
  return ENROLLMENT_STATUS_LABELS[status] || status
}

function enrollmentStatusColor(status?: string | null) {
  if (status === 'ACTIVE' || status === 'IN_SCHOOL') return 'green'
  if (status === 'SUSPENDED') return 'gold'
  if (status === 'TRANSFERRED' || status === 'LEAVE') return 'orange'
  if (status === 'GRADUATED') return 'blue'
  return 'default'
}

function factTypeLabel(type: string) {
  return FACT_LABELS[type] || type
}

function approvalStatusLabel(status: string) {
  return FACT_STATUS_LABELS[status] || status
}

function approvalStatusColor(status: string) {
  if (status === 'APPROVED') return 'green'
  if (status === 'REJECTED') return 'red'
  return 'gold'
}

function formatFactPeriod(record: FactRecordLike) {
  const started = record.started_on || '-'
  const ended = record.ended_on || '-'
  return started === '-' && ended === '-' ? '-' : `${started} ~ ${ended}`
}

function formatDateTime(value?: string | null) {
  if (!value) return '-'
  const normalized = value.replace('T', ' ').replace('Z', '')
  return normalized.length >= 16 ? normalized.slice(0, 16) : normalized
}

function factSourceLabel(record: FactRecordLike) {
  return record.source_label || record.source || '-'
}

function operatorLabel(name?: string | null, id?: number | null) {
  if (name) return name
  if (id != null) return `#${id}`
  return '-'
}

const isReadonlyProfile = computed(() => {
  const status = profile.value?.student.enrollment_status
  return !status || !ACTIVE_ENROLLMENT_STATUSES.has(status)
})

const readonlyMessage = computed(() => {
  if (!profile.value || !isReadonlyProfile.value) return ''
  const parts = [`该学生当前为${enrollmentStatusLabel(profile.value.student.enrollment_status)}状态，画像页已切换为只读。`]
  if (profile.value.student.enrollment_status_reason) {
    parts.push(`原因：${profile.value.student.enrollment_status_reason}`)
  }
  return parts.join(' ')
})

const factMetrics = computed(() => {
  if (!profile.value) return []
  return [
    { key: 'research_count', label: '科研', value: profile.value.research_count },
    { key: 'competition_count', label: '竞赛', value: profile.value.competition_count },
    { key: 'practice_count', label: '实践', value: profile.value.practice_count },
    { key: 'volunteer_hours', label: '志愿时长', value: profile.value.volunteer_hours },
    { key: 'leadership_count', label: '学生骨干', value: profile.value.leadership_count },
  ]
})

const FACT_METRIC_ICON: Record<string, unknown> = {
  research_count: ExperimentOutlined,
  competition_count: TrophyOutlined,
  practice_count: FlagOutlined,
  volunteer_hours: HeartOutlined,
  leadership_count: TeamOutlined,
}

function factMetricIcon(key: string) {
  return FACT_METRIC_ICON[key] || FlagOutlined
}

async function loadPendingFacts() {
  try {
    const resp = await adminListPendingFacts({ student_id: studentId, page: 1, size: 100 })
    if (!resp) {
      pendingFactsSupported.value = false
      pendingFacts.value = []
      return
    }
    pendingFactsSupported.value = true
    pendingFacts.value = resp.items.filter((item) => item.student_id === studentId)
  } catch {
    pendingFactsSupported.value = false
    pendingFacts.value = []
  }
}

async function loadProfile() {
  loading.value = true
  try {
    const [profileResp, correctionResp] = await Promise.all([
      adminGetProfile(studentId),
      adminListCorrections({ student_id: studentId, status: 'PENDING', page: 1, size: 1 }),
    ])
    profile.value = profileResp.data
    pendingCorrectionCount.value = correctionResp.data.meta.total
    await loadPendingFacts()
  } finally {
    loading.value = false
  }
}

const factCols = [
  {
    title: '类型',
    dataIndex: 'fact_type',
    key: 'fact_type',
    width: 100,
    customRender: ({ text }: { text: string }) => factTypeLabel(text),
  },
  { title: '标题', dataIndex: 'title', key: 'title', width: 220 },
  {
    title: '时间范围',
    key: 'period',
    width: 180,
    customRender: ({ record }: { record: ProfileFactOut }) => formatFactPeriod(record),
  },
  { title: '状态', key: 'approval_status', width: 100 },
  { title: '治理信息', key: 'governance', width: 260 },
  { title: '审核意见', key: 'review_comment', width: 220 },
  { title: '更新时间', key: 'updated_at', width: 160 },
  { title: '操作', key: 'actions', width: 90 },
]

const pendingFactCols = [
  {
    title: '类型',
    dataIndex: 'fact_type',
    key: 'fact_type',
    width: 100,
    customRender: ({ text }: { text: string }) => factTypeLabel(text),
  },
  { title: '标题', dataIndex: 'title', key: 'title', width: 220 },
  {
    title: '时间范围',
    key: 'period',
    width: 180,
    customRender: ({ record }: { record: ProfileFactOut }) => formatFactPeriod(record),
  },
  { title: '状态', key: 'approval_status', width: 100 },
  { title: '治理信息', key: 'governance', width: 280 },
  { title: '审核意见', key: 'review_comment', width: 220 },
  { title: '操作', key: 'actions', width: 120 },
]

const showFactDrawer = ref(false)
const factSubmitting = ref(false)
const factForm = reactive({
  fact_type: 'RESEARCH',
  title: '',
  description: '',
  role_in_activity: '',
  started_on: undefined as string | undefined,
  ended_on: undefined as string | undefined,
  hours: undefined as number | undefined,
  rank_label: '',
})

function resetFactForm() {
  Object.assign(factForm, {
    fact_type: 'RESEARCH',
    title: '',
    description: '',
    role_in_activity: '',
    started_on: undefined,
    ended_on: undefined,
    hours: undefined,
    rank_label: '',
  })
}

function closeFactDrawer() {
  showFactDrawer.value = false
}

function onOpenFactDrawer() {
  if (isReadonlyProfile.value) {
    message.warning('非在读学生画像仅支持查看，不能新增成长事实')
    return
  }
  showFactDrawer.value = true
}

async function onSubmitFact() {
  if (isReadonlyProfile.value) {
    message.warning('非在读学生画像仅支持查看，不能新增成长事实')
    return
  }
  factSubmitting.value = true
  try {
    await adminAddFact(studentId, {
      fact_type: factForm.fact_type,
      title: factForm.title,
      description: factForm.description || undefined,
      role_in_activity: factForm.role_in_activity || undefined,
      started_on: factForm.started_on || undefined,
      ended_on: factForm.ended_on || undefined,
      hours: factForm.hours ?? undefined,
      rank_label: factForm.rank_label || undefined,
      source: 'TEACHER_ENTRY',
    })
    message.success('已添加')
    closeFactDrawer()
    resetFactForm()
    await loadProfile()
  } finally {
    factSubmitting.value = false
  }
}

async function onDeleteFact(factId: number) {
  if (isReadonlyProfile.value) {
    message.warning('非在读学生画像仅支持查看，不能删除成长事实')
    return
  }
  await adminDeleteFact(factId)
  message.success('已删除')
  await loadProfile()
}

const decisionModalOpen = ref(false)
const decisionSubmitting = ref(false)
const decisionTarget = ref<ProfileFactOut | null>(null)
const decisionForm = reactive<{
  decision: 'APPROVED' | 'REJECTED'
  comment: string
}>({
  decision: 'APPROVED',
  comment: '',
})

function openDecisionModal(record: FactRecordLike, decision: 'APPROVED' | 'REJECTED') {
  if (isReadonlyProfile.value) {
    message.warning('非在读学生画像仅支持查看，不能处理学生补录')
    return
  }
  decisionTarget.value = record as ProfileFactOut
  decisionForm.decision = decision
  decisionForm.comment = record.review_comment || ''
  decisionModalOpen.value = true
}

function closeDecisionModal() {
  decisionModalOpen.value = false
  decisionTarget.value = null
  decisionForm.decision = 'APPROVED'
  decisionForm.comment = ''
}

async function onSubmitDecision() {
  if (!decisionTarget.value) return
  decisionSubmitting.value = true
  try {
    await adminDecideFact(decisionTarget.value.id, {
      decision: decisionForm.decision,
      comment: decisionForm.comment || undefined,
    })
    message.success(decisionForm.decision === 'APPROVED' ? '已通过学生补录' : '已驳回学生补录')
    closeDecisionModal()
    await loadProfile()
  } finally {
    decisionSubmitting.value = false
  }
}

async function onDownloadSnapshot(format: 'pdf' | 'xlsx') {
  snapshotLoading.value = format
  try {
    const ok = await downloadStudentProfileSnapshot(studentId, format)
    if (!ok) {
      message.info('画像快照导出接口尚未上线，后端合并后可直接使用')
      return
    }
    message.success(`已开始下载 ${format.toUpperCase()} 快照`)
  } finally {
    snapshotLoading.value = ''
  }
}

onMounted(loadProfile)
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }

.readonly-text {
  color: #999;
  font-size: 12px;
}

.meta-stack {
  display: flex;
  flex-direction: column;
  gap: 4px;
  line-height: 1.4;
}

.student-hero-card {
  background:
    linear-gradient(135deg, rgba(176, 0, 24, 0.08), rgba(255, 255, 255, 0) 55%),
    #fff;
}
</style>
