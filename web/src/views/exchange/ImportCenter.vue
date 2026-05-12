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
        <a-card :bordered="false" class="mb16 default-import-card">
          <div class="default-import-head">
            <div>
              <div class="default-import-title">默认数据导入</div>
              <div class="default-import-sub">一键导入仓库内默认学生花名册与默认培养方案，保留原有手工导入流程。</div>
            </div>
            <a-space wrap>
              <a-button :loading="defaultImportLoading.students" @click="onDefaultImport('students')">
                <template #icon><UserAddOutlined /></template>
                导入默认学生
              </a-button>
              <a-button :loading="defaultImportLoading.curriculum" @click="onDefaultImport('curriculum')">
                <template #icon><ReadOutlined /></template>
                导入默认培养方案
              </a-button>
              <a-button type="primary" :loading="defaultImportLoading.all" @click="onDefaultImport('all')">
                <template #icon><DatabaseOutlined /></template>
                导入全部默认
              </a-button>
            </a-space>
          </div>

          <a-alert
            v-if="defaultImportSummary"
            class="mt16"
            type="success"
            show-icon
            :message="defaultImportSummary.title"
          >
            <template #description>
              <a-descriptions :column="1" bordered size="small">
                <a-descriptions-item
                  v-for="item in defaultImportSummary.results"
                  :key="item.import_type"
                  :label="defaultImportLabel(item.import_type)"
                >
                  <div>{{ formatDefaultImportResult(item) }}</div>
                  <div v-if="item.warnings.length" class="import-warnings">
                    <div v-for="warning in item.warnings.slice(0, 3)" :key="warning">
                      {{ warning }}
                    </div>
                  </div>
                </a-descriptions-item>
              </a-descriptions>
            </template>
          </a-alert>
        </a-card>

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

    <aside class="exchange-side-panel">
      <div class="side-panel-head">
        <strong>导入任务面板</strong>
        <span>×</span>
      </div>

      <section class="quality-card">
        <ExclamationCircleOutlined />
        <div>
          <p>校验状态</p>
          <h3>{{ preview ? preview.batch.status : latestBatch?.status || '等待上传' }}</h3>
          <span>导入前先校验，致命错误为 0 后才允许正式提交。</span>
        </div>
      </section>

      <section class="side-section">
        <h3>最新批次</h3>
        <template v-if="latestBatch">
          <div class="side-kv">
            <span>批次号</span>
            <strong>{{ latestBatch.batch_no }}</strong>
          </div>
          <div class="side-kv">
            <span>文件</span>
            <strong>{{ latestBatch.filename }}</strong>
          </div>
          <div class="side-kv">
            <span>正常 / 警告 / 致命</span>
            <strong>{{ latestBatch.ok_rows }} / {{ latestBatch.warn_rows }} / {{ latestBatch.fatal_rows }}</strong>
          </div>
        </template>
        <p v-else class="side-muted">暂无导入批次，上传文件后展示校验摘要。</p>
      </section>

      <section class="side-section">
        <h3>数据质量</h3>
        <div class="quality-bars">
          <div>
            <span>校验通过</span>
            <i :style="{ width: `${qualityPercent.ok}%` }" />
            <strong>{{ qualityPercent.ok }}%</strong>
          </div>
          <div>
            <span>需修正</span>
            <i class="warn" :style="{ width: `${qualityPercent.warn}%` }" />
            <strong>{{ qualityPercent.warn }}%</strong>
          </div>
        </div>
      </section>

      <section class="side-section">
        <h3>快捷导出</h3>
        <div class="side-actions vertical">
          <a-button @click="dlStudents">导出学生名册</a-button>
          <a-button @click="dlTranscripts">导出成绩单</a-button>
          <a-button type="primary" @click="dlCurriculum">导出培养方案</a-button>
        </div>
      </section>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloudUploadOutlined,
  DatabaseOutlined,
  ExclamationCircleOutlined,
  FileTextOutlined,
  ReadOutlined,
  UserAddOutlined,
} from '@ant-design/icons-vue'
import {
  importAllDefaults,
  importDefaultCurriculum,
  importDefaultStudents,
  uploadImport, commitImport, listImports,
  downloadErrorReport, downloadStudents, downloadTranscripts, downloadCurriculum,
  type DefaultImportResult, type ImportType, type ImportPreviewResult, type ImportBatchBrief,
} from '@/api/exchange'
import StatusTag from '@/components/StatusTag.vue'

const activeTab = ref('import')
const importType = ref<ImportType>('student')
const preview = ref<ImportPreviewResult | null>(null)
const defaultImportLoading = reactive({ students: false, curriculum: false, all: false })
const defaultImportSummary = ref<{ title: string; results: DefaultImportResult[] } | null>(null)
const latestBatch = computed(() => preview.value?.batch || batches.value[0] || null)
const qualityPercent = computed(() => {
  const batch = latestBatch.value
  if (!batch || !batch.total_rows) return { ok: 0, warn: 0 }
  return {
    ok: Math.round((batch.ok_rows / batch.total_rows) * 100),
    warn: Math.round(((batch.warn_rows + batch.fatal_rows) / batch.total_rows) * 100),
  }
})
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

function defaultImportLabel(importType: string) {
  if (importType === 'DEFAULT_STUDENTS') return '默认学生'
  if (importType === 'DEFAULT_CURRICULUM') return '默认培养方案'
  return importType
}

function formatDefaultImportResult(result: DefaultImportResult) {
  return [
    `总计 ${result.total_rows} 条`,
    `新增 ${result.created_count}`,
    `更新 ${result.updated_count}`,
    `跳过 ${result.skipped_count}`,
    `警告 ${result.warning_count}`,
  ].join(' · ')
}

async function onDefaultImport(kind: 'students' | 'curriculum' | 'all') {
  defaultImportLoading[kind] = true
  try {
    if (kind === 'students') {
      const resp = await importDefaultStudents()
      defaultImportSummary.value = {
        title: '默认学生花名册导入完成',
        results: [resp.data],
      }
      message.success('默认学生导入完成')
    } else if (kind === 'curriculum') {
      const resp = await importDefaultCurriculum()
      defaultImportSummary.value = {
        title: '默认培养方案导入完成',
        results: [resp.data],
      }
      message.success('默认培养方案导入完成')
    } else {
      const resp = await importAllDefaults()
      defaultImportSummary.value = {
        title: '全部默认数据导入完成',
        results: [resp.data.students, resp.data.curriculum],
      }
      message.success('全部默认数据导入完成')
    }
  } catch {
    message.error('默认数据导入失败')
  } finally {
    defaultImportLoading[kind] = false
  }
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
.exchange-page {
  padding-right: 364px;
}

.mb16 { margin-bottom: 16px; }
.mt8 { margin-top: 8px; }
.mt16 { margin-top: 16px; }

.default-import-card :deep(.ant-card-body) {
  padding: 18px 20px;
}

.default-import-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.default-import-title {
  color: var(--text);
  font-size: 16px;
  font-weight: 800;
}

.default-import-sub {
  margin-top: 6px;
  color: var(--text-3);
  font-size: 12px;
  line-height: 1.7;
}

.import-warnings {
  margin-top: 8px;
  color: var(--text-3);
  font-size: 12px;
  line-height: 1.6;
}

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

.exchange-side-panel {
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
.side-kv {
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

.quality-card {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  padding: 14px;
  background: linear-gradient(135deg, #fff7f8, #fff);
  border: 1px solid #ffe0e5;
  border-radius: 12px;
}

.quality-card > .anticon {
  display: grid;
  width: 46px;
  height: 46px;
  place-items: center;
  color: var(--ruc-red);
  background: #ffe4e8;
  border-radius: 999px;
  font-size: 22px;
}

.quality-card p,
.side-muted {
  margin: 0;
  color: var(--text-3);
  font-size: 12px;
  line-height: 1.7;
}

.quality-card h3 {
  margin: 4px 0;
  color: var(--text);
  font-size: 16px;
}

.quality-card span {
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

.side-kv {
  min-height: 32px;
  color: var(--text-3);
  font-size: 12px;
}

.side-kv strong {
  max-width: 190px;
  overflow: hidden;
  color: var(--text-2);
  font-weight: 600;
  text-align: right;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.quality-bars {
  display: grid;
  gap: 12px;
}

.quality-bars div {
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr) 44px;
  gap: 10px;
  align-items: center;
  color: var(--text-2);
  font-size: 12px;
}

.quality-bars i {
  display: block;
  height: 10px;
  background: linear-gradient(90deg, var(--ruc-red), #e65d69);
  border-radius: 999px;
}

.quality-bars i.warn {
  background: linear-gradient(90deg, #d8941f, #f4c46a);
}

.quality-bars strong {
  color: var(--text);
  text-align: right;
}

.side-actions.vertical {
  display: grid;
  gap: 10px;
}

@media (max-width: 1320px) {
  .exchange-page {
    padding-right: 0;
  }

  .default-import-head,
  .import-hero :deep(.ant-card-body) {
    flex-direction: column;
    align-items: stretch;
  }

  .exchange-side-panel {
    position: static;
    width: auto;
    margin-top: 14px;
    border: 1px solid var(--line-soft);
    border-radius: 12px;
  }
}
</style>
