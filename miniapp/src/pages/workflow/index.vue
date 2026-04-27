<template>
  <view class="container">
    <view class="page-hero">
      <text class="hello">您好，同学</text>
      <text class="slogan">不忘初心，砥砺前行</text>
    </view>

    <view class="hero-card" @tap="goQuiz">
      <view class="quiz-icon">团</view>
      <view class="hero-copy">
        <text class="hero-title">理论自测</text>
        <text class="hero-desc">
          党史、团章、思政题库随机抽题，即时判分并用于日常自查。
        </text>
      </view>
      <text class="hero-arrow">›</text>
    </view>

    <template v-if="workflows.length">
      <view
        v-for="workflow in workflows"
        :key="workflow.id"
        class="flow-card"
        @tap="onDetail(workflow.id)"
      >
        <view class="flow-header">
          <view class="flow-main">
            <text class="flow-name">{{ workflow.template_name }}</text>
            <text class="flow-date">开始时间：{{ formatDate(workflow.started_at) }}</text>
          </view>
          <text class="flow-status" :class="workflow.status.toLowerCase()">
            {{ statusLabel(workflow.status) }}
          </text>
        </view>

        <view class="node-preview" v-if="workflow.nodes?.length">
          <view
            v-for="node in previewNodes(workflow)"
            :key="node.id"
            class="preview-node"
            :class="node.status.toLowerCase()"
          >
            <view class="preview-dot">{{ node.status === 'DONE' ? '✓' : '' }}</view>
            <text class="preview-name">{{ node.node_name }}</text>
          </view>
        </view>

        <view class="flow-section">
          <text class="flow-section-label">当前节点</text>
          <text class="flow-section-value">
            {{ workflow.current_node_name || "等待进入下一节点" }}
          </text>
        </view>

        <view class="flow-section" v-if="workflow.next_action_hint">
          <text class="flow-section-label">下一步需要完成</text>
          <text class="flow-section-value emphasis">{{ workflow.next_action_hint }}</text>
        </view>

        <view class="flow-footer">
          <text class="flow-link">查看完整时间轴与节点要求</text>
        </view>
      </view>
    </template>

    <view v-else class="empty-panel">
      <text class="empty-title">当前暂无党团流程记录</text>
      <text class="empty-desc">如已报名相关流程，可稍后下拉刷新或联系负责老师确认。</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { onPullDownRefresh, onShow } from "@dcloudio/uni-app";
import { getMyWorkflows, type StudentWorkflow } from "@/api/workflow";
import { openMiniappPage } from "@/utils/navigation";

const workflows = ref<StudentWorkflow[]>([]);

const STATUS_MAP: Record<string, string> = {
  ACTIVE: "进行中",
  COMPLETED: "已完成",
  SUSPENDED: "已暂停",
  IN_PROGRESS: "进行中",
  CANCELLED: "已取消",
};

function statusLabel(status: string) {
  return STATUS_MAP[status] || status;
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  const normalized = value.replace("T", " ").replace("Z", "");
  return normalized.length >= 16 ? normalized.slice(0, 16) : normalized;
}

function previewNodes(workflow: StudentWorkflow) {
  return [...(workflow.nodes || [])]
    .sort((a, b) => a.sort_order - b.sort_order)
    .slice(0, 4)
}

async function onDetail(id: number) {
  try {
    await openMiniappPage(`/pages/workflow/detail?id=${id}`);
  } catch {
    uni.showToast({ title: "页面跳转失败", icon: "none" });
  }
}

async function goQuiz() {
  try {
    await openMiniappPage("/pages/workflow/quiz");
  } catch {
    uni.showToast({ title: "页面跳转失败", icon: "none" });
  }
}

async function reload() {
  try {
    const response = await getMyWorkflows();
    workflows.value = response.data;
  } catch {
    workflows.value = [];
  }
}

onShow(() => {
  void reload();
});

onPullDownRefresh(async () => {
  await reload();
  uni.stopPullDownRefresh();
});
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 0 24rpx 28rpx;
  background:
    linear-gradient(180deg, #b70f24 0, #b70f24 310rpx, #f8f3f4 560rpx),
    #f8f3f4;
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.page-hero {
  margin: 0 -24rpx;
  padding: 48rpx 44rpx 78rpx;
  color: #fff;
  background:
    radial-gradient(circle at 88% 36%, rgba(255,255,255,0.18), transparent 130rpx),
    linear-gradient(135deg, #b70f24, #8b1020);
}

.hello {
  display: block;
  font-size: 38rpx;
  font-weight: 800;
}

.slogan {
  display: block;
  margin-top: 16rpx;
  font-size: 26rpx;
  opacity: 0.9;
}

.hero-card {
  margin-top: -52rpx;
  padding: 26rpx 24rpx;
  border-radius: 24rpx;
  background: rgba(255,255,255,0.94);
  color: #202124;
  border: 1rpx solid #f0d5da;
  box-shadow: 0 16rpx 38rpx rgba(127,23,34,0.16);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20rpx;
}

.quiz-icon {
  width: 100rpx;
  height: 100rpx;
  border-radius: 24rpx;
  background: #fff1f2;
  color: #b70f24;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 42rpx;
  font-weight: 800;
}

.hero-copy {
  flex: 1;
}

.hero-title {
  display: block;
  font-size: 34rpx;
  font-weight: 800;
}

.hero-desc {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: #8a6b72;
}

.hero-arrow {
  flex-shrink: 0;
  font-size: 36rpx;
  color: #b70f24;
}

.flow-card {
  padding: 24rpx;
  border-radius: 22rpx;
  background: #fff;
  border: 1rpx solid #f0e2e5;
  box-shadow: var(--shadow-card);
}

.flow-header {
  display: flex;
  justify-content: space-between;
  gap: 18rpx;
}

.flow-main {
  flex: 1;
}

.flow-name {
  display: block;
  font-size: 30rpx;
  font-weight: 800;
  color: #1e293b;
}

.flow-date {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #64748b;
}

.flow-status {
  flex-shrink: 0;
  align-self: flex-start;
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
}

.node-preview {
  display: flex;
  align-items: flex-start;
  margin-top: 28rpx;
  padding: 0 8rpx;
}

.preview-node {
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10rpx;
}

.preview-node::after {
  content: "";
  position: absolute;
  left: 50%;
  right: -50%;
  top: 20rpx;
  height: 4rpx;
  background: #e5e7eb;
  z-index: 0;
}

.preview-node:last-child::after { display: none; }

.preview-dot {
  position: relative;
  z-index: 1;
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  background: #e5e7eb;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
  font-weight: 800;
}

.preview-node.done .preview-dot,
.preview-node.completed .preview-dot {
  background: #22c55e;
}

.preview-node.pending .preview-dot {
  background: #d1d5db;
}

.preview-node:not(.done):not(.completed):not(.pending) .preview-dot {
  background: #b70f24;
}

.preview-name {
  width: 120rpx;
  text-align: center;
  font-size: 21rpx;
  color: #64748b;
  line-height: 1.35;
}

.flow-status.active,
.flow-status.in_progress {
  background: #eff6ff;
  color: #1d4ed8;
}

.flow-status.completed {
  background: #f0fdf4;
  color: #15803d;
}

.flow-status.suspended,
.flow-status.cancelled {
  background: #f8fafc;
  color: #64748b;
}

.flow-section {
  margin-top: 18rpx;
  padding: 18rpx 16rpx;
  border-radius: 18rpx;
  background: #f8fafc;
}

.flow-section-label {
  display: block;
  font-size: 20rpx;
  color: #94a3b8;
}

.flow-section-value {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  line-height: 1.6;
  color: #334155;
}

.flow-section-value.emphasis {
  color: #a61e2d;
  font-weight: 600;
}

.flow-footer {
  margin-top: 18rpx;
}

.flow-link {
  font-size: 22rpx;
  color: #a61e2d;
}

.empty-panel {
  padding: 40rpx 32rpx;
  border-radius: 24rpx;
  background: #fff;
  border: 1rpx solid #e8edf3;
  text-align: center;
}

.empty-title {
  display: block;
  font-size: 28rpx;
  font-weight: 600;
  color: #1e293b;
}

.empty-desc {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #64748b;
}
</style>
