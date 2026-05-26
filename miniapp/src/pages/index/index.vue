<template>
  <view class="container" style="background-color: #f8f3f4;">
    <view class="hero-card" style="background-color: #b70f24; color: #ffffff;">
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
          <text class="hero-title">{{ greeting }}，{{ displayName }}</text>
          <text class="hero-subtitle">祝你今天学习顺利</text>
          <view class="hero-line" />
        </view>

        <view class="hero-figure">
          <image class="hero-student" src="/static/hero-student.png" mode="aspectFit" />
        </view>
      </view>

      <view class="hero-building" />
    </view>

    <view class="sync-card">
      <view class="sync-dot" :class="{ loading: isAnySectionLoading }" />
      <view class="sync-copy">
        <text class="sync-title">{{ syncStatusTitle }}</text>
        <text class="sync-desc">{{ syncStatusDescription }}</text>
      </view>
      <view class="sync-action" hover-class="hover-opacity" @tap="loadDashboard">↻</view>
    </view>

    <view class="metric-row">
      <view
        v-for="metric in dashboardMetrics"
        :key="metric.key"
        class="metric-card"
        :class="metric.key"
        hover-class="hover-scale"
        @tap="goTo(metric.path)"
      >
        <text class="metric-label">{{ metric.label }}</text>
        <text class="metric-value">{{ metric.value }}</text>
        <view class="metric-line" />
        <view class="metric-icon">{{ metric.icon }}</view>
        <text class="metric-helper">{{ metric.helper }}</text>
      </view>
    </view>

    <view class="section-card">
      <view class="section-head">
        <view>
          <text class="section-title">重点入口</text>
          <text class="section-subtitle">学业分析、模板下载、进度中心</text>
        </view>
      </view>

      <view class="priority-grid">
        <view
          v-for="item in shortcutEntries"
          :key="item.key"
          class="priority-card"
          hover-class="hover-scale"
          @tap="goTo(item.url)"
        >
          <view class="priority-mark" :class="item.tone">{{ item.mark }}</view>
          <text class="priority-label">{{ item.label }}</text>
          <text class="priority-desc">{{ item.desc }}</text>
        </view>
      </view>
    </view>

    <view class="section-card">
      <view class="section-head">
        <view>
          <text class="section-title">常用服务</text>
        </view>
        <view class="section-link" hover-class="hover-opacity" @tap="goTo('/pages/request/index')">
          <text>全部服务</text>
          <view class="mini-chevron" />
        </view>
      </view>

      <view class="entry-grid">
        <view
          v-for="item in entries"
          :key="item.key"
          class="entry-card"
          hover-class="hover-scale"
          @tap="goTo(item.url)"
        >
          <view class="entry-mark" :class="item.tone">{{ item.mark }}</view>
          <text class="entry-label">{{ item.label }}</text>
          <text v-if="item.desc" class="entry-desc">{{ item.desc }}</text>
        </view>
      </view>
    </view>

    <view class="section-card">
      <view class="section-head">
        <view>
          <text class="section-title">待办提醒</text>
        </view>
        <view class="section-actions">
          <text class="section-action" hover-class="hover-opacity" @tap="refreshSection('requests')">
            {{ sectionMeta.requests.loading ? "申请同步中" : "刷新申请" }}
          </text>
          <text class="section-action" hover-class="hover-opacity" @tap="refreshSection('workflows')">
            {{ sectionMeta.workflows.loading ? "流程同步中" : "刷新流程" }}
          </text>
        </view>
      </view>

      <InlineStateNotice
        v-if="todoNotice"
        compact
        :tone="todoNotice.tone"
        :title="todoNotice.title"
        :description="todoNotice.description"
        action-text="重试"
        @action="refreshTodoSections"
      />

      <template v-if="focusItems.length">
        <view
          v-for="item in focusItems"
          :key="item.key"
          class="focus-item"
          hover-class="hover-opacity"
          @tap="goTo(item.path)"
        >
          <view class="focus-leading" :class="item.tone">{{ item.badge }}</view>
          <view class="focus-body">
            <text class="focus-title">{{ item.title }}</text>
            <text class="focus-desc">{{ item.desc }}</text>
          </view>
          <view class="focus-arrow"><view class="mini-chevron" /></view>
        </view>
      </template>
      <view v-else-if="!todoSectionUnavailable" class="empty-panel">
        当前暂无待办事项，可直接从下方常用服务进入事务申请或党团进度。
      </view>
    </view>

    <view class="section-card">
      <view class="section-head">
        <view>
          <text class="section-title">最新通知</text>
        </view>
        <view class="section-actions">
          <text class="section-action" hover-class="hover-opacity" @tap="refreshSection('notices')">
            {{ sectionMeta.notices.loading ? "通知同步中" : "刷新通知" }}
          </text>
          <text class="section-action" hover-class="hover-opacity" @tap="goTo('/pages/notice/index')">查看全部</text>
        </view>
      </view>

      <InlineStateNotice
        v-if="noticeSectionNotice"
        compact
        :tone="noticeSectionNotice.tone"
        :title="noticeSectionNotice.title"
        :description="noticeSectionNotice.description"
        action-text="重试"
        @action="refreshSection('notices')"
      />

      <template v-if="recentNotices.length">
        <view
          v-for="notice in recentNotices"
          :key="noticeKey(notice)"
          class="notice-row"
          hover-class="hover-opacity"
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
            <view class="notice-arrow"><view class="mini-chevron" /></view>
          </view>
        </view>
      </template>
      <view v-else-if="!noticeSectionUnavailable" class="empty-panel">暂无通知，可稍后下拉刷新。</view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { onPullDownRefresh, onShow } from "@dcloudio/uni-app";
import InlineStateNotice from "@/components/InlineStateNotice.vue";
import { useAuthStore } from "@/store/auth";
import { getMyNotices, type StudentNoticeItem } from "@/api/notice";
import {
  getMyRequests,
  getMyWorkflows,
  type RequestBrief,
  type StudentWorkflow,
} from "@/api/workflow";
import { getErrorMessage } from "@/utils/error";
import { openMiniappPage, openNoticeDetail } from "@/utils/navigation";

type HomeSectionKey = "notices" | "requests" | "workflows";
type HomeSectionMeta = {
  loading: boolean;
  error: string;
  fromCache: boolean;
  hasLoaded: boolean;
  lastSuccessAt: string;
};
type HomeSectionNotice = {
  tone: "error" | "warning" | "info";
  title: string;
  description: string;
};
type HomeDashboardCache = {
  notices?: {
    items: StudentNoticeItem[];
    syncedAt: string;
  };
  requests?: {
    items: RequestBrief[];
    syncedAt: string;
  };
  workflows?: {
    items: StudentWorkflow[];
    syncedAt: string;
  };
};
type HomeSectionDataMap = {
  notices: StudentNoticeItem[];
  requests: RequestBrief[];
  workflows: StudentWorkflow[];
};
type HomeSectionCacheMap = {
  notices?: HomeDashboardCache["notices"];
  requests?: HomeDashboardCache["requests"];
  workflows?: HomeDashboardCache["workflows"];
};

const HOME_CACHE_KEY_PREFIX = "sip.home.dashboard.cache.v2";
const SECTION_KEYS: HomeSectionKey[] = ["notices", "requests", "workflows"];
const SECTION_LABELS: Record<HomeSectionKey, string> = {
  notices: "通知",
  requests: "申请",
  workflows: "流程",
};

const entries: Array<{
  key: string;
  mark: string;
  tone: "primary" | "blue" | "gold" | "green" | "orange" | "slate";
  label: string;
  desc: string;
  url: string;
}> = [
  {
    key: "my-requests",
    mark: "申",
    tone: "primary",
    label: "我的申请",
    desc: "发起请假、证明、盖章等常见申请。",
    url: "/pages/request/index",
  },
  {
    key: "certificate-request",
    mark: "绩",
    tone: "blue",
    label: "成绩证明",
    desc: "查看学业辅助提示与证明办理入口。",
    url: "/pages/request/create?category=CERTIFICATE&type_code=CERTIFICATE_IN_SCHOOL",
  },
  {
    key: "honor-public",
    mark: "奖",
    tone: "gold",
    label: "荣誉公示",
    desc: "查看学院荣誉公示与历史荣誉信息。",
    url: "/pages/honor/index",
  },
  {
    key: "leave-request",
    mark: "假",
    tone: "green",
    label: "请假审批",
    desc: "进入事务申请并选择请假类服务。",
    url: "/pages/request/create?category=LEAVE&type_code=LEAVE_PERSONAL",
  },
  {
    key: "service-request-list",
    mark: "事",
    tone: "slate",
    label: "事务办理",
    desc: "进入事务申请列表查看可办理事项。",
    url: "/pages/request/index",
  },
  {
    key: "policy-query",
    mark: "费",
    tone: "orange",
    label: "政策查询",
    desc: "查询政策说明、办理指引和服务指南。",
    url: "/pages/knowledge/index",
  },
  {
    key: "course-service",
    mark: "课",
    tone: "blue",
    label: "课程事务",
    desc: "课程、培养方案和教务政策查询。",
    url: "/pages/knowledge/index",
  },
  {
    key: "help-center",
    mark: "问",
    tone: "primary",
    label: "帮助中心",
    desc: "查询常见问题和办理指引。",
    url: "/pages/knowledge/index",
  },
];

const shortcutEntries = [
  {
    key: "academic-analysis",
    mark: "学",
    tone: "blue",
    label: "学业分析",
    desc: "上传成绩单 PDF，查看学业缺口与候选课程。",
    url: "/pages/academic/index",
  },
  {
    key: "template-library",
    mark: "模",
    tone: "gold",
    label: "常用模板",
    desc: "查看模板下载与官方来源信息。",
    url: "/pages/knowledge/index",
  },
  {
    key: "progress-center",
    mark: "进",
    tone: "green",
    label: "进度中心",
    desc: "聚合申请与党团流程，查看当前步骤。",
    url: "/pages/progress/index",
  },
] as const;

const recentNotices = ref<StudentNoticeItem[]>([]);
const workflows = ref<StudentWorkflow[]>([]);
const requests = ref<RequestBrief[]>([]);
const displayName = ref("同学");
const dashboardRefreshing = ref(false);
const cacheHydrated = ref(false);
const activeCacheScope = ref("");
const sectionMeta = reactive<Record<HomeSectionKey, HomeSectionMeta>>({
  notices: {
    loading: false,
    error: "",
    fromCache: false,
    hasLoaded: false,
    lastSuccessAt: "",
  },
  requests: {
    loading: false,
    error: "",
    fromCache: false,
    hasLoaded: false,
    lastSuccessAt: "",
  },
  workflows: {
    loading: false,
    error: "",
    fromCache: false,
    hasLoaded: false,
    lastSuccessAt: "",
  },
});

const greeting = computed(() => {
  const hour = new Date().getHours();
  if (hour < 11) return "上午好";
  if (hour < 14) return "中午好";
  if (hour < 19) return "下午好";
  return "晚上好";
});
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
const isAnySectionLoading = computed(
  () =>
    dashboardRefreshing.value ||
    SECTION_KEYS.some((key) => sectionMeta[key].loading),
);
const cachedSections = computed(() =>
  SECTION_KEYS.filter((key) => sectionMeta[key].fromCache),
);
const failedSections = computed(() =>
  SECTION_KEYS.filter((key) => !!sectionMeta[key].error),
);
const todoSectionUnavailable = computed(
  () =>
    ["requests", "workflows"].every(
      (key) =>
        !!sectionMeta[key as HomeSectionKey].error &&
        !sectionMeta[key as HomeSectionKey].hasLoaded,
    ),
);
const noticeSectionUnavailable = computed(
  () => !!sectionMeta.notices.error && !sectionMeta.notices.hasLoaded,
);
const syncStatusTitle = computed(() => {
  if (isAnySectionLoading.value) return "数据同步中";
  if (failedSections.value.length && cachedSections.value.length) {
    return "展示最近成功数据";
  }
  if (failedSections.value.length) return "部分数据暂不可用";
  if (cachedSections.value.length) return "展示最近成功数据";
  return "数据同步正常";
});
const syncStatusDescription = computed(() => {
  const latestSuccessAt = getLatestSuccessAt();
  if (!latestSuccessAt) {
    return "尚未成功同步首页数据，可点击右侧刷新重试。";
  }
  const messages = [
    `${cachedSections.value.length ? "最近成功同步" : "最近同步时间"}：${formatDateTime(latestSuccessAt)}`,
  ];
  if (cachedSections.value.length) {
    messages.push(`${formatSectionNames(cachedSections.value)} 当前显示缓存数据`);
  }
  const unavailableSections = failedSections.value.filter(
    (key) => !sectionMeta[key].hasLoaded,
  );
  if (unavailableSections.length) {
    messages.push(`${formatSectionNames(unavailableSections)} 暂未拉取成功`);
  }
  return messages.join(" · ");
});
const todoNotice = computed<HomeSectionNotice | null>(() => {
  const errors = ["requests", "workflows"].filter(
    (key) => !!sectionMeta[key as HomeSectionKey].error,
  ) as HomeSectionKey[];
  const cached = ["requests", "workflows"].filter(
    (key) => sectionMeta[key as HomeSectionKey].fromCache,
  ) as HomeSectionKey[];

  if (errors.length === 0 && cached.length === 0) return null;
  if (todoSectionUnavailable.value) {
    return {
      tone: "error",
      title: "待办提醒暂不可用",
      description: `${formatSectionNames(errors)} 加载失败，可点击重试重新同步。`,
    };
  }
  if (errors.length) {
    return {
      tone: "warning",
      title: "待办提醒未完全更新",
      description: `${formatSectionNames(errors)} 刷新失败，当前保留最近成功数据。`,
    };
  }
  return {
    tone: "info",
    title: "待办提醒当前显示缓存",
    description: `${formatSectionNames(cached)} 暂未完成实时同步，请稍后重试。`,
  };
});
const noticeSectionNotice = computed<HomeSectionNotice | null>(() => {
  if (!sectionMeta.notices.error && !sectionMeta.notices.fromCache) return null;
  if (noticeSectionUnavailable.value) {
    return {
      tone: "error",
      title: "通知暂不可用",
      description: `${sectionMeta.notices.error || "通知列表加载失败"}，可点击重试重新同步。`,
    };
  }
  if (sectionMeta.notices.error) {
    return {
      tone: "warning",
      title: "通知未完全更新",
      description: "通知同步失败，当前保留最近成功数据。",
    };
  }
  return {
    tone: "info",
    title: "通知当前显示缓存",
    description: "弱网下已回退到最近成功数据，请留意同步时间。",
  };
});

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

function formatSectionNames(keys: HomeSectionKey[]) {
  return keys.map((key) => SECTION_LABELS[key]).join("、");
}

function isUnread(notice: StudentNoticeItem) {
  return !notice.read_at;
}

function noticeKey(notice: StudentNoticeItem) {
  return notice.delivery_id == null ? notice.id : notice.delivery_id;
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

function formatDateTime(value?: string | null) {
  if (!value) return "";
  const normalized = value.replace("T", " ").replace("Z", "");
  return normalized.length >= 16 ? normalized.slice(0, 16) : normalized;
}

function getDashboardCacheScope() {
  const auth = useAuthStore();
  if (auth.user?.student_id) return `student:${auth.user.student_id}`;
  if (auth.user?.id) return `user:${auth.user.id}`;
  return "anonymous";
}

function getDashboardCacheKey() {
  return `${HOME_CACHE_KEY_PREFIX}:${getDashboardCacheScope()}`;
}

function getLatestSuccessAt() {
  const timestamps = SECTION_KEYS
    .map((key) => sectionMeta[key].lastSuccessAt)
    .filter(Boolean)
    .map((value) => new Date(value).getTime())
    .filter((value) => Number.isFinite(value));
  if (!timestamps.length) return "";
  return new Date(Math.max(...timestamps)).toISOString();
}

function readDashboardCache(): HomeDashboardCache {
  const raw = uni.getStorageSync(getDashboardCacheKey());
  if (!raw || typeof raw !== "string") return {};
  try {
    const parsed = JSON.parse(raw) as HomeDashboardCache;
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function writeDashboardCache(cache: HomeDashboardCache) {
  uni.setStorageSync(getDashboardCacheKey(), JSON.stringify(cache));
}

function setSectionItems<K extends HomeSectionKey>(
  key: K,
  items: HomeSectionDataMap[K],
) {
  if (key === "notices") {
    recentNotices.value = items as StudentNoticeItem[];
    return;
  }
  if (key === "requests") {
    requests.value = items as RequestBrief[];
    return;
  }
  workflows.value = items as StudentWorkflow[];
}

function applyCachedSection<K extends HomeSectionKey>(
  key: K,
  cache: HomeSectionCacheMap[K],
) {
  if (!cache || !Array.isArray(cache.items) || !cache.syncedAt) return;
  setSectionItems(key, cache.items as HomeSectionDataMap[K]);
  sectionMeta[key].fromCache = true;
  sectionMeta[key].hasLoaded = true;
  sectionMeta[key].lastSuccessAt = cache.syncedAt;
}

function hydrateDashboardCache() {
  if (cacheHydrated.value) return;
  const cache = readDashboardCache();
  applyCachedSection("notices", cache.notices);
  applyCachedSection("requests", cache.requests);
  applyCachedSection("workflows", cache.workflows);
  cacheHydrated.value = true;
}

function clearDashboardData() {
  recentNotices.value = [];
  requests.value = [];
  workflows.value = [];
  SECTION_KEYS.forEach((key) => {
    sectionMeta[key].loading = false;
    sectionMeta[key].error = "";
    sectionMeta[key].fromCache = false;
    sectionMeta[key].hasLoaded = false;
    sectionMeta[key].lastSuccessAt = "";
  });
}

function persistSectionCache<K extends HomeSectionKey>(
  key: K,
  items: HomeSectionDataMap[K],
  syncedAt: string,
) {
  const cache = readDashboardCache();
  cache[key] = {
    items,
    syncedAt,
  } as HomeDashboardCache[K];
  writeDashboardCache(cache);
}

function markSectionSuccess<K extends HomeSectionKey>(
  key: K,
  items: HomeSectionDataMap[K],
) {
  const syncedAt = new Date().toISOString();
  setSectionItems(key, items);
  sectionMeta[key].error = "";
  sectionMeta[key].fromCache = false;
  sectionMeta[key].hasLoaded = true;
  sectionMeta[key].lastSuccessAt = syncedAt;
  persistSectionCache(key, items, syncedAt);
}

async function syncDisplayName() {
  let auth: ReturnType<typeof useAuthStore> | null = null;
  try {
    auth = useAuthStore();
    if (auth.user && !auth.user.student_id) {
      displayName.value = "访客";
      return;
    }
    if (auth.user?.display_name) {
      displayName.value = auth.user.display_name;
      return;
    }
  } catch {
    auth = null;
  }

  if (auth && !auth.user) {
    try {
      const user = await auth.fetchMe();
      if (user && !user.student_id) {
        displayName.value = "访客";
        return;
      }
      if (user?.display_name) {
        displayName.value = user.display_name;
      }
    } catch {
      // ignore profile fetch failures on home hydration
    }
  }
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

async function refreshSection(key: HomeSectionKey) {
  sectionMeta[key].loading = true;
  try {
    if (key === "notices") {
      const response = await getMyNotices({ page: 1, size: 5 });
      markSectionSuccess("notices", response.data.items || []);
      return;
    }
    if (key === "requests") {
      const response = await getMyRequests({ page: 1, size: 20 });
      markSectionSuccess("requests", response.data.items || []);
      return;
    }
    const response = await getMyWorkflows();
    markSectionSuccess("workflows", response.data || []);
  } catch (error) {
    sectionMeta[key].error = getErrorMessage(
      error,
      `${SECTION_LABELS[key]}同步失败`,
    );
    sectionMeta[key].fromCache = sectionMeta[key].hasLoaded;
  } finally {
    sectionMeta[key].loading = false;
  }
}

async function refreshTodoSections() {
  await Promise.all([
    refreshSection("requests"),
    refreshSection("workflows"),
  ]);
}

async function loadDashboard() {
  dashboardRefreshing.value = true;
  try {
    await syncDisplayName();
    const auth = useAuthStore();
    const nextScope = getDashboardCacheScope();
    if (nextScope !== activeCacheScope.value) {
      clearDashboardData();
      cacheHydrated.value = false;
      activeCacheScope.value = nextScope;
    }
    if (!auth.isLoggedIn || !auth.user?.student_id) {
      clearDashboardData();
      return;
    }
    hydrateDashboardCache();
    await Promise.all([
      refreshSection("notices"),
      refreshSection("requests"),
      refreshSection("workflows"),
    ]);
  } finally {
    dashboardRefreshing.value = false;
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
  padding: 0 24rpx 34rpx;
  background:
    linear-gradient(180deg, #b70f24 0, #b70f24 372rpx, #fff7f7 612rpx, #f8f3f4 100%),
    var(--bg-color);
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.hero-card {
  position: relative;
  min-height: 416rpx;
  padding: 44rpx 32rpx 108rpx;
  border-radius: 0 0 42rpx 42rpx;
  background:
    linear-gradient(90deg, rgba(127, 23, 34, 0.18), transparent 42%),
    radial-gradient(circle at 16% 18%, rgba(255,255,255,0.18), transparent 34%),
    radial-gradient(circle at 92% 8%, rgba(255,255,255,0.14), transparent 30%),
    linear-gradient(150deg, #c40e25 0%, #b70f24 48%, #8b1020 100%);
  color: #fff;
  box-shadow: 0 20rpx 46rpx rgba(127, 23, 34, 0.2);
  overflow: hidden;
  margin: 0 -24rpx;
}

.hero-card::before,
.hero-card::after {
  content: '';
  position: absolute;
  inset: auto auto 26rpx 34rpx;
  width: 360rpx;
  height: 360rpx;
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
  font-size: 42rpx;
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
  margin-top: 34rpx;
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
  font-size: 46rpx;
  font-weight: 800;
  line-height: 1.2;
}

.hero-subtitle {
  display: block;
  margin-top: 12rpx;
  font-size: 28rpx;
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
  position: absolute;
  z-index: 1;
  right: 18rpx;
  bottom: 26rpx;
  width: 286rpx;
  height: 282rpx;
  pointer-events: none;
}

.hero-student {
  width: 100%;
  height: 100%;
}

.hero-building {
  position: absolute;
  right: 160rpx;
  bottom: 34rpx;
  width: 360rpx;
  height: 150rpx;
  opacity: 0.24;
  background:
    linear-gradient(180deg, transparent 0, transparent 48rpx, rgba(255, 255, 255, 0.4) 48rpx, rgba(255, 255, 255, 0.4) 52rpx, transparent 52rpx),
    repeating-linear-gradient(90deg, rgba(255, 255, 255, 0.3) 0 12rpx, transparent 12rpx 26rpx),
    linear-gradient(180deg, rgba(255, 255, 255, 0.26), rgba(255, 255, 255, 0.12));
  clip-path: polygon(0 100%, 0 56%, 10% 44%, 18% 50%, 28% 36%, 40% 44%, 52% 30%, 64% 40%, 72% 28%, 82% 34%, 92% 20%, 100% 24%, 100% 100%);
}

.sync-card {
  position: relative;
  z-index: 2;
  margin-top: -70rpx;
  padding: 24rpx 26rpx;
  border-radius: 22rpx;
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
  min-height: 154rpx;
  padding: 22rpx 18rpx 18rpx;
  border-radius: 18rpx;
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
  margin-top: 12rpx;
  font-size: 42rpx;
  font-weight: 800;
  color: #b70f24;
}

.metric-label {
  display: block;
  font-size: 24rpx;
  color: #6a4b55;
}

.metric-line {
  width: 42rpx;
  height: 5rpx;
  margin-top: 14rpx;
  border-radius: 999rpx;
  background: currentColor;
  opacity: 0.28;
}

.metric-helper {
  display: none;
}

.section-card {
  padding: 30rpx 24rpx 28rpx;
  border-radius: 22rpx;
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

.section-subtitle {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #8b7280;
}

.section-link {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 10rpx;
  font-size: 24rpx;
  color: #b2959e;
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.section-action {
  flex-shrink: 0;
  font-size: 22rpx;
  color: #b2959e;
}

.entry-grid {
  display: flex;
  flex-wrap: wrap;
  row-gap: 30rpx;
}

.priority-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16rpx;
}

.priority-card {
  padding: 20rpx 16rpx 18rpx;
  border-radius: 20rpx;
  background: #fff;
  border: 1rpx solid #f0e2e5;
  box-shadow: var(--shadow-soft);
}

.priority-mark {
  width: 72rpx;
  height: 72rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid rgba(240, 226, 229, 0.92);
  box-shadow: 0 12rpx 24rpx rgba(41, 18, 23, 0.08);
  color: var(--primary-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 900;
  letter-spacing: 0;
}

.priority-mark.primary {
  background: linear-gradient(135deg, rgba(183, 15, 36, 0.12), rgba(255, 255, 255, 0.96));
  border-color: rgba(183, 15, 36, 0.16);
  color: var(--primary-color);
}

.priority-mark.blue {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.12), rgba(255, 255, 255, 0.96));
  border-color: rgba(37, 99, 235, 0.18);
  color: var(--accent-blue);
}

.priority-mark.gold {
  background: linear-gradient(135deg, rgba(215, 154, 43, 0.16), rgba(255, 255, 255, 0.96));
  border-color: rgba(215, 154, 43, 0.22);
  color: var(--accent-gold);
}

.priority-mark.green {
  background: linear-gradient(135deg, rgba(22, 163, 74, 0.12), rgba(255, 255, 255, 0.96));
  border-color: rgba(22, 163, 74, 0.18);
  color: var(--accent-green);
}

.priority-mark.orange {
  background: linear-gradient(135deg, rgba(234, 122, 34, 0.14), rgba(255, 255, 255, 0.96));
  border-color: rgba(234, 122, 34, 0.2);
  color: var(--accent-orange);
}

.priority-mark.slate {
  background: linear-gradient(135deg, rgba(51, 65, 85, 0.1), rgba(255, 255, 255, 0.96));
  border-color: rgba(51, 65, 85, 0.16);
  color: rgba(51, 65, 85, 0.9);
}

.priority-label {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  font-weight: 700;
  color: #1f2937;
}

.priority-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 20rpx;
  line-height: 1.5;
  color: #8b7280;
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
  width: 78rpx;
  height: 78rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid rgba(240, 226, 229, 0.92);
  box-shadow: 0 14rpx 30rpx rgba(41, 18, 23, 0.12);
  color: var(--primary-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 900;
  letter-spacing: 2rpx;
}

.entry-mark.primary {
  background: linear-gradient(135deg, rgba(183, 15, 36, 0.12), rgba(255, 255, 255, 0.96));
  border-color: rgba(183, 15, 36, 0.16);
  color: var(--primary-color);
}

.entry-mark.blue {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.12), rgba(255, 255, 255, 0.96));
  border-color: rgba(37, 99, 235, 0.18);
  color: var(--accent-blue);
}

.entry-mark.gold {
  background: linear-gradient(135deg, rgba(215, 154, 43, 0.16), rgba(255, 255, 255, 0.96));
  border-color: rgba(215, 154, 43, 0.22);
  color: var(--accent-gold);
}

.entry-mark.green {
  background: linear-gradient(135deg, rgba(22, 163, 74, 0.12), rgba(255, 255, 255, 0.96));
  border-color: rgba(22, 163, 74, 0.18);
  color: var(--accent-green);
}

.entry-mark.orange {
  background: linear-gradient(135deg, rgba(234, 122, 34, 0.14), rgba(255, 255, 255, 0.96));
  border-color: rgba(234, 122, 34, 0.2);
  color: var(--accent-orange);
}

.entry-mark.slate {
  background: linear-gradient(135deg, rgba(51, 65, 85, 0.1), rgba(255, 255, 255, 0.96));
  border-color: rgba(51, 65, 85, 0.16);
  color: rgba(51, 65, 85, 0.9);
}

.entry-label {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  color: #374151;
  text-align: center;
  line-height: 1.45;
}

.entry-desc {
  display: block;
  margin-top: 6rpx;
  max-width: 152rpx;
  font-size: 20rpx;
  line-height: 1.55;
  color: #9b8b90;
  text-align: center;
  overflow: hidden;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
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
  width: 44rpx;
  height: 44rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
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
  width: 44rpx;
  height: 44rpx;
  display: flex;
  align-items: center;
  justify-content: center;
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

:deep(.notice.compact) {
  margin-bottom: 18rpx;
}
</style>
