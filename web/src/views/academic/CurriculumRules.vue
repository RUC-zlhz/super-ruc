<template>
  <div class="curriculum-page">
    <a-page-header title="培养方案管理" sub-title="培养方案、开课记录与课程等价关系维护" />

    <div class="metric-grid">
      <div v-for="metric in metrics" :key="metric.key" class="metric-tile">
        <span class="metric-icon"><component :is="metric.icon" /></span>
        <div class="metric-label">{{ metric.label }}</div>
        <div class="metric-value">{{ metric.value }}</div>
        <div class="metric-sub">{{ metric.sub }}</div>
      </div>
    </div>

    <a-form layout="inline" class="filter-card curriculum-filter" @finish="refreshCurriculum">
      <a-form-item label="年级">
        <a-input v-model:value="planFilters.grade_code" placeholder="年级代码" allow-clear />
      </a-form-item>
      <a-form-item label="专业">
        <a-input v-model:value="planFilters.major_code" placeholder="专业代码" allow-clear />
      </a-form-item>
      <a-form-item label="学期">
        <a-input v-model:value="offeringFilters.term_code" placeholder="如 2026-SPRING" allow-clear />
      </a-form-item>
      <a-form-item>
          <a-button type="primary" html-type="submit">
            <template #icon><SearchOutlined /></template>
            查询
          </a-button>
        </a-form-item>
    </a-form>

    <div class="curriculum-workbench">
      <section class="plan-rail panel-card">
        <div class="panel-head">
          <div>
            <div class="panel-title">培养方案列表</div>
            <div class="panel-sub">按年级、专业筛选后选择方案</div>
          </div>
          <a-tag color="red">{{ planPagination.total || plans.length }} 个</a-tag>
        </div>
        <a-spin :spinning="planLoading">
          <div v-if="plans.length" class="plan-list">
            <button
              v-for="plan in plans"
              :key="plan.id"
              class="plan-card"
              :class="{ active: selectedPlan?.id === plan.id }"
              type="button"
              @click="selectPlan(plan)"
            >
              <span class="plan-name">{{ plan.plan_name }}</span>
              <span class="plan-meta">{{ plan.major_code || '全部专业' }} · {{ plan.grade_code || '全年级' }}</span>
              <span class="plan-foot">
                <a-tag :color="plan.is_active ? 'green' : 'default'">{{ plan.is_active ? '启用' : '停用' }}</a-tag>
                <span>总学分 {{ plan.total_credits_required ?? '-' }}</span>
              </span>
            </button>
          </div>
          <a-empty v-else image="simple" description="暂无培养方案" />
        </a-spin>
      </section>

      <section class="module-board">
        <a-card :bordered="false" class="selected-plan-card">
          <div class="selected-plan-head">
            <div>
              <div class="panel-title">{{ selectedPlan?.plan_name || '请选择培养方案' }}</div>
              <div class="panel-sub">
                {{ selectedPlan ? `${selectedPlan.grade_code || '全年级'} / ${selectedPlan.major_code || '全部专业'}` : '选择左侧方案后查看模块与课程' }}
              </div>
            </div>
            <a-tag color="red">模块 {{ modules.length }}</a-tag>
          </div>
          <a-table
            :columns="moduleCols"
            :data-source="modules"
            :loading="moduleLoading"
            :pagination="false"
            row-key="id"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'module_type'">
                <a-tag :color="record.module_type === 'REQUIRED' ? 'red' : 'blue'">
                  {{ moduleTypeLabel(record.module_type) }}
                </a-tag>
              </template>
            </template>
          </a-table>
        </a-card>

        <a-card :bordered="false" title="开课记录" class="mt16">
          <a-table
            :columns="offeringCols"
            :data-source="offerings"
            :loading="offeringLoading"
            :pagination="offeringPagination"
            row-key="id"
            size="small"
            @change="onOfferingTableChange"
          />
        </a-card>
      </section>

      <aside class="equiv-panel panel-card">
        <div class="panel-head">
          <div>
            <div class="panel-title">课程等价关系</div>
            <div class="panel-sub">查看替代规则与课程映射</div>
          </div>
          <a-tag color="orange">{{ equivalences.length }} 条</a-tag>
        </div>
        <a-table
          :columns="equivCols"
          :data-source="equivalences"
          :loading="equivLoading"
          :pagination="{ pageSize: 6, size: 'small' }"
          row-key="id"
          size="small"
        />
        <div class="equiv-note">
          完全替代、条件替代与部分替代需结合培养方案模块要求共同判断。
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  BookOutlined,
  ClusterOutlined,
  NodeIndexOutlined,
  ReadOutlined,
  SearchOutlined
} from '@ant-design/icons-vue'
import { get } from '@/utils/request'
import type { ApiEnvelope } from '@/utils/request'
import type { Paginated } from '@/api/types'

const metrics = computed(() => [
  {
    key: 'plans',
    label: '培养方案数',
    value: plans.value.length,
    sub: '当前筛选结果',
    icon: BookOutlined,
  },
  {
    key: 'modules',
    label: '模块数',
    value: modules.value.length,
    sub: selectedPlan.value ? selectedPlan.value.plan_name : '最近查看方案',
    icon: ClusterOutlined,
  },
  {
    key: 'offerings',
    label: '课程数',
    value: offeringPagination.total || offerings.value.length,
    sub: '开课记录',
    icon: ReadOutlined,
  },
  {
    key: 'equivalences',
    label: '等价关系数',
    value: equivalences.value.length,
    sub: '课程替代规则',
    icon: NodeIndexOutlined,
  },
])

type CurriculumModule = {
  id: number
  module_code: string
  module_name: string
  module_type: string
  credits_required: number
  courses?: Record<string, unknown>[] | null
  sort_order: number
}

type CurriculumPlanBrief = {
  id: number
  grade_code: string
  major_code: string
  plan_name: string
  version_label?: string | null
  total_credits_required?: number | null
  is_active: boolean
}

type CurriculumPlanDetail = CurriculumPlanBrief & {
  modules: CurriculumModule[]
}

type CourseOffering = {
  id: number
  term_code: string
  course_code: string
  course_name: string
  credits: number
  course_type?: string | null
  teacher?: string | null
}

type CourseEquivalence = {
  id: number
  source_course_code: string
  source_course_name?: string | null
  target_course_code: string
  target_course_name?: string | null
  ratio: number
  is_active: boolean
}

// ---------- 培养方案 ----------
const planFilters = reactive<{ grade_code?: string; major_code?: string }>({})
const plans = ref<CurriculumPlanBrief[]>([])
const planLoading = ref(false)
const planPagination = reactive({ current: 1, pageSize: 20, total: 0 })

async function loadPlans() {
  planLoading.value = true
  try {
    const resp = await get<ApiEnvelope<Paginated<CurriculumPlanBrief>>>('/admin/curriculum/plans', {
      params: {
        ...planFilters,
        page: planPagination.current,
        size: planPagination.pageSize,
      },
    })
    plans.value = resp.data.items
    planPagination.total = resp.data.meta.total
    if (!selectedPlan.value || !plans.value.some((plan) => plan.id === selectedPlan.value?.id)) {
      if (plans.value[0]) {
        await selectPlan(plans.value[0])
      } else {
        selectedPlan.value = null
        modules.value = []
      }
    }
  } finally {
    planLoading.value = false
  }
}

// ---------- 模块 ----------
const moduleCols = [
  { title: '编码', dataIndex: 'module_code', key: 'module_code', width: 120 },
  { title: '名称', dataIndex: 'module_name', key: 'module_name' },
  { title: '类型', key: 'module_type', width: 100 },
  { title: '要求学分', dataIndex: 'credits_required', key: 'credits_required', width: 100 },
]
const selectedPlan = ref<CurriculumPlanBrief | null>(null)
const modules = ref<CurriculumModule[]>([])
const moduleLoading = ref(false)

function moduleTypeLabel(value?: string | null) {
  return {
    REQUIRED: '必修',
    ELECTIVE: '选修',
    GENERAL: '通识',
    PRACTICE: '实践',
    OTHER: '其他',
  }[value || ''] || value || '-'
}

async function selectPlan(plan: CurriculumPlanBrief) {
  selectedPlan.value = plan
  moduleLoading.value = true
  try {
    const resp = await get<ApiEnvelope<CurriculumPlanDetail>>(`/admin/curriculum/plans/${plan.id}`)
    selectedPlan.value = resp.data
    modules.value = [...(resp.data.modules || [])].sort((a, b) => a.sort_order - b.sort_order)
  } finally {
    moduleLoading.value = false
  }
}

// ---------- 开课记录 ----------
const offeringCols = [
  { title: '课程编码', dataIndex: 'course_code', key: 'course_code', width: 120 },
  { title: '课程名', dataIndex: 'course_name', key: 'course_name' },
  { title: '学期', dataIndex: 'term_code', key: 'term_code', width: 120 },
  { title: '学分', dataIndex: 'credits', key: 'credits', width: 80 },
  { title: '教师', dataIndex: 'teacher', key: 'teacher', width: 120 },
]
const offeringFilters = reactive<{ term_code?: string }>({})
const offerings = ref<CourseOffering[]>([])
const offeringLoading = ref(false)
const offeringPagination = reactive({ current: 1, pageSize: 20, total: 0 })

async function loadOfferings() {
  offeringLoading.value = true
  try {
    const resp = await get<ApiEnvelope<Paginated<CourseOffering>>>('/admin/curriculum/offerings', {
      params: { ...offeringFilters, page: offeringPagination.current, size: offeringPagination.pageSize },
    })
    offerings.value = resp.data.items
    offeringPagination.total = resp.data.meta.total
  } finally {
    offeringLoading.value = false
  }
}

function onOfferingTableChange(p: any) {
  offeringPagination.current = p.current
  offeringPagination.pageSize = p.pageSize
  loadOfferings()
}

// ---------- 课程等价 ----------
const equivCols = [
  { title: '源课程', dataIndex: 'source_course_code', key: 'source_course_code', width: 140 },
  { title: '源课程名', dataIndex: 'source_course_name', key: 'source_course_name' },
  { title: '目标课程', dataIndex: 'target_course_code', key: 'target_course_code', width: 140 },
  { title: '目标课程名', dataIndex: 'target_course_name', key: 'target_course_name' },
  { title: '比例', dataIndex: 'ratio', key: 'ratio', width: 80 },
  { title: '启用', dataIndex: 'is_active', key: 'is_active', width: 80 },
]
const equivalences = ref<CourseEquivalence[]>([])
const equivLoading = ref(false)

async function loadEquivalences() {
  equivLoading.value = true
  try {
    const resp = await get<ApiEnvelope<Paginated<CourseEquivalence>>>('/admin/curriculum/equivalences')
    equivalences.value = resp.data.items
  } finally {
    equivLoading.value = false
  }
}

async function refreshCurriculum() {
  offeringPagination.current = 1
  await Promise.all([loadPlans(), loadOfferings()])
}

onMounted(() => {
  loadPlans()
  loadOfferings()
  loadEquivalences()
})
</script>

<style scoped>
.curriculum-filter {
  margin-bottom: 14px;
}

.curriculum-workbench {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr) 360px;
  gap: 16px;
  align-items: start;
}

.plan-rail,
.equiv-panel {
  padding: 16px;
}

.panel-head,
.selected-plan-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.panel-title {
  color: var(--text);
  font-size: 17px;
  font-weight: 700;
}

.panel-sub {
  margin-top: 5px;
  color: var(--text-3);
  font-size: 12px;
  line-height: 1.5;
}

.plan-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.plan-card {
  display: flex;
  width: 100%;
  padding: 13px 14px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius);
  background: #fff;
  color: inherit;
  text-align: left;
  cursor: pointer;
  flex-direction: column;
  gap: 7px;
  transition: border-color 0.18s ease, background 0.18s ease, box-shadow 0.18s ease;
}

.plan-card:hover,
.plan-card.active {
  border-color: rgba(176, 0, 24, 0.35);
  background: linear-gradient(135deg, #fff7f8, #fff);
  box-shadow: 0 8px 18px rgba(176, 0, 24, 0.08);
}

.plan-name {
  color: var(--text);
  font-weight: 700;
  line-height: 1.35;
}

.plan-meta,
.plan-foot {
  color: var(--text-3);
  font-size: 12px;
}

.plan-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.module-board {
  min-width: 0;
}

.selected-plan-card :deep(.ant-card-body) {
  padding: 16px !important;
}

.equiv-panel {
  position: sticky;
  top: 86px;
}

.equiv-note {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: var(--radius);
  background: #fff8f0;
  color: #8a5b13;
  font-size: 12px;
  line-height: 1.7;
}

@media (max-width: 1440px) {
  .curriculum-workbench {
    grid-template-columns: 280px minmax(0, 1fr);
  }

  .equiv-panel {
    position: static;
    grid-column: 1 / -1;
  }
}

@media (max-width: 980px) {
  .curriculum-workbench {
    grid-template-columns: 1fr;
  }
}
</style>
