<template>
  <view class="container">
    <EmptyState
      v-if="isGuest"
      icon="绑"
      tone="warning"
      title="请先绑定学号"
      description="访客身份不能查看学业缺口、成绩单 PDF 核验候选或课程建议。"
      action-text="去绑定"
      @action="goBindStudent"
    />
    <view v-else-if="loading" class="loading">加载中...</view>
    <template v-else>
      <InlineStateNotice
        v-if="pageError"
        :tone="result ? 'warning' : 'error'"
        :title="result ? '学业数据未完全更新' : '学业数据加载失败'"
        :description="result ? `${pageError}，当前保留上次加载结果。` : `${pageError}，可点击重试重新同步。`"
        action-text="重试"
        @action="reload"
      />

      <template v-if="result">
        <view class="weak-hint">
        <text class="weak-icon">i</text>
        <view class="weak-copy">
          <text class="weak-title">学业结论边界</text>
          <text class="weak-text">{{ result?.disclaimer || defaultDisclaimer }}</text>
        </view>
      </view>

      <view class="summary-card">
        <view class="credit-row">
          <view class="credit-col">
            <text class="num">{{ formatCredits(result.total_credits_earned) }}</text>
            <text class="lbl">已获学分</text>
          </view>
          <view class="credit-col">
            <text class="num">{{ formatCredits(result.total_credits_required) }}</text>
            <text class="lbl">参考要求</text>
          </view>
          <view class="credit-col">
            <text class="num gap" :class="{ positive: totalGapPositive }">
              {{ formatCredits(totalGapCredits) }}
            </text>
            <text class="lbl">差额参考</text>
          </view>
        </view>
      </view>

      <view class="conclusion-card" :class="riskToneClass">
        <view class="conclusion-head">
          <text class="conclusion-kicker">学分缺口结论</text>
          <text class="conclusion-pill">{{ riskLabel }}</text>
        </view>
        <text class="conclusion-text">
          {{ result.conclusion_text || fallbackConclusion }}
        </text>
        <view class="conclusion-grid">
          <view>
            <text class="conclusion-num">{{ gapModuleCount }}</text>
            <text class="conclusion-label">缺口模块</text>
          </view>
          <view>
            <text class="conclusion-num">{{ highPrioritySuggestionCount }}</text>
            <text class="conclusion-label">建议课程</text>
          </view>
        </view>
      </view>

      <view class="warning-card">
        <text class="warning-icon">!</text>
        <view class="warning-copy">
        <text class="warning-title">数据提示</text>
        <template v-if="result.data_warnings?.length">
        <text v-for="warning in result.data_warnings" :key="warning" class="warning-item">
          {{ warning }}
        </text>
        </template>
        <text v-else class="warning-item">当前数据仅供参考，请以正式审核结果为准。</text>
        </view>
      </view>

      <view class="upload-card">
        <view class="upload-head">
          <view>
            <text class="upload-title">成绩单 PDF 核验</text>
            <text class="upload-desc">上传后仅生成待核验记录，不会直接改写正式成绩。</text>
          </view>
          <button
            class="upload-btn"
            size="mini"
            :loading="uploadingTranscript"
            :disabled="uploadingTranscript"
            hover-class="hover-opacity"
            @tap="onUploadTranscriptPdf"
          >
            上传 PDF
          </button>
        </view>
        <view v-if="transcriptUpload" class="upload-result">
          <view class="upload-result-main">
            <text class="upload-result-title">已提交人工核验</text>
            <text class="upload-result-meta">
              批次 {{ transcriptUpload.batch_no }} · 疑似课程 {{ transcriptUpload.parsed_courses_count }} 条 · 正式写入 {{ transcriptUpload.formal_records_written }} 条
            </text>
          </view>
          <text
            v-for="warning in transcriptUpload.data_warnings"
            :key="warning"
            class="upload-warning"
          >
            {{ warning }}
          </text>
        </view>
      </view>

      <view v-if="transcriptUpload" class="review-card">
        <view class="review-head">
          <view class="review-head-main">
            <text class="review-title">候选课程与教师核验边界</text>
            <text class="review-desc">
              {{ transcriptBoundaryText }}
            </text>
          </view>
          <text class="review-pill" :class="{ warned: transcriptUpload.review_required }">
            {{ transcriptUpload.review_required ? '待教师核验' : '已核验' }}
          </text>
        </view>

        <view class="review-metrics">
          <view class="review-metric">
            <text class="review-metric-value">{{ transcriptUpload.parsed_courses_count }}</text>
            <text class="review-metric-label">候选课程</text>
          </view>
          <view class="review-metric">
            <text class="review-metric-value">{{ transcriptUpload.formal_records_written }}</text>
            <text class="review-metric-label">正式写入</text>
          </view>
          <view class="review-metric">
            <text class="review-metric-value">{{ transcriptUpload.data_warnings.length }}</text>
            <text class="review-metric-label">提示信息</text>
          </view>
        </view>

        <view v-if="candidateCourses.length" class="candidate-list">
          <view
            v-for="course in candidateCourses"
            :key="candidateCourseKey(course)"
            class="candidate-card"
          >
            <view class="candidate-head">
              <view class="candidate-main">
                <text class="candidate-title">
                  {{ course.course_code || '待识别课程' }} · {{ course.course_name || '待识别名称' }}
                </text>
                <text class="candidate-raw">原始行 {{ course.line_no }}：{{ course.raw_text }}</text>
              </view>
              <text class="candidate-confidence">{{ confidenceLabel(course.confidence) }}</text>
            </view>

            <view class="candidate-meta">
              <text v-if="course.credits != null" class="candidate-chip">学分 {{ formatCredits(course.credits) }}</text>
              <text v-if="course.term_code" class="candidate-chip">学期 {{ course.term_code }}</text>
              <text v-if="course.score != null" class="candidate-chip">成绩 {{ course.score }}</text>
              <text v-if="course.grade_letter" class="candidate-chip">等级 {{ course.grade_letter }}</text>
              <text class="candidate-chip" :class="{ pass: course.pass_flag }">
                {{ course.pass_flag ? '判定通过' : '待教师确认' }}
              </text>
            </view>
          </view>
        </view>
        <view v-else class="empty-tiny">暂无解析出的候选课程</view>

        <view v-if="transcriptUpload.data_warnings.length" class="review-warnings">
          <text class="review-warnings-title">核验提示</text>
          <text
            v-for="warning in transcriptUpload.data_warnings"
            :key="warning"
            class="review-warning-item"
          >
            {{ warning }}
          </text>
        </view>
      </view>

      <view class="section">
        <view class="section-head">
          <text class="section-title">模块完成情况</text>
          <text class="plan-name">共 {{ result.modules.length }} 个模块</text>
        </view>
        <view
          v-for="m in result.modules"
          :key="m.module_code"
          class="module-card"
        >
          <view class="module-icon">{{ moduleIcon(m.module_type) }}</view>
          <view class="module-main">
          <view class="mod-head">
            <text class="mod-name">{{ m.module_name }}</text>
            <text class="mod-tag" :class="{ done: m.credits_gap <= 0 }">
              {{ m.credits_gap <= 0 ? '已完成' : '进行中' }}
            </text>
          </view>
          <text class="mod-meta">完成 {{ formatCredits(m.credits_earned) }} / 要求 {{ formatCredits(m.credits_required) }} 学分</text>
          <view class="progress-track">
            <view
              class="progress-fill"
              :style="{ width: Math.min(100, m.credits_required ? (m.credits_earned / m.credits_required * 100) : 0) + '%' }"
            />
          </view>
          <text class="mod-percent">
            {{ Math.min(100, m.credits_required ? Math.round(m.credits_earned / m.credits_required * 100) : 0) }}%
          </text>
          <text v-if="m.note" class="mod-note">{{ m.note }}</text>
          </view>
        </view>
        <view v-if="!result.modules.length" class="empty-tiny">暂无模块数据</view>
      </view>

      <view class="section">
        <view class="section-head">
          <text class="section-title">课程类型建议</text>
          <text class="plan-name">
            {{ result.recommendation_term_code || '当前学期' }} · 共 {{ result.suggested_courses?.length || 0 }} 条
          </text>
        </view>
        <view
          v-for="course in result.suggested_courses || []"
          :key="suggestedCourseKey(course)"
          class="suggest-card"
        >
          <view class="suggest-head">
            <text class="suggest-title">{{ course.course_name || course.course_code || '待选课程' }}</text>
            <text class="suggest-tag">{{ course.course_type || course.module_name || '参考建议' }}</text>
          </view>
          <text class="suggest-meta">
            {{ [course.course_code, course.module_name, formatCredits(course.credits)].filter(Boolean).join(' · ') }}
          </text>
          <text v-if="course.reason" class="suggest-reason">{{ course.reason }}</text>
        </view>
        <view v-if="!result.suggested_courses?.length" class="empty-tiny">
          暂无课程类型建议，请以教务审核和培养方案为准。
        </view>
      </view>

      <view class="footer-hint">
        <text class="footer-icon">盾</text>
        <view>
          <text class="footer-title">最终毕业资格以学校正式审核为准</text>
          <text class="footer-text">请持续关注教务通知，及时完成相关学习要求。</text>
        </view>
      </view>
      </template>

      <view v-else-if="!pageError" class="empty">暂无学业数据</view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import EmptyState from '@/components/EmptyState.vue'
import InlineStateNotice from '@/components/InlineStateNotice.vue'
import {
  getMyAcademicGap,
  type TranscriptPdfCandidateCourse,
  uploadTranscriptPdf,
  type AcademicGapResult,
  type SuggestedCourse,
  type TranscriptPdfUploadResult,
} from '@/api/report'
import { useAuthStore } from '@/store/auth'
import { getErrorMessage } from '@/utils/error'
import { openMiniappPage } from '@/utils/navigation'

const auth = useAuthStore()
const result = ref<AcademicGapResult | null>(null)
const loading = ref(false)
const uploadingTranscript = ref(false)
const transcriptUpload = ref<TranscriptPdfUploadResult | null>(null)
const pageError = ref('')
const hasLoaded = ref(false)
const defaultDisclaimer = '本结果仅为辅助提示，不构成毕业资格、课程替代或教务最终结论；请以学院/学校正式审核结果为准。'
const isGuest = computed(() => auth.isLoggedIn && !auth.user?.student_id)
const RISK_LABELS: Record<string, string> = {
  HIGH: '高关注',
  MEDIUM: '待跟进',
  LOW: '低关注',
}

const MODULE_TYPE_LABELS: Record<string, string> = {
  REQUIRED: '必修模块',
  ELECTIVE: '选修模块',
  GENERAL: '通识模块',
  PRACTICE: '实践模块',
}

const totalGapCredits = computed(() => {
  if (!result.value) return null
  if (result.value.credits_gap != null) return result.value.credits_gap
  if (result.value.total_credits_required == null) return null
  return Math.max(result.value.total_credits_required - result.value.total_credits_earned, 0)
})

const totalGapPositive = computed(() => (totalGapCredits.value == null ? 0 : totalGapCredits.value) > 0)
const riskLevel = computed(() => result.value?.risk_level || (totalGapPositive.value ? 'MEDIUM' : 'LOW'))
const riskLabel = computed(() => RISK_LABELS[riskLevel.value] || '待核验')
const riskToneClass = computed(() => `risk-${riskLevel.value.toLowerCase()}`)
const gapModuleCount = computed(() => result.value?.modules.filter((item) => item.credits_gap > 0).length || 0)
const highPrioritySuggestionCount = computed(() => result.value?.suggested_courses?.length || 0)
const fallbackConclusion = computed(() => {
  if (totalGapCredits.value == null) return '当前缺少培养方案或成绩数据，暂不能形成学分差额结论。'
  if (totalGapCredits.value <= 0) return '按当前数据未发现总学分差额。'
  return `按当前数据仍有 ${formatCredits(totalGapCredits.value)} 学分缺口。`
})
const candidateCourses = computed(() => transcriptUpload.value?.parsed_courses || [])
const transcriptBoundaryText = computed(() => {
  if (!transcriptUpload.value) return ''
  if (transcriptUpload.value.review_required) {
    return '这些解析结果仅作为教师人工核验的候选项，正式成绩不会因学生上传直接写入。'
  }
  return '当前结果已通过人工核验；如后续重新上传，仍会进入教师复核流程。'
})

function formatCredits(value?: number | null) {
  if (value == null) return '-'
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

function moduleTypeLabel(moduleType: string) {
  return MODULE_TYPE_LABELS[moduleType] || moduleType
}

function moduleIcon(moduleType: string) {
  if (moduleType === 'REQUIRED') return '书'
  if (moduleType === 'ELECTIVE') return '帽'
  if (moduleType === 'PRACTICE') return '验'
  if (moduleType === 'GENERAL') return '星'
  return '学'
}

function suggestedCourseKey(course: SuggestedCourse) {
  return [
    course.module_code || 'module',
    course.course_code || course.course_name || 'course',
    course.course_type || 'type',
  ].join('-')
}

function candidateCourseKey(course: TranscriptPdfCandidateCourse) {
  return [course.line_no, course.course_code || course.course_name || course.raw_text].join('-')
}

function confidenceLabel(confidence: string) {
  return confidence ? confidence.toUpperCase() : 'LOW'
}

async function onUploadTranscriptPdf() {
  const selected = await new Promise<any>((resolve) => {
    uni.chooseMessageFile({
      count: 1,
      type: 'file',
      success: resolve,
      fail: () => resolve(null),
    })
  })
  const file = selected?.tempFiles?.[0] as { path?: string; tempFilePath?: string; name?: string } | undefined
  const filePath = file?.path || file?.tempFilePath
  if (!filePath) return
  if (file?.name && !file.name.toLowerCase().endsWith('.pdf')) {
    uni.showToast({ title: '请选择 PDF 文件', icon: 'none' })
    return
  }

  uploadingTranscript.value = true
  try {
    transcriptUpload.value = await uploadTranscriptPdf(filePath)
    uni.showToast({ title: '已提交核验', icon: 'none' })
  } finally {
    uploadingTranscript.value = false
  }
}

async function reload() {
  if (isGuest.value) {
    result.value = null
    pageError.value = ''
    hasLoaded.value = false
    transcriptUpload.value = null
    return
  }
  loading.value = true
  try {
    pageError.value = ''
    const resp = await getMyAcademicGap()
    result.value = resp.data
    hasLoaded.value = true
  } catch (error) {
    pageError.value = getErrorMessage(error, '学业数据加载失败')
    if (!hasLoaded.value) {
      result.value = null
    }
  } finally {
    loading.value = false
  }
}

function goBindStudent() {
  void openMiniappPage('/pages/profile/index')
}

onShow(reload)

onPullDownRefresh(async () => {
  try {
    await reload()
  } finally {
    uni.stopPullDownRefresh()
  }
})
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 28rpx 36rpx 36rpx;
  background:
    radial-gradient(circle at 100% 22%, rgba(183, 15, 36, 0.08), transparent 180rpx),
    linear-gradient(180deg, #fff 0, #fff 120rpx, #f7f1f2 420rpx),
    #f7f1f2;
}

.weak-hint {
  display: flex;
  gap: 18rpx;
  background: #fff6f7;
  color: #b70f24;
  padding: 28rpx;
  border-radius: 18rpx;
  border: 2rpx solid #d13b4b;
  margin-bottom: 28rpx;
  box-shadow: var(--shadow-soft);
}
.weak-icon {
  width: 54rpx;
  height: 54rpx;
  border-radius: 50%;
  border: 4rpx solid #d43346;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  font-weight: 800;
}
.weak-copy { flex: 1; }
.weak-title {
  display: block;
  font-size: 30rpx;
  font-weight: 800;
}
.weak-text {
  display: block;
  margin-top: 8rpx;
  font-size: 26rpx;
  line-height: 1.7;
}

.loading { text-align: center; padding: 80rpx 0; color: #999; font-size: 28rpx; }
.empty { text-align: center; padding: 80rpx 0; color: #999; font-size: 28rpx; }
.empty-tiny { text-align: center; padding: 16rpx 0; color: #bbb; font-size: 24rpx; }

.summary-card {
  position: relative;
  z-index: 2;
  margin-top: 0;
  background: rgba(255,255,255,0.97);
  border-radius: 28rpx;
  padding: 36rpx 24rpx;
  margin-bottom: 28rpx;
  box-shadow: var(--shadow-float);
  border: 1rpx solid rgba(240,226,229,0.92);
}
.credit-row { display: flex; justify-content: space-around; }
.credit-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  border-right: 1rpx solid #f0e2e5;
}
.credit-col:last-child { border-right: none; }
.num { font-size: 64rpx; font-weight: 900; color: #b70f24; }
.num.gap { color: #16a34a; }
.num.gap.positive { color: #b70f24; }
.lbl { font-size: 25rpx; color: #6b7280; margin-top: 6rpx; }

.conclusion-card {
  margin-bottom: 28rpx;
  padding: 28rpx;
  border-radius: 28rpx;
  background: #fff;
  border: 1rpx solid #f0e2e5;
  box-shadow: var(--shadow-card);
}
.conclusion-card.risk-high {
  background: linear-gradient(180deg, #fff7f7, #fff);
  border-color: #efc2c8;
}
.conclusion-card.risk-medium {
  background: linear-gradient(180deg, #fffaf0, #fff);
  border-color: #f1d9a8;
}
.conclusion-card.risk-low {
  background: linear-gradient(180deg, #f4fff8, #fff);
  border-color: #bfe8cf;
}
.conclusion-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18rpx;
}
.conclusion-kicker {
  font-size: 24rpx;
  color: #6b7280;
}
.conclusion-pill {
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  background: #fff1f2;
  color: #b70f24;
  font-size: 22rpx;
  font-weight: 800;
}
.risk-medium .conclusion-pill {
  background: #fff7ed;
  color: #b45309;
}
.risk-low .conclusion-pill {
  background: #ecfdf3;
  color: #15803d;
}
.conclusion-text {
  display: block;
  margin-top: 14rpx;
  color: #202124;
  font-size: 31rpx;
  line-height: 1.55;
  font-weight: 800;
}
.conclusion-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
  margin-top: 20rpx;
}
.conclusion-grid > view {
  padding: 18rpx;
  border-radius: 20rpx;
  background: rgba(255,255,255,0.76);
  border: 1rpx solid #f3e8eb;
}
.conclusion-num {
  display: block;
  color: #b70f24;
  font-size: 36rpx;
  font-weight: 900;
}
.conclusion-label {
  display: block;
  margin-top: 4rpx;
  color: #6b7280;
  font-size: 22rpx;
}

.warning-card {
  display: flex;
  gap: 18rpx;
  background: #fff9ec;
  border-radius: 22rpx;
  padding: 22rpx;
  margin-bottom: 28rpx;
  border: 1rpx solid #f6df9f;
  box-shadow: var(--shadow-soft);
}
.warning-icon {
  width: 50rpx;
  height: 50rpx;
  border-radius: 50%;
  border: 4rpx solid #c98a16;
  color: #c98a16;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  font-weight: 800;
}
.warning-copy { flex: 1; }
.plan-name {
  color: #8a7b80;
  font-size: 24rpx;
}
.warning-title {
  display: block;
  font-size: 26rpx;
  font-weight: 600;
  color: #ad6800;
  margin-bottom: 8rpx;
}
.warning-item {
  display: block;
  font-size: 24rpx;
  color: #ad6800;
  line-height: 1.6;
}

.upload-card {
  background: #fff;
  border-radius: 28rpx;
  padding: 24rpx;
  margin-bottom: 28rpx;
  box-shadow: var(--shadow-card);
  border: 1rpx solid #f0e2e5;
}
.upload-head {
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
  align-items: center;
}
.upload-title {
  display: block;
  font-size: 30rpx;
  color: #242022;
  font-weight: 800;
}
.upload-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  line-height: 1.5;
  color: #6b7280;
}
.upload-btn {
  flex-shrink: 0;
  min-width: 150rpx;
  height: 64rpx;
  line-height: 64rpx;
  border-radius: 999rpx;
  background: #b70f24;
  color: #fff;
  font-size: 24rpx;
  font-weight: 700;
}
.upload-btn::after {
  border: none;
}
.upload-result {
  margin-top: 22rpx;
  padding: 20rpx;
  border-radius: 20rpx;
  background: #fff6f7;
  border: 1rpx solid #f2c8cf;
}
.upload-result-main {
  margin-bottom: 12rpx;
}
.upload-result-title {
  display: block;
  color: #b70f24;
  font-size: 26rpx;
  font-weight: 800;
}
.upload-result-meta {
  display: block;
  margin-top: 6rpx;
  color: #6b7280;
  font-size: 23rpx;
  line-height: 1.5;
}
.upload-warning {
  display: block;
  color: #9f1239;
  font-size: 23rpx;
  line-height: 1.55;
}

.review-card {
  margin-bottom: 28rpx;
  padding: 24rpx;
  border-radius: 28rpx;
  background: linear-gradient(180deg, #fffdfd, #fff7f8);
  border: 1rpx solid #f0d7dd;
  box-shadow: var(--shadow-card);
}

.review-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18rpx;
}

.review-head-main {
  flex: 1;
  min-width: 0;
}

.review-title {
  display: block;
  font-size: 30rpx;
  font-weight: 800;
  color: #202124;
}

.review-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  line-height: 1.65;
  color: #6b7280;
}

.review-pill {
  flex-shrink: 0;
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: #f0fdf4;
  color: #15803d;
  font-size: 22rpx;
  font-weight: 700;
}

.review-pill.warned {
  background: #fff7ed;
  color: #b45309;
}

.review-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14rpx;
  margin-top: 18rpx;
}

.review-metric {
  padding: 16rpx 14rpx;
  border-radius: 20rpx;
  background: #fff;
  border: 1rpx solid #f0e2e5;
  text-align: center;
}

.review-metric-value {
  display: block;
  font-size: 32rpx;
  font-weight: 800;
  color: #b70f24;
}

.review-metric-label {
  display: block;
  margin-top: 6rpx;
  font-size: 22rpx;
  color: #6b7280;
}

.candidate-list {
  margin-top: 20rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.candidate-card {
  padding: 20rpx;
  border-radius: 22rpx;
  background: #fff;
  border: 1rpx solid #f0e2e5;
}

.candidate-head {
  display: flex;
  justify-content: space-between;
  gap: 14rpx;
  align-items: flex-start;
}

.candidate-main {
  flex: 1;
  min-width: 0;
}

.candidate-title {
  display: block;
  font-size: 27rpx;
  font-weight: 800;
  color: #1f2937;
}

.candidate-raw {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #6b7280;
}

.candidate-confidence {
  flex-shrink: 0;
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: #fff1f2;
  color: #b70f24;
  font-size: 20rpx;
  font-weight: 700;
}

.candidate-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 14rpx;
}

.candidate-chip {
  padding: 6rpx 12rpx;
  border-radius: 999rpx;
  background: #f8fafc;
  color: #475569;
  font-size: 20rpx;
}

.candidate-chip.pass {
  background: #ecfdf3;
  color: #15803d;
}

.review-warnings {
  margin-top: 18rpx;
  padding: 18rpx;
  border-radius: 20rpx;
  background: #fff7ed;
  border: 1rpx solid #fed7aa;
}

.review-warnings-title {
  display: block;
  font-size: 24rpx;
  font-weight: 800;
  color: #b45309;
}

.review-warning-item {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #9a5b00;
}

.suggest-card {
  padding: 20rpx 0;
  border-bottom: 1rpx solid #f0e2e5;
}

.suggest-card:last-child {
  border-bottom: none;
}

.suggest-head {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
  align-items: flex-start;
}

.suggest-title {
  flex: 1;
  color: #242022;
  font-size: 28rpx;
  line-height: 1.45;
  font-weight: 800;
}

.suggest-tag {
  flex-shrink: 0;
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  background: #fff1f2;
  color: #b70f24;
  font-size: 22rpx;
}

.suggest-meta,
.suggest-reason {
  display: block;
  margin-top: 8rpx;
  color: #6b7280;
  font-size: 23rpx;
  line-height: 1.55;
}

.section {
  background: #fff;
  border-radius: 28rpx;
  padding: 24rpx;
  margin-bottom: 22rpx;
  box-shadow: var(--shadow-card);
  border: 1rpx solid #f0e2e5;
}
.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18rpx;
}
.section-title {
  font-size: 31rpx;
  font-weight: 800;
  display: block;
  padding-left: 16rpx;
  border-left: 8rpx solid #b70f24;
}

.module-card {
  position: relative;
  display: flex;
  gap: 20rpx;
  padding: 22rpx 0 24rpx;
  border-bottom: 1rpx solid #f0e2e5;
}
.module-card:last-child { border-bottom: none; }
.module-icon {
  width: 84rpx;
  height: 84rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, #d51f35, #9f1021);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 800;
}
.module-main { flex: 1; min-width: 0; position: relative; }
.mod-head { display: flex; justify-content: space-between; align-items: center; }
.mod-name { font-size: 31rpx; color: #333; font-weight: 800; }
.mod-tag {
  font-size: 22rpx; padding: 6rpx 18rpx; border-radius: 999rpx;
  background: #fff1f2; color: #b70f24;
}
.mod-tag.done {
  background: #ecfdf3;
  color: #15803d;
}
.mod-meta { display: block; font-size: 25rpx; color: #6b7280; margin-top: 8rpx; }

.progress-track {
  margin-top: 18rpx;
  height: 16rpx;
  background: #edf0f3;
  border-radius: 999rpx;
  overflow: hidden;
  margin-right: 90rpx;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #fb7185, #b70f24);
  transition: width .3s ease;
}
.mod-percent {
  position: absolute;
  right: 0;
  top: 88rpx;
  color: #b70f24;
  font-size: 28rpx;
  font-weight: 800;
}
.mod-note {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  color: #999;
  line-height: 1.6;
}

.footer-hint {
  display: flex;
  gap: 20rpx;
  align-items: center;
  background: linear-gradient(135deg, #b70f24, #8b1020);
  border-radius: 24rpx;
  padding: 24rpx;
  color: #fff;
}
.footer-icon {
  width: 68rpx;
  height: 68rpx;
  border-radius: 50%;
  border: 2rpx solid rgba(255,255,255,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}
.footer-title {
  display: block;
  font-size: 28rpx;
  font-weight: 800;
}
.footer-text {
  display: block;
  margin-top: 6rpx;
  font-size: 23rpx;
  opacity: 0.88;
}
</style>
