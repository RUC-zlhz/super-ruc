<template>
  <view class="container">
    <text class="page-title">我的党团进度</text>

    <view class="quiz-entry" @tap="goQuiz">
      <text class="quiz-entry-title">理论自测</text>
      <text class="quiz-entry-sub">党史 / 团章 / 思政 — 随机抽题 · 即时判分</text>
      <text class="quiz-entry-arrow">›</text>
    </view>

    <view v-if="workflows.length" class="flow-list">
      <view class="flow-card" v-for="wf in workflows" :key="wf.id" @tap="onDetail(wf.id)">
        <view class="flow-header">
          <text class="flow-name">{{ wf.template_name }}</text>
          <text class="flow-status" :class="wf.status.toLowerCase()">{{ statusLabel(wf.status) }}</text>
        </view>
        <text class="flow-node" v-if="wf.current_node_name">
          当前节点：{{ wf.current_node_name }}
        </text>
        <text class="flow-date">开始：{{ wf.started_at?.slice(0, 10) }}</text>
      </view>
    </view>

    <view v-else class="empty">
      <text>暂无党团流程记录</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getMyWorkflows, type StudentWorkflow } from '@/api/workflow'

const workflows = ref<StudentWorkflow[]>([])

const STATUS_MAP: Record<string, string> = {
  IN_PROGRESS: '进行中',
  COMPLETED: '已完成',
  CANCELLED: '已取消',
}

function statusLabel(s: string) { return STATUS_MAP[s] || s }

function onDetail(id: number) {
  uni.navigateTo({ url: `/pages/workflow/detail?id=${id}` })
}

function goQuiz() {
  uni.navigateTo({ url: '/pages/workflow/quiz' })
}

onMounted(async () => {
  try {
    const resp = await getMyWorkflows()
    workflows.value = resp.data
  } catch { /* ok */ }
})
</script>

<style scoped>
.container { padding: 24rpx; }
.page-title { font-size: 34rpx; font-weight: 600; display: block; margin-bottom: 24rpx; }

.flow-list { margin-top: 8rpx; }
.flow-card {
  background: #fff;
  padding: 24rpx;
  border-radius: 12rpx;
  margin-bottom: 16rpx;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06);
}
.flow-header { display: flex; justify-content: space-between; align-items: center; }
.flow-name { font-size: 30rpx; font-weight: 600; }
.flow-status { font-size: 24rpx; padding: 4rpx 12rpx; border-radius: 4rpx; }
.flow-status.in_progress { background: #e6f7ff; color: #1890ff; }
.flow-status.completed { background: #f6ffed; color: #52c41a; }
.flow-node { font-size: 26rpx; color: #666; display: block; margin-top: 8rpx; }
.flow-date { font-size: 24rpx; color: #999; display: block; margin-top: 4rpx; }

.empty { text-align: center; padding: 80rpx 0; color: #999; font-size: 28rpx; }

.quiz-entry {
  background: linear-gradient(135deg, #7f1722 0%, #b02a37 100%);
  color: #fff;
  padding: 24rpx 28rpx;
  border-radius: 12rpx;
  margin-bottom: 20rpx;
  position: relative;
}
.quiz-entry-title { display: block; font-size: 30rpx; font-weight: 600; }
.quiz-entry-sub { display: block; font-size: 24rpx; opacity: 0.85; margin-top: 6rpx; }
.quiz-entry-arrow {
  position: absolute;
  right: 28rpx;
  top: 50%;
  transform: translateY(-50%);
  font-size: 40rpx;
}
</style>
