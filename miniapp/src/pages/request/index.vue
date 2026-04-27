<template>
  <view class="container">
    <view class="hero-card">
      <view class="hero-copy">
        <text class="hero-icon">📋</text>
        <view>
          <text class="hero-title">线上提交申请，实时查看办理进度</text>
          <text class="hero-desc">
            高效便捷 · 透明可追踪 · 校园服务更贴心
          </text>
        </view>
      </view>
    </view>

    <view class="launch-btn" @tap="goCreate">
      <text class="launch-plus">＋</text>
      <text>发起申请</text>
    </view>

    <view class="metric-row">
      <view class="metric-card">
        <text class="metric-icon">▤</text>
        <text class="metric-value">{{ requests.length }}</text>
        <text class="metric-label">当前列表</text>
      </view>
      <view class="metric-card">
        <text class="metric-icon muted">⌛</text>
        <text class="metric-value emphasis">{{ pendingCount }}</text>
        <text class="metric-label">待处理</text>
      </view>
      <view class="metric-card">
        <text class="metric-icon warn">!</text>
        <text class="metric-value warning">{{ attentionCount }}</text>
        <text class="metric-label">需关注</text>
      </view>
    </view>

    <scroll-view scroll-x class="tab-row" show-scrollbar="false">
      <view
        v-for="t in STATUS_TABS"
        :key="t.value"
        class="tab-chip"
        :class="{ active: tab === t.value }"
        @tap="onTab(t.value)"
      >
        {{ t.label }}
      </view>
    </scroll-view>

    <view class="create-entry" @tap="goCreate">
      <view class="create-copy">
        <text class="create-title">材料不完整？可先保存草稿</text>
        <text class="create-desc">被驳回或需补充的申请，会在列表中以红色提醒突出展示。</text>
      </view>
      <text class="create-arrow">›</text>
    </view>

    <view v-if="requests.length" class="list">
      <view
        v-for="request in requests"
        :key="request.id"
        class="req-card"
        @tap="goDetail(request.id)"
      >
        <view class="req-head">
          <view class="req-icon">{{ requestIcon(request.type_code) }}</view>
          <view class="req-main">
            <text class="req-title">{{ request.title }}</text>
            <text class="req-no">编号：{{ request.request_no }}</text>
          </view>
          <text class="req-status" :class="request.status.toLowerCase()">
            {{ statusLabel(request.status) }}
          </text>
        </view>

        <view class="meta-grid">
          <view class="meta-item">
            <text class="meta-label">事务类型</text>
            <text class="meta-value">{{ request.type_code }}</text>
          </view>
          <view class="meta-item">
            <text class="meta-label">最近更新时间</text>
            <text class="meta-value">{{ formatDateTime(request.updated_at) }}</text>
          </view>
        </view>

        <view
          v-if="request.status === 'REJECTED' || request.status === 'OFFLINE_HANDLED'"
          class="attention-box"
          :class="{ warning: request.status === 'OFFLINE_HANDLED' }"
        >
          {{
            request.status === "REJECTED"
              ? "该申请已被驳回，请检查补充材料或说明后重新提交。"
              : "该事项已转线下办理，请留意老师联系方式与后续通知。"
          }}
        </view>
      </view>
    </view>

    <view v-else-if="!loading" class="empty-panel">
      <text class="empty-title">当前筛选下暂无申请记录</text>
      <text class="empty-desc">可切换状态筛选，或直接发起新的事务申请。</text>
      <view class="empty-action" @tap="goCreate">立即发起</view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onPullDownRefresh, onShow } from "@dcloudio/uni-app";
import {
  getMyRequests,
  getRequestStatusLabel,
  type RequestBrief,
} from "@/api/workflow";
import { openMiniappPage } from "@/utils/navigation";

const STATUS_TABS = [
  { label: "全部", value: "" },
  { label: "草稿", value: "DRAFT" },
  { label: "待处理", value: "SUBMITTED,IN_REVIEW" },
  { label: "已通过", value: "APPROVED" },
  { label: "已驳回", value: "REJECTED" },
  { label: "转线下办理", value: "OFFLINE_HANDLED" },
];

const tab = ref("");
const requests = ref<RequestBrief[]>([]);
const loading = ref(false);

const pendingCount = computed(
  () =>
    requests.value.filter((item) =>
      ["SUBMITTED", "IN_REVIEW"].includes(item.status),
    ).length,
);
const attentionCount = computed(
  () =>
    requests.value.filter((item) =>
      ["REJECTED", "OFFLINE_HANDLED"].includes(item.status),
    ).length,
);

function statusLabel(status: string) {
  return getRequestStatusLabel(status);
}

function requestIcon(typeCode?: string | null) {
  const code = typeCode || "";
  if (code.includes("CERT")) return "证";
  if (code.includes("LEAVE")) return "假";
  if (code.includes("HONOR") || code.includes("SCHOLAR")) return "奖";
  if (code.includes("DORM")) return "宿";
  return "事";
}

function formatDateTime(value?: string | null) {
  if (!value) return "-";
  const normalized = value.replace("T", " ").replace("Z", "");
  return normalized.length >= 16 ? normalized.slice(0, 16) : normalized;
}

async function reload() {
  loading.value = true;
  try {
    const statusParam = tab.value.includes(",") ? undefined : tab.value || undefined;
    const response = await getMyRequests({ status: statusParam, page: 1, size: 20 });
    let items = response.data.items;
    if (tab.value.includes(",")) {
      const allowed = new Set(tab.value.split(","));
      items = items.filter((item) => allowed.has(item.status));
    }
    requests.value = items;
  } finally {
    loading.value = false;
  }
}

function onTab(value: string) {
  tab.value = value;
  void reload();
}

async function goCreate() {
  try {
    await openMiniappPage("/pages/request/create");
  } catch {
    uni.showToast({ title: "页面跳转失败", icon: "none" });
  }
}

async function goDetail(id: number) {
  try {
    await openMiniappPage(`/pages/request/detail?id=${id}`);
  } catch {
    uni.showToast({ title: "页面跳转失败", icon: "none" });
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
  padding: 24rpx;
  background: #f8f3f4;
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.hero-card {
  padding: 24rpx;
  border-radius: 20rpx;
  background:
    radial-gradient(circle at 90% 20%, rgba(183,15,36,0.08), transparent 120rpx),
    #fff8f9;
  border: 1rpx solid #f0d5da;
  display: flex;
  gap: 20rpx;
  box-shadow: var(--shadow-soft);
}

.hero-copy {
  display: flex;
  align-items: center;
  gap: 20rpx;
  flex: 1;
}

.hero-icon {
  width: 78rpx;
  height: 78rpx;
  border-radius: 20rpx;
  background: #fff1f2;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
}

.hero-title {
  display: block;
  font-size: 30rpx;
  font-weight: 800;
  color: #1e293b;
}

.hero-desc {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: #64748b;
}

.launch-btn {
  height: 88rpx;
  border-radius: 20rpx;
  background: linear-gradient(135deg, #d51f35, #b70f24);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14rpx;
  font-size: 34rpx;
  font-weight: 800;
  box-shadow: 0 12rpx 28rpx rgba(183,15,36,0.24);
}

.launch-plus {
  font-size: 34rpx;
  line-height: 1;
}

.metric-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16rpx;
}

.metric-card {
  min-height: 128rpx;
  padding: 20rpx 18rpx;
  border-radius: 20rpx;
  background: #fff;
  border: 1rpx solid #f0e2e5;
  box-shadow: var(--shadow-soft);
  text-align: center;
}

.metric-icon {
  display: block;
  height: 30rpx;
  color: #b70f24;
  font-size: 28rpx;
}

.metric-icon.muted { color: #64748b; }
.metric-icon.warn { color: #d97706; }

.metric-value {
  display: block;
  margin-top: 8rpx;
  font-size: 42rpx;
  font-weight: 800;
  color: #1e293b;
}

.metric-value.emphasis {
  color: #a61e2d;
}

.metric-value.warning {
  color: #d97706;
}

.metric-label {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #334155;
}

.tab-row {
  white-space: nowrap;
}

.tab-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-right: 12rpx;
  padding: 14rpx 24rpx;
  border-radius: 999rpx;
  background: #fff;
  border: 1rpx solid #f0e2e5;
  color: #64748b;
  font-size: 24rpx;
}

.tab-chip.active {
  background: #b70f24;
  border-color: #b70f24;
  color: #fff;
  font-weight: 800;
}

.create-entry {
  padding: 24rpx;
  border-radius: 22rpx;
  background: #fff;
  border: 1rpx solid #f0d5da;
  box-shadow: var(--shadow-soft);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20rpx;
}

.create-copy {
  flex: 1;
}

.create-title {
  display: block;
  font-size: 28rpx;
  font-weight: 600;
  color: #1e293b;
}

.create-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #64748b;
}

.create-arrow {
  color: #94a3b8;
  font-size: 34rpx;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.req-card {
  padding: 24rpx;
  border-radius: 22rpx;
  background: #fff;
  border: 1rpx solid #f0e2e5;
  box-shadow: var(--shadow-card);
}

.req-head {
  display: flex;
  align-items: flex-start;
  gap: 18rpx;
}

.req-icon {
  width: 78rpx;
  height: 78rpx;
  border-radius: 50%;
  background: #fff1f2;
  color: #b70f24;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 30rpx;
}

.req-main {
  flex: 1;
  min-width: 0;
}

.req-title {
  display: block;
  font-size: 30rpx;
  font-weight: 800;
  color: #1e293b;
  line-height: 1.5;
}

.req-no {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #64748b;
}

.req-status {
  flex-shrink: 0;
  align-self: flex-start;
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
}

.req-status.draft {
  background: #f1f5f9;
  color: #475569;
}

.req-status.submitted,
.req-status.in_review {
  background: #fff7ed;
  color: #c2410c;
}

.req-status.approved {
  background: #f0fdf4;
  color: #15803d;
}

.req-status.rejected {
  background: #fff1f2;
  color: #be123c;
}

.req-status.withdrawn {
  background: #f8fafc;
  color: #64748b;
}

.req-status.offline_handled {
  background: #fef3c7;
  color: #b45309;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
  margin-top: 18rpx;
}

.meta-item {
  padding: 16rpx;
  border-radius: 18rpx;
  background: #f8fafc;
}

.meta-label {
  display: block;
  font-size: 20rpx;
  color: #94a3b8;
}

.meta-value {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #334155;
  line-height: 1.5;
}

.attention-box {
  margin-top: 18rpx;
  padding: 18rpx 16rpx;
  border-radius: 18rpx;
  background: #fff1f2;
  color: #be123c;
  font-size: 22rpx;
  line-height: 1.7;
}

.attention-box.warning {
  background: #fff7ed;
  color: #b45309;
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

.empty-action {
  display: inline-flex;
  margin-top: 20rpx;
  padding: 14rpx 26rpx;
  border-radius: 999rpx;
  background: #a61e2d;
  color: #fff;
  font-size: 24rpx;
}
</style>
