<template>
  <view class="container">
    <view v-if="stage === 'pick'" class="pick-card">
      <view class="quiz-hero">
        <view class="hero-top">
          <view>
            <text class="hero-kicker">理论自测</text>
            <text class="hero-title">欢迎来到理论自测</text>
            <text class="hero-sub">选择主题与题量，检验学习成果</text>
          </view>
          <view class="hero-badge">答</view>
        </view>

        <view class="hero-strip">
          <view class="hero-strip-item">
            <text class="hero-strip-value">{{ TOPICS.length }}</text>
            <text class="hero-strip-label">主题方向</text>
          </view>
          <view class="hero-strip-item">
            <text class="hero-strip-value">{{ maxLimit }}</text>
            <text class="hero-strip-label">最高题量</text>
          </view>
          <view class="hero-strip-item">
            <text class="hero-strip-value">即时</text>
            <text class="hero-strip-label">提交判分</text>
          </view>
        </view>
      </view>

      <view class="setup-card">
        <view class="block-head">
          <text class="block-title">选择主题</text>
          <text class="block-meta">{{ form.topic ? "已选择 1 项" : "请先选择 1 个主题" }}</text>
        </view>
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
      </view>

      <view class="setup-card">
        <view class="block-head">
          <text class="block-title">选择题量</text>
          <text class="block-meta">建议从 10 题开始逐步增加</text>
        </view>
        <view class="limit-row">
          <view
            v-for="limit in LIMITS"
            :key="limit"
            class="limit-pill"
            :class="{ active: form.limit === limit }"
            @tap="form.limit = limit"
          >
            {{ limit }}题
          </view>
        </view>
      </view>

      <view class="pick-summary">
        <text class="summary-title">开始前提醒</text>
        <text class="summary-line">主题：{{ form.topic || "未选择主题" }}</text>
        <text class="summary-line">题量：{{ form.limit }} 题</text>
        <text class="summary-line">提交后将立即显示得分与逐题结果。</text>
      </view>

      <button :type="UNI_BUTTON_TYPE.primary" class="primary-btn" hover-class="hover-scale" @tap="startQuiz">
        <text class="btn-icon">⚡</text> 开始自测
      </button>
      <text class="hint">
        本结果仅为学习辅助，分数不作为党团发展正式依据。
      </text>
    </view>

    <view v-else-if="stage === 'answer'" class="answer-stage">
      <view class="answer-hero">
        <view class="hero-top compact">
          <view>
            <text class="hero-kicker">正在答题</text>
            <text class="hero-title small">{{ current?.topic || "理论自测" }}</text>
          </view>
          <text class="question-pill">第 {{ currentIdx + 1 }} 题</text>
        </view>

        <view class="answer-strip">
          <view class="answer-strip-item">
            <text class="answer-strip-label">答题进度</text>
            <text class="answer-strip-value">{{ currentIdx + 1 }}/{{ questions.length }}</text>
          </view>
          <view class="answer-strip-item">
            <text class="answer-strip-label">题型</text>
            <text class="answer-strip-value">{{ qtypeLabel(current?.qtype) || "-" }}</text>
          </view>
        </view>

        <view class="progress-bar">
          <view class="progress-fill" :style="{ width: `${progressPercent}%` }" />
        </view>
      </view>

      <view class="question-card">
        <view class="question-head">
          <text class="question-index">题目 {{ currentIdx + 1 }}</text>
          <text class="qtype-tag" :class="current?.qtype?.toLowerCase()">
            {{ qtypeLabel(current?.qtype) }}
          </text>
        </view>
        <text class="stem">{{ current?.stem }}</text>
      </view>

      <radio-group
        v-if="current?.qtype === 'SINGLE'"
        @change="onSingleChange"
      >
        <label
          v-for="opt in current.options_json || []"
          :key="opt.key"
          class="opt-item"
          :class="{ checked: answers[current.id] === opt.key }"
        >
          <radio :value="opt.key" :checked="answers[current.id] === opt.key" />
          <text class="opt-text">{{ opt.key }}. {{ opt.text }}</text>
        </label>
      </radio-group>

      <checkbox-group
        v-else-if="current?.qtype === 'MULTI'"
        @change="onMultiChange"
      >
        <label
          v-for="opt in current.options_json || []"
          :key="opt.key"
          class="opt-item"
          :class="{ checked: isMultiChecked(current.id, opt.key) }"
        >
          <checkbox
            :value="opt.key"
            :checked="isMultiChecked(current.id, opt.key)"
          />
          <text class="opt-text">{{ opt.key }}. {{ opt.text }}</text>
        </label>
      </checkbox-group>

      <radio-group v-else-if="current?.qtype === 'JUDGE'" @change="onSingleChange">
        <label class="opt-item" :class="{ checked: answers[current.id] === 'TRUE' }">
          <radio value="TRUE" :checked="answers[current.id] === 'TRUE'" />
          <text class="opt-text">正确</text>
        </label>
        <label class="opt-item" :class="{ checked: answers[current.id] === 'FALSE' }">
          <radio value="FALSE" :checked="answers[current.id] === 'FALSE'" />
          <text class="opt-text">错误</text>
        </label>
      </radio-group>

      <view class="answer-note">
        {{ current?.qtype === "MULTI" ? "多选题需选中全部正确答案。" : "请根据当前题目选择你认为正确的答案。" }}
      </view>

      <view class="answer-spacer" />

      <view class="answer-footer safe-area-inset-bottom">
        <view class="footer-copy">
          <text class="footer-title">{{ current?.topic || "理论自测" }}</text>
          <text class="footer-desc">
            {{ currentIdx < questions.length - 1 ? "确认当前题后可继续下一题" : "最后一题，确认后即可提交判分" }}
          </text>
        </view>
        <view class="footer-actions">
          <button
            v-if="currentIdx > 0"
            size="mini"
            class="flex-btn"
            hover-class="hover-opacity"
            @tap="prevQ"
          >
            <text class="btn-icon">‹</text> 上一题
          </button>
          <button
            v-if="currentIdx < questions.length - 1"
            :type="UNI_BUTTON_TYPE.primary"
            size="mini"
            class="flex-btn"
            hover-class="hover-opacity"
            @tap="nextQ"
          >
            下一题 <text class="btn-icon">›</text>
          </button>
          <button
            v-else
            :type="UNI_BUTTON_TYPE.primary"
            size="mini"
            :loading="submitting"
            class="flex-btn"
            hover-class="hover-scale"
            @tap="submitQuiz"
          >
            <text class="btn-icon">✓</text> 提交
          </button>
        </view>
      </view>
    </view>

    <view v-else-if="stage === 'result' && result" class="result-card">
      <view class="result-banner">
        <text class="result-kicker">本次结果</text>
        <text class="result-title">{{ result.score }}分</text>
        <text class="result-sub">
          答对 {{ result.correct }}/{{ result.total }} 题
        </text>

        <view class="result-strip">
          <view class="result-strip-item">
            <text class="result-strip-value">{{ accuracyPercent }}%</text>
            <text class="result-strip-label">正确率</text>
          </view>
          <view class="result-strip-item">
            <text class="result-strip-value">{{ result.total - result.correct }}</text>
            <text class="result-strip-label">错题数</text>
          </view>
        </view>
      </view>

      <view class="review-list">
        <view
          v-for="(item, idx) in result.items"
          :key="item.question_id"
          class="review-item"
        >
          <view class="review-head">
            <text class="review-idx">第 {{ idx + 1 }} 题</text>
            <text :class="['review-flag', item.is_correct ? 'ok' : 'bad']">
              {{ item.is_correct ? '回答正确' : '需要复习' }}
            </text>
          </view>
          <text class="review-answer">正确答案：{{ item.correct_key }}</text>
          <text v-if="item.explanation" class="review-exp">
            解析：{{ item.explanation }}
          </text>
        </view>
      </view>
      <button :type="UNI_BUTTON_TYPE.primary" class="primary-btn" hover-class="hover-scale" @tap="restart">
            <text class="btn-icon">↺</text> 再来一轮
          </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { UNI_BUTTON_TYPE } from "@/utils/uni-button";
import {
  drawQuiz,
  submitQuiz as apiSubmitQuiz,
  type QuizDrawResult,
  type QuizQuestionStudent,
  type QuizSubmitResult,
  type QuizType,
} from "@/api/workflow";

type Stage = "pick" | "answer" | "result";
const stage = ref<Stage>("pick");

const form = reactive({ topic: "", limit: 20 });
const TOPICS = [
  { label: "马克思主义基本原理", value: "马克思主义基本原理", icon: "册" },
  { label: "思想道德与法治", value: "思想道德与法治", icon: "法" },
  { label: "中国近现代史纲要", value: "中国近现代史纲要", icon: "史" },
];
const LIMITS = [10, 20, 30];
const questions = ref<QuizQuestionStudent[]>([]);
const currentIdx = ref(0);
const batchId = ref("");
const answers = reactive<Record<number, string>>({});
const submitting = ref(false);
const result = ref<QuizSubmitResult | null>(null);

const current = computed(() => questions.value[currentIdx.value]);
const maxLimit = Math.max(...LIMITS);
const progressPercent = computed(() =>
  Math.round(((currentIdx.value + 1) / Math.max(questions.value.length, 1)) * 100),
);
const accuracyPercent = computed(() => {
  if (!result.value?.total) return 0;
  return Math.round((result.value.correct / result.value.total) * 100);
});

function qtypeLabel(t?: QuizType) {
  if (t === "SINGLE") return "单选";
  if (t === "MULTI") return "多选";
  if (t === "JUDGE") return "判断";
  return "";
}

function pickTopic(topic: string) {
  form.topic = form.topic === topic ? "" : topic;
}

async function startQuiz() {
  try {
    const resp = await drawQuiz({
      topic: form.topic || undefined,
      limit: form.limit > 0 ? form.limit : 5,
    });
    const data = resp.data as QuizDrawResult;
    if (!data.questions.length) {
      uni.showToast({ title: "暂无题目", icon: "none" });
      return;
    }
    questions.value = data.questions;
    batchId.value = data.batch_id;
    currentIdx.value = 0;
    for (const k of Object.keys(answers)) delete answers[Number(k)];
    stage.value = "answer";
  } catch {
    /* toast handled in request */
  }
}

function onSingleChange(e: any) {
  if (!current.value) return;
  answers[current.value.id] = e.detail.value;
}

function onMultiChange(e: any) {
  if (!current.value) return;
  const picked: string[] = e.detail.value || [];
  answers[current.value.id] = picked.sort().join(",");
}

function isMultiChecked(qid: number, key: string) {
  const raw = answers[qid];
  if (!raw) return false;
  return raw.split(",").includes(key);
}

function prevQ() {
  if (currentIdx.value > 0) currentIdx.value--;
}

function nextQ() {
  if (currentIdx.value < questions.value.length - 1) currentIdx.value++;
}

async function submitQuiz() {
  submitting.value = true;
  try {
    const payload = {
      batch_id: batchId.value,
      answers: questions.value.map((q) => ({
        question_id: q.id,
        answer: answers[q.id] || "",
      })),
    };
    const resp = await apiSubmitQuiz(payload);
    result.value = resp.data;
    stage.value = "result";
  } finally {
    submitting.value = false;
  }
}

function restart() {
  stage.value = "pick";
  result.value = null;
  questions.value = [];
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 24rpx 24rpx 36rpx;
  background:
    radial-gradient(circle at 100% 0, rgba(183, 15, 36, 0.08), transparent 220rpx),
    linear-gradient(180deg, #fff 0, #fff8f8 260rpx, #f8f3f4 100%),
    #f8f3f4;
}

.pick-card,
.result-card {
  background: transparent;
}

.quiz-hero,
.answer-hero,
.result-banner {
  padding: 34rpx 30rpx;
  border-radius: 28rpx;
  background:
    radial-gradient(circle at 86% 22%, rgba(255, 255, 255, 0.18), transparent 120rpx),
    linear-gradient(135deg, #d51f35, #b70f24 58%, #8b1020);
  color: #fff;
  box-shadow: 0 18rpx 40rpx rgba(93, 18, 30, 0.16);
}

.quiz-hero {
  margin: 0 -24rpx 0;
  min-height: 184rpx;
  border-radius: 0 0 28rpx 28rpx;
  padding: 42rpx 42rpx 76rpx;
  background:
    radial-gradient(circle at 84% 18%, rgba(255, 255, 255, 0.2), transparent 130rpx),
    linear-gradient(135deg, #cf1c32, #ab1024 64%, #86101f);
}

.pick-card .setup-card:first-of-type {
  position: relative;
  z-index: 2;
  margin-top: -42rpx;
  border-radius: 30rpx 30rpx 24rpx 24rpx;
}

.answer-hero {
  color: #202124;
  background: rgba(255, 255, 255, 0.98);
  border: 1rpx solid #f0e2e5;
  box-shadow: var(--shadow-card);
}

.answer-hero .hero-kicker {
  color: #b70f24;
  background: #fff1f2;
}

.answer-hero .hero-title,
.answer-hero .answer-strip-value {
  color: #202124;
}

.answer-hero .answer-strip-label {
  color: #8a8f98;
}

.answer-hero .question-pill {
  color: #b70f24;
  background: #fff1f2;
  border-color: #f0c9cf;
}

.hero-top {
  display: flex;
  justify-content: space-between;
  gap: 18rpx;
}

.hero-top.compact {
  align-items: flex-start;
}

.hero-kicker {
  display: inline-flex;
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.16);
  font-size: 20rpx;
  letter-spacing: 2rpx;
}

.hero-title {
  display: block;
  margin-top: 18rpx;
  font-size: 38rpx;
  font-weight: 800;
}

.hero-title.small {
  font-size: 34rpx;
}

.hero-sub {
  display: block;
  margin-top: 10rpx;
  font-size: 25rpx;
  line-height: 1.65;
  color: rgba(255, 255, 255, 0.88);
}

.hero-badge,
.question-pill {
  flex-shrink: 0;
  min-width: 92rpx;
  height: 92rpx;
  padding: 0 24rpx;
  border-radius: 28rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.12);
  color: #fff6d7;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  font-weight: 800;
}

.question-pill {
  height: auto;
  min-height: 72rpx;
  font-size: 24rpx;
  padding: 0 20rpx;
}

.hero-strip,
.answer-strip,
.result-strip {
  display: flex;
  gap: 14rpx;
  margin-top: 24rpx;
}

.hero-strip-item,
.answer-strip-item,
.result-strip-item {
  flex: 1;
  padding: 18rpx 16rpx;
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.14);
}

.answer-strip-item {
  background: #fff8f9;
  border: 1rpx solid #f0e2e5;
}

.hero-strip-value,
.answer-strip-value,
.result-strip-value {
  display: block;
  font-size: 30rpx;
  font-weight: 800;
}

.hero-strip-label,
.answer-strip-label,
.result-strip-label {
  display: block;
  margin-top: 8rpx;
  font-size: 20rpx;
  color: rgba(255, 255, 255, 0.84);
}

.setup-card,
.question-card,
.review-list {
  margin-top: 18rpx;
  padding: 24rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.98);
  border: 1rpx solid #f0e2e5;
  box-shadow: var(--shadow-card);
}

.block-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16rpx;
  margin-bottom: 18rpx;
}

.block-title,
.summary-title {
  display: block;
  font-size: 29rpx;
  font-weight: 800;
  color: #202124;
}

.block-meta {
  flex-shrink: 0;
  font-size: 22rpx;
  color: #8a8f98;
}

.topic-grid {
  display: flex;
  gap: 16rpx;
}

.topic-card {
  position: relative;
  flex: 1;
  min-height: 168rpx;
  padding: 18rpx 14rpx;
  border-radius: 20rpx;
  border: 1rpx solid #f0e2e5;
  background: linear-gradient(180deg, #fff, #fff8f9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14rpx;
}

.topic-card.active {
  border-color: #b70f24;
  background: linear-gradient(135deg, #d51f35, #8b1020);
  color: #fff;
  box-shadow: 0 12rpx 28rpx rgba(183, 15, 36, 0.2);
}

.topic-icon {
  width: 58rpx;
  height: 58rpx;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.16);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  font-weight: 800;
}

.topic-label {
  width: 150rpx;
  text-align: center;
  font-size: 23rpx;
  line-height: 1.45;
}

.topic-check {
  position: absolute;
  right: 14rpx;
  top: 14rpx;
  width: 32rpx;
  height: 32rpx;
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
  height: 72rpx;
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

.pick-summary {
  margin-top: 18rpx;
  padding: 22rpx 24rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, #fff8f1 0%, #fff 52%, #fff1f2 100%);
  border: 1rpx solid #f0d5da;
  box-shadow: var(--shadow-soft);
}

.summary-line {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  line-height: 1.65;
  color: #5f6368;
}

.primary-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  margin-top: 28rpx;
  height: 84rpx;
  line-height: 84rpx;
  border-radius: 20rpx;
  background: linear-gradient(135deg, #d51f35, #b70f24);
  color: #fff;
  font-weight: 800;
}

.flex-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
}

.btn-icon {
  font-size: 32rpx;
}

.hint {
  display: block;
  margin-top: 18rpx;
  color: #999;
  font-size: 24rpx;
  line-height: 1.6;
  text-align: center;
}

.answer-stage {
  min-height: calc(100vh - 48rpx);
}

.progress-bar {
  height: 10rpx;
  border-radius: 999rpx;
  background: #f3e6e8;
  overflow: hidden;
  margin-top: 20rpx;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #d51f35, #b70f24);
}

.question-card {
  margin-bottom: 18rpx;
  border-radius: 22rpx;
}

.question-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16rpx;
}

.question-index {
  display: inline-flex;
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: #fff1f2;
  color: #b70f24;
  font-size: 22rpx;
  font-weight: 700;
}

.stem {
  display: block;
  margin-top: 18rpx;
  font-size: 30rpx;
  line-height: 1.75;
  color: #202124;
}

.qtype-tag {
  display: inline-block;
  font-size: 22rpx;
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
}

.qtype-tag.single {
  background: #e6f7ff;
  color: #1890ff;
}

.qtype-tag.multi {
  background: #f9f0ff;
  color: #722ed1;
}

.qtype-tag.judge {
  background: #fff7e6;
  color: #fa8c16;
}

.opt-item {
  display: flex;
  align-items: center;
  min-height: 88rpx;
  padding: 18rpx 18rpx;
  border: 1rpx solid #f0e2e5;
  border-radius: 20rpx;
  margin-bottom: 14rpx;
  background: #fff;
  box-shadow: var(--shadow-soft);
}

.opt-item.checked {
  border-color: #f0c9cf;
  background: linear-gradient(90deg, #fff1f3, #fff);
  box-shadow: 0 10rpx 24rpx rgba(183, 15, 36, 0.09);
}

.opt-text {
  margin-left: 12rpx;
  font-size: 28rpx;
  line-height: 1.6;
  color: #334155;
}

.answer-note {
  margin-top: 12rpx;
  padding: 18rpx 20rpx;
  border-radius: 18rpx;
  background: #fff8f9;
  color: #8a6b72;
  font-size: 22rpx;
  line-height: 1.6;
}

.answer-spacer {
  height: 150rpx;
}

.answer-footer {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  padding: 18rpx 24rpx calc(18rpx + env(safe-area-inset-bottom));
  background: rgba(255, 255, 255, 0.97);
  border-top: 1rpx solid #f0e2e5;
  box-shadow: 0 -10rpx 28rpx rgba(82, 28, 38, 0.08);
  backdrop-filter: blur(12rpx);
}

.footer-copy {
  flex: 1;
  min-width: 0;
}

.footer-title {
  display: block;
  font-size: 26rpx;
  font-weight: 800;
  color: #1e293b;
}

.footer-desc {
  display: block;
  margin-top: 6rpx;
  font-size: 22rpx;
  line-height: 1.5;
  color: #8a8f98;
}

.footer-actions {
  display: flex;
  align-items: center;
  gap: 10rpx;
  flex-shrink: 0;
}

.footer-actions button {
  min-width: 136rpx;
  border-radius: 999rpx;
}

.result-banner {
  margin-bottom: 18rpx;
  min-height: 246rpx;
  background:
    radial-gradient(circle at 80% 28%, rgba(255, 226, 156, 0.3), transparent 130rpx),
    linear-gradient(135deg, #cf1c32, #9f1021 62%, #7f1722);
}

.result-kicker {
  display: block;
  font-size: 24rpx;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.88);
}

.result-title {
  display: block;
  font-size: 74rpx;
  font-weight: 800;
  color: #fff;
  margin-top: 10rpx;
}

.result-sub {
  display: block;
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.86);
  margin-top: 4rpx;
}

.review-list {
  margin-bottom: 24rpx;
}

.review-item {
  padding: 18rpx 0;
  border-bottom: 1rpx solid #f0e2e5;
}

.review-item:last-child {
  border-bottom: none;
}

.review-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.review-idx {
  display: inline-block;
  font-size: 26rpx;
  font-weight: 700;
  color: #202124;
}

.review-flag {
  display: inline-block;
  font-size: 22rpx;
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
}

.review-flag.ok {
  background: #f6ffed;
  color: #52c41a;
}

.review-flag.bad {
  background: #fff1f0;
  color: #f5222d;
}

.review-answer {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  color: #555;
}

.review-exp {
  display: block;
  margin-top: 6rpx;
  font-size: 22rpx;
  color: #888;
  line-height: 1.6;
}
</style>
