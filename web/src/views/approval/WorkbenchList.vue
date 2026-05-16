<template>
  <div class="workbench-page">
    <a-page-header title="审批工作台" sub-title="学生事务申请审批与进度管理" />

    <div class="metric-grid">
      <div v-for="metric in metrics" :key="metric.key" class="metric-tile">
        <span class="metric-icon"><component :is="metric.icon" /></span>
        <div class="metric-label">{{ metric.label }}</div>
        <div class="metric-value">{{ metric.value }}</div>
        <div class="metric-sub">{{ metric.sub }}</div>
      </div>
    </div>

    <a-form layout="inline" :model="filters" class="filter-card" @finish="onSearch">
      <a-form-item label="关键字">
        <a-input v-model:value="filters.q" placeholder="单号 / 申请人 / 标题" allow-clear />
      </a-form-item>
      <a-form-item label="类型">
        <a-input v-model:value="filters.type_code" placeholder="LEAVE / CERTIFICATE / STAMP..." allow-clear />
      </a-form-item>
      <a-form-item label="状态">
        <a-select v-model:value="filters.status" style="width: 160px" allow-clear>
          <a-select-option value="SUBMITTED">待受理</a-select-option>
          <a-select-option value="IN_REVIEW">审核中</a-select-option>
          <a-select-option value="APPROVED">已通过</a-select-option>
          <a-select-option value="REJECTED">已驳回</a-select-option>
          <a-select-option value="OFFLINE_HANDLED">转线下</a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item>
          <a-button type="primary" html-type="submit">
            <template #icon><SearchOutlined /></template>
            查询
          </a-button>
        </a-form-item>
    </a-form>

    <a-table
      :columns="columns"
      :data-source="rows"
      :loading="loading"
      :pagination="pagination"
      row-key="id"
      class="visual-table"
      @change="onTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <StatusTag :status="record.status" />
        </template>
        <template v-else-if="column.key === 'actions'">
          <router-link class="action-link" :to="`/approval/${record.id}`">查看详情</router-link>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { SearchOutlined } from '@ant-design/icons-vue'
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  FileDoneOutlined,
  InboxOutlined,
} from '@ant-design/icons-vue'
import { listAdminRequests, type RequestBrief, type RequestStatus } from '@/api/workflow'
import StatusTag from '@/components/StatusTag.vue'

const columns = [
  { title: '单号', dataIndex: 'request_no', key: 'request_no' },
  { title: '类型', dataIndex: 'type_code', key: 'type_code' },
  { title: '标题', dataIndex: 'title', key: 'title' },
  { title: '状态', key: 'status' },
  { title: '版本', dataIndex: 'revision', key: 'revision', width: 70 },
  { title: '更新时间', dataIndex: 'updated_at', key: 'updated_at' },
  { title: '操作', key: 'actions', width: 100 },
]

const filters = reactive<{
  q?: string
  type_code?: string
  status?: RequestStatus
}>({})

const rows = ref<RequestBrief[]>([])
const loading = ref(false)
const pagination = reactive({ current: 1, pageSize: 20, total: 0 })

const metrics = computed(() => {
  const pending = rows.value.filter((item) => item.status === 'SUBMITTED').length
  const reviewing = rows.value.filter((item) => item.status === 'IN_REVIEW').length
  const approved = rows.value.filter((item) => item.status === 'APPROVED').length
  return [
    {
      key: 'total',
      label: '申请总数',
      value: pagination.total || rows.value.length,
      sub: '当前筛选结果',
      icon: FileDoneOutlined,
    },
    {
      key: 'pending',
      label: '待审批',
      value: pending,
      sub: '当前页待处理',
      icon: InboxOutlined,
    },
    {
      key: 'reviewing',
      label: '审核中',
      value: reviewing,
      sub: '已进入审批链路',
      icon: ClockCircleOutlined,
    },
    {
      key: 'approved',
      label: '已通过',
      value: approved,
      sub: '当前页通过数',
      icon: CheckCircleOutlined,
    },
  ]
})

async function reload() {
  loading.value = true
  try {
    const resp = await listAdminRequests({
      q: filters.q,
      type_code: filters.type_code,
      status: filters.status,
      page: pagination.current,
      size: pagination.pageSize,
    })
    rows.value = resp.data.items
    pagination.total = resp.data.meta.total
  } finally {
    loading.value = false
  }
}

function onSearch() {
  pagination.current = 1
  void reload()
}

function onTableChange(p: any) {
  pagination.current = p.current
  pagination.pageSize = p.pageSize
  reload()
}

onMounted(reload)
</script>

<style scoped>
.action-link {
  color: var(--ruc-red);
  font-weight: 600;
}
</style>
