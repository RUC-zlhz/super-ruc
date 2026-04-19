<template>
  <view class="container">
    <view v-if="loading" class="loading">加载中...</view>

    <template v-else-if="notice">
      <view class="head-card">
        <text class="title">{{ notice.title }}</text>
        <view class="meta-row">
          <text class="source" :class="sourceClass(notice.source_type)">
            {{ sourceLabel(notice.source_type) }}
          </text>
          <text class="published-at" v-if="notice.published_at">
            {{ fmt(notice.published_at) }}
          </text>
        </view>
        <text v-if="notice.summary" class="summary">{{ notice.summary }}</text>
      </view>

      <view class="body-card">
        <text class="body-text" v-if="notice.body_md">{{ notice.body_md }}</text>
        <view v-else class="empty-tiny">暂无正文</view>
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
  try {
    const resp = await getNoticeDetail(noticeId.value)
    notice.value = resp.data
    if (deliveryId.value != null) {
      try { await markRead(deliveryId.value) } catch { /* ok */ }
    }
  } catch {
    notice.value = null
  } finally {
    loading.value = false
  }
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
.container { padding: 24rpx; }
.loading, .empty { text-align: center; padding: 80rpx 0; color: #999; font-size: 28rpx; }
.empty-tiny { text-align: center; padding: 16rpx 0; color: #bbb; font-size: 24rpx; }

.head-card {
  background: #fff; padding: 28rpx; border-radius: 12rpx;
  margin-bottom: 16rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06);
}
.title {
  display: block; font-size: 34rpx; font-weight: 600;
  color: #333; line-height: 1.5;
}
.summary {
  display: block;
  margin-top: 12rpx;
  font-size: 26rpx;
  color: #666;
  line-height: 1.6;
}
.meta-row {
  display: flex; align-items: center; justify-content: space-between;
  margin-top: 16rpx;
}
.source {
  font-size: 22rpx; padding: 4rpx 14rpx; border-radius: 4rpx;
}
.source.manual { background: #fff1f0; color: #7f1722; }
.source.feed { background: #e6f7ff; color: #1890ff; }
.source.system { background: #f9f0ff; color: #722ed1; }
.published-at { font-size: 24rpx; color: #999; }

.body-card {
  background: #fff; padding: 28rpx; border-radius: 12rpx;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06);
}
.body-text {
  font-size: 28rpx; color: #333; line-height: 1.7;
  white-space: pre-wrap; word-break: break-all;
}
</style>
