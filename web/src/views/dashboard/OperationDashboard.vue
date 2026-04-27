<template>
  <div class="operation-dashboard">
    <a-page-header title="运营看板" sub-title="学院事务运营、通知触达与学业缺口弱提示" />

    <a-alert
      type="info"
      show-icon
      class="mb16"
      message="overview 弱提示边界"
      :description="dashboard.disclaimer"
    />

    <div v-if="dashboard.generatedAt" class="board-meta mb16">
      数据生成时间：{{ formatDateTime(dashboard.generatedAt) }} · 当前仅消费 canonical overview
    </div>

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
        <div v-for="metric in dashboard.metrics" :key="metric.key" class="metric-tile">
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

      <a-row :gutter="[16, 16]" class="mb16">
        <a-col :xs="24" :xl="14">
          <a-card title="事务申请分布" :bordered="false" class="visual-card">
            <template v-if="dashboard.requestDistribution.length">
              <div class="chart-stack">
                <div
                  v-for="item in dashboard.requestDistribution"
                  :key="item.key"
                  class="chart-row"
                >
                  <div class="chart-head">
                    <span class="chart-label">{{ item.label }}</span>
                    <span class="chart-value">{{ item.value }}</span>
                  </div>
                  <a-progress
                    :percent="item.percent"
                    :show-info="false"
                    stroke-color="#8b3a2e"
                  />
                  <div class="chart-helper">{{ item.helper }}</div>
                </div>
              </div>
            </template>
            <a-empty v-else description="overview 暂无事务申请分布" />
          </a-card>
        </a-col>

        <a-col :xs="24" :xl="10">
          <a-card title="通知触达概况" :bordered="false" class="visual-card">
            <template v-if="dashboard.noticeDelivery.length">
              <div class="notice-grid">
                <div
                  v-for="item in dashboard.noticeDelivery"
                  :key="item.key"
                  class="notice-item"
                >
                  <div class="notice-value">{{ item.value }}</div>
                  <div class="notice-label">{{ item.label }}</div>
                  <div class="chart-helper">{{ item.helper }}</div>
                </div>
              </div>
            </template>
            <a-empty v-else description="overview 暂无通知送达汇总" />
          </a-card>
        </a-col>
      </a-row>

      <a-row :gutter="[16, 16]">
        <a-col :xs="24" :xl="14">
          <a-card title="流程节点负载" :bordered="false" class="visual-card">
            <template v-if="dashboard.workflowLoad.length">
              <div class="chart-stack">
                <div
                  v-for="item in dashboard.workflowLoad"
                  :key="item.key"
                  class="chart-row"
                >
                  <div class="chart-head">
                    <span class="chart-label">{{ item.label }}</span>
                    <span class="chart-value">{{ item.value }}</span>
                  </div>
                  <a-progress
                    :percent="item.percent"
                    :show-info="false"
                    status="active"
                    stroke-color="#c2410c"
                  />
                  <div class="chart-helper">{{ item.helper }}</div>
                </div>
              </div>
            </template>
            <a-empty v-else description="overview 暂无流程节点负载" />
          </a-card>
        </a-col>
        <a-col :xs="24" :xl="10">
          <a-card title="弱结论边界" :bordered="false" class="visual-card risk-card">
            <div class="academic-gap-intro">
              {{ dashboard.academicGap.description }}
            </div>
            <div class="academic-gap-intro subtle">
              当前分布仅基于“当前筛选 + 当前页列表”生成，不代表本次筛选下的全量统计结果。
            </div>
            <template v-if="dashboard.academicGap.items.length">
              <div
                v-for="item in dashboard.academicGap.items"
                :key="item.key"
                class="gap-item"
              >
                <div class="gap-title-row">
                  <div class="gap-title">{{ item.title }}</div>
                  <div class="gap-count">{{ item.count ?? 0 }}</div>
                </div>
                <div class="chart-helper">{{ item.description }}</div>
              </div>
            </template>
            <a-empty v-else description="当前页暂无 academic-gap 汇总卡片" />
          </a-card>
        </a-col>
      </a-row>

      <a-card class="mt16" :title="dashboard.academicGap.title" :bordered="false">
        <a-form layout="inline" :model="academicGapFilters" class="filter-card compact" @finish="onAcademicGapSearch">
          <a-form-item label="关键字">
            <a-input
              v-model:value="academicGapFilters.keyword"
              allow-clear
              placeholder="学号或姓名"
              style="width: 180px"
            />
          </a-form-item>
          <a-form-item label="年级">
            <a-input
              v-model:value="academicGapFilters.grade_code"
              allow-clear
              placeholder="如 2022"
              style="width: 120px"
            />
          </a-form-item>
          <a-form-item label="专业">
            <a-input
              v-model:value="academicGapFilters.major_code"
              allow-clear
              placeholder="如 CS"
              style="width: 120px"
            />
          </a-form-item>
          <a-form-item label="风险级别">
            <a-select
              v-model:value="academicGapFilters.risk_level"
              allow-clear
              placeholder="全部"
              style="width: 140px"
            >
              <a-select-option value="HIGH">高关注</a-select-option>
              <a-select-option value="MEDIUM">待跟进</a-select-option>
              <a-select-option value="LOW">低关注</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item>
            <a-space>
              <a-button type="primary" html-type="submit" :loading="loadingAcademicGap">
                查询
              </a-button>
              <a-button @click="resetAcademicGapFilters">重置</a-button>
            </a-space>
          </a-form-item>
        </a-form>

        <div class="academic-gap-intro mb16">
          当前列表仅作学业缺口弱提示，不输出毕业、预警等强结论。上方右侧卡片与下方表格摘要都只基于“当前筛选 + 当前页”可见数据生成。点击“查看明细”可下钻到单学生 canonical academic-gap 详情。
        </div>

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
          row-key="student_id"
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
                查看明细
              </a-button>
            </template>
          </template>
        </a-table>
      </a-card>
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
import {
  AlertOutlined,
  BellOutlined,
  FileDoneOutlined,
  FormOutlined,
  TeamOutlined,
} from '@ant-design/icons-vue'
import {
  buildDashboardViewModel,
  deriveAcademicRiskLevel,
  fetchAcademicGap,
  fetchAcademicGapList,
  fetchOverview,
  formatCredits,
  type AcademicGapAggregateItem,
  type AcademicGapResult,
  type OverviewResult,
} from '@/api/report'

const overview = ref<OverviewResult | null>(null)
const loadingOverview = ref(false)
const loadingAcademicGap = ref(false)
const overviewError = ref('')
const academicGapError = ref('')

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
    const resp = await fetchOverview()
    overview.value = resp.data
  } catch {
    overview.value = null
    overviewError.value = '请稍后刷新，若持续失败请检查 overview 接口与当前登录态。'
  } finally {
    loadingOverview.value = false
  }
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
  } catch {
    academicGapRows.value = []
    academicGapPagination.total = 0
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

async function openAcademicGapDetail(studentId: number) {
  academicGapDrawerOpen.value = true
  academicGapDetailLoading.value = true
  try {
    const resp = await fetchAcademicGap(studentId)
    academicGapDetail.value = resp.data
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
