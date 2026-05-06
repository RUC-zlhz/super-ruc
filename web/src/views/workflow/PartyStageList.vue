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
            <a-button type="primary" @click="showTemplateDrawer = true">
            <template #icon><PlusOutlined /></template>
            新建模板
          </a-button>
          </a-form-item>
        </a-form>
        <a-table
          :columns="templateCols"
          :data-source="templates"
          :loading="tplLoading"
          :custom-row="templateRowProps"
          :row-class-name="templateRowClassName"
          row-key="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'is_active'">
              <a-tag :color="record.is_active ? 'green' : 'default'">
                {{ record.is_active ? '生效' : '停用' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'actions'">
              <a-button type="link" size="small" @click="viewNodes(record)">
                <template #icon><NodeIndexOutlined /></template>
                节点
              </a-button>
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
              <a-button type="primary" html-type="submit">
                <template #icon><SearchOutlined /></template>
                查询
              </a-button>
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
              <StatusTag :status="record.current_node_status || record.status" />
            </template>
            <template v-else-if="column.key === 'due_date'">
              {{ record.due_date || '-' }}
            </template>
          </template>
        </a-table>
      </a-tab-pane>

      <a-tab-pane key="reminders" tab="节点提醒">
        <a-alert
          class="mb16"
          type="info"
          show-icon
          message="提醒规则查询接口暂未接通；当前页面仅保留手动生成入口和最近一次生成结果。"
        />
        <a-button type="primary" :loading="reminderLoading" @click="generateReminders">
          <template #icon><BellOutlined /></template>
          生成待办提醒
        </a-button>
        <a-card class="mt16" title="最近一次生成结果" :bordered="false">
          <template v-if="lastReminderRun">
            <div class="reminder-result-grid">
              <div>
                <span>生成条数</span>
                <strong>{{ lastReminderRun.created }}</strong>
              </div>
              <div>
                <span>渠道</span>
                <strong>{{ lastReminderRun.channel }}</strong>
              </div>
              <div>
                <span>生成时间</span>
                <strong>{{ lastReminderRun.generatedAt }}</strong>
              </div>
            </div>
          </template>
          <a-empty v-else description="尚未执行手动提醒生成" />
        </a-card>
      </a-tab-pane>
    </a-tabs>

    <aside class="stage-side-panel">
      <div class="side-panel-head">
        <strong>流程配置面板</strong>
        <a-button type="text" size="small" :disabled="!selectedTemplatePreview" @click="clearSelectedTemplate">
          <template #icon><CloseOutlined /></template>
        </a-button>
      </div>
      <template v-if="selectedTemplatePreview">
        <div class="stage-type-card">
          <BranchesOutlined />
          <div>
            <p>当前模板</p>
            <h3>{{ selectedTemplatePreview.name }}</h3>
            <span>{{ selectedTemplatePreview.code }}</span>
          </div>
        </div>

        <section class="side-section">
          <h3>流程概览</h3>
          <div class="stage-progress-row">
            <span>模板状态</span>
            <a-tag :color="selectedTemplatePreview.is_active ? 'green' : 'default'">
              {{ selectedTemplatePreview.is_active ? '生效' : '未生效' }}
            </a-tag>
          </div>
          <div class="stage-progress-row">
            <span>学生流程</span>
            <strong>{{ flowPagination.total || flows.length }}</strong>
          </div>
          <div class="stage-progress-row">
            <span>最近提醒生成</span>
            <strong>{{ lastReminderRun?.created ?? 0 }}</strong>
          </div>
        </section>

        <section class="side-section">
          <h3>节点预览</h3>
          <div v-if="nodes.length" class="node-timeline">
            <div v-for="node in nodes.slice(0, 5)" :key="node.id">
              <i />
              <span>{{ node.name }}</span>
              <em>{{ node.due_rule_days || 0 }} 天</em>
            </div>
          </div>
          <p v-else class="side-muted">当前模板暂无节点配置。</p>
        </section>

        <div class="side-actions vertical">
            <a-button @click="showTemplateDrawer = true">
              <template #icon><PlusOutlined /></template>
              新建模板
            </a-button>
            <a-button
              type="primary"
              @click="viewNodes(selectedTemplatePreview)"
            >
              <template #icon><EyeOutlined /></template>
              查看节点
            </a-button>
          </div>
      </template>
      <a-empty v-else description="请选择记录" />
    </aside>

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
          <a-select v-model:value="tplForm.kind" style="width: 100%">
            <a-select-option value="PARTY">党员发展</a-select-option>
            <a-select-option value="YOUTH_LEAGUE">团员培养</a-select-option>
            <a-select-option value="OTHER">其他</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="tplForm.description" :rows="3" />
        </a-form-item>
        <a-form-item>
            <a-button type="primary" html-type="submit">
              <template #icon><SaveOutlined /></template>
              保存
            </a-button>
          </a-form-item>
      </a-form>
    </a-drawer>

    <!-- 节点列表 Modal -->
    <a-modal
      v-model:open="showNodesModal"
      :title="`流程节点 — ${selectedTemplatePreview?.name || ''}`"
      width="720"
      :footer="null"
    >
      <a-table :columns="nodeCols" :data-source="nodes" row-key="id" size="small">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'is_active'">
            <a-tag :color="record.is_active ? 'green' : 'default'">
              {{ record.is_active ? '启用' : '停用' }}
            </a-tag>
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
  CloseOutlined,
  NodeIndexOutlined,
  TeamOutlined,
  SearchOutlined,
  PlusOutlined,
  SaveOutlined,
  EyeOutlined
} from '@ant-design/icons-vue'
import { get, post } from '@/utils/request'
import type { ApiEnvelope } from '@/utils/request'
import type { Paginated } from '@/api/types'
import StatusTag from '@/components/StatusTag.vue'

const activeTab = ref('templates')
const selectedTemplateId = ref<number | null>(null)
const selectedTemplatePreview = computed(() => {
  if (selectedTemplateId.value == null) return null
  return templates.value.find((item) => item.id === selectedTemplateId.value) ?? null
})
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
    sub: selectedTemplatePreview.value ? selectedTemplatePreview.value.name : '请先选择模板',
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
    label: '最近提醒生成',
    value: lastReminderRun.value?.created ?? 0,
    sub: lastReminderRun.value ? `最近生成于 ${lastReminderRun.value.generatedAt}` : '尚未执行手动提醒生成',
    icon: BellOutlined,
  },
])

// ---------- 模板 ----------
type WorkflowNode = {
  id: number
  code: string
  name: string
  sort_order: number
  stage_group?: string | null
  due_rule_days?: number | null
  is_active: boolean
}

type WorkflowTemplate = {
  id: number
  code: string
  name: string
  kind: string
  description?: string | null
  version_label?: string | null
  is_active: boolean
  nodes: WorkflowNode[]
}

type StudentWorkflowBrief = {
  id: number
  student_no?: string | null
  student_name?: string | null
  template_code: string
  template_name: string
  current_node_name?: string | null
  current_node_status?: string | null
  due_date?: string | null
}

const templateCols = [
  { title: '编码', dataIndex: 'code', key: 'code', width: 140 },
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '类型', dataIndex: 'kind', key: 'kind', width: 120 },
  { title: '状态', key: 'is_active', width: 80 },
  { title: '操作', key: 'actions', width: 100 },
]
const templates = ref<WorkflowTemplate[]>([])
const nodes = computed(() => {
  const current = selectedTemplatePreview.value?.nodes ?? []
  return [...current].sort((a, b) => a.sort_order - b.sort_order)
})
const tplLoading = ref(false)
const lastReminderRun = ref<{ created: number; generatedAt: string; channel: string } | null>(null)

async function loadTemplates() {
  tplLoading.value = true
  try {
    const resp = await get<ApiEnvelope<WorkflowTemplate[]>>('/admin/workflow/templates')
    templates.value = resp.data
    if (selectedTemplateId.value != null && !templates.value.some((item) => item.id === selectedTemplateId.value)) {
      clearSelectedTemplate()
    }
  } finally {
    tplLoading.value = false
  }
}

function clearSelectedTemplate() {
  selectedTemplateId.value = null
  showNodesModal.value = false
}

function templateRowProps(record: WorkflowTemplate) {
  return {
    class: 'selectable-template-row',
    onClick: () => {
      selectedTemplateId.value = record.id
    },
  }
}

function templateRowClassName(record: WorkflowTemplate) {
  return record.id === selectedTemplateId.value
    ? 'selectable-template-row selected-template-row'
    : 'selectable-template-row'
}

const showTemplateDrawer = ref(false)
const tplForm = reactive({ code: '', name: '', kind: 'PARTY', description: '' })

async function onSubmitTemplate() {
  await post<ApiEnvelope<WorkflowTemplate>>('/admin/workflow/templates', {
    ...tplForm,
    nodes: [],
  })
  message.success('保存成功')
  showTemplateDrawer.value = false
  Object.assign(tplForm, { code: '', name: '', kind: 'PARTY', description: '' })
  loadTemplates()
}

// ---------- 节点 ----------
const nodeCols = [
  { title: '序号', dataIndex: 'sort_order', key: 'sort_order', width: 70 },
  { title: '编码', dataIndex: 'code', key: 'code', width: 140 },
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '阶段', dataIndex: 'stage_group', key: 'stage_group', width: 120 },
  { title: '预计天数', dataIndex: 'due_rule_days', key: 'due_rule_days', width: 100 },
  { title: '状态', key: 'is_active', width: 80 },
]
const showNodesModal = ref(false)

function viewNodes(tpl: WorkflowTemplate | Record<string, any>, openModal = true) {
  const normalized = tpl as WorkflowTemplate
  selectedTemplateId.value = normalized.id
  showNodesModal.value = openModal
}

// ---------- 学生流程 ----------
const flowCols = [
  { title: '学号', dataIndex: 'student_no', key: 'student_no', width: 120 },
  { title: '姓名', dataIndex: 'student_name', key: 'student_name', width: 100 },
  { title: '模板', dataIndex: 'template_code', key: 'template_code', width: 140 },
  { title: '当前节点', dataIndex: 'current_node_name', key: 'current_node_name' },
  { title: '节点状态', key: 'status', width: 100 },
  { title: '到期日', key: 'due_date', width: 120 },
]
const flowFilters = reactive<{ student_no?: string; template_code?: string }>({})
const flows = ref<StudentWorkflowBrief[]>([])
const flowLoading = ref(false)
const flowPagination = reactive({ current: 1, pageSize: 20, total: 0 })

async function reloadStudentFlows() {
  flowLoading.value = true
  try {
    const resp = await get<ApiEnvelope<Paginated<StudentWorkflowBrief>>>('/admin/workflow/students', {
      params: {
        template_code: flowFilters.template_code,
        page: flowPagination.current,
        size: flowPagination.pageSize,
      },
    })
    const items = resp.data.items
    flows.value = flowFilters.student_no
      ? items.filter((item) => item.student_no?.includes(flowFilters.student_no || ''))
      : items
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
const reminderLoading = ref(false)

async function generateReminders() {
  reminderLoading.value = true
  try {
    const resp = await post<ApiEnvelope<{ created: number }>>('/admin/workflow/reminders/generate', {
      channel: 'IN_APP',
    })
    lastReminderRun.value = {
      created: resp.data.created,
      channel: 'IN_APP',
      generatedAt: new Date().toLocaleString('zh-CN', { hour12: false }),
    }
    message.success(`已生成 ${resp.data.created} 条提醒`)
  } finally {
    reminderLoading.value = false
  }
}

onMounted(() => {
  loadTemplates()
  reloadStudentFlows()
})
</script>

<style scoped>
.party-stage-page {
  padding-right: 364px;
}

.mb16 { margin-bottom: 16px; }

.stage-side-panel {
  position: fixed;
  top: 58px;
  right: 0;
  bottom: 0;
  z-index: 12;
  width: 350px;
  overflow-y: auto;
  padding: 18px;
  background: #fff;
  border-left: 1px solid var(--line-soft);
  box-shadow: var(--shadow-card);
}

.side-panel-head,
.stage-progress-row,
.side-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.side-panel-head {
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--line-soft);
}

.side-panel-head strong {
  color: var(--text);
  font-size: 16px;
}

.side-panel-head span {
  color: var(--text-3);
  font-size: 18px;
}

.stage-type-card {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  padding: 14px;
  background: linear-gradient(135deg, #fff7f8, #fff);
  border: 1px solid #ffe0e5;
  border-radius: 12px;
}

.stage-type-card > .anticon {
  display: grid;
  width: 46px;
  height: 46px;
  place-items: center;
  color: var(--ruc-red);
  background: #ffe4e8;
  border-radius: 999px;
  font-size: 22px;
}

.stage-type-card p,
.side-muted {
  margin: 0;
  color: var(--text-3);
  font-size: 12px;
  line-height: 1.7;
}

.stage-type-card h3 {
  margin: 4px 0;
  color: var(--text);
  font-size: 16px;
}

.stage-type-card span {
  color: var(--text-2);
  font-size: 12px;
}

.side-section {
  padding: 16px 0;
  border-bottom: 1px solid var(--line-soft);
}

.side-section h3 {
  margin: 0 0 10px;
  color: var(--text);
  font-size: 14px;
}

.stage-progress-row {
  min-height: 32px;
  color: var(--text-3);
  font-size: 12px;
}

.stage-progress-row strong {
  color: var(--ruc-red);
  font-family: var(--font-number);
  font-size: 18px;
}

.node-timeline {
  display: grid;
  gap: 10px;
}

.node-timeline div {
  display: grid;
  grid-template-columns: 12px minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  color: var(--text-2);
  font-size: 12px;
}

.node-timeline i {
  width: 9px;
  height: 9px;
  background: var(--ruc-red);
  border-radius: 999px;
  box-shadow: 0 0 0 4px #ffe4e8;
}

.node-timeline em {
  color: var(--text-3);
  font-style: normal;
}

.side-actions {
  margin-top: 16px;
}

.side-actions .ant-btn {
  flex: 1;
}

@media (max-width: 1320px) {
  .party-stage-page {
    padding-right: 0;
  }

  .stage-side-panel {
    position: static;
    width: auto;
    margin-top: 14px;
    border: 1px solid var(--line-soft);
    border-radius: 12px;
  }
}
</style>
