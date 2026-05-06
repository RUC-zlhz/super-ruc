<template>
  <view class="container">
    <view class="page-hero">
      <view class="hero-top">
        <view class="hero-copy">
          <text class="hero-kicker">党团发展</text>
          <text class="hello">您好，同学</text>
          <text class="slogan">围绕培养流程逐步推进，及时掌握当前节点与理论自测安排。</text>
        </view>
        <view class="hero-badge">RUC</view>
      </view>

      <view class="hero-strip">
        <view class="hero-strip-item">
          <text class="hero-strip-value">{{ workflows.length }}</text>
          <text class="hero-strip-label">全部流程</text>
        </view>
        <view class="hero-strip-item">
          <text class="hero-strip-value">{{ activeWorkflowCount }}</text>
          <text class="hero-strip-label">进行中</text>
        </view>
        <view class="hero-strip-item">
          <text class="hero-strip-value">{{ completedWorkflowCount }}</text>
          <text class="hero-strip-label">已完成</text>
        </view>
      </view>
    </view>

    <view class="hero-card" hover-class="hover-scale" @tap="goQuiz">
      <view class="quiz-icon">团</view>
      <view class="hero-card-main">
        <text class="hero-card-tag">学习自查</text>
        <text class="hero-title">理论自测</text>
        <text class="hero-desc">
          党史、团章、思政题库随机抽题，即时判分并用于日常自查。
        </text>
      </view>
      <view class="hero-side">
        <text class="hero-side-label">立即进入</text>
        <text class="hero-arrow">›</text>
      </view>
    </view>

    <view class="section-header">
      <view>
        <text class="section-title">我的党团流程</text>
        <text class="section-desc">按当前节点与下一步要求梳理你的发展进度。</text>
      </view>
      <view class="section-badge">{{ attentionWorkflowCount }} 项待关注</view>
    </view>

    <InlineStateNotice
      v-if="pageError"
      :tone="workflows.length ? 'warning' : 'error'"
      :title="workflows.length ? '流程列表未完全更新' : '流程列表加载失败'"
      :description="workflows.length ? `${pageError}，当前保留上次加载结果。` : `${pageError}，可点击重试重新同步。`"
      action-text="重试"
      @action="reload"
    />

    <view v-if="loading && !workflows.length" class="empty-panel">
      <view class="empty-badge">同步中</view>
      <text class="empty-title">流程列表加载中</text>
      <text class="empty-desc">正在同步你的党团发展进度，请稍候。</text>
    </view>

    <template v-else-if="workflows.length">
      <view
        v-for="workflow in workflows"
        :key="workflow.id"
        class="flow-card"
        hover-class="hover-opacity"
        @tap="onDetail(workflow.id)"
      >
        <view class="flow-header">
          <view class="flow-main">
            <view class="flow-badges">
              <text class="flow-badge primary">{{ statusLabel(workflow.status) }}</text>
              <text class="flow-badge">{{ workflow.nodes?.length || 0 }} 个节点</text>
            </view>
            <text class="flow-name">{{ workflow.template_name }}</text>
            <text class="flow-date">开始时间：{{ formatDate(workflow.started_at) }}</text>
          </view>
          <text class="flow-status" :class="workflow.status.toLowerCase()">
            {{ doneNodeCount(workflow) }}/{{ workflow.nodes?.length || 0 }}
          </text>
        </view>

        <view class="flow-summary-strip">
          <view class="summary-chip">
            <text class="summary-chip-label">当前节点</text>
            <text class="summary-chip-value">{{ workflow.current_node_name || "待进入" }}</text>
          </view>
          <view class="summary-chip">
            <text class="summary-chip-label">完成进度</text>
            <text class="summary-chip-value">{{ progressLabel(workflow) }}</text>
          </view>
        </view>

        <view class="node-preview" v-if="workflow.nodes?.length">
          <view
            v-for="node in previewNodes(workflow)"
            :key="node.id"
            class="preview-node"
            :class="node.status.toLowerCase()"
          >
            <view class="preview-dot">{{ node.status === "DONE" ? "✓" : "" }}</view>
            <text class="preview-name">{{ node.node_name }}</text>
          </view>
        </view>

        <view class="flow-insight">
          <text class="flow-section-label">下一步需要完成</text>
          <text class="flow-section-value emphasis">
            {{ workflow.next_action_hint || "当前暂无额外待办说明，可查看完整时间轴确认后续节点。" }}
          </text>
        </view>

        <view class="flow-footer">
          <text class="flow-link">查看完整时间轴与节点要求</text>
          <text class="flow-arrow">›</text>
        </view>
      </view>
    </template>

    <view v-else-if="!pageError" class="empty-panel">
      <view class="empty-badge">暂无进度</view>
      <text class="empty-title">当前暂无党团流程记录</text>
      <text class="empty-desc">如已报名相关流程，可稍后下拉刷新或联系负责老师确认。</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onPullDownRefresh, onShow } from "@dcloudio/uni-app";
import InlineStateNotice from "@/components/InlineStateNotice.vue";
import { getMyWorkflows, type StudentWorkflow } from "@/api/workflow";
import { getErrorMessage } from "@/utils/error";
import { openMiniappPage } from "@/utils/navigation";

const workflows = ref<StudentWorkflow[]>([]);
const loading = ref(false);
const pageError = ref("");
const hasLoaded = ref(false);

const STATUS_MAP: Record<string, string> = {
  ACTIVE: "进行中",
  COMPLETED: "已完成",
  SUSPENDED: "已暂停",
  IN_PROGRESS: "进行中",
  CANCELLED: "已取消",
};

const activeWorkflowCount = computed(() =>
  workflows.value.filter((workflow) => ["ACTIVE", "IN_PROGRESS"].includes(workflow.status)).length,
);

const completedWorkflowCount = computed(() =>
  workflows.value.filter((workflow) => workflow.status === "COMPLETED").length,
);

const attentionWorkflowCount = computed(() =>
  workflows.value.filter((workflow) => !!workflow.current_node_name || !!workflow.next_action_hint).length,
);

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
    .slice(0, 4);
}

function doneNodeCount(workflow: StudentWorkflow) {
  return (workflow.nodes || []).filter((node) => node.status === "DONE").length;
}

function progressLabel(workflow: StudentWorkflow) {
  const total = workflow.nodes?.length || 0;
  if (!total) return "暂无节点";
  return `${doneNodeCount(workflow)}/${total}`;
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
  loading.value = true;
  try {
    pageError.value = "";
    const response = await getMyWorkflows();
    workflows.value = response.data;
    hasLoaded.value = true;
  } catch (error) {
    pageError.value = getErrorMessage(error, "流程列表加载失败");
    if (!hasLoaded.value) {
      workflows.value = [];
    }
  } finally {
    loading.value = false;
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
  padding: 0 24rpx 32rpx;
  background:
    linear-gradient(180deg, #b70f24 0, #b70f24 318rpx, #fff4f5 508rpx, #f8f3f4 100%),
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
  letter-spacing: 2rpx;
}

.hello {
  display: block;
  margin-top: 18rpx;
  font-size: 42rpx;
  font-weight: 800;
  line-height: 1.2;
}

.slogan {
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
  font-size: 24rpx;
  font-weight: 800;
  letter-spacing: 2rpx;
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

.hero-card {
  margin-top: -34rpx;
  padding: 26rpx 24rpx;
  border-radius: 28rpx;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(255, 246, 246, 0.98));
  color: #202124;
  border: 1rpx solid #f0d5da;
  box-shadow: 0 20rpx 46rpx rgba(100, 18, 30, 0.16);
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.quiz-icon {
  width: 104rpx;
  height: 104rpx;
  border-radius: 28rpx;
  background: linear-gradient(135deg, #fff1d6, #ffe8a3);
  color: #b70f24;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 44rpx;
  font-weight: 800;
  box-shadow: inset 0 0 0 1rpx rgba(183, 15, 36, 0.08);
}

.hero-card-main {
  flex: 1;
  min-width: 0;
}

.hero-card-tag {
  display: inline-flex;
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: #fff2f3;
  color: #a61e2d;
  font-size: 20rpx;
  font-weight: 700;
}

.hero-title {
  display: block;
  margin-top: 14rpx;
  font-size: 34rpx;
  font-weight: 800;
}

.hero-desc {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.75;
  color: #7a6067;
}

.hero-side {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8rpx;
}

.hero-side-label {
  font-size: 22rpx;
  color: #b70f24;
  font-weight: 700;
}

.hero-arrow {
  font-size: 36rpx;
  color: #b70f24;
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

.flow-card {
  padding: 26rpx 24rpx;
  border-radius: 22rpx;
  background:
    linear-gradient(180deg, rgba(255, 251, 251, 0.98), rgba(255, 255, 255, 0.98));
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
  min-width: 0;
}

.flow-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}

.flow-badge {
  display: inline-flex;
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  background: #f8f1f2;
  color: #8a6b72;
  font-size: 20rpx;
}

.flow-badge.primary {
  background: #fff1f2;
  color: #b70f24;
  font-weight: 700;
}

.flow-name {
  display: block;
  margin-top: 14rpx;
  font-size: 31rpx;
  font-weight: 800;
  color: #1e293b;
  line-height: 1.45;
}

.flow-date {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  color: #64748b;
}

.flow-status {
  flex-shrink: 0;
  min-width: 104rpx;
  align-self: flex-start;
  padding: 18rpx 16rpx;
  border-radius: 22rpx;
  font-size: 24rpx;
  font-weight: 800;
  text-align: center;
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

.flow-summary-strip {
  display: flex;
  gap: 14rpx;
  margin-top: 22rpx;
}

.summary-chip {
  flex: 1;
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
  line-height: 1.5;
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
  background: #ead7da;
  z-index: 0;
}

.preview-node:last-child::after {
  display: none;
}

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

.flow-insight {
  margin-top: 22rpx;
  padding: 22rpx 20rpx;
  border-radius: 22rpx;
  background:
    linear-gradient(135deg, #fff8f9, #fff);
  border: 1rpx solid #f4dde1;
}

.flow-section-label {
  display: block;
  font-size: 20rpx;
  color: #94a3b8;
}

.flow-section-value {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: #334155;
}

.flow-section-value.emphasis {
  color: #a61e2d;
  font-weight: 700;
}

.flow-footer {
  margin-top: 18rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.flow-link {
  font-size: 22rpx;
  color: #a61e2d;
}

.flow-arrow {
  font-size: 30rpx;
  color: #a61e2d;
}

.empty-panel {
  padding: 42rpx 32rpx;
  border-radius: 28rpx;
  background: #fff;
  border: 1rpx solid #e8edf3;
  box-shadow: var(--shadow-card);
  text-align: center;
}

.empty-badge {
  display: inline-flex;
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  background: #fff1f2;
  color: #b70f24;
  font-size: 20rpx;
  font-weight: 700;
}

.empty-title {
  display: block;
  margin-top: 18rpx;
  font-size: 28rpx;
  font-weight: 700;
  color: #1e293b;
}

.empty-desc {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: #64748b;
}
</style>
