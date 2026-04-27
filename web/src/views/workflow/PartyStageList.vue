<template>
  <div class="party-stage-page">
    <a-page-header title="党团流程管理" sub-title="党团相关流程模板、节点、学生流程及提醒规则" />

    <div class="metric-grid">
      <div v-for="metric in metrics" :key="metric.key" class="metric-tile">
        <span class="metric-icon"><component :is="metric.icon" /></span>
        <div class="metric-label">{{ metric.label }}</div>
        <div class="metric-value">{{ metric.value }}</div>
        <div class="metric-sub">{{ metric.sub }}</div>
      </div>
    </div>

    <a-tabs v-model:activeKey="activeTab">
      <a-tab-pane key="templates" tab="流程模板">
        <a-form layout="inline" class="filter-card">
          <a-form-item>
            <a-button type="primary" @click="showTemplateDrawer = true">新建模板</a-button>
          </a-form-item>
        </a-form>
        <a-table
          :columns="templateCols"
          :data-source="templates"
          :loading="tplLoading"
          row-key="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'is_active'">
              <a-tag :color="record.is_active ? 'green' : 'default'">
                {{ record.is_active ? '生效' : '停用' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'actions'">
              <a-button type="link" size="small" @click="viewNodes(record)">节点</a-button>
            </template>
          </template>
        </a-table>
      </a-tab-pane>

      <a-tab-pane key="students" tab="学生流程">
        <a-form layout="inline" class="filter-card" @finish="reloadStudentFlows">
          <a-form-item label="学号">
            <a-input v-model:value="flowFilters.student_no" placeholder="学号" allow-clear />
          </a-form-item>
          <a-form-item label="模板">
            <a-input v-model:value="flowFilters.template_code" placeholder="模板编码" allow-clear />
          </a-form-item>
          <a-form-item>
            <a-button type="primary" html-type="submit">查询</a-button>
          </a-form-item>
        </a-form>
        <a-table
          :columns="flowCols"
          :data-source="flows"
          :loading="flowLoading"
          :pagination="flowPagination"
          row-key="id"
          @change="onFlowTableChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <StatusTag :status="record.status" />
            </template>
          </template>
        </a-table>
      </a-tab-pane>

      <a-tab-pane key="reminders" tab="节点提醒">
        <a-table
          :columns="reminderCols"
          :data-source="reminders"
          :loading="reminderLoading"
          row-key="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'is_active'">
              <a-tag :color="record.is_active ? 'blue' : 'default'">
                {{ record.is_active ? '启用' : '停用' }}
              </a-tag>
            </template>
          </template>
        </a-table>
      </a-tab-pane>
    </a-tabs>

    <!-- 模板新建/编辑抽屉 -->
    <a-drawer :open="showTemplateDrawer" title="流程模板" width="480" @close="showTemplateDrawer = false">
      <a-form layout="vertical" :model="tplForm" @finish="onSubmitTemplate">
        <a-form-item label="编码" :rules="[{ required: true }]">
          <a-input v-model:value="tplForm.code" />
        </a-form-item>
        <a-form-item label="名称" :rules="[{ required: true }]">
          <a-input v-model:value="tplForm.name" />
        </a-form-item>
        <a-form-item label="类型">
          <a-select v-model:value="tplForm.category" style="width: 100%">
            <a-select-option value="PARTY">党员发展</a-select-option>
            <a-select-option value="YOUTH">团员培养</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="tplForm.description" :rows="3" />
        </a-form-item>
        <a-form-item>
          <a-button type="primary" html-type="submit">保存</a-button>
        </a-form-item>
      </a-form>
    </a-drawer>

    <!-- 节点列表 Modal -->
    <a-modal
      v-model:open="showNodesModal"
      :title="`流程节点 — ${selectedTemplate?.name || ''}`"
      width="720"
      :footer="null"
    >
      <a-table :columns="nodeCols" :data-source="nodes" row-key="id" size="small">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'is_required'">
            {{ record.is_required ? '必须' : '可选' }}
          </template>
        </template>
      </a-table>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import {
  BellOutlined,
  BranchesOutlined,
  NodeIndexOutlined,
  TeamOutlined,
} from '@ant-design/icons-vue'
import { get, post } from '@/utils/request'
import type { ApiEnvelope } from '@/utils/request'
import type { Paginated } from '@/api/types'
import StatusTag from '@/components/StatusTag.vue'

const activeTab = ref('templates')
const metrics = computed(() => [
  {
    key: 'templates',
    label: '流程模板数',
    value: templates.value.length,
    sub: '当前模板配置',
    icon: BranchesOutlined,
  },
  {
    key: 'nodes',
    label: '节点总数',
    value: nodes.value.length,
    sub: selectedTemplate.value ? selectedTemplate.value.name : '最近查看模板',
    icon: NodeIndexOutlined,
  },
  {
    key: 'flows',
    label: '学生流程',
    value: flowPagination.total || flows.value.length,
    sub: '当前筛选结果',
    icon: TeamOutlined,
  },
  {
    key: 'reminders',
    label: '提醒规则数',
    value: reminders.value.length,
    sub: '节点提醒配置',
    icon: BellOutlined,
  },
])

// ---------- 模板 ----------
const templateCols = [
  { title: '编码', dataIndex: 'code', key: 'code', width: 140 },
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '类型', dataIndex: 'category', key: 'category', width: 100 },
  { title: '状态', key: 'is_active', width: 80 },
  { title: '操作', key: 'actions', width: 100 },
]
const templates = ref<any[]>([])
const tplLoading = ref(false)

async function loadTemplates() {
  tplLoading.value = true
  try {
    const resp = await get<ApiEnvelope<any[]>>('/admin/workflow/templates')
    templates.value = resp.data
  } finally {
    tplLoading.value = false
  }
}

const showTemplateDrawer = ref(false)
const tplForm = reactive({ code: '', name: '', category: 'PARTY', description: '' })

async function onSubmitTemplate() {
  await post<ApiEnvelope<any>>('/admin/workflow/templates', tplForm)
  message.success('保存成功')
  showTemplateDrawer.value = false
  Object.assign(tplForm, { code: '', name: '', category: 'PARTY', description: '' })
  loadTemplates()
}

// ---------- 节点 ----------
const nodeCols = [
  { title: '序号', dataIndex: 'seq', key: 'seq', width: 60 },
  { title: '编码', dataIndex: 'code', key: 'code', width: 140 },
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '必须', key: 'is_required', width: 80 },
  { title: '预计天数', dataIndex: 'expected_days', key: 'expected_days', width: 100 },
]
const showNodesModal = ref(false)
const selectedTemplate = ref<any>(null)
const nodes = ref<any[]>([])

async function viewNodes(tpl: any) {
  selectedTemplate.value = tpl
  const resp = await get<ApiEnvelope<any[]>>(`/admin/workflow/templates/${tpl.id}/nodes`)
  nodes.value = resp.data
  showNodesModal.value = true
}

// ---------- 学生流程 ----------
const flowCols = [
  { title: '学号', dataIndex: 'student_no', key: 'student_no', width: 120 },
  { title: '姓名', dataIndex: 'student_name', key: 'student_name', width: 100 },
  { title: '模板', dataIndex: 'template_code', key: 'template_code', width: 140 },
  { title: '当前节点', dataIndex: 'current_node_name', key: 'current_node_name' },
  { title: '状态', key: 'status', width: 100 },
  { title: '开始日期', dataIndex: 'started_at', key: 'started_at', width: 120 },
]
const flowFilters = reactive<{ student_no?: string; template_code?: string }>({})
const flows = ref<any[]>([])
const flowLoading = ref(false)
const flowPagination = reactive({ current: 1, pageSize: 20, total: 0 })

async function reloadStudentFlows() {
  flowLoading.value = true
  try {
    const resp = await get<ApiEnvelope<Paginated<any>>>('/admin/workflow/student-workflows', {
      params: { ...flowFilters, page: flowPagination.current, size: flowPagination.pageSize },
    })
    flows.value = resp.data.items
    flowPagination.total = resp.data.meta.total
  } finally {
    flowLoading.value = false
  }
}

function onFlowTableChange(p: any) {
  flowPagination.current = p.current
  flowPagination.pageSize = p.pageSize
  reloadStudentFlows()
}

// ---------- 提醒 ----------
const reminderCols = [
  { title: '提醒名称', dataIndex: 'name', key: 'name' },
  { title: '节点编码', dataIndex: 'node_code', key: 'node_code', width: 140 },
  { title: '提前天数', dataIndex: 'advance_days', key: 'advance_days', width: 100 },
  { title: '状态', key: 'is_active', width: 80 },
]
const reminders = ref<any[]>([])
const reminderLoading = ref(false)

async function loadReminders() {
  reminderLoading.value = true
  try {
    const resp = await get<ApiEnvelope<any[]>>('/admin/workflow/reminders')
    reminders.value = resp.data
  } finally {
    reminderLoading.value = false
  }
}

onMounted(() => {
  loadTemplates()
  reloadStudentFlows()
  loadReminders()
})
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
</style>
