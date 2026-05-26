<template>
  <div class="exchange-page">
    <a-page-header title="导入导出中心" sub-title="学生、课程与荣誉数据批量导入、模板下载与结果追踪" />

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
            :scroll="{ x: 'max-content' }"
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

        <a-card title="成绩单 PDF 核验" :bordered="false" class="mb16 transcript-review-card">
          <template #extra>
            <a-space>
              <a-button :loading="transcriptReviewLoading" @click="loadTranscriptPdfReviews">刷新</a-button>
            </a-space>
          </template>
          <a-alert
            class="mb16"
            type="info"
            show-icon
            message="学生上传的成绩单 PDF 只生成候选批次，教师核验并提交后才写入正式成绩。"
          />
          <a-table
            :columns="transcriptReviewBatchCols"
            :data-source="transcriptReviewBatches"
            :loading="transcriptReviewLoading"
            :pagination="{ pageSize: 6 }"
            :scroll="{ x: 'max-content' }"
            row-key="id"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <StatusTag :status="record.status" />
              </template>
              <template v-else-if="column.key === 'student'">
                <span>{{ record.summary?.student_no || '-' }}</span>
                <span class="muted"> / {{ record.summary?.student_name || '-' }}</span>
              </template>
              <template v-else-if="column.key === 'parsed'">
                {{ record.summary?.parsed_courses_count || 0 }} 条候选
              </template>
              <template v-else-if="column.key === 'actions'">
                <a-button type="link" size="small" @click="openTranscriptPdfReview(record.id)">
                  {{ record.status === 'COMMITTED' ? '查看' : '核验' }}
                </a-button>
              </template>
            </template>
          </a-table>

          <template v-if="transcriptReviewDetail">
            <a-divider />
            <a-descriptions title="核验批次" :column="4" size="small" bordered>
              <a-descriptions-item label="批次号">{{ transcriptReviewDetail.batch.batch_no }}</a-descriptions-item>
              <a-descriptions-item label="学生">
                {{ transcriptReviewSummary.student_no || '-' }} / {{ transcriptReviewSummary.student_name || '-' }}
              </a-descriptions-item>
              <a-descriptions-item label="文件">{{ transcriptReviewDetail.batch.filename }}</a-descriptions-item>
              <a-descriptions-item label="状态">
                <StatusTag :status="transcriptReviewDetail.batch.status" />
              </a-descriptions-item>
              <a-descriptions-item label="解析字符数">
                {{ transcriptReviewSummary.parsed_text_chars || 0 }}
              </a-descriptions-item>
              <a-descriptions-item label="候选数">
                {{ transcriptReviewSummary.parsed_courses_count || transcriptReviewRecords.length }}
              </a-descriptions-item>
              <a-descriptions-item label="已写入">
                {{ transcriptReviewSummary.formal_records_written || 0 }}
              </a-descriptions-item>
              <a-descriptions-item label="审核备注">
                {{ transcriptReviewDetail.batch.note || '-' }}
              </a-descriptions-item>
            </a-descriptions>

            <div v-if="transcriptReviewWarnings.length" class="review-warnings">
              <a-tag v-for="warning in transcriptReviewWarnings" :key="warning" color="orange">{{ warning }}</a-tag>
            </div>

            <a-space class="mt8">
              <a-button
                :disabled="isTranscriptReviewCommitted"
                @click="addTranscriptReviewRecord"
              >
                新增课程
              </a-button>
            </a-space>

            <a-table
              class="mt8"
              :columns="transcriptReviewRecordCols"
              :data-source="transcriptReviewRecords"
              :pagination="false"
              :scroll="{ x: 'max-content' }"
              row-key="client_key"
              size="small"
            >
              <template #bodyCell="{ column, record, index }">
                <template v-if="column.key === 'course_code'">
                  <a-input v-model:value="record.course_code" :disabled="isTranscriptReviewCommitted" />
                </template>
                <template v-else-if="column.key === 'course_name'">
                  <a-input v-model:value="record.course_name" :disabled="isTranscriptReviewCommitted" />
                </template>
                <template v-else-if="column.key === 'credits'">
                  <a-input-number
                    v-model:value="record.credits"
                    :disabled="isTranscriptReviewCommitted"
                    :min="0"
                    :precision="1"
                    style="width: 88px"
                  />
                </template>
                <template v-else-if="column.key === 'term_code'">
                  <a-input v-model:value="record.term_code" :disabled="isTranscriptReviewCommitted" placeholder="2025-FALL" />
                </template>
                <template v-else-if="column.key === 'score'">
                  <a-input-number
                    v-model:value="record.score"
                    :disabled="isTranscriptReviewCommitted"
                    :min="0"
                    :max="100"
                    style="width: 88px"
                  />
                </template>
                <template v-else-if="column.key === 'grade_letter'">
                  <a-input v-model:value="record.grade_letter" :disabled="isTranscriptReviewCommitted" />
                </template>
                <template v-else-if="column.key === 'pass_flag'">
                  <a-switch v-model:checked="record.pass_flag" :disabled="isTranscriptReviewCommitted" />
                </template>
                <template v-else-if="column.key === 'note'">
                  <a-input v-model:value="record.note" :disabled="isTranscriptReviewCommitted" />
                </template>
                <template v-else-if="column.key === 'actions'">
                  <a-button
                    type="link"
                    danger
                    size="small"
                    :disabled="isTranscriptReviewCommitted"
                    @click="removeTranscriptReviewRecord(index)"
                  >
                    删除
                  </a-button>
                </template>
              </template>
            </a-table>

            <a-textarea
              v-model:value="transcriptReviewNote"
              class="mt8"
              :disabled="isTranscriptReviewCommitted"
              :rows="2"
              placeholder="核验说明"
            />
            <a-space class="mt8">
              <a-button
                type="primary"
                :disabled="isTranscriptReviewCommitted"
                :loading="transcriptReviewCommitLoading"
                @click="onCommitTranscriptPdfReview"
              >
                提交核验结果
              </a-button>
            </a-space>
          </template>
        </a-card>

        <!-- 批次列表 -->
        <a-card title="历史批次" :bordered="false">
          <a-table
            :columns="batchCols"
            :data-source="batches"
            :loading="batchLoading"
            :pagination="batchPagination"
            :scroll="{ x: 'max-content' }"
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
  uploadImport, commitImport, listImports, getImport, commitTranscriptPdfReview,
  downloadErrorReport, downloadStudents, downloadTranscripts, downloadCurriculum,
  TRANSCRIPT_PDF_REVIEW_IMPORT_TYPE,
  type DefaultImportResult, type ImportType, type ImportPreviewResult, type ImportBatchBrief,
  type TranscriptPdfReviewRecord,
} from '@/api/exchange'
import StatusTag from '@/components/StatusTag.vue'

const activeTab = ref('import')
const importType = ref<ImportType>('student')
const preview = ref<ImportPreviewResult | null>(null)
const transcriptReviewBatches = ref<ImportBatchBrief[]>([])
const transcriptReviewDetail = ref<ImportPreviewResult | null>(null)
const transcriptReviewRecords = ref<EditableTranscriptReviewRecord[]>([])
const transcriptReviewNote = ref('')
const transcriptReviewLoading = ref(false)
const transcriptReviewCommitLoading = ref(false)
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
const transcriptReviewBatchCols = [
  { title: '批次号', dataIndex: 'batch_no', key: 'batch_no', width: 180 },
  { title: '学生', key: 'student', width: 180 },
  { title: '文件名', dataIndex: 'filename', key: 'filename', ellipsis: true },
  { title: '候选', key: 'parsed', width: 100 },
  { title: '状态', key: 'status', width: 100 },
  { title: '上传时间', dataIndex: 'started_at', key: 'started_at', width: 180 },
  { title: '操作', key: 'actions', width: 90 },
]
const transcriptReviewRecordCols = [
  { title: '课程编码', key: 'course_code', width: 130 },
  { title: '课程名称', key: 'course_name', width: 190 },
  { title: '学分', key: 'credits', width: 100 },
  { title: '学期', key: 'term_code', width: 130 },
  { title: '成绩', key: 'score', width: 100 },
  { title: '等级', key: 'grade_letter', width: 90 },
  { title: '通过', key: 'pass_flag', width: 80 },
  { title: '备注', key: 'note', width: 160 },
  { title: '操作', key: 'actions', width: 70 },
]

interface EditableTranscriptReviewRecord extends TranscriptPdfReviewRecord {
  client_key: string
  course_code: string
  course_name: string
  credits: number
  term_code: string
  pass_flag: boolean
}

const transcriptReviewSummary = computed<Record<string, any>>(() => (
  transcriptReviewDetail.value?.batch.summary || {}
))
const transcriptReviewWarnings = computed<string[]>(() => {
  const warnings = transcriptReviewSummary.value.data_warnings
  return Array.isArray(warnings) ? warnings.filter((item) => typeof item === 'string') : []
})
const isTranscriptReviewCommitted = computed(() => transcriptReviewDetail.value?.batch.status === 'COMMITTED')

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

function normalizeReviewRecord(candidate: Record<string, any>, index: number): EditableTranscriptReviewRecord {
  const score = candidate.score == null || candidate.score === '' ? null : Number(candidate.score)
  const passFlag = typeof candidate.pass_flag === 'boolean'
    ? candidate.pass_flag
    : (score == null ? true : score >= 60)
  return {
    client_key: `${candidate.line_no ?? 'new'}-${index}-${Date.now()}`,
    line_no: candidate.line_no ?? null,
    course_code: String(candidate.course_code || ''),
    course_name: String(candidate.course_name || ''),
    credits: Number(candidate.credits ?? 0),
    term_code: String(candidate.term_code || ''),
    score,
    grade_letter: candidate.grade_letter == null ? null : String(candidate.grade_letter),
    pass_flag: passFlag,
    note: candidate.note == null ? null : String(candidate.note),
  }
}

function buildTranscriptReviewRecords(detail: ImportPreviewResult): EditableTranscriptReviewRecord[] {
  const summaryCandidates = detail.batch.summary?.candidate_courses
  const rowCandidates = detail.rows
    .filter((row) => row.field_name === 'parsed_courses' && row.raw_data)
    .map((row) => row.raw_data as Record<string, any>)
  const candidates = Array.isArray(summaryCandidates) && summaryCandidates.length
    ? summaryCandidates
    : rowCandidates
  return candidates.map((item, index) => normalizeReviewRecord(item, index))
}

async function loadTranscriptPdfReviews() {
  transcriptReviewLoading.value = true
  try {
    const resp = await listImports({
      import_type: TRANSCRIPT_PDF_REVIEW_IMPORT_TYPE,
      page: 1,
      size: 20,
    })
    transcriptReviewBatches.value = resp.data.items
  } finally {
    transcriptReviewLoading.value = false
  }
}

async function openTranscriptPdfReview(batchId: number) {
  transcriptReviewLoading.value = true
  try {
    const resp = await getImport(batchId)
    transcriptReviewDetail.value = resp.data
    transcriptReviewRecords.value = buildTranscriptReviewRecords(resp.data)
    transcriptReviewNote.value = resp.data.batch.note || ''
  } finally {
    transcriptReviewLoading.value = false
  }
}

function addTranscriptReviewRecord() {
  transcriptReviewRecords.value.push(normalizeReviewRecord({}, transcriptReviewRecords.value.length))
}

function removeTranscriptReviewRecord(index: number) {
  transcriptReviewRecords.value.splice(index, 1)
}

function validateTranscriptReviewRecords() {
  if (!transcriptReviewRecords.value.length) {
    message.warning('请至少保留一条核验课程')
    return false
  }
  const termPattern = /^\d{4}-(SPRING|SUMMER|FALL|WINTER)$/
  for (const record of transcriptReviewRecords.value) {
    if (!record.course_code.trim() || !record.course_name.trim()) {
      message.warning('核验课程必须填写课程编码和课程名称')
      return false
    }
    if (!termPattern.test(record.term_code.trim().toUpperCase())) {
      message.warning('学期格式必须为 YYYY-SPRING/SUMMER/FALL/WINTER')
      return false
    }
  }
  return true
}

async function onCommitTranscriptPdfReview() {
  if (!transcriptReviewDetail.value || !validateTranscriptReviewRecords()) return
  transcriptReviewCommitLoading.value = true
  try {
    const records = transcriptReviewRecords.value.map((record) => ({
      line_no: record.line_no ?? undefined,
      course_code: record.course_code.trim(),
      course_name: record.course_name.trim(),
      credits: Number(record.credits || 0),
      term_code: record.term_code.trim().toUpperCase(),
      score: record.score == null ? null : Number(record.score),
      grade_letter: record.grade_letter?.trim() || null,
      pass_flag: record.pass_flag,
      note: record.note?.trim() || null,
    }))
    await commitTranscriptPdfReview(transcriptReviewDetail.value.batch.id, {
      records,
      note: transcriptReviewNote.value.trim() || null,
    })
    message.success('成绩单 PDF 核验已提交')
    await openTranscriptPdfReview(transcriptReviewDetail.value.batch.id)
    await Promise.all([loadTranscriptPdfReviews(), loadBatches()])
  } finally {
    transcriptReviewCommitLoading.value = false
  }
}

// 批次列表
const batchCols = [
  { title: '批次号', dataIndex: 'batch_no', key: 'batch_no', width: 160 },
  { title: '类型', dataIndex: 'import_type', key: 'import_type', width: 120 },
  { title: '文件名', dataIndex: 'filename', key: 'filename', ellipsis: true },
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

onMounted(() => {
  loadBatches()
  loadTranscriptPdfReviews()
})
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

.muted {
  color: var(--text-3);
}

.review-warnings {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
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
