<template>
  <view class="container">
    <EmptyState
      v-if="loading"
      icon="◷"
      tone="muted"
      title="通知加载中"
      description="正在获取通知详情，请稍候。"
      compact
    />

    <template v-else-if="notice">
      <view class="notice-hero">
        <text class="hero-kicker">通知详情</text>
        <text class="hero-date" v-if="notice.published_at">{{ fmt(notice.published_at) }}</text>
      </view>

      <view class="head-card">
        <view class="title-row">
          <view class="title-icon">告</view>
        <text class="title">{{ notice.title }}</text>
        </view>
        <view class="meta-row">
          <text class="source-icon">源</text>
          <text class="source" :class="sourceClass(notice.source_type)">
            来源：{{ sourceLabel(notice.source_type) }}
          </text>
        </view>
        <view class="meta-row">
          <text class="source-icon time">时</text>
          <text class="published-at" v-if="notice.published_at">
            发布时间：{{ fmt(notice.published_at) }}
          </text>
        </view>
        <view
          v-if="readSyncFailed"
          class="sync-warning"
          @tap="retryMarkRead"
        >
          已打开通知，但已读同步失败，点击重试
        </view>
      </view>

      <view v-if="notice.summary" class="section-card summary-card">
        <view class="section-title-row">
          <text class="section-icon">摘</text>
          <text class="section-title">摘要</text>
        </view>
        <text class="summary">{{ notice.summary }}</text>
      </view>

      <view class="body-card section-card">
        <view class="section-title-row">
          <text class="section-icon">文</text>
          <text class="section-title">正文</text>
        </view>
        <text class="body-text" v-if="notice.body_md">{{ notice.body_md }}</text>
        <view v-else class="empty-tiny">暂无正文</view>
      </view>

      <view class="bottom-spacer" />
      <view class="bottom-actions safe-area-inset-bottom">
        <view class="bottom-action secondary" hover-class="hover-opacity" @tap="toggleFavorite">
          {{ favorited ? '★' : '☆' }}<text>{{ favorited ? '已收藏' : '收藏' }}</text>
        </view>
        <view class="bottom-action primary" hover-class="hover-opacity" @tap="shareNotice">↗<text>分享</text></view>
      </view>
    </template>

    <EmptyState
      v-else
      icon="?"
      tone="danger"
      title="未找到通知"
      description="该通知可能已失效或无权访问，可返回列表重试。"
      action-text="返回列表"
      @action="goBack"
      compact
    />
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import EmptyState from '@/components/EmptyState.vue'
import { getNoticeDetail, markRead, type NoticeDetail } from '@/api/notice'
import { formatShanghaiDateTime } from '@/utils/datetime'

const notice = ref<NoticeDetail | null>(null)
const loading = ref(false)
const noticeId = ref<number | null>(null)
const deliveryId = ref<number | null>(null)
const readSyncFailed = ref(false)
const favorited = ref(false)

const SOURCE_LABELS: Record<string, string> = {
  MANUAL: '手工发布',
  FEED: '订阅抓取',
  SYSTEM: '系统提醒',
}
function sourceLabel(s: string) { return SOURCE_LABELS[s] || s }
function sourceClass(s: string) {
  if (s === 'SYSTEM') return 'system'
  if (s === 'FEED') return 'feed'
  return 'manual'
}

function fmt(s?: string | null) {
  return formatShanghaiDateTime(s)
}

function noticeShareText() {
  if (!notice.value) return ''
  const source = notice.value.source_url ? `\n${notice.value.source_url}` : ''
  return `${notice.value.title}${source}`
}

function toggleFavorite() {
  favorited.value = !favorited.value
  uni.showToast({
    title: favorited.value ? '已收藏到本地' : '已取消收藏',
    icon: 'none',
  })
}

function shareNotice() {
  const text = noticeShareText()
  if (!text) {
    uni.showToast({ title: '暂无可分享内容', icon: 'none' })
    return
  }
  uni.setClipboardData({
    data: text,
    success() {
      uni.showToast({ title: '通知标题已复制', icon: 'none' })
    },
  })
}

function goBack() {
  uni.navigateBack({
    delta: 1,
    fail() {
      uni.switchTab({ url: '/pages/notice/index' })
    },
  })
}

async function loadDetail() {
  if (noticeId.value == null) return
  loading.value = true
  readSyncFailed.value = false
  try {
    const resp = await getNoticeDetail(noticeId.value)
    notice.value = resp.data
    await syncReadState()
  } catch {
    notice.value = null
  } finally {
    loading.value = false
  }
}

async function syncReadState() {
  if (deliveryId.value == null) return
  try {
    await markRead(deliveryId.value)
    readSyncFailed.value = false
  } catch {
    readSyncFailed.value = true
  }
}

async function retryMarkRead() {
  await syncReadState()
}

onMounted(() => {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1] as any
  const opts = current?.options || {}
  const noticeIdParam = opts.noticeId != null ? opts.noticeId : opts.id
  const parsedNoticeId = Number(noticeIdParam)
  const parsedDeliveryId = Number(opts.deliveryId)
  noticeId.value = Number.isFinite(parsedNoticeId) && parsedNoticeId > 0 ? parsedNoticeId : null
  deliveryId.value = Number.isFinite(parsedDeliveryId) && parsedDeliveryId > 0 ? parsedDeliveryId : null
  loadDetail()
})
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 0 24rpx 0;
  background:
    linear-gradient(180deg, #b70f24 0, #b70f24 228rpx, #f8f3f4 462rpx),
    #f7f1f2;
}
.empty-tiny { text-align: center; padding: 16rpx 0; color: #bbb; font-size: 24rpx; }

.notice-hero {
  position: relative;
  margin: 0 -24rpx;
  min-height: 196rpx;
  padding: 50rpx 42rpx 70rpx;
  color: #fff;
  background:
    radial-gradient(circle at 86% 28%, rgba(255,255,255,0.2), transparent 150rpx),
    linear-gradient(135deg, #c9152b, #9f1021 62%, #7f1722);
  overflow: hidden;
}

.notice-hero::after {
  content: "";
  position: absolute;
  right: -74rpx;
  bottom: -58rpx;
  width: 350rpx;
  height: 180rpx;
  border-radius: 180rpx 0 0 0;
  background: rgba(255,255,255,0.12);
}

.hero-kicker {
  display: block;
  font-size: 42rpx;
  font-weight: 900;
}

.hero-date {
  display: block;
  margin-top: 14rpx;
  font-size: 25rpx;
  opacity: 0.88;
}

.head-card {
  position: relative;
  z-index: 2;
  margin-top: -48rpx;
  background: rgba(255,255,255,0.98);
  padding: 34rpx 30rpx;
  border-radius: 18rpx;
  margin-bottom: 18rpx;
  box-shadow: var(--shadow-float);
  border: 1rpx solid rgba(240,226,229,0.9);
}
.title-row {
  display: flex;
  align-items: flex-start;
  gap: 18rpx;
}
.title-icon {
  width: 68rpx;
  height: 68rpx;
  border-radius: 18rpx;
  background: linear-gradient(135deg, #d51f35, #9f1021);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  font-weight: 900;
  flex-shrink: 0;
}
.title {
  display: block;
  flex: 1;
  font-size: 38rpx;
  font-weight: 900;
  color: #202124;
  line-height: 1.42;
}
.summary {
  display: block;
  padding: 24rpx;
  border-radius: 20rpx;
  background: #fff8f9;
  font-size: 28rpx;
  color: #333;
  line-height: 1.8;
}
.meta-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
  margin-top: 18rpx;
}
.source-icon {
  width: 42rpx;
  height: 42rpx;
  border-radius: 50%;
  background: #fff1f2;
  color: #b70f24;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20rpx;
  font-weight: 800;
}
.source-icon.time {
  background: #f8f3f4;
}
.source {
  font-size: 26rpx;
  color: #60646c;
}
.source.manual,
.source.feed,
.source.system { background: transparent; }
.published-at { font-size: 26rpx; color: #60646c; }
.sync-warning {
  margin-top: 18rpx;
  padding: 18rpx 20rpx;
  border-radius: 16rpx;
  background: #fff1f2;
  font-size: 24rpx;
  color: #b70f24;
}

.section-card {
  background: #fff;
  padding: 28rpx;
  border-radius: 18rpx;
  margin-bottom: 18rpx;
  box-shadow: var(--shadow-card);
  border: 1rpx solid #f0e2e5;
}
.summary-card {
  border-color: #f0c9cf;
}
.section-title-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
  margin-bottom: 20rpx;
}
.section-icon {
  width: 42rpx;
  height: 42rpx;
  border-radius: 10rpx;
  background: #b70f24;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
  font-weight: 800;
}
.section-title {
  color: #b70f24;
  font-size: 30rpx;
  font-weight: 800;
}
.body-text {
  font-size: 29rpx; color: #333; line-height: 1.9;
  white-space: pre-wrap; word-break: break-all;
}
.bottom-spacer { height: 126rpx; }
.bottom-actions {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  min-height: calc(112rpx + env(safe-area-inset-bottom));
  padding: 14rpx 76rpx calc(14rpx + env(safe-area-inset-bottom));
  background: rgba(255,255,255,0.98);
  border-top: 1rpx solid #f0e2e5;
  display: flex;
  justify-content: space-between;
  gap: 72rpx;
  box-shadow: 0 -8rpx 28rpx rgba(82,28,38,0.08);
}
.bottom-action {
  width: 128rpx;
  height: 88rpx;
  border-radius: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6rpx;
  font-size: 38rpx;
  font-weight: 800;
}
.bottom-action.secondary {
  color: #9f1021;
  background: transparent;
  border: none;
}
.bottom-action.primary {
  color: #9f1021;
  background: transparent;
  box-shadow: none;
}
.bottom-action text {
  font-size: 24rpx;
  color: #1f2937;
  font-weight: 500;
}
</style>
