<template>
  <view class="container">
    <view class="page-hero">
      <view class="hero-top">
        <view class="hero-copy">
          <text class="hero-kicker">统一进度</text>
          <text class="hero-title">申请与党团流程一处查看</text>
          <text class="hero-desc">聚合当前步骤、详情路径和最近更新时间，方便你持续跟进。</text>
        </view>
        <view class="hero-badge">进</view>
      </view>

      <view class="hero-strip">
        <view class="hero-strip-item">
          <text class="hero-strip-value">{{ items.length }}</text>
          <text class="hero-strip-label">全部事项</text>
        </view>
        <view class="hero-strip-item">
          <text class="hero-strip-value">{{ requestCount }}</text>
          <text class="hero-strip-label">事务申请</text>
        </view>
        <view class="hero-strip-item">
          <text class="hero-strip-value">{{ workflowCount }}</text>
          <text class="hero-strip-label">党团流程</text>
        </view>
      </view>
    </view>

    <view class="section-header">
      <view>
        <text class="section-title">我的进度事项</text>
        <text class="section-desc">{{ syncDescription }}</text>
      </view>
      <text class="section-badge">{{ attentionCount }} 项待跟进</text>
    </view>

    <InlineStateNotice
      v-if="pageError"
      :tone="items.length ? 'warning' : 'error'"
      :title="items.length ? '进度列表未完全更新' : '进度列表加载失败'"
      :description="items.length ? `${pageError}，当前保留上次加载结果。` : `${pageError}，可点击重试重新同步。`"
      action-text="重试"
      @action="reload"
    />

    <EmptyState
      v-if="loading && !items.length"
      icon="进"
      tone="muted"
      title="统一进度加载中"
      description="正在同步你的申请与党团流程，请稍候。"
    />

    <template v-else-if="items.length">
      <view
        v-for="item in items"
        :key="item.id"
        class="progress-card"
        hover-class="hover-opacity"
        @tap="openDetail(item.detail_url)"
      >
        <view class="progress-head">
          <view class="progress-main">
            <view class="progress-badges">
              <text class="progress-badge primary">{{ sourceTypeLabel(item.source_type) }}</text>
              <text class="progress-badge">{{ item.status_label }}</text>
            </view>
            <text class="progress-title">{{ item.title }}</text>
            <text v-if="item.category" class="progress-category">{{ item.category }}</text>
          </view>
          <text class="progress-updated">{{ formatDateTime(item.updated_at) }}</text>
        </view>

        <view class="progress-summary">
          <view class="summary-chip">
            <text class="summary-chip-label">当前步骤</text>
            <text class="summary-chip-value emphasis">{{ currentStepLabel(item) }}</text>
          </view>
          <view class="summary-chip">
            <text class="summary-chip-label">详情路径</text>
            <text class="summary-chip-value url">{{ item.detail_url }}</text>
          </view>
        </view>

        <view class="progress-foot">
          <text class="progress-due">
            {{ item.due_date ? `截止：${formatDate(item.due_date)}` : '暂无办理截止时间' }}
          </text>
          <view class="progress-open">
            <text>打开详情</text>
            <view class="mini-chevron" />
          </view>
        </view>
      </view>
    </template>

    <EmptyState
      v-else-if="!pageError"
      icon="进"
      tone="primary"
      title="当前暂无进度事项"
      description="新的申请记录或党团流程进展会自动汇总到这里。"
    />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import EmptyState from '@/components/EmptyState.vue'
import InlineStateNotice from '@/components/InlineStateNotice.vue'
import { getMyProgress, type ProgressItem } from '@/api/progress'
import { getErrorMessage } from '@/utils/error'
import { openMiniappPage } from '@/utils/navigation'

const items = ref<ProgressItem[]>([])
const loading = ref(false)
const pageError = ref('')
const hasLoaded = ref(false)
const generatedAt = ref('')

const requestCount = computed(() =>
  items.value.filter((item) => item.source_type === 'REQUEST').length,
)

const workflowCount = computed(() =>
  items.value.filter((item) => item.source_type === 'WORKFLOW').length,
)

const attentionCount = computed(() =>
  items.value.filter((item) =>
    ['SUBMITTED', 'IN_REVIEW', 'ACTIVE', 'IN_PROGRESS', 'REJECTED', 'SUSPENDED'].includes(item.status),
  ).length,
)

const syncDescription = computed(() => {
  if (!generatedAt.value) return '按最近更新时间汇总你的申请与党团流程。'
  return `最近同步：${formatDateTime(generatedAt.value)}`
})

function sourceTypeLabel(sourceType: string) {
  if (sourceType === 'REQUEST') return '事务申请'
  if (sourceType === 'WORKFLOW') return '党团流程'
  return sourceType
}

function currentStepLabel(item: ProgressItem) {
  if (item.current_step) return item.current_step
  if (item.source_type === 'REQUEST') {
    return '请打开申请详情查看当前办理说明'
  }
  return '请打开流程详情查看当前节点'
}

function formatDate(value?: string | null) {
  if (!value) return '-'
  return value.length >= 10 ? value.slice(0, 10) : value
}

function formatDateTime(value?: string | null) {
  if (!value) return '-'
  const normalized = value.replace('T', ' ').replace('Z', '')
  return normalized.length >= 16 ? normalized.slice(0, 16) : normalized
}

async function openDetail(url: string) {
  try {
    await openMiniappPage(url)
  } catch {
    uni.showToast({ title: '页面跳转失败', icon: 'none' })
  }
}

async function reload() {
  loading.value = true
  try {
    pageError.value = ''
    const response = await getMyProgress()
    items.value = response.data.items || []
    generatedAt.value = response.data.generated_at || ''
    hasLoaded.value = true
  } catch (error) {
    pageError.value = getErrorMessage(error, '进度列表加载失败')
    if (!hasLoaded.value) {
      items.value = []
      generatedAt.value = ''
    }
  } finally {
    loading.value = false
  }
}

onShow(() => {
  void reload()
})

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
  padding: 0 24rpx 32rpx;
  background:
    linear-gradient(180deg, #b70f24 0, #b70f24 318rpx, #fff4f5 516rpx, #f8f3f4 100%),
    #f8f3f4;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.page-hero {
  margin: 0 -24rpx;
  padding: 48rpx 38rpx 42rpx;
  color: #fff;
  background:
    radial-gradient(circle at 86% 22%, rgba(255, 255, 255, 0.16), transparent 140rpx),
    linear-gradient(135deg, #d51f35, #b70f24 58%, #89101f);
}

.hero-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18rpx;
}

.hero-copy {
  flex: 1;
  min-width: 0;
}

.hero-kicker {
  display: inline-flex;
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.16);
  font-size: 20rpx;
  letter-spacing: 0;
}

.hero-title {
  display: block;
  margin-top: 18rpx;
  font-size: 42rpx;
  font-weight: 800;
  line-height: 1.2;
}

.hero-desc {
  display: block;
  margin-top: 14rpx;
  font-size: 24rpx;
  line-height: 1.75;
  color: rgba(255, 255, 255, 0.88);
}

.hero-badge {
  width: 96rpx;
  height: 96rpx;
  border-radius: 28rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.24);
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  font-weight: 900;
}

.hero-strip {
  display: flex;
  gap: 16rpx;
  margin-top: 28rpx;
}

.hero-strip-item {
  flex: 1;
  min-height: 120rpx;
  padding: 22rpx 18rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.14);
  border: 1rpx solid rgba(255, 255, 255, 0.14);
  backdrop-filter: blur(10rpx);
}

.hero-strip-value {
  display: block;
  font-size: 38rpx;
  font-weight: 800;
}

.hero-strip-label {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.84);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18rpx;
  padding: 8rpx 2rpx 2rpx;
}

.section-title {
  display: block;
  font-size: 30rpx;
  font-weight: 800;
  color: #1f2937;
}

.section-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #8a7280;
}

.section-badge {
  flex-shrink: 0;
  margin-top: 6rpx;
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: #fff1f2;
  color: #b70f24;
  font-size: 22rpx;
}

.progress-card {
  padding: 26rpx 24rpx;
  border-radius: 22rpx;
  background: linear-gradient(180deg, rgba(255, 251, 251, 0.98), rgba(255, 255, 255, 0.98));
  border: 1rpx solid #f0e2e5;
  box-shadow: var(--shadow-card);
}

.progress-head {
  display: flex;
  justify-content: space-between;
  gap: 18rpx;
}

.progress-main {
  flex: 1;
  min-width: 0;
}

.progress-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}

.progress-badge {
  display: inline-flex;
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  background: #f8f1f2;
  color: #8a6b72;
  font-size: 20rpx;
}

.progress-badge.primary {
  background: #fff1f2;
  color: #b70f24;
  font-weight: 700;
}

.progress-title {
  display: block;
  margin-top: 14rpx;
  font-size: 31rpx;
  font-weight: 800;
  color: #1e293b;
  line-height: 1.45;
}

.progress-category {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #64748b;
}

.progress-updated {
  flex-shrink: 0;
  font-size: 22rpx;
  color: #94a3b8;
}

.progress-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
  margin-top: 22rpx;
}

.summary-chip {
  padding: 18rpx;
  border-radius: 20rpx;
  background: #f8fafc;
}

.summary-chip-label {
  display: block;
  font-size: 20rpx;
  color: #94a3b8;
}

.summary-chip-value {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  font-weight: 700;
  color: #334155;
  line-height: 1.6;
}

.summary-chip-value.emphasis {
  color: #a61e2d;
}

.summary-chip-value.url {
  font-size: 22rpx;
  font-weight: 600;
  word-break: break-all;
}

.progress-foot {
  margin-top: 18rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14rpx;
}

.progress-due {
  font-size: 22rpx;
  color: #64748b;
}

.progress-open {
  display: flex;
  align-items: center;
  gap: 10rpx;
  color: #b70f24;
  font-size: 24rpx;
  font-weight: 700;
}
</style>
