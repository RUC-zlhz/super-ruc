<template>
  <view class="container">
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
        :key="n.id"
        class="notice-card"
        :class="{ unread: !n.is_read }"
        @tap="onDetail(n)"
      >
        <view class="notice-head">
          <text class="notice-title">{{ n.title }}</text>
          <text class="notice-source">{{ sourceLabel(n.source_type) }}</text>
        </view>
        <text class="notice-preview" v-if="n.body">{{ n.body.slice(0, 80) }}</text>
        <view class="notice-footer">
          <text class="notice-date">{{ n.published_at?.slice(0, 16).replace('T', ' ') }}</text>
          <text class="notice-flag" v-if="!n.is_read">未读</text>
        </view>
      </view>
    </view>

    <view v-else-if="!loading" class="empty">暂无通知</view>

    <view v-if="hasMore" class="load-more" @tap="loadMore">加载更多</view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getMyNotices, type StudentNoticeItem } from '@/api/notice'

const TABS = [
  { label: '全部', value: 'all' },
  { label: '未读', value: 'unread' },
  { label: '已读', value: 'read' },
]
const tab = ref<'all' | 'unread' | 'read'>('all')

const SOURCE_LABELS: Record<string, string> = {
  MANUAL: '手工发布',
  FEED: '订阅抓取',
  SYSTEM: '系统提醒',
}
function sourceLabel(s: string) { return SOURCE_LABELS[s] || s }

const notices = ref<StudentNoticeItem[]>([])
const page = ref(1)
const size = 20
const total = ref(0)
const loading = ref(false)
const hasMore = computed(() => notices.value.length < total.value)

const visibleNotices = computed(() => {
  if (tab.value === 'unread') return notices.value.filter(n => !n.is_read)
  if (tab.value === 'read') return notices.value.filter(n => n.is_read)
  return notices.value
})

async function reload(reset = true) {
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
  page.value += 1
  reload(false)
}

function onTab(v: 'all' | 'unread' | 'read') {
  tab.value = v
}

function onDetail(n: StudentNoticeItem) {
  n.is_read = true
  uni.navigateTo({ url: `/pages/notice/detail?id=${n.id}` })
}

onMounted(() => reload())
</script>

<style scoped>
.container { padding: 24rpx; }

.tab-row { display: flex; background: #fff; border-radius: 12rpx; margin-bottom: 16rpx; }
.tab {
  flex: 1; text-align: center; padding: 20rpx 0;
  font-size: 26rpx; color: #555;
}
.tab.active { color: #7f1722; border-bottom: 4rpx solid #7f1722; }

.list {}
.notice-card {
  background: #fff; padding: 24rpx; border-radius: 12rpx;
  margin-bottom: 16rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06);
  position: relative;
}
.notice-card.unread::before {
  content: ''; position: absolute; top: 24rpx; right: 24rpx;
  width: 16rpx; height: 16rpx; border-radius: 50%; background: #ff4d4f;
}
.notice-head { display: flex; justify-content: space-between; align-items: flex-start; }
.notice-title { font-size: 30rpx; font-weight: 600; color: #333; flex: 1; }
.notice-source {
  flex-shrink: 0; font-size: 22rpx; color: #7f1722;
  background: #fff1f0; padding: 2rpx 12rpx; border-radius: 4rpx;
  margin-left: 12rpx;
}
.notice-preview { display: block; font-size: 26rpx; color: #666; margin-top: 8rpx; }
.notice-footer { display: flex; justify-content: space-between; margin-top: 12rpx; }
.notice-date { font-size: 22rpx; color: #999; }
.notice-flag { font-size: 22rpx; color: #ff4d4f; }

.empty { text-align: center; padding: 80rpx 0; color: #999; font-size: 28rpx; }
.load-more { text-align: center; padding: 24rpx 0; color: #7f1722; font-size: 26rpx; }
</style>
