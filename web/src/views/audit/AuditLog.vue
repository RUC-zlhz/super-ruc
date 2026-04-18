<template>
  <div>
    <a-page-header title="审计日志" sub-title="FR-013" />

    <a-form layout="inline" :model="filters" class="mb16" @finish="reload">
      <a-form-item label="事件类型">
        <a-input v-model:value="filters.event_type" placeholder="如 LOGIN / UPDATE / DELETE" allow-clear />
      </a-form-item>
      <a-form-item label="实体">
        <a-input v-model:value="filters.entity_code" placeholder="如 student / request" allow-clear />
      </a-form-item>
      <a-form-item label="操作人 ID">
        <a-input-number v-model:value="filters.actor_user_id" placeholder="用户 ID" :min="1" />
      </a-form-item>
      <a-form-item label="起始">
        <a-date-picker v-model:value="filters.since" show-time />
      </a-form-item>
      <a-form-item label="截止">
        <a-date-picker v-model:value="filters.until" show-time />
      </a-form-item>
      <a-form-item>
        <a-button type="primary" html-type="submit">查询</a-button>
      </a-form-item>
    </a-form>

    <a-table
      :columns="columns"
      :data-source="rows"
      :loading="loading"
      :pagination="pagination"
      row-key="id"
      @change="onTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'result_code'">
          <a-tag :color="record.result_code === 'OK' ? 'green' : 'red'">
            {{ record.result_code }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'detail'">
          <span v-if="record.detail">
            {{ JSON.stringify(record.detail).slice(0, 80) }}
          </span>
          <span v-else>-</span>
        </template>
      </template>
    </a-table>

    <a-divider />

    <a-card title="日志归档（v1.5）" :bordered="false" size="small">
      <a-space>
        <span>留存天数：</span>
        <a-input-number v-model:value="archiveDays" :min="30" :max="3650" />
        <a-popconfirm title="确定归档超期日志？" @confirm="onArchive">
          <a-button type="primary" danger>执行归档</a-button>
        </a-popconfirm>
      </a-space>
      <div v-if="archiveResult" class="mt8">
        已搬迁 <strong>{{ archiveResult.moved }}</strong> 条记录（留存 {{ archiveResult.retention_days }} 天）
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { listAuditLogs, archiveAuditLogs, type AuditLogOut } from '@/api/audit'

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 70 },
  { title: '事件', dataIndex: 'event_type', key: 'event_type', width: 110 },
  { title: '实体', dataIndex: 'entity_code', key: 'entity_code', width: 100 },
  { title: '操作', dataIndex: 'action', key: 'action', width: 100 },
  { title: '结果', key: 'result_code', width: 80 },
  { title: '操作人', dataIndex: 'actor_user_id', key: 'actor_user_id', width: 80 },
  { title: '角色', dataIndex: 'actor_role', key: 'actor_role', width: 120 },
  { title: 'IP', dataIndex: 'ip_address', key: 'ip_address', width: 130 },
  { title: '详情', key: 'detail' },
  { title: '时间', dataIndex: 'occurred_at', key: 'occurred_at', width: 180 },
]

const filters = reactive<{
  event_type?: string
  entity_code?: string
  actor_user_id?: number
  since?: any
  until?: any
}>({})

const rows = ref<AuditLogOut[]>([])
const loading = ref(false)
const pagination = reactive({ current: 1, pageSize: 20, total: 0 })

async function reload() {
  loading.value = true
  try {
    const resp = await listAuditLogs({
      event_type: filters.event_type,
      entity_code: filters.entity_code,
      actor_user_id: filters.actor_user_id,
      since: filters.since?.toISOString?.() || filters.since,
      until: filters.until?.toISOString?.() || filters.until,
      page: pagination.current,
      size: pagination.pageSize,
    })
    rows.value = resp.data.items
    pagination.total = resp.data.meta.total
  } finally {
    loading.value = false
  }
}

function onTableChange(p: any) {
  pagination.current = p.current
  pagination.pageSize = p.pageSize
  reload()
}

// 归档
const archiveDays = ref(180)
const archiveResult = ref<{ moved: number; retention_days: number } | null>(null)

async function onArchive() {
  try {
    const resp = await archiveAuditLogs(archiveDays.value)
    archiveResult.value = resp.data
    message.success(`已归档 ${resp.data.moved} 条`)
  } catch {
    message.error('归档失败')
  }
}

onMounted(reload)
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
.mt8 { margin-top: 8px; }
</style>
