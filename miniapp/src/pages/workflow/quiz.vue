<template>
  <view class="container">
    <text class="page-title">理论自测</text>

    <!-- 选题阶段 -->
    <view v-if="stage === 'pick'" class="pick-card">
      <view class="row">
        <text class="label">主题</text>
        <input
          class="input"
          v-model="form.topic"
          placeholder="如：党史 / 团章（留空抽全库）"
        />
      </view>
      <view class="row">
        <text class="label">题量</text>
        <input
          class="input"
          type="number"
          v-model.number="form.limit"
          placeholder="默认 5"
        />
      </view>
      <button type="primary" class="primary-btn" @tap="startQuiz">开始自测</button>
      <text class="hint">
        本结果仅为学习辅助，分数不作为党团发展正式依据。
      </text>
    </view>

    <!-- 答题阶段 -->
    <view v-else-if="stage === 'answer'" class="answer-card">
      <view class="progress">
        <text>第 {{ currentIdx + 1 }} / {{ questions.length }} 题</text>
        <text class="topic">{{ current?.topic }}</text>
      </view>
      <text class="stem">{{ current?.stem }}</text>
      <text class="qtype-tag" :class="current?.qtype.toLowerCase()">
        {{ qtypeLabel(current?.qtype) }}
      </text>

      <!-- SINGLE: 单选 -->
      <radio-group
        v-if="current?.qtype === 'SINGLE'"
        @change="onSingleChange"
      >
        <label
          v-for="opt in current.options_json || []"
          :key="opt.key"
          class="opt-item"
        >
          <radio :value="opt.key" :checked="answers[current.id] === opt.key" />
          <text class="opt-text">{{ opt.key }}. {{ opt.text }}</text>
        </label>
      </radio-group>

      <!-- MULTI: 多选 -->
      <checkbox-group
        v-else-if="current?.qtype === 'MULTI'"
        @change="onMultiChange"
      >
        <label
          v-for="opt in current.options_json || []"
          :key="opt.key"
          class="opt-item"
        >
          <checkbox
            :value="opt.key"
            :checked="isMultiChecked(current.id, opt.key)"
          />
          <text class="opt-text">{{ opt.key }}. {{ opt.text }}</text>
        </label>
      </checkbox-group>

      <!-- JUDGE: 判断 -->
      <radio-group v-else-if="current?.qtype === 'JUDGE'" @change="onSingleChange">
        <label class="opt-item">
          <radio value="TRUE" :checked="answers[current.id] === 'TRUE'" />
          <text class="opt-text">正确</text>
        </label>
        <label class="opt-item">
          <radio value="FALSE" :checked="answers[current.id] === 'FALSE'" />
          <text class="opt-text">错误</text>
        </label>
      </radio-group>

      <view class="btn-row">
        <button size="mini" :disabled="currentIdx === 0" @tap="prevQ">上一题</button>
        <button
          v-if="currentIdx < questions.length - 1"
          type="primary"
          size="mini"
          @tap="nextQ"
        >下一题</button>
        <button
          v-else
          type="primary"
          size="mini"
          :loading="submitting"
          @tap="submitQuiz"
        >提交</button>
      </view>
    </view>

    <!-- 结果阶段 -->
    <view v-else-if="stage === 'result' && result" class="result-card">
      <text class="result-title">得分 {{ result.score }} 分</text>
      <text class="result-sub">
        {{ result.correct }} / {{ result.total }} 题正确
      </text>
      <view class="review-list">
        <view
          v-for="(item, idx) in result.items"
          :key="item.question_id"
          class="review-item"
        >
          <text class="review-idx">第 {{ idx + 1 }} 题</text>
          <text :class="['review-flag', item.is_correct ? 'ok' : 'bad']">
            {{ item.is_correct ? '✓ 正确' : '✗ 错误' }}
          </text>
          <text class="review-answer">正确答案：{{ item.correct_key }}</text>
          <text v-if="item.explanation" class="review-exp">
            解析：{{ item.explanation }}
          </text>
        </view>
      </view>
      <button type="primary" class="primary-btn" @tap="restart">再来一轮</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import {
  drawQuiz,
  submitQuiz as apiSubmitQuiz,
  type QuizDrawResult,
  type QuizQuestionStudent,
  type QuizSubmitResult,
  type QuizType,
} from '@/api/workflow'

type Stage = 'pick' | 'answer' | 'result'
const stage = ref<Stage>('pick')

const form = reactive({ topic: '', limit: 5 })
const questions = ref<QuizQuestionStudent[]>([])
const currentIdx = ref(0)
const batchId = ref('')
const answers = reactive<Record<number, string>>({})
const submitting = ref(false)
const result = ref<QuizSubmitResult | null>(null)

const current = computed(() => questions.value[currentIdx.value])

function qtypeLabel(t?: QuizType) {
  if (t === 'SINGLE') return '单选'
  if (t === 'MULTI') return '多选'
  if (t === 'JUDGE') return '判断'
  return ''
}

async function startQuiz() {
  try {
    const resp = await drawQuiz({
      topic: form.topic || undefined,
      limit: form.limit > 0 ? form.limit : 5,
    })
    const data = resp.data as QuizDrawResult
    if (!data.questions.length) {
      uni.showToast({ title: '暂无题目', icon: 'none' })
      return
    }
    questions.value = data.questions
    batchId.value = data.batch_id
    currentIdx.value = 0
    for (const k of Object.keys(answers)) delete answers[Number(k)]
    stage.value = 'answer'
  } catch {
    /* toast handled in request */
  }
}

function onSingleChange(e: any) {
  if (!current.value) return
  answers[current.value.id] = e.detail.value
}

function onMultiChange(e: any) {
  if (!current.value) return
  const picked: string[] = e.detail.value || []
  answers[current.value.id] = picked.sort().join(',')
}

function isMultiChecked(qid: number, key: string) {
  const raw = answers[qid]
  if (!raw) return false
  return raw.split(',').includes(key)
}

function prevQ() { if (currentIdx.value > 0) currentIdx.value-- }
function nextQ() {
  if (currentIdx.value < questions.value.length - 1) currentIdx.value++
}

async function submitQuiz() {
  submitting.value = true
  try {
    const payload = {
      batch_id: batchId.value,
      answers: questions.value.map((q) => ({
        question_id: q.id,
        answer: answers[q.id] || '',
      })),
    }
    const resp = await apiSubmitQuiz(payload)
    result.value = resp.data
    stage.value = 'result'
  } finally {
    submitting.value = false
  }
}

function restart() {
  stage.value = 'pick'
  result.value = null
  questions.value = []
}
</script>

<style scoped>
.container { padding: 24rpx; }
.page-title { font-size: 34rpx; font-weight: 600; display: block; margin-bottom: 24rpx; }

.pick-card, .answer-card, .result-card {
  background: #fff;
  border-radius: 12rpx;
  padding: 24rpx;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06);
}
.row { display: flex; align-items: center; margin-bottom: 20rpx; }
.label { width: 120rpx; font-size: 28rpx; color: #333; }
.input {
  flex: 1;
  border: 1rpx solid #ddd;
  border-radius: 8rpx;
  padding: 12rpx 16rpx;
  font-size: 28rpx;
}
.primary-btn { margin-top: 16rpx; }
.hint { display: block; margin-top: 20rpx; color: #999; font-size: 24rpx; line-height: 1.5; }

.progress {
  display: flex;
  justify-content: space-between;
  font-size: 26rpx;
  color: #666;
  margin-bottom: 16rpx;
}
.topic { color: #7f1722; }
.stem {
  display: block;
  font-size: 30rpx;
  line-height: 1.6;
  margin-bottom: 12rpx;
}
.qtype-tag {
  display: inline-block;
  font-size: 22rpx;
  padding: 2rpx 12rpx;
  border-radius: 4rpx;
  margin-bottom: 16rpx;
}
.qtype-tag.single { background: #e6f7ff; color: #1890ff; }
.qtype-tag.multi { background: #f9f0ff; color: #722ed1; }
.qtype-tag.judge { background: #fff7e6; color: #fa8c16; }

.opt-item {
  display: flex;
  align-items: center;
  padding: 16rpx 8rpx;
  border-bottom: 1rpx solid #f0f0f0;
}
.opt-text { margin-left: 12rpx; font-size: 28rpx; }

.btn-row {
  display: flex;
  justify-content: space-between;
  margin-top: 24rpx;
  gap: 16rpx;
}
.btn-row button { flex: 1; }

.result-title {
  display: block;
  font-size: 40rpx;
  font-weight: 700;
  color: #7f1722;
  text-align: center;
  margin-bottom: 8rpx;
}
.result-sub {
  display: block;
  font-size: 26rpx;
  color: #666;
  text-align: center;
  margin-bottom: 24rpx;
}
.review-list { margin-bottom: 24rpx; }
.review-item {
  padding: 16rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
}
.review-idx {
  display: inline-block;
  font-size: 26rpx;
  font-weight: 600;
  margin-right: 12rpx;
}
.review-flag {
  display: inline-block;
  font-size: 24rpx;
  padding: 2rpx 10rpx;
  border-radius: 4rpx;
}
.review-flag.ok { background: #f6ffed; color: #52c41a; }
.review-flag.bad { background: #fff1f0; color: #f5222d; }
.review-answer {
  display: block;
  margin-top: 6rpx;
  font-size: 24rpx;
  color: #555;
}
.review-exp {
  display: block;
  margin-top: 4rpx;
  font-size: 22rpx;
  color: #888;
  line-height: 1.5;
}
</style>
