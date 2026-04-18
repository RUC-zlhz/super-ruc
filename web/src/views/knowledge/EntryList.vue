<template>
  <div>
    <a-page-header title="知识库管理" sub-title="FR-001 / FR-002 / FR-003" />

    <a-form layout="inline" :model="filters" class="mb16" @finish="reload">
      <a-form-item label="关键字">
        <a-input v-model:value="filters.q" placeholder="标题 / 编码" allow-clear style="width: 200px" />
      </a-form-item>
      <a-form-item label="分类">
        <a-input v-model:value="filters.category" placeholder="分类编码" allow-clear style="width: 160px" />
      </a-form-item>
      <a-form-item>
        <a-button type="primary" html-type="submit">查询</a-button>
      </a-form-item>
      <a-form-item>
        <a-button type="primary" @click="showDrawer = true">新增条目</a-button>
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
        <template v-if="column.key === 'is_active'">
          <a-tag :color="record.is_active ? 'green' : 'default'">
            {{ record.is_active ? '生效' : '停用' }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'tags'">
          <a-tag v-for="t in (record.tags || [])" :key="t" size="small">{{ t }}</a-tag>
        </template>
        <template v-else-if="column.key === 'actions'">
          <a-button type="link" size="small" @click="onEdit(record)">编辑</a-button>
          <a-popconfirm title="确定删除该条目？" @confirm="onDelete(record.id)">
            <a-button type="link" size="small" danger>删除</a-button>
          </a-popconfirm>
        </template>
      </template>
    </a-table>

    <a-drawer
      :open="showDrawer"
      :title="editingId ? '编辑知识条目' : '新增知识条目'"
      width="520"
      @close="resetForm"
    >
      <a-form layout="vertical" :model="form" @finish="onSubmit">
        <a-form-item label="编码" name="code" :rules="[{ required: true, message: '请输入编码' }]">
          <a-input v-model:value="form.code" />
        </a-form-item>
        <a-form-item label="标题" name="title" :rules="[{ required: true, message: '请输入标题' }]">
          <a-input v-model:value="form.title" />
        </a-form-item>
        <a-form-item label="分类">
          <a-input v-model:value="form.category" />
        </a-form-item>
        <a-form-item label="内容" name="body">
          <a-textarea v-model:value="form.body" :rows="6" />
        </a-form-item>
        <a-form-item label="来源链接">
          <a-input v-model:value="form.source_url" />
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
import { listEntries, upsertEntry, deleteEntry, type KnowledgeEntry } from '@/api/knowledge'

const columns = [
  { title: '编码', dataIndex: 'code', key: 'code', width: 120 },
  { title: '标题', dataIndex: 'title', key: 'title' },
  { title: '分类', dataIndex: 'category', key: 'category', width: 120 },
  { title: '标签', key: 'tags', width: 200 },
  { title: '状态', key: 'is_active', width: 80 },
  { title: '更新时间', dataIndex: 'updated_at', key: 'updated_at', width: 180 },
  { title: '操作', key: 'actions', width: 140 },
]

const filters = reactive<{ q?: string; category?: string }>({})
const rows = ref<KnowledgeEntry[]>([])
const loading = ref(false)
const pagination = reactive({ current: 1, pageSize: 20, total: 0 })

const showDrawer = ref(false)
const submitting = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({
  code: '',
  title: '',
  category: '',
  body: '',
  source_url: '',
})

async function reload() {
  loading.value = true
  try {
    const resp = await listEntries({
      q: filters.q,
      category: filters.category,
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

function onEdit(record: KnowledgeEntry | Record<string, any>) {
  editingId.value = record.id
  Object.assign(form, {
    code: record.code,
    title: record.title,
    category: record.category || '',
    body: record.body || '',
    source_url: record.source_url || '',
  })
  showDrawer.value = true
}

function resetForm() {
  showDrawer.value = false
  editingId.value = null
  Object.assign(form, { code: '', title: '', category: '', body: '', source_url: '' })
}

async function onSubmit() {
  submitting.value = true
  try {
    const payload: any = { ...form }
    if (editingId.value) payload.id = editingId.value
    await upsertEntry(payload)
    message.success(editingId.value ? '更新成功' : '创建成功')
    resetForm()
    reload()
  } finally {
    submitting.value = false
  }
}

async function onDelete(id: number) {
  await deleteEntry(id)
  message.success('已删除')
  reload()
}

onMounted(reload)
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
</style>
