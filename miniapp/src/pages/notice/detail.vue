<template>
  <view class="container">
    <view v-if="loading" class="loading">加载中...</view>

    <template v-else-if="notice">
      <view class="head-card">
        <text class="title">{{ notice.title }}</text>
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

      <view v-if="notice.summary" class="section-card">
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
        <view class="bottom-action">☆<text>收藏</text></view>
        <view class="bottom-action">↗<text>分享</text></view>
      </view>
    </template>

    <view v-else class="empty">未找到通知</view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getNoticeDetail, markRead, type NoticeDetail } from '@/api/notice'

const notice = ref<NoticeDetail | null>(null)
const loading = ref(false)
const noticeId = ref<number | null>(null)
const deliveryId = ref<number | null>(null)
const readSyncFailed = ref(false)

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
  if (!s) return ''
  return s.slice(0, 16).replace('T', ' ')
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
  const parsedNoticeId = Number(opts.noticeId ?? opts.id)
  const parsedDeliveryId = Number(opts.deliveryId)
  noticeId.value = Number.isFinite(parsedNoticeId) && parsedNoticeId > 0 ? parsedNoticeId : null
  deliveryId.value = Number.isFinite(parsedDeliveryId) && parsedDeliveryId > 0 ? parsedDeliveryId : null
  loadDetail()
})
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 28rpx 24rpx 0;
  background:
    linear-gradient(180deg, #b70f24 0, #b70f24 230rpx, #f8f3f4 430rpx),
    #f8f3f4;
}
.loading, .empty { text-align: center; padding: 80rpx 0; color: #999; font-size: 28rpx; }
.empty-tiny { text-align: center; padding: 16rpx 0; color: #bbb; font-size: 24rpx; }

.head-card {
  background: #fff;
  padding: 34rpx 30rpx;
  border-radius: 22rpx;
  margin-bottom: 18rpx;
  box-shadow: 0 16rpx 40rpx rgba(82, 28, 38, 0.14);
}
.title {
  display: block;
  font-size: 40rpx;
  font-weight: 800;
  color: #202124;
  line-height: 1.42;
}
.summary {
  display: block;
  padding: 22rpx;
  border-radius: 14rpx;
  background: #fff6f7;
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
  width: 38rpx;
  height: 38rpx;
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
  border-radius: 22rpx;
  margin-bottom: 18rpx;
  box-shadow: var(--shadow-card);
  border: 1rpx solid #f0e2e5;
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
  height: calc(104rpx + env(safe-area-inset-bottom));
  padding-bottom: env(safe-area-inset-bottom);
  background: rgba(255,255,255,0.98);
  border-top: 1rpx solid #f0e2e5;
  display: flex;
  justify-content: center;
  gap: 130rpx;
  box-shadow: 0 -8rpx 28rpx rgba(82,28,38,0.08);
}
.bottom-action {
  height: 104rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #202124;
  font-size: 34rpx;
}
.bottom-action text {
  margin-top: 4rpx;
  font-size: 23rpx;
}
</style>
