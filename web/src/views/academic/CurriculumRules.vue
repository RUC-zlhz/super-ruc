<template>
  <div>
    <a-page-header title="培养方案管理" sub-title="FR-015" />

    <a-tabs v-model:activeKey="activeTab">
      <a-tab-pane key="plans" tab="培养方案">
        <a-form layout="inline" class="mb16" @finish="loadPlans">
          <a-form-item label="年级">
            <a-input v-model:value="planFilters.grade_code" placeholder="年级代码" allow-clear />
          </a-form-item>
          <a-form-item label="专业">
            <a-input v-model:value="planFilters.major_code" placeholder="专业代码" allow-clear />
          </a-form-item>
          <a-form-item>
            <a-button type="primary" html-type="submit">查询</a-button>
          </a-form-item>
        </a-form>
        <a-table
          :columns="planCols"
          :data-source="plans"
          :loading="planLoading"
          row-key="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'actions'">
              <a-button type="link" size="small" @click="viewModules(record)">模块</a-button>
            </template>
          </template>
        </a-table>
      </a-tab-pane>

      <a-tab-pane key="offerings" tab="开课记录">
        <a-form layout="inline" class="mb16" @finish="loadOfferings">
          <a-form-item label="学期">
            <a-input v-model:value="offeringFilters.semester" placeholder="如 2025-2026-1" allow-clear />
          </a-form-item>
          <a-form-item>
            <a-button type="primary" html-type="submit">查询</a-button>
          </a-form-item>
        </a-form>
        <a-table
          :columns="offeringCols"
          :data-source="offerings"
          :loading="offeringLoading"
          :pagination="offeringPagination"
          row-key="id"
          @change="onOfferingTableChange"
        />
      </a-tab-pane>

      <a-tab-pane key="equivalences" tab="课程等价">
        <a-table
          :columns="equivCols"
          :data-source="equivalences"
          :loading="equivLoading"
          row-key="id"
        />
      </a-tab-pane>
    </a-tabs>

    <!-- 模块 Modal -->
    <a-modal
      v-model:open="showModulesModal"
      :title="`培养模块 — ${selectedPlan?.name || ''}`"
      width="720"
      :footer="null"
    >
      <a-table :columns="moduleCols" :data-source="modules" row-key="id" size="small">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'is_required'">
            {{ record.is_required ? '必修' : '选修' }}
          </template>
        </template>
      </a-table>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { get } from '@/utils/request'
import type { ApiEnvelope } from '@/utils/request'
import type { Paginated } from '@/api/types'

const activeTab = ref('plans')

// ---------- 培养方案 ----------
const planCols = [
  { title: '编码', dataIndex: 'code', key: 'code', width: 120 },
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '年级', dataIndex: 'grade_code', key: 'grade_code', width: 100 },
  { title: '专业', dataIndex: 'major_code', key: 'major_code', width: 120 },
  { title: '总学分', dataIndex: 'total_credits', key: 'total_credits', width: 80 },
  { title: '操作', key: 'actions', width: 100 },
]
const planFilters = reactive<{ grade_code?: string; major_code?: string }>({})
const plans = ref<any[]>([])
const planLoading = ref(false)

async function loadPlans() {
  planLoading.value = true
  try {
    const resp = await get<ApiEnvelope<any[]>>('/admin/curriculum/plans', {
      params: planFilters,
    })
    plans.value = resp.data
  } finally {
    planLoading.value = false
  }
}

// ---------- 模块 ----------
const moduleCols = [
  { title: '编码', dataIndex: 'code', key: 'code', width: 120 },
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '类型', dataIndex: 'module_type', key: 'module_type', width: 100 },
  { title: '必修', key: 'is_required', width: 80 },
  { title: '最低学分', dataIndex: 'min_credits', key: 'min_credits', width: 100 },
]
const showModulesModal = ref(false)
const selectedPlan = ref<any>(null)
const modules = ref<any[]>([])

async function viewModules(plan: any) {
  selectedPlan.value = plan
  const resp = await get<ApiEnvelope<any[]>>(`/admin/curriculum/plans/${plan.id}/modules`)
  modules.value = resp.data
  showModulesModal.value = true
}

// ---------- 开课记录 ----------
const offeringCols = [
  { title: '课程编码', dataIndex: 'course_code', key: 'course_code', width: 120 },
  { title: '课程名', dataIndex: 'course_name', key: 'course_name' },
  { title: '学期', dataIndex: 'semester', key: 'semester', width: 120 },
  { title: '学分', dataIndex: 'credits', key: 'credits', width: 80 },
  { title: '教师', dataIndex: 'instructor_name', key: 'instructor_name', width: 120 },
]
const offeringFilters = reactive<{ semester?: string }>({})
const offerings = ref<any[]>([])
const offeringLoading = ref(false)
const offeringPagination = reactive({ current: 1, pageSize: 20, total: 0 })

async function loadOfferings() {
  offeringLoading.value = true
  try {
    const resp = await get<ApiEnvelope<Paginated<any>>>('/admin/curriculum/offerings', {
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
  { title: '类型', dataIndex: 'equiv_type', key: 'equiv_type', width: 100 },
]
const equivalences = ref<any[]>([])
const equivLoading = ref(false)

async function loadEquivalences() {
  equivLoading.value = true
  try {
    const resp = await get<ApiEnvelope<any[]>>('/admin/curriculum/equivalences')
    equivalences.value = resp.data
  } finally {
    equivLoading.value = false
  }
}

onMounted(() => {
  loadPlans()
  loadOfferings()
  loadEquivalences()
})
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
</style>
