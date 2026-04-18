<template>
  <div>
    <a-page-header title="荣誉公示管理" sub-title="FR-017" />

    <a-form layout="inline" :model="filters" class="mb16" @finish="reload">
      <a-form-item label="关键字">
        <a-input v-model:value="filters.q" placeholder="标题 / 获奖人" allow-clear style="width: 180px" />
      </a-form-item>
      <a-form-item label="级别">
        <a-select v-model:value="filters.level" style="width: 140px" allow-clear>
          <a-select-option value="NATIONAL">国家级</a-select-option>
          <a-select-option value="PROVINCIAL">省部级</a-select-option>
          <a-select-option value="MINISTERIAL">厅局级</a-select-option>
          <a-select-option value="SCHOOL">校级</a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item label="状态">
        <a-select v-model:value="filters.status" style="width: 120px" allow-clear>
          <a-select-option value="ACTIVE">生效</a-select-option>
          <a-select-option value="ARCHIVED">归档</a-select-option>
          <a-select-option value="REVOKED">撤销</a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item>
        <a-button type="primary" html-type="submit">查询</a-button>
      </a-form-item>
      <a-form-item>
        <a-button type="primary" @click="openEditor()">新增荣誉</a-button>
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
          <a-tag :color="record.status === 'ACTIVE' ? 'green' : record.status === 'REVOKED' ? 'red' : 'default'">
            {{ record.status }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'recipients'">
          {{ (record.recipient_names || []).join('、') || '-' }}
        </template>
        <template v-else-if="column.key === 'actions'">
          <a-button type="link" size="small" @click="openEditor(record)">编辑</a-button>
          <a-popconfirm
            v-if="record.status === 'ACTIVE'"
            title="确定归档？"
            @confirm="onArchive(record.id)"
          >
            <a-button type="link" size="small">归档</a-button>
          </a-popconfirm>
        </template>
      </template>
    </a-table>

    <a-drawer
      :open="showDrawer"
      :title="editingId ? '编辑荣誉记录' : '新增荣誉记录'"
      width="600"
      @close="resetForm"
    >
      <a-form layout="vertical" :model="form" @finish="onSubmit">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="标题" :rules="[{ required: true }]">
              <a-input v-model:value="form.title" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="类别编码" :rules="[{ required: true }]">
              <a-input v-model:value="form.category_code" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="级别" :rules="[{ required: true }]">
              <a-select v-model:value="form.level">
                <a-select-option value="NATIONAL">国家级</a-select-option>
                <a-select-option value="PROVINCIAL">省部级</a-select-option>
                <a-select-option value="MINISTERIAL">厅局级</a-select-option>
                <a-select-option value="SCHOOL">校级</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="授奖单位" :rules="[{ required: true }]">
              <a-input v-model:value="form.awarded_by" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="公布日期" :rules="[{ required: true }]">
              <a-date-picker v-model:value="form.announced_at" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="文号">
              <a-input v-model:value="form.document_no" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="简介">
          <a-textarea v-model:value="form.summary" :rows="3" />
        </a-form-item>
        <a-form-item label="榜样风采（Markdown）">
          <a-textarea v-model:value="form.story_md" :rows="4" />
        </a-form-item>
        <a-form-item>
          <a-checkbox v-model:checked="form.is_collective">集体荣誉</a-checkbox>
        </a-form-item>
        <a-form-item>
          <a-checkbox v-model:checked="form.consent_flag">已获获奖人同意展示</a-checkbox>
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
  adminListRecords, adminCreateRecord, adminUpdateRecord, adminArchiveRecord,
  type HonorRecordBrief, type HonorRecordIn,
} from '@/api/honor'

const columns = [
  { title: '标题', dataIndex: 'title', key: 'title' },
  { title: '级别', dataIndex: 'level', key: 'level', width: 90 },
  { title: '授奖单位', dataIndex: 'awarded_by', key: 'awarded_by', width: 140 },
  { title: '获奖人', key: 'recipients', width: 200 },
  { title: '公布日期', dataIndex: 'announced_at', key: 'announced_at', width: 120 },
  { title: '状态', key: 'status', width: 80 },
  { title: '操作', key: 'actions', width: 140 },
]

const filters = reactive<{ q?: string; level?: string; status?: string }>({})
const rows = ref<HonorRecordBrief[]>([])
const loading = ref(false)
const pagination = reactive({ current: 1, pageSize: 20, total: 0 })

async function reload() {
  loading.value = true
  try {
    const resp = await adminListRecords({
      q: filters.q,
      level: filters.level,
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
const form = reactive<any>({
  title: '',
  category_code: '',
  level: 'SCHOOL',
  awarded_by: '',
  announced_at: null,
  document_no: '',
  summary: '',
  story_md: '',
  is_collective: false,
  consent_flag: false,
})

function openEditor(record?: HonorRecordBrief) {
  if (record) {
    editingId.value = record.id
    Object.assign(form, {
      title: record.title,
      category_code: record.category_code,
      level: record.level,
      awarded_by: record.awarded_by,
      announced_at: record.announced_at,
      summary: record.summary || '',
      is_collective: record.is_collective,
    })
  }
  showDrawer.value = true
}

function resetForm() {
  showDrawer.value = false
  editingId.value = null
  Object.assign(form, {
    title: '', category_code: '', level: 'SCHOOL', awarded_by: '',
    announced_at: null, document_no: '', summary: '', story_md: '',
    is_collective: false, consent_flag: false,
  })
}

async function onSubmit() {
  submitting.value = true
  try {
    const payload: HonorRecordIn = { ...form }
    if (editingId.value) {
      await adminUpdateRecord(editingId.value, payload)
    } else {
      await adminCreateRecord(payload)
    }
    message.success('保存成功')
    resetForm()
    reload()
  } finally {
    submitting.value = false
  }
}

async function onArchive(id: number) {
  await adminArchiveRecord(id)
  message.success('已归档')
  reload()
}

onMounted(reload)
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
</style>
