<template>
  <view class="container">
    <view class="page-head">
      <text class="page-back">‹</text>
      <text class="page-title">通知中心</text>
      <view class="page-actions">
        <view class="page-action">⌕</view>
        <view class="page-action more">•••</view>
      </view>
    </view>

    <view class="search-shell">
      <view class="fake-search">
        <text class="search-icon">⌕</text>
        <text>搜索通知标题或来源</text>
      </view>
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
            <view class="notice-title-wrap">
              <text class="notice-title">{{ n.title }}</text>
              <text class="pin-corner" v-if="n.is_pinned">置顶</text>
            </view>
            <view class="notice-state-flag">
              <view v-if="isUnread(n)" class="state-dot unread" />
              <text v-else class="read-mark">✓</text>
            </view>
          </view>
          <text class="notice-source">{{ noticeTag(n) }}</text>
          <text class="notice-preview" v-if="n.summary">{{ n.summary.slice(0, 80) }}</text>
          <view class="notice-footer">
            <text class="notice-date">◷ {{ n.published_at?.slice(0, 16).replace('T', ' ') }}</text>
            <text class="notice-arrow">›</text>
          </view>
        </view>
      </view>
    </view>

    <view v-else-if="!loading" class="empty">暂无通知</view>

    <view v-if="hasMore" class="load-more" @tap="loadMore">加载更多</view>
    <view v-else-if="!loading && notices.length" class="load-end">没有更多了</view>
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
    radial-gradient(circle at 92% 34rpx, rgba(183, 15, 36, 0.08), transparent 180rpx),
    linear-gradient(180deg, #fff 0, #fff 210rpx, var(--bg-color) 520rpx),
    var(--bg-color);
}

.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  margin-bottom: 20rpx;
}

.page-back {
  width: 60rpx;
  height: 60rpx;
  border-radius: 50%;
  color: #111827;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 44rpx;
  line-height: 1;
}

.page-title {
  flex: 1;
  text-align: center;
  font-size: 40rpx;
  font-weight: 800;
  color: #111827;
  margin-left: -60rpx;
}

.page-actions {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.page-action {
  width: 60rpx;
  height: 60rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.94);
  border: 1rpx solid #efe3e6;
  color: #111827;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  box-shadow: var(--shadow-soft);
}

.page-action.more {
  width: 84rpx;
  border-radius: 999rpx;
  letter-spacing: 4rpx;
}

.search-shell {
  margin-bottom: 18rpx;
}

.fake-search {
  height: 76rpx;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid #f0e2e5;
  color: #9aa0a6;
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 0 22rpx;
  font-size: 24rpx;
  box-shadow: var(--shadow-soft);
}

.search-icon {
  font-size: 34rpx;
}

.tab-row {
  display: flex;
  background: #f5f2f3;
  border-radius: 999rpx;
  padding: 10rpx;
  margin-bottom: 24rpx;
  box-shadow: inset 0 0 0 1rpx rgba(183, 15, 36, 0.04);
}
.tab {
  flex: 1;
  text-align: center;
  padding: 18rpx 0;
  border-radius: 999rpx;
  font-size: 28rpx;
  color: #4b5563;
  font-weight: 600;
}
.tab.active {
  color: #fff;
  background: linear-gradient(135deg, #c8142f, #a20e20);
  font-weight: 800;
  box-shadow: 0 10rpx 22rpx rgba(183, 15, 36, 0.22);
}

.notice-card {
  display: flex;
  gap: 22rpx;
  background: var(--card-elevated);
  padding: 30rpx 28rpx;
  border-radius: 28rpx;
  margin-bottom: 20rpx;
  border: 1rpx solid #f0e2e5;
  box-shadow: var(--shadow-card);
  position: relative;
  overflow: hidden;
}
.notice-card.unread::before {
  content: '';
  position: absolute;
  top: 30rpx;
  right: 28rpx;
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: #ff4d4f;
  box-shadow: 0 0 0 8rpx rgba(255, 77, 79, 0.1);
}
.notice-card.pinned::after {
  content: '';
  position: absolute;
  right: -38rpx;
  top: -38rpx;
  width: 96rpx;
  height: 96rpx;
  background: linear-gradient(135deg, #c8142f, #a20e20);
  transform: rotate(45deg);
}
.notice-icon {
  flex-shrink: 0;
  width: 92rpx;
  height: 92rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #c83045, #a20e20);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  font-weight: 800;
  box-shadow: 0 14rpx 28rpx rgba(200, 48, 69, 0.2);
}
.notice-icon.muted {
  background: linear-gradient(135deg, #d7dbe1, #bcc3cd);
  box-shadow: none;
}
.notice-main { flex: 1; min-width: 0; }
.notice-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18rpx;
}
.notice-title-wrap {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
}
.notice-title {
  font-size: 31rpx;
  line-height: 1.45;
  font-weight: 800;
  color: #202124;
  flex: 1;
}
.notice-source {
  display: inline-block;
  margin-top: 12rpx;
  font-size: 23rpx;
  color: #b70f24;
  background: #fff1f2;
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
}
.pin-corner {
  color: #b70f24;
  background: #fff1f2;
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  flex-shrink: 0;
}
.notice-preview {
  display: block;
  font-size: 26rpx;
  line-height: 1.72;
  color: #5f6368;
  margin-top: 16rpx;
}
.notice-state-flag {
  width: 42rpx;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-shrink: 0;
}
.state-dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: #d4dae2;
}
.state-dot.unread {
  background: #c8142f;
}
.notice-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 18rpx;
}
.notice-date {
  font-size: 22rpx;
  color: #999;
}
.read-mark {
  font-size: 24rpx;
  color: #b8bdc5;
}
.notice-arrow {
  font-size: 30rpx;
  color: #c0a7ae;
}

.empty {
  text-align: center;
  padding: 96rpx 0;
  color: #999;
  font-size: 28rpx;
}
.load-more {
  width: 300rpx;
  margin: 18rpx auto 0;
  text-align: center;
  padding: 20rpx 0;
  border-radius: 999rpx;
  color: #b70f24;
  background: rgba(255, 255, 255, 0.96);
  font-size: 26rpx;
  font-weight: 700;
  box-shadow: var(--shadow-soft);
}

.load-end {
  margin: 20rpx auto 0;
  text-align: center;
  color: #c1a6ac;
  font-size: 24rpx;
}
</style>
