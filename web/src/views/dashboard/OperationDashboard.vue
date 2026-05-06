<template>
  <div class="operation-dashboard">
    <a-page-header title="运营看板" sub-title="学院事务运营、通知触达与学业缺口弱提示" />

    <div v-if="dashboard.generatedAt" class="board-meta mb16">
      数据生成时间：{{ formatDateTime(dashboard.generatedAt) }} · {{ overviewFilters.term_code || '全量学期' }}
    </div>

    <a-form layout="inline" :model="overviewFilters" class="filter-card compact mb16" @finish="loadOverview">
      <a-form-item label="看板学期">
        <a-input
          v-model:value="overviewFilters.term_code"
          allow-clear
          placeholder="如 2025-FALL"
          style="width: 150px"
        />
      </a-form-item>
      <a-form-item>
        <a-space>
          <a-button type="primary" html-type="submit" :loading="loadingOverview">
            <template #icon><SearchOutlined /></template>
            刷新看板
          </a-button>
          <a-button @click="resetOverviewFilters">
            <template #icon><ReloadOutlined /></template>
            全量
          </a-button>
        </a-space>
      </a-form-item>
    </a-form>

    <a-alert
      v-if="overviewError"
      type="error"
      show-icon
      class="mb16"
      message="运营看板加载失败"
      :description="overviewError"
    />

    <a-alert
      v-if="academicGapError"
      type="error"
      show-icon
      class="mb16"
      message="学业缺口聚合加载失败"
      :description="academicGapError"
    />

    <a-alert
      v-for="warning in dashboard.warnings"
      :key="warning"
      type="warning"
      show-icon
      class="mb16"
      message="数据提示"
      :description="warning"
    />

    <a-spin :spinning="loadingOverview || loadingAcademicGap">
      <div class="metric-grid five">
        <div v-for="metric in dashboard.metrics.slice(0, 5)" :key="metric.key" class="metric-tile">
          <span class="metric-icon"><component :is="metricIcon(metric.key)" /></span>
          <div class="metric-label">{{ metric.label }}</div>
          <div class="metric-value">{{ metric.value }}</div>
          <div class="metric-sub">{{ metric.sub_label || 'overview 汇总指标' }}</div>
        </div>
      </div>

      <a-card
        v-if="!dashboard.hasData"
        class="mb16"
        title="当前概览为空"
        :bordered="false"
      >
        <a-empty description="overview 已返回，但当前没有可视化价值较高的运营数据" />
      </a-card>

      <div class="dashboard-board">
        <section class="dashboard-canvas">
          <div class="chart-mosaic">
            <a-card title="事务申请分布" :bordered="false" class="visual-card donut-card">
              <template v-if="dashboard.requestDistribution.length">
                <div class="donut-row">
                  <div class="donut-visual">
                    <div class="donut-core">
                      <strong>{{ dashboard.requestDistribution.reduce((sum, item) => sum + item.value, 0) }}</strong>
                      <span>总申请</span>
                    </div>
                  </div>
                  <div class="donut-legend">
                    <div
                      v-for="item in dashboard.requestDistribution.slice(0, 6)"
                      :key="item.key"
                      class="legend-line"
                    >
                      <span class="legend-dot" />
                      <span>{{ item.label }}</span>
                      <strong>{{ item.percent }}%</strong>
                    </div>
                  </div>
                </div>
              </template>
              <a-empty v-else description="overview 暂无事务申请分布" />
            </a-card>

            <a-card title="通知触达概况" :bordered="false" class="visual-card notice-card">
              <template v-if="dashboard.noticeDelivery.length">
                <div class="delivery-list">
                  <div v-for="item in dashboard.noticeDelivery" :key="item.key" class="delivery-row">
                    <div class="delivery-row__meta">
                      <strong>{{ item.label }}</strong>
                      <span>{{ item.helper }}</span>
                    </div>
                    <div class="delivery-row__value">
                      <strong>{{ item.value }}</strong>
                      <div class="delivery-row__track">
                        <i :style="{ width: `${noticeDeliveryPercent(item)}%` }" />
                      </div>
                    </div>
                  </div>
                </div>
              </template>
              <a-empty v-else description="overview 暂无通知送达汇总" />
            </a-card>

            <a-card title="流程节点负载" :bordered="false" class="visual-card bar-card">
              <template v-if="dashboard.workflowLoad.length">
                <div
                  v-for="item in dashboard.workflowLoad.slice(0, 5)"
                  :key="item.key"
                  class="load-bar-row"
                >
                  <span>{{ item.label }}</span>
                  <div class="load-track">
                    <i :style="{ width: `${Math.min(item.percent, 100)}%` }" />
                  </div>
                  <strong>{{ item.percent }}%</strong>
                </div>
              </template>
              <a-empty v-else description="overview 暂无流程节点负载" />
            </a-card>
          </div>

          <div class="dashboard-lower">
            <a-card title="学业缺口概览" :bordered="false" class="visual-card summary-card">
              <template v-if="dashboard.academicGap.items.length">
                <p class="summary-intro">{{ dashboard.disclaimer }}</p>
                <div class="summary-grid">
                  <div
                    v-for="item in dashboard.academicGap.items"
                    :key="item.key"
                    :class="['summary-tile', item.key]"
                  >
                    <span>{{ item.title }}</span>
                    <strong>{{ item.count ?? 0 }}</strong>
                    <p>{{ item.description }}</p>
                  </div>
                </div>
              </template>
              <a-empty v-else description="当前筛选条件下暂无学业缺口摘要" />
            </a-card>

            <a-card class="gap-table-card" :title="dashboard.academicGap.title" :bordered="false">
              <a-form layout="inline" :model="academicGapFilters" class="filter-card compact" @finish="onAcademicGapSearch">
                <a-form-item label="关键字">
                  <a-input
                    v-model:value="academicGapFilters.keyword"
                    allow-clear
                    placeholder="学号或姓名"
                    style="width: 160px"
                  />
                </a-form-item>
                <a-form-item label="年级">
                  <a-input
                    v-model:value="academicGapFilters.grade_code"
                    allow-clear
                    placeholder="如 2022"
                    style="width: 110px"
                  />
                </a-form-item>
                <a-form-item label="专业">
                  <a-input
                    v-model:value="academicGapFilters.major_code"
                    allow-clear
                    placeholder="如 CS"
                    style="width: 110px"
                  />
                </a-form-item>
                <a-form-item label="风险">
                  <a-select
                    v-model:value="academicGapFilters.risk_level"
                    allow-clear
                    placeholder="全部"
                    style="width: 118px"
                  >
                    <a-select-option value="HIGH">高关注</a-select-option>
                    <a-select-option value="MEDIUM">待跟进</a-select-option>
                    <a-select-option value="LOW">低关注</a-select-option>
                  </a-select>
                </a-form-item>
                <a-form-item>
                  <a-space>
                    <a-button type="primary" html-type="submit" :loading="loadingAcademicGap">
                      <template #icon><SearchOutlined /></template>
                      查询
                    </a-button>
                    <a-button @click="resetAcademicGapFilters">
                      <template #icon><ReloadOutlined /></template>
                      重置
                    </a-button>
                  </a-space>
                </a-form-item>
              </a-form>

              <a-table
                :columns="academicGapColumns"
                :data-source="academicGapRows"
                :loading="loadingAcademicGap"
                :pagination="{
                  current: academicGapPagination.current,
                  pageSize: academicGapPagination.pageSize,
                  total: academicGapPagination.total,
                  showSizeChanger: true,
                }"
                :custom-row="academicGapRowProps"
                :row-class-name="academicGapRowClassName"
                row-key="student_id"
                size="small"
                @change="onAcademicGapTableChange"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'student'">
                    <div class="gap-student-name">{{ record.student_name }}</div>
                    <div class="detail-muted">{{ record.student_no }}</div>
                  </template>
                  <template v-else-if="column.key === 'risk_level'">
                    <a-tag :color="academicRiskColor(record as AcademicGapAggregateItem)">
                      {{ academicRiskLabel(record as AcademicGapAggregateItem) }}
                    </a-tag>
                  </template>
                  <template v-else-if="column.key === 'credits'">
                    <div>参考：{{ formatCredits(record.total_credits_required) }}</div>
                    <div class="detail-muted">已获：{{ formatCredits(record.total_credits_earned) }}</div>
                  </template>
                  <template v-else-if="column.key === 'credits_gap'">
                    <span :class="['gap-emphasis', academicRiskClass(record as AcademicGapAggregateItem)]">
                      {{ formatCredits(record.credits_gap) }}
                    </span>
                  </template>
                  <template v-else-if="column.key === 'warnings'">
                    <span v-if="record.data_warnings.length">
                      {{ record.data_warnings[0] }}
                    </span>
                    <span v-else class="detail-muted">-</span>
                  </template>
                  <template v-else-if="column.key === 'generated_at'">
                    {{ formatDateTime(record.generated_at) }}
                  </template>
                  <template v-else-if="column.key === 'actions'">
                    <a-button type="link" size="small" @click="openAcademicGapDetail(record.student_id)">
                      <template #icon><EyeOutlined /></template>
                      查看明细
                    </a-button>
                  </template>
                </template>
              </a-table>
            </a-card>
          </div>
        </section>

        <aside class="dashboard-side-panel">
          <div class="side-head">
            <strong>学业缺口详情</strong>
            <a-button type="text" size="small" :disabled="!selectedGapRow" @click="clearSelectedGap">
              <template #icon><CloseOutlined /></template>
            </a-button>
          </div>
          <template v-if="selectedGapRow">
            <div class="side-section student-card">
              <div class="side-avatar">{{ selectedGapRow.student_name.slice(0, 1) }}</div>
              <div>
                <strong>{{ selectedGapRow.student_name }}</strong>
                <p>{{ selectedGapRow.student_no }}</p>
                <p>{{ selectedGapRow.major_code || '-' }} · {{ selectedGapRow.grade_code || '-' }}</p>
              </div>
            </div>
            <a-spin :spinning="selectedGapDetailLoading">
              <div class="side-section">
                <h3>缺口描述</h3>
                <p>
                  当前参考要求 {{ formatCredits(selectedGapRow.total_credits_required) }}，
                  已获 {{ formatCredits(selectedGapRow.total_credits_earned) }}，
                  差额参考 {{ formatCredits(selectedGapRow.credits_gap) }}。
                </p>
                <p class="detail-muted">
                  风险等级：{{ academicRiskLabel(selectedGapRow) }} · 生成时间：{{ formatDateTime(selectedGapRow.generated_at) }}
                </p>
              </div>
              <div class="side-section">
                <h3>培养方案</h3>
                <p>{{ selectedGapDetail?.plan_name || '当前明细未返回培养方案名称' }}</p>
              </div>
              <div class="side-section">
                <h3>数据提示</h3>
                <ul v-if="selectedGapWarnings.length">
                  <li v-for="warning in selectedGapWarnings" :key="warning">{{ warning }}</li>
                </ul>
                <p v-else class="detail-muted">当前未返回额外 warning。</p>
              </div>
              <div class="side-section">
                <h3>模块概况</h3>
                <div v-if="selectedGapModules.length" class="module-list">
                  <div v-for="module in selectedGapModules.slice(0, 5)" :key="module.module_code" class="module-row">
                    <div>
                      <strong>{{ module.module_name }}</strong>
                      <p>{{ module.module_code }} · {{ module.module_type }}</p>
                    </div>
                    <div class="module-metrics">
                      <span>差额 {{ formatCredits(module.credits_gap) }}</span>
                      <span>已获 {{ formatCredits(module.credits_earned) }}</span>
                    </div>
                  </div>
                </div>
                <p v-else class="detail-muted">当前明细未返回模块差额。</p>
              </div>
              <div class="side-actions">
                <a-button @click="openAcademicGapDetail(selectedGapRow.student_id)">
                  <template #icon><EyeOutlined /></template>
                  查看完整明细
                </a-button>
                <a-button type="primary" @click="goToStudentProfile(selectedGapRow.student_id)">
                  <template #icon><CheckCircleOutlined /></template>
                  查看学生画像
                </a-button>
              </div>
            </a-spin>
          </template>
          <a-empty v-else description="请选择记录" />
        </aside>
      </div>
    </a-spin>

    <a-drawer
      :open="academicGapDrawerOpen"
      width="760"
      title="学业缺口明细"
      @close="closeAcademicGapDrawer"
    >
      <a-spin :spinning="academicGapDetailLoading">
        <template v-if="academicGapDetail">
          <a-alert
            type="warning"
            show-icon
            class="mb16"
            message="学业弱结论边界"
            :description="academicGapDetail.disclaimer"
          />

          <a-alert
            v-for="warning in academicGapDetail.data_warnings"
            :key="warning"
            type="warning"
            show-icon
            class="mb16"
            message="数据提示"
            :description="warning"
          />

          <a-descriptions :column="2" bordered size="small" class="mb16">
            <a-descriptions-item label="学生">
              {{ academicGapDetail.student_name }}（{{ academicGapDetail.student_no }}）
            </a-descriptions-item>
            <a-descriptions-item label="培养方案">
              {{ academicGapDetail.plan_name || '-' }}
            </a-descriptions-item>
            <a-descriptions-item label="年级">
              {{ academicGapDetail.grade_code || '-' }}
            </a-descriptions-item>
            <a-descriptions-item label="专业">
              {{ academicGapDetail.major_code || '-' }}
            </a-descriptions-item>
            <a-descriptions-item label="参考要求">
              {{ formatCredits(academicGapDetail.total_credits_required) }}
            </a-descriptions-item>
            <a-descriptions-item label="已获学分">
              {{ formatCredits(academicGapDetail.total_credits_earned) }}
            </a-descriptions-item>
            <a-descriptions-item label="生成时间" :span="2">
              {{ formatDateTime(academicGapDetail.generated_at) }}
            </a-descriptions-item>
          </a-descriptions>

          <a-table
            :columns="academicGapDetailColumns"
            :data-source="academicGapDetail.modules"
            :pagination="false"
            row-key="module_code"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'module'">
                <div class="gap-student-name">{{ record.module_name }}</div>
                <div class="detail-muted">{{ record.module_code }} · {{ record.module_type }}</div>
              </template>
              <template v-else-if="column.key === 'credits_required'">
                {{ formatCredits(record.credits_required) }}
              </template>
              <template v-else-if="column.key === 'credits_earned'">
                {{ formatCredits(record.credits_earned) }}
              </template>
              <template v-else-if="column.key === 'credits_gap'">
                <span :class="['gap-emphasis', record.credits_gap > 0 ? 'high' : 'low']">
                  {{ formatCredits(record.credits_gap) }}
                </span>
              </template>
              <template v-else-if="column.key === 'note'">
                <span v-if="record.note">{{ record.note }}</span>
                <span v-else class="detail-muted">-</span>
              </template>
            </template>
          </a-table>
        </template>
        <a-empty v-else-if="!academicGapDetailLoading" description="暂无学业缺口明细" />
      </a-spin>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  AlertOutlined,
  BellOutlined,
  CloseOutlined,
  FileDoneOutlined,
  FormOutlined,
  TeamOutlined,
  SearchOutlined,
  ReloadOutlined,
  EyeOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons-vue'
import {
  buildDashboardViewModel,
  deriveAcademicRiskLevel,
  type DashboardNoticeDatum,
  fetchAcademicGap,
  fetchAcademicGapList,
  fetchOverview,
  formatCredits,
  type AcademicGapAggregateItem,
  type AcademicGapResult,
  type OverviewResult,
} from '@/api/report'

const router = useRouter()
const overview = ref<OverviewResult | null>(null)
const loadingOverview = ref(false)
const loadingAcademicGap = ref(false)
const overviewError = ref('')
const academicGapError = ref('')

const overviewFilters = reactive<{ term_code?: string }>({})

const academicGapFilters = reactive<{
  keyword?: string
  grade_code?: string
  major_code?: string
  risk_level?: 'HIGH' | 'MEDIUM' | 'LOW'
}>({})

const academicGapRows = ref<AcademicGapAggregateItem[]>([])
const academicGapPagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
})

const academicGapDrawerOpen = ref(false)
const academicGapDetailLoading = ref(false)
const academicGapDetail = ref<AcademicGapResult | null>(null)
const selectedGapStudentId = ref<number | null>(null)
const selectedGapDetailLoading = ref(false)
const selectedGapDetail = ref<AcademicGapResult | null>(null)
const academicGapDetailCache = new Map<number, AcademicGapResult>()

const academicGapColumns = [
  { title: '学生', key: 'student', width: 180 },
  { title: '年级', dataIndex: 'grade_code', key: 'grade_code', width: 90 },
  { title: '专业', dataIndex: 'major_code', key: 'major_code', width: 90 },
  { title: '风险级别', key: 'risk_level', width: 100 },
  { title: '学分概况', key: 'credits', width: 150 },
  { title: '差额参考', key: 'credits_gap', width: 100 },
  { title: '数据提示', key: 'warnings' },
  { title: '生成时间', key: 'generated_at', width: 170 },
  { title: '操作', key: 'actions', width: 100 },
]

const academicGapDetailColumns = [
  { title: '模块', key: 'module' },
  { title: '参考要求', key: 'credits_required', width: 100 },
  { title: '已获学分', key: 'credits_earned', width: 100 },
  { title: '差额参考', key: 'credits_gap', width: 100 },
  { title: '备注', key: 'note', width: 220 },
]

const dashboard = computed(() => buildDashboardViewModel(overview.value, academicGapRows.value))
const selectedGapRow = computed(() => {
  if (selectedGapStudentId.value == null) return null
  return academicGapRows.value.find((item) => item.student_id === selectedGapStudentId.value) ?? null
})
const selectedGapWarnings = computed(() => {
  if (selectedGapDetail.value?.data_warnings?.length) {
    return selectedGapDetail.value.data_warnings
  }
  return selectedGapRow.value?.data_warnings ?? []
})
const selectedGapModules = computed(() => {
  const modules = selectedGapDetail.value?.modules ?? []
  return modules.filter((item) => item.credits_gap > 0 || Boolean(item.note))
})

const METRIC_ICON: Record<string, unknown> = {
  students: TeamOutlined,
  requests: FormOutlined,
  pending_approvals: FileDoneOutlined,
  notices: BellOutlined,
  deliveries: BellOutlined,
  overdue_nodes: AlertOutlined,
}

function metricIcon(key: string) {
  return METRIC_ICON[key] || FormOutlined
}

function noticeDeliveryPercent(item: DashboardNoticeDatum) {
  const maxValue = Math.max(...dashboard.value.noticeDelivery.map((row) => row.value), 0)
  if (maxValue <= 0) return 0
  return Math.max(0, Math.min(100, Math.round((item.value / maxValue) * 100)))
}

function formatDateTime(value?: string | null) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

async function loadOverview() {
  loadingOverview.value = true
  overviewError.value = ''
  try {
    const resp = await fetchOverview({ term_code: overviewFilters.term_code })
    overview.value = resp.data
  } catch {
    overview.value = null
    overviewError.value = '请稍后刷新，若持续失败请检查 overview 接口与当前登录态。'
  } finally {
    loadingOverview.value = false
  }
}

function resetOverviewFilters() {
  overviewFilters.term_code = undefined
  loadOverview()
}

async function loadAcademicGapList() {
  loadingAcademicGap.value = true
  academicGapError.value = ''
  try {
    const resp = await fetchAcademicGapList({
      keyword: academicGapFilters.keyword,
      grade_code: academicGapFilters.grade_code,
      major_code: academicGapFilters.major_code,
      risk_level: academicGapFilters.risk_level,
      page: academicGapPagination.current,
      page_size: academicGapPagination.pageSize,
    })
    academicGapRows.value = resp.data.items
    academicGapPagination.total = resp.data.meta.total
    syncSelectedGap()
  } catch {
    academicGapRows.value = []
    academicGapPagination.total = 0
    clearSelectedGap()
    academicGapError.value = '请检查 academic-gap 聚合接口是否可用，或稍后重试。'
  } finally {
    loadingAcademicGap.value = false
  }
}

function onAcademicGapSearch() {
  academicGapPagination.current = 1
  loadAcademicGapList()
}

function resetAcademicGapFilters() {
  academicGapFilters.keyword = undefined
  academicGapFilters.grade_code = undefined
  academicGapFilters.major_code = undefined
  academicGapFilters.risk_level = undefined
  academicGapPagination.current = 1
  loadAcademicGapList()
}

function onAcademicGapTableChange(pagination: { current?: number; pageSize?: number }) {
  academicGapPagination.current = pagination.current ?? academicGapPagination.current
  academicGapPagination.pageSize = pagination.pageSize ?? academicGapPagination.pageSize
  loadAcademicGapList()
}

function academicRiskLabel(item: AcademicGapAggregateItem) {
  const risk = deriveAcademicRiskLevel(item)
  if (risk === 'HIGH') return '高关注'
  if (risk === 'MEDIUM') return '待跟进'
  return '低关注'
}

function academicRiskColor(item: AcademicGapAggregateItem) {
  const risk = deriveAcademicRiskLevel(item)
  if (risk === 'HIGH') return 'red'
  if (risk === 'MEDIUM') return 'orange'
  return 'green'
}

function academicRiskClass(item: AcademicGapAggregateItem) {
  const risk = deriveAcademicRiskLevel(item)
  if (risk === 'HIGH') return 'high'
  if (risk === 'MEDIUM') return 'medium'
  return 'low'
}

function clearSelectedGap() {
  selectedGapStudentId.value = null
  selectedGapDetail.value = null
  selectedGapDetailLoading.value = false
}

function syncSelectedGap() {
  if (selectedGapStudentId.value == null) return
  if (!academicGapRows.value.some((item) => item.student_id === selectedGapStudentId.value)) {
    clearSelectedGap()
  }
}

async function loadGapDetailIntoPanel(studentId: number, force = false) {
  if (!force && academicGapDetailCache.has(studentId)) {
    selectedGapDetail.value = academicGapDetailCache.get(studentId) ?? null
    return
  }
  selectedGapDetailLoading.value = true
  try {
    const resp = await fetchAcademicGap(studentId)
    academicGapDetailCache.set(studentId, resp.data)
    if (selectedGapStudentId.value === studentId) {
      selectedGapDetail.value = resp.data
    }
  } catch {
    if (selectedGapStudentId.value === studentId) {
      selectedGapDetail.value = null
    }
  } finally {
    if (selectedGapStudentId.value === studentId) {
      selectedGapDetailLoading.value = false
    }
  }
}

async function selectAcademicGap(studentId: number, force = false) {
  selectedGapStudentId.value = studentId
  selectedGapDetail.value = academicGapDetailCache.get(studentId) ?? null
  await loadGapDetailIntoPanel(studentId, force)
}

function academicGapRowProps(record: AcademicGapAggregateItem) {
  return {
    class: 'selectable-gap-row',
    onClick: () => {
      void selectAcademicGap(record.student_id)
    },
  }
}

function academicGapRowClassName(record: AcademicGapAggregateItem) {
  return record.student_id === selectedGapStudentId.value
    ? 'selectable-gap-row selected-gap-row'
    : 'selectable-gap-row'
}

async function openAcademicGapDetail(studentId: number) {
  await selectAcademicGap(studentId)
  academicGapDrawerOpen.value = true
  academicGapDetailLoading.value = true
  try {
    if (academicGapDetailCache.has(studentId)) {
      academicGapDetail.value = academicGapDetailCache.get(studentId) ?? null
      return
    }
    const resp = await fetchAcademicGap(studentId)
    academicGapDetail.value = resp.data
    academicGapDetailCache.set(studentId, resp.data)
  } catch {
    academicGapDetail.value = null
  } finally {
    academicGapDetailLoading.value = false
  }
}

function closeAcademicGapDrawer() {
  academicGapDrawerOpen.value = false
  academicGapDetail.value = null
}

function goToStudentProfile(studentId: number) {
  void router.push({ name: 'student-profile', params: { studentId } })
}

onMounted(async () => {
  await Promise.all([loadOverview(), loadAcademicGapList()])
})
</script>

<style scoped>
.mb16 {
  margin-bottom: 16px;
}

.board-meta {
  color: #8c8c8c;
  font-size: 12px;
}

.operation-dashboard {
  padding-right: 394px;
}

.dashboard-board {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 14px;
  align-items: start;
}

.dashboard-canvas {
  min-width: 0;
}

.chart-mosaic {
  display: grid;
  grid-template-columns: 1.08fr 1fr 1fr;
  gap: 14px;
  margin-bottom: 14px;
}

.dashboard-lower {
  display: grid;
  grid-template-columns: minmax(260px, 0.78fr) minmax(0, 1.42fr);
  gap: 14px;
  align-items: start;
}

.visual-card {
  min-height: 100%;
}

.delivery-list {
  display: grid;
  gap: 12px;
}

.delivery-row {
  display: grid;
  gap: 10px;
  padding: 12px 14px;
  background: #fbfcfe;
  border: 1px solid var(--line-soft);
  border-radius: 12px;
}

.delivery-row__meta,
.delivery-row__value,
.module-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.delivery-row__meta strong,
.module-row strong {
  color: var(--text);
  font-size: 14px;
}

.delivery-row__meta span,
.module-row p,
.summary-tile p {
  margin: 0;
  color: var(--text-3);
  font-size: 12px;
  line-height: 1.6;
}

.delivery-row__value strong {
  color: var(--ruc-red);
  font-family: var(--font-number);
  font-size: 20px;
}

.delivery-row__track {
  flex: 1;
  min-width: 0;
  height: 8px;
  overflow: hidden;
  background: #edf0f5;
  border-radius: 999px;
}

.delivery-row__track i {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, var(--ruc-red), #ef7f62);
  border-radius: inherit;
}

.summary-intro {
  margin: 0 0 12px;
  color: var(--text-3);
  font-size: 12px;
  line-height: 1.8;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.summary-tile {
  min-height: 148px;
  padding: 14px;
  background: #fbfcfe;
  border: 1px solid var(--line-soft);
  border-radius: 12px;
}

.summary-tile span {
  display: block;
  color: var(--text-2);
  font-size: 13px;
}

.summary-tile strong {
  display: block;
  margin: 10px 0 8px;
  color: var(--text);
  font-family: var(--font-number);
  font-size: 28px;
  line-height: 1;
}

.summary-tile.high strong {
  color: #c40018;
}

.summary-tile.medium strong {
  color: #d46b08;
}

.summary-tile.low strong {
  color: #389e0d;
}

.donut-row {
  display: grid;
  grid-template-columns: 144px minmax(0, 1fr);
  gap: 14px;
  align-items: center;
}

.donut-visual {
  position: relative;
  display: grid;
  width: 144px;
  height: 144px;
  place-items: center;
  border-radius: 999px;
  background:
    radial-gradient(circle, #fff 0 43%, transparent 44%),
    conic-gradient(#c40018 0 35%, #e15461 35% 58%, #f08b66 58% 73%, #f3c46b 73% 86%, #dfe3ea 86% 100%);
}

.donut-core {
  display: grid;
  width: 82px;
  height: 82px;
  place-items: center;
  border-radius: 999px;
  background: #fff;
  box-shadow: inset 0 0 0 1px var(--line-soft);
}

.donut-core strong {
  color: var(--text);
  font-size: 24px;
  line-height: 1;
}

.donut-core span {
  margin-top: -18px;
  color: var(--text-3);
  font-size: 12px;
}

.donut-legend {
  display: grid;
  gap: 9px;
}

.legend-line {
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
  color: var(--text-2);
  font-size: 12px;
}

.legend-line strong {
  color: var(--text);
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--ruc-red);
}

.trend-svg {
  width: 100%;
  height: 150px;
}

.trend-svg line {
  stroke: #eef1f5;
  stroke-width: 1;
}

.trend-svg polyline,
.side-trend polyline {
  fill: none;
  stroke: var(--ruc-red);
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 3;
}

.trend-svg circle,
.side-trend circle {
  fill: #fff;
  stroke: var(--ruc-red);
  stroke-width: 3;
}

.trend-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.trend-summary div {
  padding: 10px 12px;
  background: #fff7f8;
  border: 1px solid #ffe1e6;
  border-radius: 10px;
}

.trend-summary strong {
  display: block;
  color: var(--ruc-red);
  font-size: 22px;
  line-height: 1.1;
}

.trend-summary span {
  color: var(--text-2);
  font-size: 12px;
}

.load-bar-row {
  display: grid;
  grid-template-columns: 78px minmax(0, 1fr) 42px;
  gap: 10px;
  align-items: center;
  min-height: 28px;
  color: var(--text-2);
  font-size: 12px;
}

.load-track {
  height: 12px;
  overflow: hidden;
  background: #eef0f3;
  border-radius: 999px;
}

.load-track i {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, var(--ruc-red), #e75a5f);
  border-radius: inherit;
}

.load-bar-row strong {
  color: var(--text-2);
  font-size: 12px;
  text-align: right;
}

.risk-card {
  background: linear-gradient(135deg, #fff6f4, #fff) !important;
  border-color: #ffd7d1 !important;
}

.risk-card-body {
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr);
  gap: 12px;
  color: var(--text-2);
  font-size: 12px;
  line-height: 1.7;
}

.risk-card-body > .anticon {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  color: var(--ruc-red);
  background: #ffe1e6;
  border-radius: 999px;
  font-size: 24px;
}

.risk-card-body strong {
  color: var(--ruc-red);
  font-size: 14px;
}

.risk-card-body p {
  margin: 8px 0;
}

.risk-card-body ul,
.dashboard-side-panel ul {
  margin: 8px 0 0;
  padding-left: 16px;
}

.confidence {
  margin-top: 12px;
}

.confidence span {
  display: block;
  margin-bottom: 6px;
  color: var(--text);
  font-weight: 600;
}

.confidence i {
  display: block;
  width: 62%;
  height: 6px;
  background: linear-gradient(90deg, var(--ruc-red), #f0a3a3);
  border-radius: 999px;
}

.gap-table-card :deep(.filter-card) {
  margin: 0 0 10px;
  padding: 0;
  background: transparent;
  border: 0;
  box-shadow: none;
}

.dashboard-side-panel {
  position: fixed;
  top: 58px;
  right: 0;
  bottom: 0;
  z-index: 12;
  width: 380px;
  overflow-y: auto;
  padding: 20px 20px 18px;
  background: #fff;
  border: 1px solid var(--line-soft);
  border-top: 0;
  border-right: 0;
  border-bottom: 0;
  border-radius: 0;
  box-shadow: var(--shadow-card);
}

.side-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: -2px -2px 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--line-soft);
}

.side-head strong {
  font-size: 16px;
}

.side-head :deep(.ant-btn) {
  color: var(--text-3);
}

.side-section {
  padding: 14px 0;
  border-bottom: 1px solid var(--line-soft);
}

.side-section h3 {
  margin: 0 0 8px;
  color: var(--text);
  font-size: 14px;
}

.side-section p,
.side-section li {
  margin: 0;
  color: var(--text-2);
  font-size: 12px;
  line-height: 1.7;
}

.student-card {
  display: grid;
  grid-template-columns: 58px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
}

.side-avatar {
  display: grid;
  width: 56px;
  height: 56px;
  place-items: center;
  color: #fff;
  background: var(--ruc-red);
  border-radius: 999px;
  font-size: 24px;
  font-weight: 800;
}

.side-trend {
  width: 100%;
  height: 118px;
  background:
    repeating-linear-gradient(0deg, transparent 0 28px, #eef1f5 28px 29px),
    linear-gradient(180deg, #fff, #fff7f8);
  border-radius: 10px;
}

.side-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 16px;
}

.module-list {
  display: grid;
  gap: 10px;
}

.module-row {
  align-items: flex-start;
  padding: 12px;
  background: #fbfcfe;
  border: 1px solid var(--line-soft);
  border-radius: 12px;
}

.module-metrics {
  display: grid;
  justify-items: end;
  gap: 4px;
  color: var(--text-2);
  font-size: 12px;
}

:deep(.selectable-gap-row > td) {
  cursor: pointer;
}

:deep(.selected-gap-row > td) {
  background: #fff4f5 !important;
}

@media (max-width: 1320px) {
  .operation-dashboard {
    padding-right: 0;
  }

  .dashboard-side-panel {
    position: static;
    width: auto;
    border: 1px solid var(--line-soft);
    border-radius: 12px;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }
}

.chart-stack {
  display: grid;
  gap: 18px;
}

.chart-row {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.chart-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.chart-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.chart-label {
  color: #262626;
  font-weight: 600;
}

.chart-value {
  color: #8b3a2e;
  font-weight: 600;
}

.chart-helper {
  margin-top: 8px;
  color: #8c8c8c;
  font-size: 12px;
  line-height: 1.6;
}

.notice-grid {
  display: grid;
  gap: 12px;
}

.notice-item {
  padding: 14px 16px;
  border-radius: 10px;
  background: #fff7f8;
  border: 1px solid #ffe3e8;
}

.notice-value {
  color: var(--ruc-red);
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
}

.notice-label {
  margin-top: 8px;
  color: #262626;
  font-weight: 600;
}

.academic-gap-intro {
  margin-bottom: 12px;
  color: #8c8c8c;
  line-height: 1.6;
}

.academic-gap-intro.subtle {
  margin-top: -4px;
  font-size: 12px;
}

.gap-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.gap-item {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.gap-item:last-child {
  border-bottom: none;
}

.gap-title {
  color: #262626;
  font-weight: 600;
}

.gap-count {
  color: var(--ruc-red);
  font-size: 20px;
  font-weight: 700;
  line-height: 1;
}

.mt16 {
  margin-top: 16px;
}

.gap-student-name {
  color: var(--text);
  font-weight: 600;
}

.detail-muted {
  color: #8c8c8c;
  font-size: 12px;
  line-height: 1.6;
}

.gap-emphasis {
  font-weight: 700;
}

.gap-emphasis.high {
  color: #cf1322;
}

.gap-emphasis.medium {
  color: #d46b08;
}

.gap-emphasis.low {
  color: #389e0d;
}
</style>
