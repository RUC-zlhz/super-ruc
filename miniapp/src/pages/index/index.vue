<template>
  <view class="container">
    <view class="header">
      <text class="welcome">你好，{{ displayName }}</text>
      <text class="subtitle">信息学院学生综合服务平台</text>
    </view>

    <view class="grid">
      <view class="grid-item" v-for="item in entries" :key="item.path" @tap="goTo(item.path)">
        <text class="grid-icon">{{ item.icon }}</text>
        <text class="grid-label">{{ item.label }}</text>
      </view>
    </view>

    <view class="section" v-if="recentNotices.length">
      <text class="section-title">最新通知</text>
      <view
        class="notice-row"
        v-for="n in recentNotices" :key="n.id"
        @tap="goTo(`/pages/notice/index?id=${n.id}`)"
      >
        <text class="notice-title">{{ n.title }}</text>
        <text class="notice-date">{{ n.published_at?.slice(0, 10) }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/store/auth'
import { getMyNotices, type StudentNoticeItem } from '@/api/notice'

const auth = useAuthStore()
const displayName = computed(() => auth.user?.display_name || '同学')

const entries = [
  { icon: '📚', label: '知识查询', path: '/pages/knowledge/index' },
  { icon: '🏛️', label: '党团进度', path: '/pages/workflow/index' },
  { icon: '📝', label: '事务申请', path: '/pages/request/index' },
  { icon: '📢', label: '通知中心', path: '/pages/notice/index' },
  { icon: '📊', label: '学业查看', path: '/pages/academic/index' },
  { icon: '🏆', label: '荣誉榜', path: '/pages/honor/index' },
]

const recentNotices = ref<StudentNoticeItem[]>([])

function goTo(path: string) {
  uni.navigateTo({ url: path })
}

onMounted(async () => {
  try {
    if (!auth.user) await auth.fetchMe()
  } catch { /* not logged in yet */ }

  try {
    const resp = await getMyNotices({ page: 1, size: 5 })
    recentNotices.value = resp.data.items
  } catch { /* ok */ }
})
</script>

<style scoped>
.container { padding: 24rpx; }
.header { padding: 32rpx 0; }
.welcome { font-size: 40rpx; font-weight: 600; color: #7f1722; display: block; }
.subtitle { font-size: 26rpx; color: #999; display: block; margin-top: 8rpx; }

.grid { display: flex; flex-wrap: wrap; margin-top: 24rpx; }
.grid-item {
  width: 33.33%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24rpx 0;
}
.grid-icon { font-size: 48rpx; }
.grid-label { font-size: 26rpx; color: #333; margin-top: 8rpx; }

.section { margin-top: 32rpx; }
.section-title { font-size: 30rpx; font-weight: 600; display: block; margin-bottom: 16rpx; }
.notice-row {
  display: flex;
  justify-content: space-between;
  padding: 16rpx 0;
  border-bottom: 1rpx solid #eee;
}
.notice-title { font-size: 28rpx; color: #333; flex: 1; }
.notice-date { font-size: 24rpx; color: #999; margin-left: 16rpx; }
</style>
