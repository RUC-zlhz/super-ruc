<template>
  <div class="exchange-page">
    <a-page-header title="导入导出中心" sub-title="教师数据批量导入、模板下载与结果追踪" />

    <div class="metric-grid">
      <div v-for="metric in metrics" :key="metric.key" class="metric-tile">
        <span class="metric-icon"><component :is="metric.icon" /></span>
        <div class="metric-label">{{ metric.label }}</div>
        <div class="metric-value">{{ metric.value }}</div>
        <div class="metric-sub">{{ metric.sub }}</div>
      </div>
    </div>

    <a-tabs v-model:activeKey="activeTab">
      <!-- 导入 -->
      <a-tab-pane key="import" tab="数据导入">
        <a-card :bordered="false" class="mb16 import-hero">
          <div class="upload-zone">
            <div class="upload-icon"><CloudUploadOutlined /></div>
            <div>
              <div class="upload-title">将文件拖拽到此处，或点击上传</div>
              <div class="upload-sub">支持 .xlsx / .csv 格式，单批次导入前会先完成校验预览。</div>
            </div>
          </div>
          <a-space>
            <a-select v-model:value="importType" style="width: 180px">
              <a-select-option value="student">学生主档</a-select-option>
              <a-select-option value="transcript">成绩单</a-select-option>
              <a-select-option value="curriculum-module">培养方案模块</a-select-option>
              <a-select-option value="course-equiv">课程等价关系</a-select-option>
              <a-select-option value="course-offering">开课记录</a-select-option>
            </a-select>
            <a-upload
              :show-upload-list="false"
              :before-upload="onBeforeUpload"
            >
              <a-button type="primary">选择 Excel 文件</a-button>
            </a-upload>
          </a-space>
        </a-card>

        <!-- 预览区 -->
        <a-card v-if="preview" :bordered="false" class="mb16">
          <a-descriptions title="校验结果" :column="4" size="small">
            <a-descriptions-item label="批次号">{{ preview.batch.batch_no }}</a-descriptions-item>
            <a-descriptions-item label="文件名">{{ preview.batch.filename }}</a-descriptions-item>
            <a-descriptions-item label="总行数">{{ preview.batch.total_rows }}</a-descriptions-item>
            <a-descriptions-item label="状态">
              <StatusTag :status="preview.batch.status" />
            </a-descriptions-item>
            <a-descriptions-item label="正常">
              <span style="color: green">{{ preview.batch.ok_rows }}</span>
            </a-descriptions-item>
            <a-descriptions-item label="警告">
              <span style="color: orange">{{ preview.batch.warn_rows }}</span>
            </a-descriptions-item>
            <a-descriptions-item label="致命">
              <span style="color: red">{{ preview.batch.fatal_rows }}</span>
            </a-descriptions-item>
          </a-descriptions>

          <a-table
            :columns="rowCols"
            :data-source="preview.rows"
            row-key="id"
            size="small"
            :pagination="{ pageSize: 50 }"
            class="mt8"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'severity'">
                <a-tag :color="severityColor(record.severity)">{{ record.severity }}</a-tag>
              </template>
            </template>
          </a-table>

          <a-space class="mt8">
            <a-button
              type="primary"
              :disabled="preview.batch.fatal_rows > 0"
              @click="onCommit"
            >
              {{ preview.batch.fatal_rows > 0 ? '存在致命错误，无法提交' : '正式提交' }}
            </a-button>
            <a-button @click="onDownloadErrors">下载错误报告</a-button>
          </a-space>
        </a-card>

        <!-- 批次列表 -->
        <a-card title="历史批次" :bordered="false">
          <a-table
            :columns="batchCols"
            :data-source="batches"
            :loading="batchLoading"
            :pagination="batchPagination"
            row-key="id"
            @change="onBatchTableChange"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <StatusTag :status="record.status" />
              </template>
              <template v-else-if="column.key === 'actions'">
                <a-button type="link" size="small" @click="onDownloadBatchErrors(record.id)">
                  错误报告
                </a-button>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-tab-pane>

      <!-- 导出 -->
      <a-tab-pane key="export" tab="数据导出">
        <a-card :bordered="false">
          <a-space direction="vertical" :size="12">
            <a-button @click="dlStudents">导出学生名册</a-button>
            <a-button @click="dlTranscripts">导出成绩单</a-button>
            <a-button @click="dlCurriculum">导出培养方案</a-button>
          </a-space>
        </a-card>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloudUploadOutlined,
  ExclamationCircleOutlined,
  FileTextOutlined,
} from '@ant-design/icons-vue'
import {
  uploadImport, commitImport, listImports,
  downloadErrorReport, downloadStudents, downloadTranscripts, downloadCurriculum,
  type ImportType, type ImportPreviewResult, type ImportBatchBrief,
} from '@/api/exchange'
import StatusTag from '@/components/StatusTag.vue'

const activeTab = ref('import')
const importType = ref<ImportType>('student')
const preview = ref<ImportPreviewResult | null>(null)
const metrics = computed(() => {
  const ok = batches.value.reduce((sum, item) => sum + item.ok_rows, 0)
  const fatal = batches.value.reduce((sum, item) => sum + item.fatal_rows, 0)
  const pending = batches.value.filter((item) => !['COMPLETED', 'COMMITTED', 'FAILED'].includes(item.status)).length
  return [
    {
      key: 'total',
      label: '总记录数',
      value: batches.value.reduce((sum, item) => sum + item.total_rows, 0),
      sub: '历史批次累计',
      icon: FileTextOutlined,
    },
    {
      key: 'ok',
      label: '校验通过',
      value: ok,
      sub: '可提交记录',
      icon: CheckCircleOutlined,
    },
    {
      key: 'fatal',
      label: '校验失败',
      value: fatal,
      sub: '需修正记录',
      icon: ExclamationCircleOutlined,
    },
    {
      key: 'pending',
      label: '待处理批次',
      value: pending,
      sub: '当前批次队列',
      icon: ClockCircleOutlined,
    },
  ]
})

const rowCols = [
  { title: '行号', dataIndex: 'row_no', key: 'row_no', width: 70 },
  { title: '级别', key: 'severity', width: 80 },
  { title: '字段', dataIndex: 'field_name', key: 'field_name', width: 120 },
  { title: '结果', dataIndex: 'result', key: 'result', width: 80 },
  { title: '消息', dataIndex: 'message', key: 'message' },
]

function severityColor(s: string) {
  return s === 'FATAL' ? 'red' : s === 'WARN' ? 'orange' : 'green'
}

async function onBeforeUpload(file: File) {
  try {
    const resp = await uploadImport(importType.value, file)
    preview.value = resp.data
    message.success('文件校验完成')
    loadBatches()
  } catch {
    message.error('上传失败')
  }
  return false // prevent default upload
}

async function onCommit() {
  if (!preview.value) return
  await commitImport(preview.value.batch.id)
  message.success('提交成功')
  preview.value = null
  loadBatches()
}

function onDownloadErrors() {
  if (!preview.value) return
  downloadErrorReport(preview.value.batch.id)
}

function onDownloadBatchErrors(batchId: number) {
  downloadErrorReport(batchId)
}

// 批次列表
const batchCols = [
  { title: '批次号', dataIndex: 'batch_no', key: 'batch_no', width: 160 },
  { title: '类型', dataIndex: 'import_type', key: 'import_type', width: 120 },
  { title: '文件名', dataIndex: 'filename', key: 'filename' },
  { title: '状态', key: 'status', width: 100 },
  { title: '总行/正常/警告/致命', key: 'counts', width: 180, customRender: ({ record }: any) =>
    `${record.total_rows} / ${record.ok_rows} / ${record.warn_rows} / ${record.fatal_rows}` },
  { title: '开始时间', dataIndex: 'started_at', key: 'started_at', width: 180 },
  { title: '操作', key: 'actions', width: 100 },
]
const batches = ref<ImportBatchBrief[]>([])
const batchLoading = ref(false)
const batchPagination = reactive({ current: 1, pageSize: 20, total: 0 })

async function loadBatches() {
  batchLoading.value = true
  try {
    const resp = await listImports({
      page: batchPagination.current,
      size: batchPagination.pageSize,
    })
    batches.value = resp.data.items
    batchPagination.total = resp.data.meta.total
  } finally {
    batchLoading.value = false
  }
}

function onBatchTableChange(p: any) {
  batchPagination.current = p.current
  batchPagination.pageSize = p.pageSize
  loadBatches()
}

function dlStudents() { downloadStudents() }
function dlTranscripts() { downloadTranscripts() }
function dlCurriculum() { downloadCurriculum() }

onMounted(loadBatches)
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
.mt8 { margin-top: 8px; }

.import-hero :deep(.ant-card-body) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.upload-zone {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  min-height: 88px;
  padding: 18px 24px;
  border: 1px dashed rgba(176, 0, 24, 0.42);
  border-radius: 14px;
  background: #fff7f8;
}

.upload-icon {
  display: grid;
  width: 52px;
  height: 52px;
  place-items: center;
  color: var(--ruc-red);
  font-size: 30px;
}

.upload-title {
  color: var(--text);
  font-size: 17px;
  font-weight: 800;
}

.upload-sub {
  margin-top: 6px;
  color: var(--text-3);
  font-size: 13px;
}
</style>
