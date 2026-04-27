<template>
  <view class="container">
    <view v-if="loading" class="loading">加载中...</view>

    <template v-else-if="workflow">
      <view class="page-hero">
        <view class="hero-head">
          <view class="hero-main">
            <text class="hero-kicker">发展流程详情</text>
            <text class="title">{{ workflow.template_name }}</text>
            <text class="meta" v-if="workflow.current_node_name">
              当前状态：{{ workflow.current_node_name }}
            </text>
          </view>
          <view class="hero-badge">党</view>
        </view>

        <view class="hero-meta-row">
          <text class="hero-meta-pill">{{ statusLabel(workflow.status) }}</text>
          <text class="hero-meta-pill">开始于 {{ formatDate(workflow.started_at).slice(0, 10) }}</text>
        </view>
      </view>

      <view class="summary-strip">
        <view class="summary-item">
          <text class="summary-label">当前节点</text>
          <text class="summary-value">{{ workflow.current_node_name || "-" }}</text>
        </view>
        <view class="summary-item">
          <text class="summary-label">完成进度</text>
          <text class="summary-value">{{ doneCount }}/{{ nodes.length || 0 }}</text>
        </view>
        <view class="summary-item">
          <text class="summary-label">当前进度</text>
          <text class="summary-value">{{ progressPercent }}%</text>
        </view>
      </view>

      <view id="current-task" class="next-card">
        <view class="card-head">
          <view>
            <text class="section-title">下一步需要完成</text>
            <text class="section-subtitle">聚焦当前节点任务、说明和材料提示</text>
          </view>
          <text class="next-status">{{ currentNode ? nodeStatusLabel(currentNode.status) : "待同步" }}</text>
        </view>

        <text class="next-main">
          {{ workflow.next_action_hint || currentNode?.required_task || "当前暂无额外待办说明" }}
        </text>

        <view class="progress-track">
          <view class="progress-fill" :style="{ width: `${progressPercent}%` }" />
        </view>

        <view v-if="currentNode" class="next-grid">
          <view class="next-item">
            <text class="next-label">节点名称</text>
            <text class="next-value">{{ currentNode.node_name }}</text>
          </view>
          <view class="next-item">
            <text class="next-label">节点编码</text>
            <text class="next-value">{{ currentNode.node_code }}</text>
          </view>
          <view class="next-item" v-if="currentNode.due_date">
            <text class="next-label">建议截止时间</text>
            <text class="next-value">{{ formatDate(currentNode.due_date) }}</text>
          </view>
          <view class="next-item" v-if="currentNode.required_task">
            <text class="next-label">所需事项</text>
            <text class="next-value">{{ currentNode.required_task }}</text>
          </view>
          <view class="next-item" v-if="currentNode.note">
            <text class="next-label">说明</text>
            <text class="next-value">{{ currentNode.note }}</text>
          </view>
          <view class="next-item" v-if="currentNode.evidence">
            <text class="next-label">材料提示</text>
            <text class="next-value">{{ currentNode.evidence }}</text>
          </view>
        </view>
      </view>

      <view class="section">
        <view class="card-head">
          <view>
            <text class="section-title">流程节点时间轴</text>
            <text class="section-subtitle">按节点顺序查看当前流程推进状态</text>
          </view>
        </view>
        <view v-if="!nodes.length" class="empty-tiny">暂无节点记录</view>
        <view v-else class="timeline">
          <view
            v-for="(node, index) in nodes"
            :key="node.id"
            class="node-row"
            :class="{ current: currentNode?.id === node.id }"
          >
            <view class="node-rail">
              <view class="node-dot" :class="nodeDotClass(node.status)" />
              <view v-if="index < nodes.length - 1" class="node-line" />
            </view>

            <view class="node-body">
              <view class="node-head">
                <text class="node-name">{{ node.node_name }}</text>
                <text class="node-status" :class="node.status.toLowerCase()">
                  {{ nodeStatusLabel(node.status) }}
                </text>
              </view>
              <text class="node-code">节点编码：{{ node.node_code }}</text>
              <text v-if="node.required_task" class="node-text">
                所需事项：{{ node.required_task }}
              </text>
              <text v-if="node.due_date" class="node-text">
                建议截止时间：{{ formatDate(node.due_date) }}
              </text>
              <text v-if="node.note" class="node-text">说明：{{ node.note }}</text>
              <text v-if="node.evidence" class="node-text">材料提示：{{ node.evidence }}</text>
              <text v-if="node.completed_at" class="node-time">
                完成时间：{{ formatDate(node.completed_at) }}
              </text>
            </view>
          </view>
        </view>
      </view>

      <view class="bottom-actions safe-area-inset-bottom">
        <view class="bottom-copy">
          <text class="bottom-title">{{ currentNode?.node_name || "当前待办" }}</text>
          <text class="bottom-desc">
            {{ workflow.next_action_hint || "查看当前节点详情并及时准备材料。" }}
          </text>
        </view>
        <view class="bottom-button" @tap="scrollToCurrentTask">查看待办</view>
      </view>
      <view class="bottom-spacer" />
    </template>

    <view v-else class="empty">未找到流程记录</view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { onPullDownRefresh } from "@dcloudio/uni-app";
import {
  getWorkflowDetail,
  type StudentWorkflow,
  type StudentWorkflowNode,
} from "@/api/workflow";

const workflow = ref<StudentWorkflow | null>(null);
const nodes = ref<StudentWorkflowNode[]>([]);
const loading = ref(false);
const workflowId = ref<number | null>(null);

const STATUS_LABELS: Record<string, string> = {
  ACTIVE: "进行中",
  COMPLETED: "已完成",
  SUSPENDED: "已暂停",
  IN_PROGRESS: "进行中",
  CANCELLED: "已取消",
};

const NODE_STATUS_LABELS: Record<string, string> = {
  PENDING: "待开始",
  DONE: "已完成",
  OVERDUE: "已逾期",
  DEFERRED: "已延期",
  MANUAL_FOLLOW_UP: "人工跟进",
};

const currentNode = computed(() => {
  return (
    nodes.value.find((node) => node.status !== "DONE") ||
    nodes.value[nodes.value.length - 1] ||
    null
  );
});

const doneCount = computed(() => nodes.value.filter((node) => node.status === "DONE").length);

const progressPercent = computed(() => {
  if (!nodes.value.length) return 0;
  return Math.round((doneCount.value / nodes.value.length) * 100);
});

function statusLabel(status: string) {
  return STATUS_LABELS[status] || status;
}

function nodeStatusLabel(status: string) {
  return NODE_STATUS_LABELS[status] || status;
}

function nodeDotClass(status: string) {
  if (status === "DONE") return "completed";
  if (status === "OVERDUE") return "overdue";
  if (status === "DEFERRED" || status === "MANUAL_FOLLOW_UP") return "manual";
  return "pending";
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  const normalized = value.replace("T", " ").replace("Z", "");
  return normalized.length >= 16 ? normalized.slice(0, 16) : normalized;
}

function scrollToCurrentTask() {
  uni.pageScrollTo({
    selector: "#current-task",
    duration: 260,
  });
}

async function loadDetail() {
  if (workflowId.value == null) return;
  loading.value = true;
  try {
    const response = await getWorkflowDetail(workflowId.value);
    workflow.value = response.data;
    nodes.value = response.data.nodes || [];
  } catch {
    workflow.value = null;
    nodes.value = [];
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  const pages = getCurrentPages();
  const current = pages[pages.length - 1] as any;
  const options = current?.options || {};
  const parsedId = Number(options.id);
  workflowId.value = Number.isFinite(parsedId) && parsedId > 0 ? parsedId : null;
  void loadDetail();
});

onPullDownRefresh(async () => {
  await loadDetail();
  uni.stopPullDownRefresh();
});
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 0 24rpx 24rpx;
  background:
    linear-gradient(180deg, #b70f24 0, #b70f24 280rpx, #f8f3f4 520rpx),
    #f8f3f4;
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.loading,
.empty {
  text-align: center;
  padding: 80rpx 0;
  color: #64748b;
  font-size: 28rpx;
}

.empty-tiny {
  text-align: center;
  padding: 16rpx 0;
  color: #94a3b8;
  font-size: 24rpx;
}

.page-hero {
  margin: 0 -24rpx;
  padding: 50rpx 38rpx 42rpx;
  background:
    radial-gradient(circle at 86% 26%, rgba(255, 255, 255, 0.18), transparent 150rpx),
    linear-gradient(135deg, #d51f35, #b70f24 58%, #8b1020);
  color: #fff;
}

.hero-head {
  display: flex;
  justify-content: space-between;
  gap: 18rpx;
}

.hero-main {
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

.title {
  display: block;
  margin-top: 18rpx;
  font-size: 36rpx;
  font-weight: 800;
  line-height: 1.4;
  color: #fff;
}

.meta {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.86);
}

.hero-badge {
  width: 92rpx;
  height: 92rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.14);
  border: 2rpx solid rgba(255, 255, 255, 0.18);
  color: #ffe7a3;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 38rpx;
  font-weight: 800;
}

.hero-meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 24rpx;
}

.hero-meta-pill {
  display: inline-flex;
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.12);
  color: #fff8eb;
  font-size: 22rpx;
}

.summary-strip {
  margin-top: -24rpx;
  display: flex;
  gap: 14rpx;
  padding: 20rpx 18rpx;
  background: rgba(255, 255, 255, 0.97);
  border-radius: 26rpx;
  box-shadow: 0 18rpx 40rpx rgba(92, 16, 28, 0.14);
  border: 1rpx solid #f0e2e5;
}

.summary-item {
  flex: 1;
  min-width: 0;
  padding: 8rpx 12rpx;
  border-right: 1rpx solid #f0e2e5;
}

.summary-item:last-child {
  border-right: none;
}

.summary-label {
  display: block;
  font-size: 20rpx;
  color: #94a3b8;
}

.summary-value {
  display: block;
  margin-top: 8rpx;
  font-size: 26rpx;
  line-height: 1.5;
  color: #b70f24;
  font-weight: 800;
}

.next-card,
.section {
  padding: 26rpx 24rpx;
  border-radius: 28rpx;
  background: #fff;
  border: 1rpx solid #f0e2e5;
  box-shadow: var(--shadow-card);
}

.next-card {
  background:
    radial-gradient(circle at 94% 18%, rgba(183, 15, 36, 0.08), transparent 120rpx),
    linear-gradient(180deg, #fffaf9, #fff);
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16rpx;
}

.section-title {
  display: block;
  font-size: 29rpx;
  font-weight: 800;
  color: #1e293b;
}

.section-subtitle {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #94a3b8;
}

.next-status {
  flex-shrink: 0;
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  background: #fff1f2;
  color: #b70f24;
  font-size: 22rpx;
  font-weight: 700;
}

.next-main {
  display: block;
  margin-top: 18rpx;
  font-size: 26rpx;
  line-height: 1.75;
  color: #a61e2d;
  font-weight: 800;
}

.progress-track {
  margin-top: 20rpx;
  height: 12rpx;
  border-radius: 999rpx;
  background: #f4dde1;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #fb7185, #b70f24);
}

.next-grid {
  display: grid;
  gap: 14rpx;
  margin-top: 22rpx;
}

.next-item {
  padding: 18rpx;
  border-radius: 20rpx;
  background: #fff8f9;
  border: 1rpx solid #f5e2e5;
}

.next-label {
  display: block;
  font-size: 20rpx;
  color: #94a3b8;
}

.next-value {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  line-height: 1.65;
  color: #334155;
}

.timeline {
  margin-top: 22rpx;
}

.node-row {
  display: flex;
  align-items: stretch;
}

.node-row.current .node-body {
  border-color: #f0c9cf;
  box-shadow: 0 12rpx 30rpx rgba(183, 15, 36, 0.08);
}

.node-rail {
  width: 40rpx;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.node-dot {
  width: 30rpx;
  height: 30rpx;
  border-radius: 50%;
  margin-top: 8rpx;
  flex-shrink: 0;
  border: 2rpx solid #d9d9d9;
  background: #fff;
}

.node-dot.completed {
  background: #22c55e;
  border-color: #22c55e;
}

.node-dot.overdue {
  background: #ef4444;
  border-color: #ef4444;
}

.node-dot.manual {
  background: #f59e0b;
  border-color: #f59e0b;
}

.node-dot.pending {
  background: #fff;
  border-color: #d9d9d9;
}

.node-line {
  width: 2rpx;
  flex: 1;
  background: #f0c9cf;
  margin-top: 6rpx;
  min-height: 44rpx;
}

.node-body {
  flex: 1;
  margin-left: 16rpx;
  margin-bottom: 26rpx;
  padding: 18rpx;
  border-radius: 22rpx;
  background: #fff;
  border: 1rpx solid #f1e6e8;
}

.node-head {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
}

.node-name {
  flex: 1;
  font-size: 28rpx;
  font-weight: 800;
  color: #1e293b;
}

.node-status {
  flex-shrink: 0;
  align-self: flex-start;
  padding: 4rpx 12rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
}

.node-status.done {
  background: #f0fdf4;
  color: #15803d;
}

.node-status.overdue {
  background: #fff1f2;
  color: #be123c;
}

.node-status.deferred,
.node-status.manual_follow_up {
  background: #fff7ed;
  color: #c2410c;
}

.node-status.pending {
  background: #f8fafc;
  color: #64748b;
}

.node-code,
.node-text,
.node-time {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.65;
  color: #64748b;
}

.bottom-actions {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding: 18rpx 24rpx calc(18rpx + env(safe-area-inset-bottom));
  background: rgba(255, 255, 255, 0.97);
  border-top: 1rpx solid #f0e2e5;
  box-shadow: 0 -10rpx 28rpx rgba(82, 28, 38, 0.1);
  backdrop-filter: blur(12rpx);
}

.bottom-copy {
  flex: 1;
  min-width: 0;
}

.bottom-title {
  display: block;
  font-size: 26rpx;
  font-weight: 800;
  color: #1e293b;
}

.bottom-desc {
  display: block;
  margin-top: 6rpx;
  font-size: 22rpx;
  line-height: 1.5;
  color: #8a8f98;
}

.bottom-button {
  flex-shrink: 0;
  min-width: 188rpx;
  height: 78rpx;
  padding: 0 28rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #d51f35, #b70f24);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  font-weight: 800;
}

.bottom-spacer {
  height: 136rpx;
}
</style>
