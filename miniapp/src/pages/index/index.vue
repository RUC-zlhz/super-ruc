<template>
  <view class="container">
    <view class="hero-card">
      <view class="hero-topbar">
        <text class="hero-page-title">首页</text>
        <view class="hero-top-actions">
          <text class="hero-top-action">•••</text>
          <text class="hero-top-action ring">◎</text>
        </view>
      </view>

      <view class="hero-main">
        <view class="hero-copy">
          <view class="hero-brand">
            <view class="hero-seal">RUC</view>
            <text class="hero-eyebrow">中国人民大学</text>
          </view>
          <text class="hero-title">你好，{{ displayName }}</text>
          <text class="hero-subtitle">祝你今天学习顺利</text>
          <view class="hero-line" />
        </view>

        <view class="hero-figure">
          <view class="hero-face">RUC</view>
          <text class="hero-figure-note">学生端</text>
        </view>
      </view>

      <view class="hero-building" />
    </view>

    <view class="sync-card">
      <view class="sync-dot" :class="{ loading }" />
      <view class="sync-copy">
        <text class="sync-title">{{ loading ? "数据同步中" : "数据同步正常" }}</text>
        <text class="sync-desc">最近同步时间：{{ latestSyncText }}</text>
      </view>
      <view class="sync-action" @tap="loadDashboard">↻</view>
    </view>

    <view class="metric-row">
      <view
        v-for="metric in dashboardMetrics"
        :key="metric.key"
        class="metric-card"
        :class="metric.key"
        @tap="goTo(metric.path)"
      >
        <view class="metric-icon">{{ metric.icon }}</view>
        <text class="metric-value">{{ metric.value }}</text>
        <text class="metric-label">{{ metric.label }}</text>
        <text class="metric-helper">{{ metric.helper }}</text>
      </view>
    </view>

    <view class="section-card">
      <view class="section-head">
        <view>
          <text class="section-title">常用服务</text>
        </view>
        <text class="section-link">全部服务 ›</text>
      </view>

      <view class="entry-grid">
        <view
          v-for="item in entries"
          :key="item.path"
          class="entry-card"
          @tap="goTo(item.path)"
        >
          <view class="entry-mark">{{ item.mark }}</view>
          <text class="entry-label">{{ item.label }}</text>
        </view>
      </view>
    </view>

    <view class="section-card">
      <view class="section-head">
        <view>
          <text class="section-title">待办提醒</text>
        </view>
        <text class="section-link">更多待办 ›</text>
      </view>

      <template v-if="focusItems.length">
        <view
          v-for="item in focusItems"
          :key="item.key"
          class="focus-item"
          @tap="goTo(item.path)"
        >
          <view class="focus-leading" :class="item.tone">{{ item.badge }}</view>
          <view class="focus-body">
            <text class="focus-title">{{ item.title }}</text>
            <text class="focus-desc">{{ item.desc }}</text>
          </view>
          <text class="focus-arrow">›</text>
        </view>
      </template>
      <view v-else class="empty-panel">
        当前暂无待办事项，可直接从下方常用服务进入事务申请或党团进度。
      </view>
    </view>

    <view class="section-card">
      <view class="section-head">
        <view>
          <text class="section-title">最新通知</text>
        </view>
        <text class="section-link" @tap="goTo('/pages/notice/index')">查看全部</text>
      </view>

      <template v-if="recentNotices.length">
        <view
          v-for="notice in recentNotices"
          :key="notice.delivery_id ?? notice.id"
          class="notice-row"
          @tap="openNotice(notice)"
        >
          <view class="notice-top">
            <view class="notice-top-main">
              <text class="notice-chip" :class="{ pinned: notice.is_pinned }">
                {{ noticeCategoryLabel(notice) }}
              </text>
              <text class="notice-title">{{ notice.title }}</text>
            </view>
            <view class="notice-side">
              <text class="notice-date">{{ formatDate(notice.published_at) }}</text>
              <view class="notice-dot" :class="{ unread: isUnread(notice) }" />
            </view>
          </view>
          <text v-if="notice.summary" class="notice-summary">{{ notice.summary }}</text>
          <view class="notice-bottom">
            <text class="notice-state" :class="{ unread: isUnread(notice) }">
              {{ isUnread(notice) ? "未读" : "已读" }}
            </text>
            <text class="notice-arrow">›</text>
          </view>
        </view>
      </template>
      <view v-else class="empty-panel">暂无通知，可稍后下拉刷新。</view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onPullDownRefresh, onShow } from "@dcloudio/uni-app";
import { useAuthStore } from "@/store/auth";
import { getMyNotices, type StudentNoticeItem } from "@/api/notice";
import { getMyRequests } from "@/api/workflow";
import { getMyWorkflows, type StudentWorkflow } from "@/api/workflow";
import { openMiniappPage, openNoticeDetail } from "@/utils/navigation";

const auth = useAuthStore();

const entries = [
  {
    mark: "知",
    label: "知识查询",
    desc: "按关键字快速查询学院政策与问答。",
    path: "/pages/knowledge/index",
  },
  {
    mark: "事",
    label: "事务申请",
    desc: "发起请假、证明、盖章等常见申请。",
    path: "/pages/request/index",
  },
  {
    mark: "知",
    label: "通知中心",
    desc: "查看学院通知、系统消息与已读状态。",
    path: "/pages/notice/index",
  },
  {
    mark: "流",
    label: "党团进度",
    desc: "查看当前节点、下一动作与历史记录。",
    path: "/pages/workflow/index",
  },
  {
    mark: "测",
    label: "理论自测",
    desc: "随机抽题，完成党团知识自查。",
    path: "/pages/workflow/quiz",
  },
  {
    mark: "学",
    label: "学业查看",
    desc: "查看学分缺口与培养方案辅助提示。",
    path: "/pages/academic/index",
  },
  {
    mark: "荣",
    label: "荣誉榜",
    desc: "查看荣誉记录、历史荣誉与学年筛选。",
    path: "/pages/honor/index",
  },
  {
    mark: "我",
    label: "我的画像",
    desc: "查看画像快照、纠错申诉与成长补录。",
    path: "/pages/profile/index",
  },
];

const recentNotices = ref<StudentNoticeItem[]>([]);
const workflows = ref<StudentWorkflow[]>([]);
const requests = ref<
  Array<{
    id: number;
    title: string;
    status: string;
    request_no: string;
    updated_at: string;
  }>
>([]);
const loading = ref(false);
const latestSyncText = ref("");

const displayName = computed(() => auth.user?.display_name || "同学");
const unreadNoticeCount = computed(
  () => recentNotices.value.filter((item) => !item.read_at).length,
);
const pendingRequestCount = computed(
  () =>
    requests.value.filter((item) =>
      ["SUBMITTED", "IN_REVIEW", "REJECTED"].includes(item.status),
    ).length,
);
const activeWorkflowCount = computed(
  () =>
    workflows.value.filter((item) =>
      ["ACTIVE", "IN_PROGRESS", "SUSPENDED"].includes(item.status),
    ).length,
);

const dashboardMetrics = computed(() => [
  {
    key: "notice",
    label: "未读通知",
    value: unreadNoticeCount.value,
    icon: "✦",
    helper: "优先处理重要通知",
    path: "/pages/notice/index",
  },
  {
    key: "request",
    label: "待跟进申请",
    value: pendingRequestCount.value,
    icon: "✓",
    helper: "包含待处理与被驳回",
    path: "/pages/request/index",
  },
  {
    key: "workflow",
    label: "在途流程",
    value: activeWorkflowCount.value,
    icon: "⌘",
    helper: "党团流程当前节点",
    path: "/pages/workflow/index",
  },
]);

const focusItems = computed(() => {
  const items: Array<{
    key: string;
    badge: string;
    title: string;
    desc: string;
    tone: "notice" | "request" | "workflow";
    path: string;
  }> = [];

  if (unreadNoticeCount.value > 0) {
    items.push({
      key: "unread-notice",
      badge: `${unreadNoticeCount.value}`,
      title: "有未读通知待处理",
      desc: "建议先查看通知中心，确认是否有办理时效要求。",
      tone: "notice",
      path: "/pages/notice/index",
    });
  }

  const latestPendingRequest = requests.value.find((item) =>
    ["SUBMITTED", "IN_REVIEW", "REJECTED"].includes(item.status),
  );
  if (latestPendingRequest) {
    items.push({
      key: `request-${latestPendingRequest.id}`,
      badge: "事",
      title: latestPendingRequest.title,
      desc: `申请编号 ${latestPendingRequest.request_no} 仍需关注当前状态。`,
      tone: "request",
      path: `/pages/request/detail?id=${latestPendingRequest.id}`,
    });
  }

  const activeWorkflow = workflows.value.find((item) =>
    ["ACTIVE", "IN_PROGRESS", "SUSPENDED"].includes(item.status),
  );
  if (activeWorkflow) {
    items.push({
      key: `workflow-${activeWorkflow.id}`,
      badge: "流",
      title: activeWorkflow.template_name,
      desc: activeWorkflow.current_node_name
        ? `当前节点：${activeWorkflow.current_node_name}`
        : "可查看当前阶段与下一步说明。",
      tone: "workflow",
      path: `/pages/workflow/detail?id=${activeWorkflow.id}`,
    });
  }

  return items;
});

function isUnread(notice: StudentNoticeItem) {
  return !notice.read_at;
}

function noticeCategoryLabel(notice: StudentNoticeItem) {
  if (notice.is_pinned) return "置顶通知";
  if (notice.category) return notice.category;
  return "通知";
}

function formatDate(value?: string | null) {
  if (!value) return "";
  const normalized = value.replace("T", " ");
  return normalized.length >= 16 ? normalized.slice(0, 16) : normalized;
}

async function goTo(path: string) {
  try {
    await openMiniappPage(path);
  } catch {
    uni.showToast({ title: "页面跳转失败", icon: "none" });
  }
}

async function openNotice(notice: StudentNoticeItem) {
  try {
    await openNoticeDetail(notice.id, notice.delivery_id);
  } catch {
    uni.showToast({ title: "通知打开失败", icon: "none" });
  }
}

async function loadDashboard() {
  loading.value = true;
  try {
    if (!auth.user) {
      try {
        await auth.fetchMe();
      } catch {
        // ignore
      }
    }

    const [noticesResp, requestsResp, workflowsResp] = await Promise.allSettled([
      getMyNotices({ page: 1, size: 5 }),
      getMyRequests({ page: 1, size: 20 }),
      getMyWorkflows(),
    ]);

    recentNotices.value =
      noticesResp.status === "fulfilled" ? noticesResp.value.data.items : [];
    requests.value =
      requestsResp.status === "fulfilled" ? requestsResp.value.data.items : [];
    workflows.value =
      workflowsResp.status === "fulfilled" ? workflowsResp.value.data : [];
    latestSyncText.value = new Date().toISOString().slice(0, 16).replace("T", " ");
  } finally {
    loading.value = false;
  }
}

onShow(() => {
  void loadDashboard();
});

onPullDownRefresh(async () => {
  await loadDashboard();
  uni.stopPullDownRefresh();
});
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 0 24rpx 28rpx;
  background:
    linear-gradient(180deg, #b70f24 0, #b70f24 318rpx, var(--bg-color) 600rpx),
    var(--bg-color);
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.hero-card {
  position: relative;
  min-height: 328rpx;
  padding: 36rpx 28rpx 76rpx;
  border-radius: 0 0 42rpx 42rpx;
  background:
    radial-gradient(circle at 18% 18%, rgba(255,255,255,0.16), transparent 34%),
    radial-gradient(circle at 86% 16%, rgba(255,255,255,0.12), transparent 28%),
    linear-gradient(135deg, #b70f24 0%, #a80d21 52%, #7f1722 100%);
  color: #fff;
  box-shadow: 0 24rpx 56rpx rgba(127, 23, 34, 0.22);
  overflow: hidden;
  margin: 0 -24rpx;
}

.hero-card::before,
.hero-card::after {
  content: '';
  position: absolute;
  inset: auto auto 26rpx 34rpx;
  width: 280rpx;
  height: 280rpx;
  border-radius: 50%;
  border: 1rpx solid rgba(255, 255, 255, 0.1);
  opacity: 0.45;
}

.hero-card::after {
  inset: 108rpx -24rpx auto auto;
  width: 360rpx;
  height: 190rpx;
  border-radius: 190rpx 0 0 0;
  background: linear-gradient(135deg, transparent, rgba(255, 255, 255, 0.16));
  border: none;
}

.hero-topbar {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.hero-page-title {
  font-size: 48rpx;
  font-weight: 800;
  line-height: 1.1;
}

.hero-top-actions {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.hero-top-action {
  min-width: 76rpx;
  height: 56rpx;
  padding: 0 18rpx;
  border-radius: var(--radius-pill);
  border: 1rpx solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  font-weight: 700;
}

.hero-top-action.ring {
  min-width: 58rpx;
  padding: 0;
  font-size: 24rpx;
}

.hero-main {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  gap: 24rpx;
  margin-top: 30rpx;
}

.hero-copy {
  flex: 1;
  min-width: 0;
}

.hero-brand {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.hero-seal {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  border: 1rpx solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20rpx;
  font-weight: 700;
  letter-spacing: 2rpx;
}

.hero-eyebrow {
  display: block;
  font-size: 24rpx;
  opacity: 0.92;
}

.hero-title {
  display: block;
  margin-top: 26rpx;
  font-size: 54rpx;
  font-weight: 800;
  line-height: 1.2;
}

.hero-subtitle {
  display: block;
  margin-top: 12rpx;
  font-size: 30rpx;
  line-height: 1.7;
  opacity: 0.88;
}

.hero-line {
  width: 68rpx;
  height: 8rpx;
  margin-top: 20rpx;
  border-radius: 999rpx;
  background: rgba(255, 241, 242, 0.95);
}

.hero-figure {
  position: relative;
  z-index: 1;
  width: 196rpx;
  align-self: flex-end;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
}

.hero-face {
  width: 168rpx;
  height: 168rpx;
  border-radius: 56rpx;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(247, 222, 209, 0.96)),
    #fff;
  box-shadow:
    inset 0 -10rpx 18rpx rgba(127, 23, 34, 0.12),
    0 18rpx 38rpx rgba(89, 16, 26, 0.16);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #b70f24;
  font-size: 34rpx;
  font-weight: 800;
}

.hero-figure-note {
  font-size: 22rpx;
  opacity: 0.88;
}

.hero-building {
  position: absolute;
  right: 160rpx;
  bottom: 22rpx;
  width: 260rpx;
  height: 112rpx;
  opacity: 0.18;
  background:
    linear-gradient(180deg, transparent 0, transparent 48rpx, rgba(255, 255, 255, 0.4) 48rpx, rgba(255, 255, 255, 0.4) 52rpx, transparent 52rpx),
    repeating-linear-gradient(90deg, rgba(255, 255, 255, 0.3) 0 12rpx, transparent 12rpx 26rpx),
    linear-gradient(180deg, rgba(255, 255, 255, 0.26), rgba(255, 255, 255, 0.12));
  clip-path: polygon(0 100%, 0 56%, 10% 44%, 18% 50%, 28% 36%, 40% 44%, 52% 30%, 64% 40%, 72% 28%, 82% 34%, 92% 20%, 100% 24%, 100% 100%);
}

.sync-card {
  position: relative;
  z-index: 2;
  margin-top: -54rpx;
  padding: 24rpx 24rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.97);
  box-shadow: var(--shadow-float);
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.sync-dot {
  width: 46rpx;
  height: 46rpx;
  border-radius: 50%;
  background: #58d26d;
  box-shadow: 0 0 0 12rpx rgba(88, 210, 109, 0.13);
}

.sync-dot.loading {
  background: #f59e0b;
  box-shadow: 0 0 0 12rpx rgba(245, 158, 11, 0.14);
}

.sync-copy {
  flex: 1;
  min-width: 0;
}

.sync-title {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
  color: #1e293b;
}

.sync-desc {
  display: block;
  margin-top: 4rpx;
  font-size: 23rpx;
  color: #8a7280;
}

.sync-action {
  width: 84rpx;
  height: 84rpx;
  border-left: 1rpx solid #f0e1e4;
  color: #b70f24;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  font-size: 44rpx;
}

.metric-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18rpx;
}

.metric-card {
  position: relative;
  min-height: 176rpx;
  padding: 24rpx 18rpx 20rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.94);
  border: 1rpx solid #f0e2e5;
  box-shadow: var(--shadow-soft);
  overflow: hidden;
}

.metric-icon {
  position: absolute;
  right: 16rpx;
  top: 18rpx;
  width: 54rpx;
  height: 54rpx;
  border-radius: 18rpx;
  background: #fff1f2;
  color: #b70f24;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
}

.metric-card.request .metric-icon {
  background: #fff7ed;
  color: #ea7a22;
}

.metric-card.workflow .metric-icon {
  background: #eef2f7;
  color: #475569;
}

.metric-value {
  display: block;
  margin-top: 42rpx;
  font-size: 42rpx;
  font-weight: 800;
  color: #b70f24;
}

.metric-label {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #6a4b55;
}

.metric-helper {
  display: block;
  margin-top: 12rpx;
  font-size: 20rpx;
  line-height: 1.5;
  color: #9c8b90;
}

.section-card {
  padding: 30rpx 24rpx;
  border-radius: 26rpx;
  background: var(--card-elevated);
  border: 1rpx solid #f0e2e5;
  box-shadow: var(--shadow-card);
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16rpx;
  margin-bottom: 20rpx;
}

.section-title {
  display: block;
  font-size: 30rpx;
  font-weight: 800;
  color: #1e293b;
}

.section-link {
  flex-shrink: 0;
  font-size: 24rpx;
  color: #b2959e;
}

.entry-grid {
  display: flex;
  flex-wrap: wrap;
  row-gap: 30rpx;
}

.entry-card {
  width: 25%;
  padding: 4rpx 8rpx;
  background: transparent;
  border: none;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.entry-mark {
  width: 84rpx;
  height: 84rpx;
  border-radius: 28rpx;
  background:
    linear-gradient(180deg, #fff7f8, #fff0f2),
    #fff;
  color: #a61e2d;
  box-shadow: inset 0 0 0 1rpx rgba(183, 15, 36, 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 700;
}

.entry-label {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  color: #374151;
  text-align: center;
  line-height: 1.45;
}

.focus-item {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 24rpx 0;
  border-bottom: 1rpx solid #eef2f6;
}

.focus-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.focus-leading {
  min-width: 86rpx;
  height: 56rpx;
  padding: 0 16rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  font-weight: 600;
}

.focus-leading.notice {
  background: #fff1f2;
  color: #be123c;
}

.focus-leading.request {
  background: #fff7ed;
  color: #c2410c;
}

.focus-leading.workflow {
  background: #eff6ff;
  color: #1d4ed8;
}

.focus-body {
  flex: 1;
  min-width: 0;
}

.focus-title {
  display: block;
  font-size: 28rpx;
  color: #1e293b;
  font-weight: 700;
}

.focus-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #64748b;
}

.focus-arrow {
  flex-shrink: 0;
  color: #94a3b8;
  font-size: 34rpx;
}

.notice-row {
  padding: 22rpx 0;
  border-bottom: 1rpx solid #eef2f6;
}

.notice-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.notice-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
}

.notice-top-main {
  flex: 1;
  min-width: 0;
}

.notice-chip {
  display: inline-flex;
  align-items: center;
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  color: #7f1722;
  background: #fff1f2;
}

.notice-chip.pinned {
  color: #b45309;
  background: #fff7ed;
}

.notice-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12rpx;
  flex-shrink: 0;
}

.notice-date,
.notice-state {
  font-size: 22rpx;
  color: #94a3b8;
}

.notice-dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: rgba(148, 163, 184, 0.38);
}

.notice-dot.unread {
  background: #c8142f;
  box-shadow: 0 0 0 8rpx rgba(200, 20, 47, 0.1);
}

.notice-state.unread {
  color: #a61e2d;
  font-weight: 600;
}

.notice-title {
  display: block;
  margin-top: 12rpx;
  font-size: 29rpx;
  line-height: 1.55;
  color: #1e293b;
  font-weight: 600;
}

.notice-summary {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: #64748b;
}

.notice-bottom {
  display: flex;
  align-items: center;
  margin-top: 12rpx;
  justify-content: flex-end;
  gap: 12rpx;
}

.notice-arrow {
  color: #b7a5aa;
  font-size: 30rpx;
}

.empty-panel {
  padding: 28rpx 20rpx;
  border-radius: 24rpx;
  background: #f8fafc;
  color: #64748b;
  font-size: 24rpx;
  line-height: 1.7;
  text-align: center;
}
</style>
