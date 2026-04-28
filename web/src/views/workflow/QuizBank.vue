<template>
  <div class="quiz-page">
    <a-page-header title="理论自测题库" sub-title="题库维护、题目管理与启停控制" />

    <div class="metric-grid five">
      <div v-for="metric in metrics" :key="metric.key" class="metric-tile">
        <span class="metric-icon"><component :is="metric.icon" /></span>
        <div class="metric-label">{{ metric.label }}</div>
        <div class="metric-value">{{ metric.value }}</div>
        <div class="metric-sub">{{ metric.sub }}</div>
      </div>
    </div>

    <div class="quiz-workbench">
      <section class="quiz-main">
        <a-form layout="inline" class="filter-card quiz-filter" @finish="onSearch">
          <a-form-item label="主题">
            <a-input v-model:value="filters.topic" allow-clear placeholder="党史 / 团章…" />
          </a-form-item>
          <a-form-item label="题型">
            <a-select
              v-model:value="filters.qtype"
              allow-clear
              placeholder="全部"
              style="width: 120px"
            >
              <a-select-option value="SINGLE">单选</a-select-option>
              <a-select-option value="MULTI">多选</a-select-option>
              <a-select-option value="JUDGE">判断</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="关键字">
            <a-input v-model:value="filters.q" allow-clear placeholder="题干关键字" />
          </a-form-item>
          <a-form-item label="状态">
            <a-select
              v-model:value="filters.is_active"
              allow-clear
              placeholder="全部"
              style="width: 120px"
            >
              <a-select-option value="true">启用</a-select-option>
              <a-select-option value="false">停用</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item>
            <a-button type="primary" html-type="submit">查询</a-button>
          </a-form-item>
          <a-form-item>
            <a-button type="primary" ghost @click="openCreate">新增题目</a-button>
          </a-form-item>
        </a-form>

        <a-table
          :columns="cols"
          :data-source="rows"
          :loading="loading"
          :pagination="pagination"
          row-key="id"
          @change="onTableChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'qtype'">
              <a-tag :color="qtypeColor(record.qtype)">{{ qtypeLabel(record.qtype) }}</a-tag>
            </template>
            <template v-else-if="column.key === 'difficulty'">
              <a-tag :color="difficultyColor(record.difficulty)">
                {{ difficultyLabel(record.difficulty) }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'is_active'">
              <a-tag :color="record.is_active ? 'green' : 'default'">
                {{ record.is_active ? '启用' : '停用' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'actions'">
              <a-button type="link" size="small" @click="openEdit(record)">编辑</a-button>
              <a-popconfirm
                v-if="record.is_active"
                title="停用该题后将不再抽到，确定？"
                @confirm="onDelete(record)"
              >
                <a-button type="link" size="small" danger>停用</a-button>
              </a-popconfirm>
              <a-button
                v-else
                type="link"
                size="small"
                @click="onReactivate(record)"
              >重新启用</a-button>
            </template>
          </template>
        </a-table>
      </section>

      <aside class="quiz-editor panel-card">
        <div class="editor-head">
          <div>
            <div class="editor-title">{{ editing ? '编辑题目' : '新增题目' }}</div>
            <div class="editor-sub">题干、选项、答案与解析集中维护</div>
          </div>
          <a-button size="small" @click="openCreate">清空</a-button>
        </div>

        <div class="topic-summary">
          <div v-for="item in topicSummary" :key="item.name" class="topic-summary-row">
            <span class="topic-dot"></span>
            <span class="topic-name">{{ item.name }}</span>
            <span class="topic-count">{{ item.count }} 题</span>
          </div>
        </div>

        <a-form layout="vertical" :model="form" class="quiz-editor-form">
          <a-row :gutter="12">
            <a-col :span="14">
              <a-form-item label="主题" required>
                <a-input v-model:value="form.topic" placeholder="党史 / 团章 / 自测…" />
              </a-form-item>
            </a-col>
            <a-col :span="10">
              <a-form-item label="题型" required>
                <a-select v-model:value="form.qtype" @change="onTypeChange">
                  <a-select-option value="SINGLE">单选</a-select-option>
                  <a-select-option value="MULTI">多选</a-select-option>
                  <a-select-option value="JUDGE">判断</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>

          <a-form-item label="难度">
            <a-select v-model:value="form.difficulty" allow-clear placeholder="请选择难度">
              <a-select-option value="EASY">简单</a-select-option>
              <a-select-option value="MEDIUM">中等</a-select-option>
              <a-select-option value="HARD">困难</a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item label="题干" required>
            <a-textarea v-model:value="form.stem" :rows="4" placeholder="请输入题目描述" />
          </a-form-item>

          <template v-if="form.qtype !== 'JUDGE'">
            <a-form-item label="选项">
              <div v-for="(opt, idx) in form.options_json" :key="idx" class="opt-row">
                <a-input
                  v-model:value="opt.key"
                  placeholder="A"
                  class="option-key-input"
                  :maxlength="2"
                />
                <a-input
                  v-model:value="opt.text"
                  placeholder="选项内容"
                  class="option-text-input"
                />
                <a-button
                  type="link"
                  danger
                  size="small"
                  :disabled="form.options_json!.length <= 2"
                  @click="removeOption(idx)"
                >删除</a-button>
              </div>
              <a-button size="small" @click="addOption">+ 新增选项</a-button>
            </a-form-item>

            <a-form-item v-if="form.qtype === 'SINGLE'" label="正确答案（A/B/…）" required>
              <a-input v-model:value="form.correct_key" style="width: 120px" :maxlength="2" />
            </a-form-item>
            <a-form-item
              v-else
              label="正确答案（多选，逗号分隔，如 A,C,D）"
              required
            >
              <a-input v-model:value="form.correct_key" style="width: 240px" />
            </a-form-item>
          </template>

          <a-form-item v-else label="判断题答案" required>
            <a-radio-group v-model:value="form.correct_key">
              <a-radio value="TRUE">正确</a-radio>
              <a-radio value="FALSE">错误</a-radio>
            </a-radio-group>
          </a-form-item>

          <a-form-item label="解析">
            <a-textarea v-model:value="form.explanation" :rows="3" />
          </a-form-item>

          <div class="editor-actions">
            <a-button type="primary" :loading="saving" @click="onSubmit">
              {{ editing ? '保存修改' : '保存题目' }}
            </a-button>
            <a-button v-if="editing" @click="openCreate">取消编辑</a-button>
          </div>
        </a-form>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  PlusCircleOutlined,
  ReadOutlined,
  TagsOutlined,
} from '@ant-design/icons-vue'
import {
  listQuizQuestions,
  createQuizQuestion,
  updateQuizQuestion,
  deleteQuizQuestion,
  type QuizDifficulty,
  type QuizOption,
  type QuizQuestion,
  type QuizType,
} from '@/api/workflow'

const cols = [
  { title: '主题', dataIndex: 'topic', key: 'topic', width: 120 },
  { title: '题型', key: 'qtype', width: 80 },
  { title: '题干', dataIndex: 'stem', key: 'stem', ellipsis: true },
  { title: '正确答案', dataIndex: 'correct_key', key: 'correct_key', width: 140 },
  { title: '难度', dataIndex: 'difficulty', key: 'difficulty', width: 80 },
  { title: '状态', key: 'is_active', width: 80 },
  { title: '操作', key: 'actions', width: 160 },
]

const filters = reactive<{
  topic?: string
  qtype?: QuizType
  q?: string
  is_active?: 'true' | 'false'
}>({})
const rows = ref<QuizQuestion[]>([])
const loading = ref(false)
const pagination = reactive({ current: 1, pageSize: 20, total: 0 })
const metrics = computed(() => [
  {
    key: 'total',
    label: '题目总数',
    value: pagination.total || rows.value.length,
    sub: '当前筛选结果',
    icon: ReadOutlined,
  },
  {
    key: 'active',
    label: '启用题目',
    value: rows.value.filter((item) => item.is_active).length,
    sub: '当前页可抽题',
    icon: CheckCircleOutlined,
  },
  {
    key: 'disabled',
    label: '停用题目',
    value: rows.value.filter((item) => !item.is_active).length,
    sub: '当前页停用',
    icon: CloseCircleOutlined,
  },
  {
    key: 'topics',
    label: '题库主题数',
    value: new Set(rows.value.map((item) => item.topic)).size,
    sub: '当前页主题',
    icon: TagsOutlined,
  },
  {
    key: 'today',
    label: '今日新增',
    value: rows.value.filter((item) => item.created_at?.slice(0, 10) === new Date().toISOString().slice(0, 10)).length,
    sub: '本地日期估算',
    icon: PlusCircleOutlined,
  },
])

const topicSummary = computed(() => {
  const counts = new Map<string, number>()
  for (const item of rows.value) {
    counts.set(item.topic || '未分类', (counts.get(item.topic || '未分类') || 0) + 1)
  }
  return Array.from(counts.entries())
    .sort((left, right) => right[1] - left[1])
    .slice(0, 4)
    .map(([name, count]) => ({ name, count }))
})

function qtypeLabel(t: QuizType) {
  return t === 'SINGLE' ? '单选' : t === 'MULTI' ? '多选' : '判断'
}
function qtypeColor(t: QuizType) {
  return t === 'SINGLE' ? 'blue' : t === 'MULTI' ? 'purple' : 'orange'
}
function difficultyLabel(t?: QuizDifficulty | null) {
  return t === 'EASY' ? '简单' : t === 'HARD' ? '困难' : t === 'MEDIUM' ? '中等' : '未设'
}
function difficultyColor(t?: QuizDifficulty | null) {
  return t === 'EASY' ? 'green' : t === 'HARD' ? 'red' : t === 'MEDIUM' ? 'orange' : 'default'
}

async function reload() {
  loading.value = true
  try {
    const isActive =
      filters.is_active === undefined ? undefined : filters.is_active === 'true'
    const resp = await listQuizQuestions({
      topic: filters.topic || undefined,
      qtype: filters.qtype,
      q: filters.q || undefined,
      is_active: isActive,
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

// -------- 表单 --------
interface FormState {
  topic: string
  qtype: QuizType
  stem: string
  options_json: QuizOption[] | null
  correct_key: string
  explanation: string
  difficulty?: QuizDifficulty
}

const emptyForm = (): FormState => ({
  topic: '',
  qtype: 'SINGLE',
  stem: '',
  options_json: [
    { key: 'A', text: '' },
    { key: 'B', text: '' },
  ],
  correct_key: 'A',
  explanation: '',
  difficulty: undefined,
})

const editing = ref<QuizQuestion | null>(null)
const form = reactive<FormState>(emptyForm())
const saving = ref(false)

function openCreate() {
  editing.value = null
  Object.assign(form, emptyForm())
}

function openEdit(record: QuizQuestion | Record<string, any>) {
  const current = record as QuizQuestion
  editing.value = current
  Object.assign(form, {
    topic: current.topic,
    qtype: current.qtype,
    stem: current.stem,
    options_json: current.options_json
      ? current.options_json.map((o) => ({ ...o }))
      : null,
    correct_key: current.correct_key,
    explanation: current.explanation || '',
    difficulty: current.difficulty ?? undefined,
  })
  if (form.qtype !== 'JUDGE' && !form.options_json) {
    form.options_json = [
      { key: 'A', text: '' },
      { key: 'B', text: '' },
    ]
  }
}

function onTypeChange(value: unknown) {
  const t = value as QuizType
  if (t === 'JUDGE') {
    form.options_json = null
    form.correct_key = 'TRUE'
  } else if (!form.options_json || form.options_json.length < 2) {
    form.options_json = [
      { key: 'A', text: '' },
      { key: 'B', text: '' },
    ]
    form.correct_key = t === 'SINGLE' ? 'A' : 'A,B'
  }
}

function addOption() {
  if (!form.options_json) form.options_json = []
  const next = String.fromCharCode(65 + form.options_json.length)
  form.options_json.push({ key: next, text: '' })
}
function removeOption(idx: number) {
  form.options_json?.splice(idx, 1)
}

async function onSubmit() {
  const payload = {
    topic: form.topic.trim(),
    qtype: form.qtype,
    stem: form.stem.trim(),
    options_json: form.qtype === 'JUDGE' ? null : form.options_json,
    correct_key: form.correct_key.trim(),
    explanation: form.explanation || null,
    difficulty: form.difficulty || null,
  }
  if (!payload.topic || !payload.stem || !payload.correct_key) {
    message.error('主题 / 题干 / 正确答案不能为空')
    return
  }
  saving.value = true
  try {
    if (editing.value) {
      await updateQuizQuestion(editing.value.id, payload)
      message.success('已更新')
    } else {
      await createQuizQuestion(payload)
      message.success('已新增')
    }
    openCreate()
    reload()
  } finally {
    saving.value = false
  }
}

async function onDelete(record: QuizQuestion | Record<string, any>) {
  const current = record as QuizQuestion
  await deleteQuizQuestion(current.id)
  message.success('已停用')
  reload()
}

async function onReactivate(record: QuizQuestion | Record<string, any>) {
  const current = record as QuizQuestion
  await updateQuizQuestion(current.id, { is_active: true })
  message.success('已重新启用')
  reload()
}

onMounted(() => reload())
</script>

<style scoped>
.quiz-workbench {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 16px;
  align-items: start;
}

.quiz-main {
  min-width: 0;
}

.quiz-filter {
  margin-bottom: 14px;
}

.quiz-editor {
  position: sticky;
  top: 86px;
  padding: 16px;
}

.editor-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.editor-title {
  color: var(--text);
  font-size: 18px;
  font-weight: 700;
}

.editor-sub {
  margin-top: 4px;
  color: var(--text-3);
  font-size: 12px;
}

.topic-summary {
  margin-bottom: 14px;
  padding: 10px 12px;
  border-radius: var(--radius);
  background: linear-gradient(135deg, #fff8f8, #fff);
  border: 1px solid var(--line-soft);
}

.topic-summary-row {
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
  min-height: 28px;
  color: var(--text-2);
  font-size: 12px;
}

.topic-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: var(--ruc-red);
}

.topic-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.topic-count {
  color: var(--text-3);
}

.quiz-editor-form :deep(.ant-form-item) {
  margin-bottom: 12px;
}

.opt-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.option-key-input {
  width: 60px;
  flex-shrink: 0;
}

.option-text-input {
  flex: 1;
  min-width: 0;
}

.editor-actions {
  display: flex;
  gap: 10px;
  padding-top: 4px;
}

@media (max-width: 1320px) {
  .quiz-workbench {
    grid-template-columns: 1fr;
  }

  .quiz-editor {
    position: static;
  }
}
</style>
