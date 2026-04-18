<template>
  <div>
    <a-page-header title="通知中心" sub-title="FR-010 / FR-011" />

    <a-form layout="inline" :model="filters" class="mb16" @finish="reload">
      <a-form-item label="关键字">
        <a-input v-model:value="filters.q" placeholder="标题" allow-clear style="width: 200px" />
      </a-form-item>
      <a-form-item label="状态">
        <a-select v-model:value="filters.status" style="width: 140px" allow-clear>
          <a-select-option value="DRAFT">草稿</a-select-option>
          <a-select-option value="PUBLISHED">已发布</a-select-option>
          <a-select-option value="ARCHIVED">已归档</a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item>
        <a-button type="primary" html-type="submit">查询</a-button>
      </a-form-item>
      <a-form-item>
        <a-button type="primary" @click="openEditor()">新建通知</a-button>
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
        <template v-if="column.key === 'status'">
          <a-tag :color="statusColor(record.status)">{{ record.status }}</a-tag>
        </template>
        <template v-else-if="column.key === 'tags'">
          <a-tag v-for="t in (record.tags || [])" :key="t" size="small">{{ t }}</a-tag>
        </template>
        <template v-else-if="column.key === 'actions'">
          <a-button type="link" size="small" @click="openEditor(record)">编辑</a-button>
          <a-button
            v-if="record.status === 'DRAFT'"
            type="link" size="small"
            @click="onPublish(record.id)"
          >发布</a-button>
          <a-button
            v-if="record.status === 'PUBLISHED'"
            type="link" size="small"
            @click="onArchive(record.id)"
          >归档</a-button>
        </template>
      </template>
    </a-table>

    <a-drawer :open="showDrawer" :title="editingId ? '编辑通知' : '新建通知'" width="560" @close="resetForm">
      <a-form layout="vertical" :model="form" @finish="onSubmit">
        <a-form-item label="标题" :rules="[{ required: true }]">
          <a-input v-model:value="form.title" />
        </a-form-item>
        <a-form-item label="来源类型">
          <a-select v-model:value="form.source_type" style="width: 100%">
            <a-select-option value="MANUAL">手工录入</a-select-option>
            <a-select-option value="CRAWL">受控抓取</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="正文">
          <a-textarea v-model:value="form.body" :rows="8" />
        </a-form-item>
        <a-form-item>
          <a-button type="primary" html-type="submit" :loading="submitting">保存</a-button>
        </a-form-item>
      </a-form>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import {
  listNotices, createNotice, publishNotice, archiveNotice,
  type NoticeOut,
} from '@/api/notice'

const columns = [
  { title: '标题', dataIndex: 'title', key: 'title' },
  { title: '标签', key: 'tags', width: 200 },
  { title: '来源', dataIndex: 'source_type', key: 'source_type', width: 100 },
  { title: '状态', key: 'status', width: 100 },
  { title: '发布时间', dataIndex: 'published_at', key: 'published_at', width: 180 },
  { title: '操作', key: 'actions', width: 180 },
]

function statusColor(s: string) {
  return s === 'PUBLISHED' ? 'green' : s === 'ARCHIVED' ? 'default' : 'blue'
}

const filters = reactive<{ q?: string; status?: string }>({})
const rows = ref<NoticeOut[]>([])
const loading = ref(false)
const pagination = reactive({ current: 1, pageSize: 20, total: 0 })

async function reload() {
  loading.value = true
  try {
    const resp = await listNotices({
      q: filters.q,
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

function onTableChange(p: any) {
  pagination.current = p.current
  pagination.pageSize = p.pageSize
  reload()
}

const showDrawer = ref(false)
const submitting = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({ title: '', body: '', source_type: 'MANUAL' })

function openEditor(record?: NoticeOut | Record<string, any>) {
  if (record) {
    editingId.value = record.id
    Object.assign(form, { title: record.title, body: record.body || '', source_type: record.source_type })
  }
  showDrawer.value = true
}

function resetForm() {
  showDrawer.value = false
  editingId.value = null
  Object.assign(form, { title: '', body: '', source_type: 'MANUAL' })
}

async function onSubmit() {
  submitting.value = true
  try {
    await createNotice(form as any)
    message.success('保存成功')
    resetForm()
    reload()
  } finally {
    submitting.value = false
  }
}

async function onPublish(id: number) {
  await publishNotice(id)
  message.success('已发布')
  reload()
}

async function onArchive(id: number) {
  await archiveNotice(id)
  message.success('已归档')
  reload()
}

onMounted(reload)
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
</style>
