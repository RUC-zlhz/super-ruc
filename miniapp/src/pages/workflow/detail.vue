<template>
  <view class="container">
    <view v-if="loading" class="loading">加载中...</view>

    <template v-else-if="workflow">
      <view class="head-card">
        <view class="head-row">
          <view class="party-icon">党</view>
          <view class="head-main">
          <text class="title">{{ workflow.template_name }}</text>
          <text class="meta" v-if="workflow.current_node_name">
            当前状态：{{ workflow.current_node_name }}
          </text>
          </view>
          <text class="status" :class="workflow.status.toLowerCase()">
            {{ statusLabel(workflow.status) }}
          </text>
        </view>
      </view>

      <view class="summary-strip">
        <view class="summary-item">
          <text class="summary-label">当前节点</text>
          <text class="summary-value">{{ workflow.current_node_name || '-' }}</text>
        </view>
        <view class="summary-item">
          <text class="summary-label">完成进度</text>
          <text class="summary-value">{{ doneCount }}/{{ nodes.length || 0 }}</text>
        </view>
        <view class="summary-item">
          <text class="summary-label">预计完成时间</text>
          <text class="summary-value">{{ currentNode?.due_date ? formatDate(currentNode.due_date).slice(0, 10) : '-' }}</text>
        </view>
      </view>

      <view class="next-card">
        <text class="section-title">下一步需要完成</text>
        <text class="next-main">
          {{ workflow.next_action_hint || currentNode?.required_task || "当前暂无额外待办说明" }}
        </text>
        <view v-if="currentNode" class="next-grid">
          <view class="next-item">
            <text class="next-label">节点名称</text>
            <text class="next-value">{{ currentNode.node_name }}</text>
          </view>
          <view class="next-item">
            <text class="next-label">状态</text>
            <text class="next-value">{{ nodeStatusLabel(currentNode.status) }}</text>
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
        <view class="next-button">去完成</view>
      </view>

      <view class="section">
        <text class="section-title">流程节点时间轴</text>
        <view v-if="!nodes.length" class="empty-tiny">暂无节点记录</view>
        <view v-else class="timeline">
          <view v-for="(node, index) in nodes" :key="node.id" class="node-row">
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
  padding: 24rpx;
  background: #f8f3f4;
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

.head-card,
.next-card,
.section {
  padding: 24rpx;
  border-radius: 22rpx;
  background: #fff;
  border: 1rpx solid #f0e2e5;
  box-shadow: var(--shadow-card);
}

.head-card {
  background:
    radial-gradient(circle at 86% 24%, rgba(255,255,255,0.16), transparent 130rpx),
    linear-gradient(135deg, #d51f35, #b70f24 58%, #8b1020);
  color: #fff;
  border: none;
}

.head-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16rpx;
}

.party-icon {
  width: 84rpx;
  height: 84rpx;
  border-radius: 24rpx;
  background: rgba(255,255,255,0.18);
  color: #ffe7a3;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 38rpx;
  font-weight: 800;
}

.head-main {
  flex: 1;
  min-width: 0;
}

.title {
  flex: 1;
  font-size: 32rpx;
  font-weight: 800;
  line-height: 1.5;
  color: #fff;
}

.status {
  flex-shrink: 0;
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
}

.status.active,
.status.in_progress {
  background: #fff2cf;
  color: #8a4b00;
}

.status.completed {
  background: #f0fdf4;
  color: #15803d;
}

.status.suspended,
.status.cancelled {
  background: #f8fafc;
  color: #64748b;
}

.meta {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: rgba(255,255,255,0.86);
}

.summary-strip {
  display: flex;
  background: #fff;
  border-radius: 20rpx;
  padding: 24rpx 12rpx;
  box-shadow: var(--shadow-card);
  border: 1rpx solid #f0e2e5;
}

.summary-item {
  flex: 1;
  text-align: center;
  border-right: 1rpx solid #f0e2e5;
}

.summary-item:last-child {
  border-right: none;
}

.summary-label {
  display: block;
  font-size: 22rpx;
  color: #8a8f98;
}

.summary-value {
  display: block;
  margin-top: 8rpx;
  font-size: 26rpx;
  color: #b70f24;
  font-weight: 800;
}

.section-title {
  display: block;
  font-size: 28rpx;
  font-weight: 800;
  color: #1e293b;
}

.next-card {
  border: 2rpx solid #f0c9cf;
  background:
    radial-gradient(circle at 92% 50%, rgba(183,15,36,0.08), transparent 120rpx),
    #fff;
}

.next-main {
  display: block;
  margin-top: 16rpx;
  font-size: 26rpx;
  line-height: 1.7;
  color: #a61e2d;
  font-weight: 800;
}

.next-grid {
  display: grid;
  gap: 14rpx;
  margin-top: 20rpx;
}

.next-item {
  padding: 16rpx;
  border-radius: 18rpx;
  background: #fff8f9;
}

.next-button {
  margin-top: 22rpx;
  height: 76rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #d51f35, #b70f24);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 800;
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
  line-height: 1.6;
  color: #334155;
}

.timeline {
  margin-top: 20rpx;
}

.node-row {
  display: flex;
  align-items: stretch;
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
  margin-top: 6rpx;
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
  padding: 0 0 28rpx 16rpx;
}

.node-head {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
  padding: 16rpx;
  border-radius: 14rpx 14rpx 0 0;
  background: #fff8f9;
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
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #64748b;
  padding-left: 16rpx;
}
</style>
