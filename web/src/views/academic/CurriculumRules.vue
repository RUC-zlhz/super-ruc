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
      <a-form-item>
        <a-button @click="openPlanEditor()">
          <template #icon><PlusOutlined /></template>
          新增方案
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
                <span>总学分 {{ formatCredits(plan.total_credits_required) }}</span>
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
            <a-space wrap>
              <a-tag color="red">模块 {{ modules.length }}</a-tag>
              <a-button size="small" :disabled="!canEditSelectedPlan" @click="openModuleEditor()">
                <template #icon><PlusOutlined /></template>
                新增模块
              </a-button>
              <a-button size="small" :disabled="!canEditSelectedPlan" @click="openPlanEditor(selectedPlanDetail)">
                <template #icon><EditOutlined /></template>
                编辑方案
              </a-button>
              <a-popconfirm title="确定删除当前培养方案？" :disabled="!canEditSelectedPlan" @confirm="deleteSelectedPlan">
                <a-button size="small" danger :disabled="!canEditSelectedPlan">
                  <template #icon><DeleteOutlined /></template>
                  删除方案
                </a-button>
              </a-popconfirm>
            </a-space>
          </div>
          <a-table
            :columns="moduleCols"
            :data-source="modules"
            :loading="moduleLoading || savingPlan"
            :pagination="false"
            row-key="module_code"
            size="small"
           :scroll="{ x: 'max-content' }">
            <template #bodyCell="{ column, record, index }">
              <template v-if="column.key === 'module_type'">
                <a-tag :color="record.module_type === 'REQUIRED' ? 'red' : 'blue'">
                  {{ moduleTypeLabel(record.module_type) }}
                </a-tag>
              </template>
              <template v-else-if="column.key === 'courses'">
                {{ normalizeCourses(record.courses).length }} 门
              </template>
              <template v-else-if="column.key === 'actions'">
                <a-space>
                  <a-button type="link" size="small" @click="openCourseEditor(asModule(record))">
                    新增课程
                  </a-button>
                  <a-button type="link" size="small" @click="openModuleEditor(asModule(record), index)">
                    编辑
                  </a-button>
                  <a-popconfirm title="确定删除该模块及其课程？" @confirm="deleteModule(index)">
                    <a-button type="link" danger size="small">删除</a-button>
                  </a-popconfirm>
                </a-space>
              </template>
            </template>
            <template #expandedRowRender="{ record }">
              <div class="course-detail">
                <div class="course-detail-head">
                  <span>课程明细</span>
                  <a-button size="small" type="primary" @click="openCourseEditor(asModule(record))">
                    <template #icon><PlusOutlined /></template>
                    新增课程
                  </a-button>
                </div>
                <a-table
                  :columns="courseCols"
                  :data-source="normalizeCourses(record.courses)"
                  :pagination="{ pageSize: 8, size: 'small' }"
                  :row-key="courseRowKey"
                  size="small"
                 :scroll="{ x: 'max-content' }">
                  <template #bodyCell="{ column, record: course, index }">
                    <template v-if="column.key === 'credits'">
                      {{ formatCredits(course.credits) }}
                    </template>
                    <template v-else-if="column.key === 'actions'">
                      <a-space>
                        <a-button type="link" size="small" @click="openCourseEditor(asModule(record), course, index)">
                          编辑
                        </a-button>
                        <a-popconfirm title="确定删除该课程？" @confirm="deleteCourse(asModule(record), index)">
                          <a-button type="link" danger size="small">删除</a-button>
                        </a-popconfirm>
                      </a-space>
                    </template>
                  </template>
                </a-table>
              </div>
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
           :scroll="{ x: 'max-content' }" />
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
         :scroll="{ x: 'max-content' }" />
        <div class="equiv-note">
          完全替代、条件替代与部分替代需结合培养方案模块要求共同判断。
        </div>
      </aside>
    </div>

    <a-drawer
      :open="planDrawer.open"
      :title="planDrawer.editingId ? '编辑培养方案' : '新增培养方案'"
      width="520"
      @close="closePlanEditor"
    >
      <a-form layout="vertical" :model="planForm" @finish="submitPlan">
        <a-form-item label="方案名称" required>
          <a-input v-model:value="planForm.plan_name" />
        </a-form-item>
        <a-form-item label="年级" required>
          <a-input v-model:value="planForm.grade_code" :disabled="!!planDrawer.editingId" />
        </a-form-item>
        <a-form-item label="专业" required>
          <a-input v-model:value="planForm.major_code" :disabled="!!planDrawer.editingId" />
        </a-form-item>
        <a-form-item label="版本">
          <a-input v-model:value="planForm.version_label" :disabled="!!planDrawer.editingId" />
        </a-form-item>
        <a-form-item label="总学分">
          <a-input-number v-model:value="planForm.total_credits_required" :min="0" :precision="1" class="full-input" />
        </a-form-item>
        <a-form-item label="生效日期">
          <a-input v-model:value="planForm.effective_from" placeholder="YYYY-MM-DD" />
        </a-form-item>
        <a-form-item label="启用">
          <a-switch v-model:checked="planForm.is_active" />
        </a-form-item>
        <a-form-item label="备注">
          <a-textarea v-model:value="planForm.note" :rows="3" />
        </a-form-item>
        <a-form-item>
          <a-space>
            <a-button type="primary" html-type="submit" :loading="savingPlan">
              <template #icon><SaveOutlined /></template>
              保存
            </a-button>
            <a-button @click="closePlanEditor">取消</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-drawer>

    <a-modal
      v-model:open="moduleModal.open"
      :title="moduleModal.editingIndex === null ? '新增模块' : '编辑模块'"
      :confirm-loading="savingPlan"
      @ok="submitModule"
    >
      <a-form layout="vertical" :model="moduleForm">
        <a-form-item label="模块编码" required>
          <a-input v-model:value="moduleForm.module_code" />
        </a-form-item>
        <a-form-item label="模块名称" required>
          <a-input v-model:value="moduleForm.module_name" />
        </a-form-item>
        <a-form-item label="模块类型">
          <a-select v-model:value="moduleForm.module_type" :options="moduleTypeOptions" />
        </a-form-item>
        <a-form-item label="要求学分">
          <a-input-number v-model:value="moduleForm.credits_required" :min="0" :precision="1" class="full-input" />
        </a-form-item>
        <a-form-item label="排序">
          <a-input-number v-model:value="moduleForm.sort_order" :min="0" class="full-input" />
        </a-form-item>
        <a-form-item label="备注">
          <a-textarea v-model:value="moduleForm.note" :rows="3" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="courseModal.open"
      :title="courseModal.editingIndex === null ? '新增课程' : '编辑课程'"
      :confirm-loading="savingPlan"
      @ok="submitCourse"
    >
      <a-form layout="vertical" :model="courseForm">
        <a-form-item label="课程编码" required>
          <a-input v-model:value="courseForm.code" />
        </a-form-item>
        <a-form-item label="课程名称" required>
          <a-input v-model:value="courseForm.name" />
        </a-form-item>
        <a-form-item label="学分">
          <a-input-number v-model:value="courseForm.credits" :min="0" :precision="1" class="full-input" />
        </a-form-item>
        <a-form-item label="开课学期">
          <a-input v-model:value="courseForm.opening_term" placeholder="如 1 / 2 / 秋 / E" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import {
  BookOutlined,
  ClusterOutlined,
  DeleteOutlined,
  EditOutlined,
  NodeIndexOutlined,
  PlusOutlined,
  ReadOutlined,
  SaveOutlined,
  SearchOutlined,
} from '@ant-design/icons-vue'
import { del, get, patch, post } from '@/utils/request'
import type { ApiEnvelope } from '@/utils/request'
import type { Paginated } from '@/api/types'

type CourseItem = {
  code?: string
  name?: string
  credits?: number | string | null
  opening_term?: string | null
  [key: string]: unknown
}

type CurriculumModule = {
  id?: number
  plan_id?: number
  module_code: string
  module_name: string
  module_type: string
  credits_required: number
  courses?: CourseItem[] | null
  note?: string | null
  sort_order: number
}

type EditableModule = CurriculumModule & {
  courses: CourseItem[]
}

type CurriculumPlanBrief = {
  id: number
  grade_code: string
  major_code: string
  plan_name: string
  version_label?: string | null
  total_credits_required?: number | null
  effective_from?: string | null
  is_active: boolean
  note?: string | null
  updated_at?: string
}

type CurriculumPlanDetail = CurriculumPlanBrief & {
  modules: CurriculumModule[]
}

type CurriculumPlanPayload = {
  grade_code: string
  major_code: string
  plan_name: string
  version_label?: string | null
  total_credits_required?: number | null
  effective_from?: string | null
  is_active: boolean
  note?: string | null
  expected_updated_at?: string | null
  modules: Omit<CurriculumModule, 'id' | 'plan_id'>[]
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

const moduleTypeOptions = [
  { label: '必修', value: 'REQUIRED' },
  { label: '选修', value: 'ELECTIVE' },
  { label: '通识', value: 'GENERAL' },
  { label: '实践', value: 'PRACTICE' },
  { label: '其他', value: 'OTHER' },
]

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

// ---------- 培养方案 ----------
const planFilters = reactive<{ grade_code?: string; major_code?: string }>({})
const plans = ref<CurriculumPlanBrief[]>([])
const planLoading = ref(false)
const savingPlan = ref(false)
const planPagination = reactive({ current: 1, pageSize: 20, total: 0 })
const selectedPlan = ref<CurriculumPlanBrief | null>(null)
const selectedPlanDetail = ref<CurriculumPlanDetail | null>(null)
const modules = ref<CurriculumModule[]>([])
const moduleLoading = ref(false)
const canEditSelectedPlan = computed(() => (
  !!selectedPlan.value
  && !!selectedPlanDetail.value
  && selectedPlan.value.id === selectedPlanDetail.value.id
  && !moduleLoading.value
  && !savingPlan.value
))
let selectPlanRequestId = 0

const planDrawer = reactive<{ open: boolean; editingId: number | null }>({
  open: false,
  editingId: null,
})
const planForm = reactive({
  grade_code: '',
  major_code: '',
  plan_name: '',
  version_label: '',
  total_credits_required: undefined as number | undefined,
  effective_from: '',
  is_active: true,
  note: '',
})

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
        selectedPlanDetail.value = null
        modules.value = []
      }
    }
  } finally {
    planLoading.value = false
  }
}

function openPlanEditor(plan?: CurriculumPlanBrief | CurriculumPlanDetail | null) {
  const source = plan || null
  planDrawer.open = true
  planDrawer.editingId = source?.id ?? null
  planForm.grade_code = source?.grade_code || ''
  planForm.major_code = source?.major_code || ''
  planForm.plan_name = source?.plan_name || ''
  planForm.version_label = source?.version_label || 'manual'
  planForm.total_credits_required = source?.total_credits_required ?? undefined
  planForm.effective_from = source?.effective_from || ''
  planForm.is_active = source?.is_active ?? true
  planForm.note = source?.note || ''
}

function closePlanEditor() {
  planDrawer.open = false
}

async function submitPlan() {
  if (!planForm.grade_code.trim() || !planForm.major_code.trim() || !planForm.plan_name.trim()) {
    message.warning('请填写年级、专业和方案名称')
    return
  }
  const payload: CurriculumPlanPayload = {
    grade_code: planForm.grade_code.trim(),
    major_code: planForm.major_code.trim(),
    plan_name: planForm.plan_name.trim(),
    version_label: planForm.version_label?.trim() || null,
    total_credits_required: planForm.total_credits_required,
    effective_from: planForm.effective_from?.trim() || null,
    is_active: planForm.is_active,
    note: planForm.note?.trim() || null,
    expected_updated_at: planDrawer.editingId && selectedPlanDetail.value?.id === planDrawer.editingId
      ? selectedPlanDetail.value.updated_at || null
      : null,
    modules: planDrawer.editingId ? buildModulesPayload(modules.value) : [],
  }
  savingPlan.value = true
  try {
    const resp = planDrawer.editingId
      ? await patch<ApiEnvelope<CurriculumPlanDetail>>(`/admin/curriculum/plans/${planDrawer.editingId}`, payload)
      : await post<ApiEnvelope<CurriculumPlanDetail>>('/admin/curriculum/plans', payload)
    message.success(planDrawer.editingId ? '培养方案已更新' : '培养方案已创建')
    closePlanEditor()
    selectedPlan.value = resp.data
    selectedPlanDetail.value = resp.data
    modules.value = normalizeModules(resp.data.modules)
    await loadPlans()
  } finally {
    savingPlan.value = false
  }
}

async function deleteSelectedPlan() {
  if (!selectedPlan.value) return
  savingPlan.value = true
  try {
    await del<ApiEnvelope<{ id: number; deleted: boolean }>>(`/admin/curriculum/plans/${selectedPlan.value.id}`)
    message.success('培养方案已删除')
    selectedPlan.value = null
    selectedPlanDetail.value = null
    modules.value = []
    await loadPlans()
  } finally {
    savingPlan.value = false
  }
}

async function selectPlan(plan: CurriculumPlanBrief) {
  const requestId = ++selectPlanRequestId
  selectedPlan.value = plan
  selectedPlanDetail.value = null
  modules.value = []
  moduleLoading.value = true
  try {
    const resp = await get<ApiEnvelope<CurriculumPlanDetail>>(`/admin/curriculum/plans/${plan.id}`)
    if (requestId !== selectPlanRequestId || selectedPlan.value?.id !== plan.id) {
      return
    }
    selectedPlan.value = resp.data
    selectedPlanDetail.value = resp.data
    modules.value = normalizeModules(resp.data.modules)
  } finally {
    if (requestId === selectPlanRequestId) {
      moduleLoading.value = false
    }
  }
}

async function saveSelectedPlan(nextModules = modules.value, messageText = '保存成功') {
  if (!selectedPlanDetail.value) return
  savingPlan.value = true
  try {
    const payload = buildPlanPayload(selectedPlanDetail.value, nextModules)
    const resp = await patch<ApiEnvelope<CurriculumPlanDetail>>(
      `/admin/curriculum/plans/${selectedPlanDetail.value.id}`,
      payload,
    )
    selectedPlan.value = resp.data
    selectedPlanDetail.value = resp.data
    modules.value = normalizeModules(resp.data.modules)
    message.success(messageText)
    await loadPlans()
  } finally {
    savingPlan.value = false
  }
}

function buildPlanPayload(plan: CurriculumPlanDetail, nextModules: CurriculumModule[]): CurriculumPlanPayload {
  return {
    grade_code: plan.grade_code,
    major_code: plan.major_code,
    plan_name: plan.plan_name,
    version_label: plan.version_label || null,
    total_credits_required: plan.total_credits_required ?? null,
    effective_from: plan.effective_from || null,
    is_active: plan.is_active,
    note: plan.note || null,
    expected_updated_at: plan.updated_at || null,
    modules: buildModulesPayload(nextModules),
  }
}

function buildModulesPayload(source: CurriculumModule[]): Omit<CurriculumModule, 'id' | 'plan_id'>[] {
  return source.map((module, index) => ({
    module_code: module.module_code,
    module_name: module.module_name,
    module_type: module.module_type || 'REQUIRED',
    credits_required: Number(module.credits_required || 0),
    courses: normalizeCourses(module.courses).map((course) => ({
      ...course,
      credits: course.credits == null || course.credits === '' ? null : Number(course.credits),
    })),
    note: module.note || null,
    sort_order: Number(module.sort_order ?? index + 1),
  }))
}

// ---------- 模块 ----------
const moduleCols = [
  { title: '编码', dataIndex: 'module_code', key: 'module_code', width: 150 },
  { title: '名称', dataIndex: 'module_name', key: 'module_name' },
  { title: '类型', key: 'module_type', width: 90 },
  { title: '要求学分', dataIndex: 'credits_required', key: 'credits_required', width: 100 },
  { title: '课程', key: 'courses', width: 80 },
  { title: '操作', key: 'actions', width: 190 },
]
const moduleModal = reactive<{ open: boolean; editingIndex: number | null }>({
  open: false,
  editingIndex: null,
})
const moduleForm = reactive({
  module_code: '',
  module_name: '',
  module_type: 'REQUIRED',
  credits_required: 0,
  sort_order: 0,
  note: '',
  courses: [] as CourseItem[],
})

function moduleTypeLabel(value?: string | null) {
  return {
    REQUIRED: '必修',
    ELECTIVE: '选修',
    GENERAL: '通识',
    PRACTICE: '实践',
    OTHER: '其他',
  }[value || ''] || value || '-'
}

function asModule(value: unknown): CurriculumModule {
  return value as CurriculumModule
}

function openModuleEditor(module?: CurriculumModule, index?: number) {
  if (!selectedPlanDetail.value) {
    message.warning('请先选择培养方案')
    return
  }
  moduleModal.open = true
  moduleModal.editingIndex = typeof index === 'number' ? index : null
  moduleForm.module_code = module?.module_code || `MODULE-${String(modules.value.length + 1).padStart(3, '0')}`
  moduleForm.module_name = module?.module_name || ''
  moduleForm.module_type = module?.module_type || 'REQUIRED'
  moduleForm.credits_required = Number(module?.credits_required || 0)
  moduleForm.sort_order = Number(module?.sort_order ?? modules.value.length + 1)
  moduleForm.note = module?.note || ''
  moduleForm.courses = normalizeCourses(module?.courses).map((course) => ({ ...course }))
}

async function submitModule() {
  if (!moduleForm.module_code.trim() || !moduleForm.module_name.trim()) {
    message.warning('请填写模块编码和名称')
    return
  }
  const nextModules: EditableModule[] = modules.value.map((module) => ({ ...module, courses: normalizeCourses(module.courses) }))
  const payload: EditableModule = {
    module_code: moduleForm.module_code.trim(),
    module_name: moduleForm.module_name.trim(),
    module_type: moduleForm.module_type,
    credits_required: Number(moduleForm.credits_required || 0),
    courses: moduleForm.courses.map((course) => ({ ...course })),
    note: moduleForm.note?.trim() || null,
    sort_order: Number(moduleForm.sort_order || nextModules.length + 1),
  }
  if (
    nextModules.some((module, index) => (
      module.module_code === payload.module_code && index !== moduleModal.editingIndex
    ))
  ) {
    message.warning('模块编码不能重复')
    return
  }
  if (moduleModal.editingIndex === null) {
    nextModules.push(payload)
  } else {
    nextModules[moduleModal.editingIndex] = { ...nextModules[moduleModal.editingIndex], ...payload }
  }
  moduleModal.open = false
  await saveSelectedPlan(nextModules, moduleModal.editingIndex === null ? '模块已新增' : '模块已更新')
}

async function deleteModule(index: number) {
  const nextModules = modules.value.filter((_, current) => current !== index)
  await saveSelectedPlan(nextModules, '模块已删除')
}

function normalizeModules(source?: CurriculumModule[] | null) {
  return [...(source || [])]
    .map((module) => ({
      ...module,
      courses: normalizeCourses(module.courses),
      sort_order: Number(module.sort_order || 0),
      credits_required: Number(module.credits_required || 0),
    }))
    .sort((a, b) => a.sort_order - b.sort_order)
}

// ---------- 模块课程 ----------
const courseCols = [
  { title: '课程编码', dataIndex: 'code', key: 'code', width: 150 },
  { title: '课程名称', dataIndex: 'name', key: 'name' },
  { title: '学分', dataIndex: 'credits', key: 'credits', width: 80 },
  { title: '开课学期', dataIndex: 'opening_term', key: 'opening_term', width: 120 },
  { title: '操作', key: 'actions', width: 120 },
]
const courseModal = reactive<{
  open: boolean
  moduleCode: string | null
  editingIndex: number | null
}>({
  open: false,
  moduleCode: null,
  editingIndex: null,
})
const courseForm = reactive({
  code: '',
  name: '',
  credits: 0 as number | undefined,
  opening_term: '',
})

function openCourseEditor(module: CurriculumModule, course?: CourseItem, index?: number) {
  courseModal.open = true
  courseModal.moduleCode = module.module_code
  courseModal.editingIndex = typeof index === 'number' ? index : null
  courseForm.code = String(course?.code || '')
  courseForm.name = String(course?.name || '')
  courseForm.credits = course?.credits == null || course.credits === '' ? 0 : Number(course.credits)
  courseForm.opening_term = course?.opening_term == null ? '' : String(course.opening_term)
}

async function submitCourse() {
  if (!courseModal.moduleCode) return
  if (!courseForm.code.trim() || !courseForm.name.trim()) {
    message.warning('请填写课程编码和名称')
    return
  }
  const nextModules: EditableModule[] = modules.value.map((module) => ({ ...module, courses: normalizeCourses(module.courses) }))
  const module = nextModules.find((item) => item.module_code === courseModal.moduleCode)
  if (!module) return
  const nextCourses = normalizeCourses(module.courses).map((course) => ({ ...course }))
  const payload: CourseItem = {
    code: courseForm.code.trim(),
    name: courseForm.name.trim(),
    credits: Number(courseForm.credits || 0),
    opening_term: courseForm.opening_term?.trim() || null,
  }
  if (
    nextCourses.some((course, index) => (
      course.code === payload.code && index !== courseModal.editingIndex
    ))
  ) {
    message.warning('同一模块内课程编码不能重复')
    return
  }
  if (courseModal.editingIndex === null) {
    nextCourses.push(payload)
  } else {
    nextCourses[courseModal.editingIndex] = { ...nextCourses[courseModal.editingIndex], ...payload }
  }
  module.courses = nextCourses
  courseModal.open = false
  await saveSelectedPlan(nextModules, courseModal.editingIndex === null ? '课程已新增' : '课程已更新')
}

async function deleteCourse(module: CurriculumModule, courseIndex: number) {
  const nextModules: EditableModule[] = modules.value.map((item) => ({ ...item, courses: normalizeCourses(item.courses) }))
  const target = nextModules.find((item) => item.module_code === module.module_code)
  if (!target) return
  target.courses = normalizeCourses(target.courses).filter((_, index) => index !== courseIndex)
  await saveSelectedPlan(nextModules, '课程已删除')
}

function normalizeCourses(value?: CourseItem[] | null): CourseItem[] {
  return Array.isArray(value) ? value.filter((course) => course && typeof course === 'object') : []
}

function courseRowKey(course: CourseItem, index?: number) {
  return `${course.code || 'course'}-${index ?? 0}`
}

function formatCredits(value?: number | string | null) {
  if (value === null || value === undefined || value === '') return '-'
  const numberValue = Number(value)
  if (!Number.isFinite(numberValue)) return String(value)
  return Number.isInteger(numberValue) ? String(numberValue) : numberValue.toFixed(1)
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

.selected-plan-head {
  flex-wrap: wrap;
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

.course-detail {
  padding: 12px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius);
  background: #fff;
}

.course-detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  color: var(--text);
  font-weight: 700;
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

.full-input {
  width: 100%;
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
