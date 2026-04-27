<template>
  <view class="container">
    <!-- 选题阶段 -->
    <view v-if="stage === 'pick'" class="pick-card">
      <view class="quiz-hero">
        <text class="hero-title">欢迎来到理论自测</text>
        <text class="hero-sub">选择主题与题量，检验学习成果</text>
      </view>

      <text class="block-title">选择主题</text>
      <view class="topic-grid">
        <view
          v-for="topic in TOPICS"
          :key="topic.value"
          class="topic-card"
          :class="{ active: form.topic === topic.value }"
          @tap="pickTopic(topic.value)"
        >
          <text class="topic-icon">{{ topic.icon }}</text>
          <text class="topic-label">{{ topic.label }}</text>
          <text v-if="form.topic === topic.value" class="topic-check">✓</text>
        </view>
      </view>

      <text class="block-title">选择题量</text>
      <view class="limit-row">
        <view v-for="limit in LIMITS" :key="limit" class="limit-pill" :class="{ active: form.limit === limit }" @tap="form.limit = limit">
          {{ limit }}题
        </view>
      </view>

      <button :type="UNI_BUTTON_TYPE.primary" class="primary-btn" @tap="startQuiz">开始自测</button>
      <text class="hint">
        本结果仅为学习辅助，分数不作为党团发展正式依据。
      </text>
    </view>

    <!-- 答题阶段 -->
    <view v-else-if="stage === 'answer'" class="answer-card">
      <view class="progress">
        <text>答题进度</text>
        <text class="topic">{{ current?.topic }}</text>
      </view>
      <view class="progress-bar">
        <view class="progress-fill" :style="{ width: `${Math.round((currentIdx + 1) / Math.max(questions.length, 1) * 100)}%` }" />
      </view>
      <text class="progress-count">{{ currentIdx + 1 }}/{{ questions.length }}</text>
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
          :type="UNI_BUTTON_TYPE.primary"
          size="mini"
          @tap="nextQ"
        >下一题</button>
        <button
          v-else
          :type="UNI_BUTTON_TYPE.primary"
          size="mini"
          :loading="submitting"
          @tap="submitQuiz"
        >提交</button>
      </view>
    </view>

    <!-- 结果阶段 -->
    <view v-else-if="stage === 'result' && result" class="result-card">
      <view class="result-banner">
        <text class="result-kicker">太棒了！继续保持</text>
        <text class="result-title">{{ result.score }}分</text>
        <text class="result-sub">
          答对 {{ result.correct }}/{{ result.total }} 题
        </text>
      </view>
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
      <button :type="UNI_BUTTON_TYPE.primary" class="primary-btn" @tap="restart">再来一轮</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { UNI_BUTTON_TYPE } from '@/utils/uni-button'
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
const TOPICS = [
  { label: '马克思主义基本原理', value: '马克思主义基本原理', icon: '册' },
  { label: '思想道德与法治', value: '思想道德与法治', icon: '法' },
  { label: '中国近现代史纲要', value: '中国近现代史纲要', icon: '史' },
]
const LIMITS = [10, 20, 30]
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

function pickTopic(topic: string) {
  form.topic = form.topic === topic ? '' : topic
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
.container {
  min-height: 100vh;
  padding: 24rpx;
  background: #f8f3f4;
}

.pick-card, .answer-card, .result-card {
  background: #fff;
  border-radius: 24rpx;
  padding: 26rpx;
  box-shadow: var(--shadow-card);
  border: 1rpx solid #f0e2e5;
}

.quiz-hero {
  margin: -26rpx -26rpx 28rpx;
  padding: 46rpx 32rpx;
  border-radius: 24rpx 24rpx 0 0;
  background:
    radial-gradient(circle at 88% 24%, rgba(255,255,255,0.16), transparent 120rpx),
    linear-gradient(135deg, #d51f35, #b70f24 62%, #8b1020);
  color: #fff;
}

.hero-title {
  display: block;
  font-size: 38rpx;
  font-weight: 800;
}

.hero-sub {
  display: block;
  margin-top: 10rpx;
  font-size: 25rpx;
  opacity: 0.9;
}

.block-title {
  display: block;
  margin: 22rpx 0 18rpx;
  padding-left: 14rpx;
  border-left: 8rpx solid #b70f24;
  font-size: 29rpx;
  font-weight: 800;
  color: #202124;
}

.topic-grid {
  display: flex;
  gap: 16rpx;
}

.topic-card {
  position: relative;
  flex: 1;
  min-height: 150rpx;
  border-radius: 18rpx;
  border: 1rpx solid #f0e2e5;
  background: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
}

.topic-card.active {
  border-color: #b70f24;
  background: linear-gradient(135deg, #b70f24, #8b1020);
  color: #fff;
  box-shadow: 0 10rpx 24rpx rgba(183,15,36,0.18);
}

.topic-icon {
  font-size: 34rpx;
  font-weight: 800;
}

.topic-label {
  width: 150rpx;
  text-align: center;
  font-size: 23rpx;
  line-height: 1.35;
}

.topic-check {
  position: absolute;
  right: 12rpx;
  bottom: 12rpx;
  width: 30rpx;
  height: 30rpx;
  border-radius: 50%;
  background: #fff;
  color: #b70f24;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20rpx;
}

.limit-row {
  display: flex;
  gap: 18rpx;
}

.limit-pill {
  flex: 1;
  height: 66rpx;
  border-radius: 999rpx;
  border: 1rpx solid #f0e2e5;
  background: #fff;
  color: #5f6368;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
}

.limit-pill.active {
  background: #b70f24;
  color: #fff;
  border-color: #b70f24;
  font-weight: 800;
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
.primary-btn {
  margin-top: 34rpx;
  height: 82rpx;
  line-height: 82rpx;
  border-radius: 18rpx;
  background: linear-gradient(135deg, #d51f35, #b70f24);
  color: #fff;
  font-weight: 800;
}
.hint { display: block; margin-top: 20rpx; color: #999; font-size: 24rpx; line-height: 1.5; }

.progress {
  display: flex;
  justify-content: space-between;
  font-size: 26rpx;
  color: #666;
  margin-bottom: 16rpx;
}
.topic { color: #7f1722; }
.progress-bar {
  height: 8rpx;
  border-radius: 999rpx;
  background: #f0e2e5;
  overflow: hidden;
  margin-bottom: 12rpx;
}
.progress-fill {
  height: 100%;
  background: #b70f24;
}
.progress-count {
  display: block;
  text-align: right;
  color: #5f6368;
  font-size: 24rpx;
  margin-bottom: 20rpx;
}
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
  min-height: 82rpx;
  padding: 16rpx 18rpx;
  border: 1rpx solid #f0e2e5;
  border-radius: 16rpx;
  margin-bottom: 14rpx;
  background: #fff;
}
.opt-text { margin-left: 12rpx; font-size: 28rpx; }

.btn-row {
  display: flex;
  justify-content: space-between;
  margin-top: 24rpx;
  gap: 16rpx;
}
.btn-row button { flex: 1; }

.result-banner {
  margin: -26rpx -26rpx 24rpx;
  padding: 42rpx 34rpx;
  border-radius: 24rpx 24rpx 0 0;
  background:
    radial-gradient(circle at 82% 26%, rgba(255,255,255,0.18), transparent 120rpx),
    linear-gradient(135deg, #d51f35, #8b1020);
  color: #fff;
}
.result-kicker {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
}
.result-title {
  display: block;
  font-size: 70rpx;
  font-weight: 700;
  color: #fff;
  margin-top: 8rpx;
}
.result-sub {
  display: block;
  font-size: 26rpx;
  color: rgba(255,255,255,0.86);
  margin-top: 4rpx;
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
