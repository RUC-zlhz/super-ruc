<template>
  <view class="container">
    <view class="top-tools">
      <view class="fake-search">
        <text class="search-icon">⌕</text>
        <text>搜索通知标题或来源</text>
      </view>
      <text class="more-dot">•••</text>
    </view>

    <view class="tab-row">
      <view
        v-for="t in TABS"
        :key="t.value"
        class="tab"
        :class="{ active: tab === t.value }"
        @tap="onTab(t.value)"
      >{{ t.label }}</view>
    </view>

    <view v-if="visibleNotices.length" class="list">
      <view
        v-for="n in visibleNotices"
        :key="n.delivery_id ?? n.id"
        class="notice-card"
        :class="{ unread: isUnread(n), pinned: n.is_pinned }"
        @tap="onDetail(n)"
      >
        <view class="notice-icon" :class="{ muted: !isUnread(n) }">{{ noticeIcon(n) }}</view>
        <view class="notice-main">
          <view class="notice-head">
            <text class="notice-title">{{ n.title }}</text>
            <text class="pin-corner" v-if="n.is_pinned">置顶</text>
          </view>
          <text class="notice-source">{{ noticeTag(n) }}</text>
          <text class="notice-preview" v-if="n.summary">{{ n.summary.slice(0, 80) }}</text>
          <view class="notice-footer">
            <text class="notice-date">◷ {{ n.published_at?.slice(0, 16).replace('T', ' ') }}</text>
            <text class="read-mark" v-if="!isUnread(n)">✓</text>
          </view>
        </view>
      </view>
    </view>

    <view v-else-if="!loading" class="empty">暂无通知</view>

    <view v-if="hasMore" class="load-more" @tap="loadMore">加载更多</view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getMyNotices, type StudentNoticeItem } from '@/api/notice'

type NoticeTab = 'all' | 'unread' | 'read'

const TABS: Array<{ label: string; value: NoticeTab }> = [
  { label: '全部', value: 'all' },
  { label: '未读', value: 'unread' },
  { label: '已读', value: 'read' },
]
const tab = ref<NoticeTab>('all')

const CATEGORY_LABELS: Record<string, string> = {
  SYSTEM: '系统通知',
  ACADEMIC: '教学通知',
  PARTY: '党团通知',
  CAMPUS: '校园通知',
}

const notices = ref<StudentNoticeItem[]>([])
const page = ref(1)
const size = 20
const total = ref(0)
const loading = ref(false)
const hasMore = computed(() => notices.value.length < total.value)

function isUnread(notice: StudentNoticeItem) {
  return !notice.read_at
}

function noticeTag(notice: StudentNoticeItem) {
  if (notice.is_pinned) return '置顶'
  if (notice.category) return CATEGORY_LABELS[notice.category] || notice.category
  return '通知'
}

function noticeIcon(notice: StudentNoticeItem) {
  const tag = notice.category || ''
  if (tag.includes('ACADEMIC') || tag.includes('教')) return '学'
  if (tag.includes('PARTY') || tag.includes('党')) return '党'
  if (tag.includes('SYSTEM') || tag.includes('系统')) return '⚙'
  if (tag.includes('CAMPUS') || tag.includes('校园')) return '园'
  return '铃'
}

const visibleNotices = computed(() => {
  if (tab.value === 'unread') return notices.value.filter(isUnread)
  if (tab.value === 'read') return notices.value.filter(n => !isUnread(n))
  return notices.value
})

async function reload(reset = true) {
  if (loading.value) return
  if (reset) { page.value = 1; notices.value = [] }
  loading.value = true
  try {
    const resp = await getMyNotices({ page: page.value, size })
    notices.value = reset ? resp.data.items : [...notices.value, ...resp.data.items]
    total.value = resp.data.meta?.total || notices.value.length
  } finally {
    loading.value = false
  }
}

function loadMore() {
  if (loading.value || !hasMore.value) return
  page.value += 1
  reload(false)
}

function onTab(v: NoticeTab) {
  tab.value = v
}

function onDetail(notice: StudentNoticeItem) {
  const query = [`noticeId=${notice.id}`]
  if (notice.delivery_id != null) {
    query.push(`deliveryId=${notice.delivery_id}`)
  }
  uni.navigateTo({ url: `/pages/notice/detail?${query.join('&')}` })
}

onShow(() => reload())
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 24rpx;
  background:
    linear-gradient(180deg, #fff 0, #fff 150rpx, #f8f3f4 420rpx),
    #f8f3f4;
}

.top-tools {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 22rpx;
}

.fake-search {
  flex: 1;
  height: 72rpx;
  border-radius: 24rpx;
  background: #fff;
  border: 1rpx solid #f0e2e5;
  color: #9aa0a6;
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 0 22rpx;
  font-size: 24rpx;
  box-shadow: var(--shadow-soft);
}

.search-icon { font-size: 34rpx; }
.more-dot { color: #1f2937; font-size: 32rpx; letter-spacing: 4rpx; }

.tab-row {
  display: flex;
  background: #f3f1f2;
  border-radius: 999rpx;
  padding: 8rpx;
  margin-bottom: 22rpx;
}
.tab {
  flex: 1;
  text-align: center;
  padding: 18rpx 0;
  border-radius: 999rpx;
  font-size: 28rpx;
  color: #222;
}
.tab.active {
  color: #fff;
  background: #b70f24;
  font-weight: 800;
  box-shadow: 0 8rpx 18rpx rgba(183,15,36,0.18);
}

.list {}
.notice-card {
  display: flex;
  gap: 22rpx;
  background: #fff;
  padding: 26rpx;
  border-radius: 24rpx;
  margin-bottom: 18rpx;
  border: 1rpx solid #f0e2e5;
  box-shadow: var(--shadow-card);
  position: relative;
  overflow: hidden;
}
.notice-card.unread::before {
  content: ''; position: absolute; top: 32rpx; right: 24rpx;
  width: 16rpx; height: 16rpx; border-radius: 50%; background: #ff4d4f;
}
.notice-card.pinned::after {
  content: "";
  position: absolute;
  right: -34rpx;
  top: -34rpx;
  width: 88rpx;
  height: 88rpx;
  background: #b70f24;
  transform: rotate(45deg);
}
.notice-icon {
  flex-shrink: 0;
  width: 86rpx;
  height: 86rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #c83045, #a20e20);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  font-weight: 800;
}
.notice-icon.muted {
  background: #d1d5db;
}
.notice-main { flex: 1; min-width: 0; }
.notice-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 18rpx; }
.notice-title {
  font-size: 31rpx;
  line-height: 1.45;
  font-weight: 800;
  color: #202124;
  flex: 1;
}
.notice-source {
  display: inline-block;
  margin-top: 10rpx;
  font-size: 23rpx;
  color: #b70f24;
  background: #fff1f2;
  padding: 4rpx 14rpx;
  border-radius: 10rpx;
}
.pin-corner {
  color: #b70f24;
  background: #fff1f2;
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
  font-size: 22rpx;
  margin-right: 20rpx;
}
.notice-preview {
  display: block;
  font-size: 26rpx;
  line-height: 1.7;
  color: #5f6368;
  margin-top: 14rpx;
}
.notice-footer { display: flex; justify-content: space-between; margin-top: 16rpx; }
.notice-date { font-size: 22rpx; color: #999; }
.read-mark { font-size: 24rpx; color: #b8bdc5; }

.empty { text-align: center; padding: 80rpx 0; color: #999; font-size: 28rpx; }
.load-more {
  width: 300rpx;
  margin: 16rpx auto 0;
  text-align: center;
  padding: 18rpx 0;
  border-radius: 999rpx;
  color: #b70f24;
  background: #fff;
  font-size: 26rpx;
  box-shadow: var(--shadow-soft);
}
</style>
