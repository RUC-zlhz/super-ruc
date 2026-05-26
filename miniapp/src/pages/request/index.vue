<template>
  <view class="container">
    <view class="hero-card">
      <view class="hero-orb hero-orb-left" />
      <view class="hero-orb hero-orb-right" />
      <view class="hero-main">
        <view class="hero-copy">
          <view class="hero-icon-wrap">
            <text class="hero-icon">申</text>
          </view>
          <view class="hero-text">
            <text class="hero-eyebrow">学生事务服务</text>
            <text class="hero-title">线上提交申请，实时查看办理进度</text>
            <text class="hero-desc">
              高效便捷 · 透明可追踪 · 校园服务更贴心
            </text>
          </view>
        </view>
        <view class="hero-side">
          <text class="hero-side-label">当前筛选</text>
          <text class="hero-side-value">{{ activeTabLabel }}</text>
          <text class="hero-side-note">{{ heroStatusNote }}</text>
        </view>
      </view>
      <view class="hero-tags">
        <text class="hero-tag">待处理 {{ pendingCount }} 项</text>
        <text class="hero-tag outline">需关注 {{ attentionCount }} 项</text>
      </view>
    </view>

    <EmptyState
      v-if="isGuest"
      icon="绑"
      tone="warning"
      title="请先绑定学号"
      description="访客身份不能查看或发起学生事务申请。绑定学生主档后再进入申请列表。"
      action-text="去绑定"
      @action="goBindStudent"
    />

    <template v-else>
    <view class="launch-btn" hover-class="hover-opacity" @tap="goCreate">
      <view class="launch-core">
        <text class="launch-plus">＋</text>
        <text class="launch-text">发起申请</text>
      </view>
      <text class="launch-note">支持先保存草稿，再补充附件后提交</text>
    </view>

    <view class="metric-row">
      <view class="metric-card">
        <text class="metric-icon">▤</text>
        <text class="metric-label">当前列表</text>
        <view class="metric-number">
          <text class="metric-value">{{ requests.length }}</text>
          <text class="metric-unit">项</text>
        </view>
        <text class="metric-note">{{ activeTabLabel === "全部" ? "展示全部状态申请" : `当前筛选：${activeTabLabel}` }}</text>
      </view>
      <view class="metric-card">
        <text class="metric-icon muted">⌛</text>
        <text class="metric-label">待处理</text>
        <view class="metric-number">
          <text class="metric-value emphasis">{{ pendingCount }}</text>
          <text class="metric-unit">项</text>
        </view>
        <text class="metric-note">已提交并进入受理流程</text>
      </view>
      <view class="metric-card attention">
        <text class="metric-icon warn">!</text>
        <text class="metric-label">需关注</text>
        <view class="metric-number">
          <text class="metric-value warning">{{ attentionCount }}</text>
          <text class="metric-unit">项</text>
        </view>
        <text class="metric-note">驳回或转线下办理</text>
      </view>
    </view>

    <view class="filter-panel">
      <view class="filter-head">
        <view>
          <text class="filter-title">状态筛选</text>
          <text class="filter-hint">{{ filterHint }}</text>
        </view>
        <text class="filter-meta">共 {{ requests.length }} 项</text>
      </view>

      <view class="filter-tabs-row">
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
        <view class="filter-button" @tap="openStatusFilter">筛选</view>
      </view>
    </view>

    <view class="create-entry" hover-class="hover-opacity" @tap="goCreate">
      <view class="create-copy">
        <text class="create-kicker">草稿补交更清晰</text>
        <text class="create-title">材料不完整？可先保存草稿</text>
        <text class="create-desc">
          被驳回或需补充的申请，会在列表中以红色提醒卡突出展示。
        </text>
      </view>
      <view class="create-arrow"><view class="mini-chevron" /></view>
    </view>

    <InlineStateNotice
      v-if="pageError"
      :tone="requests.length ? 'warning' : 'error'"
      :title="requests.length ? '申请列表未完全更新' : '申请列表加载失败'"
      :description="requests.length ? `${pageError}，当前保留上次加载结果。` : `${pageError}，可点击重试重新同步。`"
      action-text="重试"
      @action="reload"
    />

    <EmptyState
      v-if="loading && !requests.length"
      icon="…"
      tone="muted"
      title="申请列表加载中"
      description="正在同步你的申请记录，请稍候。"
    />

    <view v-else-if="requests.length" class="list">
      <view
        v-for="request in requests"
        :key="request.id"
        class="req-card"
        :class="requestToneClass(request.status)"
        hover-class="hover-opacity"
        @tap="goDetail(request.id)"
      >
        <view class="req-card-bg" />
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

        <view class="req-foot">
          <view class="req-note">
            <text class="req-note-icon">{{ requestNoteIcon(request.status) }}</text>
            <text class="req-note-text">{{ requestStatusNote(request.status) }}</text>
          </view>
          <view class="req-action">
            <text>{{ requestActionText(request.status) }}</text>
            <view class="mini-chevron" />
          </view>
        </view>
      </view>
    </view>

    <EmptyState
      v-else-if="!loading && !pageError"
      icon="档"
      tone="primary"
      title="当前筛选下暂无申请记录"
      description="可切换状态筛选，或直接发起新的事务申请。"
      action-text="立即发起"
      @action="goCreate"
    />
    </template>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onPullDownRefresh, onShow } from "@dcloudio/uni-app";
import InlineStateNotice from "@/components/InlineStateNotice.vue";
import EmptyState from "@/components/EmptyState.vue";
import {
  getMyRequests,
  getRequestStatusLabel,
  getRequestTypeBadge,
  type RequestBrief,
} from "@/api/workflow";
import { useAuthStore } from "@/store/auth";
import { getErrorMessage } from "@/utils/error";
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
const pageError = ref("");
const hasLoaded = ref(false);
const lastLoadedTab = ref("");
const currentPage = ref(1);
const hasMore = ref(true);
const auth = useAuthStore();
const isGuest = computed(() => auth.isLoggedIn && !auth.user?.student_id);

const activeTabLabel = computed(
  () => STATUS_TABS.find((item) => item.value === tab.value)?.label || "全部",
);
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
const heroStatusNote = computed(() => {
  if (!requests.value.length) return "当前筛选暂无记录";
  if (tab.value === "REJECTED") return "请优先处理被驳回的申请";
  if (tab.value === "OFFLINE_HANDLED") return "请按线下指引继续办理";
  if (tab.value === "SUBMITTED,IN_REVIEW") return "审批流正在推进中";
  return "可随时查看进度与补充材料";
});
const filterHint = computed(() => {
  if (!requests.value.length) return "切换状态后可快速定位不同办理阶段。";
  return `当前聚焦“${activeTabLabel.value}”状态，可左右滑动查看更多筛选项。`;
});

function statusLabel(status: string) {
  return getRequestStatusLabel(status);
}

function requestIcon(typeCode?: string | null) {
  return getRequestTypeBadge(typeCode);
}

function requestToneClass(status: string) {
  if (status === "APPROVED") return "tone-approved";
  if (status === "REJECTED") return "tone-rejected";
  if (status === "OFFLINE_HANDLED") return "tone-offline";
  if (status === "SUBMITTED" || status === "IN_REVIEW") return "tone-pending";
  return "tone-neutral";
}

function requestStatusNote(status: string) {
  if (status === "DRAFT") return "草稿未提交，可继续完善申请内容。";
  if (status === "SUBMITTED" || status === "IN_REVIEW") {
    return "审批流转中，请留意审核结果与通知提醒。";
  }
  if (status === "APPROVED") return "申请已办结，可查看详情与材料留档。";
  if (status === "REJECTED") return "材料需补充，请尽快修改后重新提交。";
  if (status === "WITHDRAWN") return "申请已撤回，可调整后重新发起。";
  if (status === "OFFLINE_HANDLED") return "该事项已转线下办理，请查看办理指引。";
  return "可点击查看当前申请详情。";
}

function requestActionText(status: string) {
  if (status === "APPROVED") return "查看详情";
  if (status === "REJECTED" || status === "DRAFT" || status === "WITHDRAWN") {
    return "查看并处理";
  }
  if (status === "OFFLINE_HANDLED") return "查看指引";
  return "查看进度";
}

function requestNoteIcon(status: string) {
  if (status === "APPROVED") return "✓";
  if (status === "REJECTED") return "!";
  if (status === "OFFLINE_HANDLED") return "i";
  if (status === "SUBMITTED" || status === "IN_REVIEW") return "⌛";
  return "•";
}

function formatDateTime(value?: string | null) {
  if (!value) return "-";
  const normalized = value.replace("T", " ").replace("Z", "");
  return normalized.length >= 16 ? normalized.slice(0, 16) : normalized;
}

async function reload() {
  if (isGuest.value) {
    requests.value = [];
    pageError.value = "";
    hasLoaded.value = false;
    lastLoadedTab.value = "";
    return;
  }
  loading.value = true;
  currentPage.value = 1;
  hasMore.value = true;
  try {
    pageError.value = "";
    const statusList = tab.value.split(",").map((item) => item.trim()).filter(Boolean);
    let items: RequestBrief[];
    if (statusList.length > 1) {
      const responses = await Promise.all(
        statusList.map((status) => getMyRequests({ status, page: 1, size: 100 })),
      );
      const byId = new Map<number, RequestBrief>();
      for (const response of responses) {
        for (const item of response.data.items) {
          byId.set(item.id, item);
        }
      }
      items = Array.from(byId.values()).sort(
        (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
      );
      hasMore.value = false;
    } else {
      const response = await getMyRequests({ status: statusList[0], page: currentPage.value, size: 20 });
      items = response.data.items;
      if (items.length < 20) hasMore.value = false;
    }
    requests.value = items;
    hasLoaded.value = true;
    lastLoadedTab.value = tab.value;
  } catch (error) {
    pageError.value = getErrorMessage(error, "申请列表加载失败");
    if (!hasLoaded.value || lastLoadedTab.value !== tab.value) {
      requests.value = [];
    }
  } finally {
    loading.value = false;
  }
}

async function loadMore() {
  if (!hasMore.value || loading.value) return;
  const statusList = tab.value.split(",").map((item) => item.trim()).filter(Boolean);
  if (statusList.length > 1) return;

  loading.value = true;
  try {
    const nextPage = currentPage.value + 1;
    const response = await getMyRequests({ status: statusList[0], page: nextPage, size: 20 });
    const newItems = response.data.items;
    if (newItems.length > 0) {
      requests.value = [...requests.value, ...newItems];
      currentPage.value = nextPage;
    }
    if (newItems.length < 20) {
      hasMore.value = false;
    }
  } catch (error) {
    uni.showToast({ title: "加载更多失败", icon: "none" });
  } finally {
    loading.value = false;
  }
}

async function goBindStudent() {
  await openMiniappPage("/pages/profile/index");
}

function onTab(value: string) {
  tab.value = value;
  void reload().catch(() => undefined);
}

function openStatusFilter() {
  uni.showActionSheet({
    itemList: STATUS_TABS.map((item) => item.label),
    success(res) {
      const next = STATUS_TABS[res.tapIndex];
      if (!next) return;
      onTab(next.value);
    },
  });
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
  void reload().catch(() => undefined);
});

onPullDownRefresh(async () => {
  try {
    await reload();
  } finally {
    uni.stopPullDownRefresh();
  }
});

onReachBottom(() => {
  loadMore();
});
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 28rpx 36rpx 42rpx;
  background:
    radial-gradient(circle at 100% 10%, rgba(183, 15, 36, 0.06), transparent 190rpx),
    linear-gradient(180deg, #fff 0, #fff7f7 250rpx, #f8f3f4 100%),
    #f6f0f1;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.hero-card {
  position: relative;
  overflow: hidden;
  padding: 28rpx 30rpx;
  border-radius: 16rpx;
  background:
    radial-gradient(circle at 100% 100%, rgba(183, 15, 36, 0.12), transparent 180rpx),
    linear-gradient(135deg, rgba(255, 250, 251, 0.98), rgba(255, 245, 247, 0.98));
  border: 1rpx solid #f0c9cf;
  box-shadow: 0 10rpx 24rpx rgba(146, 18, 36, 0.07);
}

.hero-orb {
  display: none;
}

.hero-orb-left {
  width: 180rpx;
  height: 180rpx;
  left: -56rpx;
  top: -60rpx;
}

.hero-orb-right {
  width: 220rpx;
  height: 220rpx;
  right: -70rpx;
  bottom: -96rpx;
}

.hero-main {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18rpx;
}

.hero-copy {
  display: flex;
  align-items: center;
  gap: 18rpx;
  flex: 1;
  min-width: 0;
}

.hero-icon-wrap {
  width: 92rpx;
  height: 92rpx;
  border-radius: 20rpx;
  background: linear-gradient(135deg, #fff1f2, #ffe1e6);
  box-shadow: inset 0 0 0 1rpx rgba(183, 15, 36, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.hero-icon {
  font-size: 42rpx;
  color: #b70f24;
  font-weight: 900;
  line-height: 1;
}

.hero-text {
  min-width: 0;
}

.hero-eyebrow {
  display: inline-flex;
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
  background: transparent;
  color: #b70f24;
  font-size: 20rpx;
  letter-spacing: 1rpx;
}

.hero-title {
  display: block;
  margin-top: 12rpx;
  font-size: 31rpx;
  font-weight: 800;
  line-height: 1.45;
  color: #1f2937;
}

.hero-desc {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: #8a7278;
}

.hero-side {
  display: none;
}

.hero-side-label {
  display: block;
  font-size: 20rpx;
  color: rgba(255, 244, 246, 0.74);
}

.hero-side-value {
  display: block;
  margin-top: 8rpx;
  font-size: 30rpx;
  font-weight: 800;
  color: #fff;
}

.hero-side-note {
  display: block;
  margin-top: 8rpx;
  font-size: 20rpx;
  line-height: 1.5;
  color: rgba(255, 244, 246, 0.72);
}

.hero-tags {
  display: none;
}

.hero-tag {
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
  font-size: 22rpx;
}

.hero-tag.outline {
  background: rgba(255, 248, 249, 0.12);
  box-shadow: inset 0 0 0 1rpx rgba(255, 255, 255, 0.18);
}

.launch-btn {
  padding: 22rpx 24rpx;
  border-radius: 18rpx;
  background: linear-gradient(135deg, #df1832, #b70f24);
  color: #fff;
  box-shadow: 0 16rpx 34rpx rgba(183, 15, 36, 0.28);
}

.launch-core {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14rpx;
}

.launch-plus {
  width: 42rpx;
  height: 42rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.94);
  color: #b70f24;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  font-weight: 800;
  line-height: 1;
}

.launch-text {
  font-size: 36rpx;
  font-weight: 800;
}

.launch-note {
  display: none;
}

.metric-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16rpx;
}

.metric-card {
  min-height: 142rpx;
  padding: 22rpx 18rpx;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.94);
  border: 1rpx solid rgba(240, 226, 229, 0.9);
  box-shadow: 0 14rpx 32rpx rgba(36, 17, 21, 0.06);
}

.metric-card.attention {
  background: linear-gradient(180deg, rgba(255, 246, 247, 0.98), rgba(255, 241, 243, 0.98));
  border-color: rgba(231, 104, 124, 0.24);
}

.metric-icon {
  display: block;
  color: #b70f24;
  font-size: 28rpx;
  line-height: 1;
}

.metric-icon.muted {
  color: #64748b;
}

.metric-icon.warn {
  color: #d9363e;
}

.metric-label {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  color: #475569;
}

.metric-number {
  display: flex;
  align-items: flex-end;
  gap: 8rpx;
  margin-top: 12rpx;
}

.metric-value {
  font-size: 44rpx;
  font-weight: 800;
  color: #1e293b;
  line-height: 1;
}

.metric-value.emphasis {
  color: #991b1b;
}

.metric-value.warning {
  color: #be123c;
}

.metric-unit {
  padding-bottom: 4rpx;
  font-size: 20rpx;
  color: #94a3b8;
}

.metric-note {
  display: none;
}

.filter-panel {
  padding: 0;
  border-radius: 0;
  background: transparent;
  border: none;
  box-shadow: none;
}

.filter-head {
  display: none;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16rpx;
}

.filter-title {
  display: block;
  font-size: 28rpx;
  font-weight: 800;
  color: #1f2937;
}

.filter-hint {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #94a3b8;
}

.filter-meta {
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  background: #fff3f4;
  color: #b70f24;
  font-size: 22rpx;
  white-space: nowrap;
}

.filter-tabs-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.tab-row {
  flex: 1;
  min-width: 0;
  white-space: nowrap;
}

.tab-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-right: 12rpx;
  padding: 15rpx 24rpx;
  border-radius: 14rpx;
  background: #f8fafc;
  border: 1rpx solid #eef2f7;
  color: #64748b;
  font-size: 24rpx;
  box-shadow: inset 0 -2rpx 0 rgba(255, 255, 255, 0.8);
}

.tab-chip.active {
  background: linear-gradient(135deg, #d51f35, #b70f24);
  border-color: #b70f24;
  color: #fff;
  font-weight: 800;
  box-shadow: 0 10rpx 24rpx rgba(183, 15, 36, 0.22);
}

.filter-button {
  flex-shrink: 0;
  min-width: 100rpx;
  height: 62rpx;
  border-radius: 14rpx;
  color: #3f3f46;
  background: rgba(255, 255, 255, 0.92);
  border: 1rpx solid #eef2f7;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
}

.create-entry {
  padding: 24rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, rgba(255, 252, 252, 0.98), rgba(255, 244, 246, 0.98));
  border: 1rpx solid rgba(240, 213, 218, 0.96);
  box-shadow: var(--shadow-soft);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20rpx;
  display: none;
}

.create-copy {
  flex: 1;
}

.create-kicker {
  display: inline-flex;
  padding: 4rpx 14rpx;
  border-radius: 999rpx;
  background: #fff1f2;
  font-size: 20rpx;
  color: #b70f24;
}

.create-title {
  display: block;
  margin-top: 10rpx;
  font-size: 28rpx;
  font-weight: 700;
  color: #1e293b;
}

.create-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: #64748b;
}

.create-arrow {
  width: 56rpx;
  height: 56rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(183, 15, 36, 0.08);
  border: 1rpx solid rgba(183, 15, 36, 0.16);
  color: #b70f24;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.req-card {
  position: relative;
  overflow: hidden;
  padding: 26rpx;
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid rgba(240, 226, 229, 0.9);
  box-shadow: 0 16rpx 34rpx rgba(41, 18, 23, 0.08);
}

.req-card-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.72), rgba(255, 255, 255, 0));
  pointer-events: none;
}

.req-card.tone-pending {
  border-color: rgba(245, 158, 11, 0.24);
}

.req-card.tone-approved {
  border-color: rgba(34, 197, 94, 0.2);
}

.req-card.tone-rejected {
  background: linear-gradient(180deg, rgba(255, 248, 249, 0.98), rgba(255, 244, 246, 0.98));
  border-color: rgba(220, 38, 38, 0.24);
}

.req-card.tone-offline {
  background: linear-gradient(180deg, rgba(255, 250, 240, 0.98), rgba(255, 246, 236, 0.98));
  border-color: rgba(217, 119, 6, 0.24);
}

.req-head,
.meta-grid,
.attention-box,
.req-foot {
  position: relative;
  z-index: 1;
}

.req-head {
  display: flex;
  align-items: flex-start;
  gap: 18rpx;
}

.req-icon {
  width: 82rpx;
  height: 82rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #fff1f2, #ffe7ea);
  color: #b70f24;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 30rpx;
  box-shadow: inset 0 0 0 1rpx rgba(183, 15, 36, 0.08);
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
  padding: 10rpx 20rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  font-weight: 700;
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
  padding: 18rpx;
  border-radius: 20rpx;
  background: rgba(248, 250, 252, 0.96);
  box-shadow: inset 0 0 0 1rpx rgba(226, 232, 240, 0.64);
}

.meta-label {
  display: block;
  font-size: 20rpx;
  color: #94a3b8;
}

.meta-value {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  color: #334155;
  line-height: 1.5;
  word-break: break-all;
}

.attention-box {
  margin-top: 18rpx;
  padding: 18rpx 18rpx;
  border-radius: 18rpx;
  background: #fff1f2;
  color: #be123c;
  font-size: 22rpx;
  line-height: 1.7;
  box-shadow: inset 0 0 0 1rpx rgba(244, 63, 94, 0.08);
}

.attention-box.warning {
  background: #fff7ed;
  color: #b45309;
  box-shadow: inset 0 0 0 1rpx rgba(245, 158, 11, 0.12);
}

.req-foot {
  margin-top: 18rpx;
  padding-top: 18rpx;
  border-top: 1rpx solid rgba(241, 229, 232, 0.9);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16rpx;
}

.req-note {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.req-note-icon {
  width: 34rpx;
  height: 34rpx;
  border-radius: 50%;
  background: #fff1f2;
  color: #b70f24;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20rpx;
  font-weight: 800;
  flex-shrink: 0;
}

.req-note-text {
  font-size: 22rpx;
  line-height: 1.6;
  color: #64748b;
}

.req-action {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 10rpx;
  color: #b70f24;
  font-size: 24rpx;
  font-weight: 700;
}

</style>
