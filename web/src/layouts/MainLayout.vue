<template>
  <div class="app-shell" :class="{ collapsed: app.siderCollapsed }">
    <aside class="sider">
      <div class="sider-brand">
        <div class="logo-mark">R</div>
        <div v-if="!app.siderCollapsed" class="logo-text">
          <div class="t1">中国人民大学</div>
          <div class="t2">教师管理员后台</div>
        </div>
      </div>

      <nav class="sider-nav">
        <template v-if="!app.siderCollapsed && favItems.length && !search">
          <div class="sider-group">常用置顶</div>
          <NavItem
            v-for="it in favItems"
            :key="'fav-' + it.key"
            :item="it"
            :active="activeKey === it.key"
            :is-fav="true"
            :collapsed="app.siderCollapsed"
            @nav="go(it.key)"
            @toggle-fav="toggleFav(it.key)"
          />
        </template>

        <template v-for="group in filteredGroups" :key="group.group">
          <div v-if="!app.siderCollapsed" class="sider-group">
            {{ group.group }}
          </div>
          <NavItem
            v-for="it in group.items"
            :key="it.key"
            :item="it"
            :active="activeKey === it.key"
            :is-fav="favs.includes(it.key)"
            :collapsed="app.siderCollapsed"
            @nav="go(it.key)"
            @toggle-fav="toggleFav(it.key)"
          />
        </template>

        <div v-if="!app.siderCollapsed && search && !hasFilteredResults" class="sider-empty">
          <div class="sider-empty-title">无匹配菜单</div>
          <div class="sider-empty-desc">请尝试搜索页面中文名、模块名或路由片段。</div>
        </div>
      </nav>

      <div class="sider-watermark" />

      <div class="sider-foot">
        <span class="foot-logo">RUC</span>
        <span v-if="!app.siderCollapsed">立学为民 · 治学报国</span>
      </div>
    </aside>

    <div class="main">
      <header class="topbar">
        <button class="icon-btn light" title="折叠侧边栏" @click="app.toggleSider">
          <MenuOutlined />
        </button>

        <div class="topbar-title">
          <span class="topbar-seal">R</span>
          <span>教师管理员管理平台</span>
        </div>

        <div class="topbar-search">
          <SearchOutlined />
          <input
            ref="searchInputRef"
            v-model="search"
            placeholder="搜索功能、菜单、数据..."
          />
          <kbd>{{ shortcutLabel }}</kbd>
        </div>

        <div class="spacer" />

        <button class="icon-btn light" title="刷新" @click="onRefresh">
          <ReloadOutlined />
        </button>

        <button class="icon-btn light bell" title="通知">
          <BellOutlined />
          <span class="notif-dot">12</span>
        </button>

        <a-dropdown>
          <div class="user-chip">
            <span class="avatar">{{ initials }}</span>
            <span class="u-txt">
              <span class="u-name">{{ auth.user?.display_name || "未登录" }}</span>
              <span class="u-role">{{ userRole }}</span>
            </span>
            <DownOutlined class="u-caret" />
          </div>
          <template #overlay>
            <a-menu @click="onUserMenu">
              <a-menu-item key="profile">个人信息</a-menu-item>
              <a-menu-item key="logout">退出登录</a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </header>

      <main class="content">
        <nav class="crumbs">
          <span class="c-home"><HomeOutlined /></span>
          <template v-for="(c, i) in crumbs" :key="i">
            <span class="c-sep"><RightOutlined /></span>
            <span :class="['c-item', { current: i === crumbs.length - 1 }]">
              {{ c }}
            </span>
          </template>
        </nav>
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  defineComponent,
  h,
  nextTick,
  onMounted,
  onUnmounted,
  ref,
  watchEffect,
} from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  BellOutlined,
  DownOutlined,
  HomeOutlined,
  MenuOutlined,
  ReloadOutlined,
  RightOutlined,
  SearchOutlined,
  StarFilled,
  StarOutlined,
} from "@ant-design/icons-vue";
import { useAuthStore } from "@/store/auth";
import { useAppStore } from "@/store/app";
import {
  getVisibleNavGroups,
  type NavGroup,
  type NavLeaf,
} from "@/config/navigation";

const auth = useAuthStore();
const app = useAppStore();
const route = useRoute();
const router = useRouter();

const visibleGroups = computed<NavGroup[]>(() =>
  getVisibleNavGroups(auth.roleCodes),
);

const search = ref("");
const searchInputRef = ref<HTMLInputElement | null>(null);
const shortcutLabel = computed(() => {
  if (typeof navigator === "undefined") return "Ctrl K";
  return navigator.platform.includes("Mac") ? "⌘K" : "Ctrl K";
});

const filteredGroups = computed<NavGroup[]>(() => {
  const q = search.value.trim().toLowerCase();
  if (!q) return visibleGroups.value;
  return visibleGroups.value
    .map((g) => ({
      ...g,
      items: g.items.filter(
        (it) =>
          it.label.toLowerCase().includes(q) ||
          it.key.toLowerCase().includes(q),
      ),
    }))
    .filter((g) => g.items.length);
});

const hasFilteredResults = computed(() =>
  filteredGroups.value.some((group) => group.items.length),
);

const FAV_KEY = "sip.favs";
const favs = ref<string[]>(
  (() => {
    try {
      return JSON.parse(
        localStorage.getItem(FAV_KEY) ||
          '["/approval/workbench","/notice/list"]',
      );
    } catch {
      return [];
    }
  })(),
);
watchEffect(() => localStorage.setItem(FAV_KEY, JSON.stringify(favs.value)));

function toggleFav(key: string) {
  favs.value = favs.value.includes(key)
    ? favs.value.filter((k) => k !== key)
    : [...favs.value, key];
}

const favItems = computed<NavLeaf[]>(() => {
  const flat = visibleGroups.value.flatMap((g) => g.items);
  return favs.value
    .map((k) => flat.find((i) => i.key === k))
    .filter(Boolean) as NavLeaf[];
});

const activeKey = computed(() => {
  const flat = visibleGroups.value.flatMap((g) => g.items);
  const match = flat.find((it) => route.path.startsWith(it.key));
  return match?.key ?? route.path;
});

const initials = computed(() => (auth.user?.display_name || "?").slice(0, 1));

const ROLE_LABEL: Record<string, string> = {
  SUPER_ADMIN: "系统管理员",
  COLLEGE_LEADER: "学院领导",
  COUNSELOR: "辅导员",
  HEAD_TEACHER: "班主任",
  YOUTH_LEAGUE_TEACHER: "团委老师",
  PARTY_BUILD_TEACHER: "党建老师",
  PARTY_BRANCH_SECRETARY: "党支部书记",
  YOUTH_LEAGUE_SECRETARY: "团支书",
  YOUTH_BRANCH_SECRETARY: "团支部书记",
  CLASS_MONITOR: "班长",
  CLASS_LEADER: "班长",
  STUDENT: "学生",
};
const userRole = computed(() => {
  const code = auth.roleCodes[0];
  return (code && ROLE_LABEL[code]) || code || "管理端用户";
});

const CRUMB_OVERRIDE: Record<string, string[]> = {
  "/dashboard": ["首页", "运营看板"],
  "/approval/workbench": ["审批管理", "审批工作台"],
  "/workflow/party-stage": ["流程管理", "党团流程管理"],
  "/notice/list": ["内容管理", "通知中心"],
  "/knowledge/entries": ["内容管理", "知识库管理"],
  "/workflow/quiz-bank": ["内容管理", "理论自测题库"],
  "/academic/curriculum": ["教学管理", "培养方案管理"],
  "/honor/list": ["荣誉管理", "荣誉公示管理"],
  "/exchange/import": ["系统管理", "导入导出中心"],
  "/system/users": ["系统管理", "用户管理"],
  "/audit/log": ["系统管理", "审计日志"],
  "/profile": ["个人中心", "个人信息"],
};
const crumbs = computed(() => {
  const override = CRUMB_OVERRIDE[route.path];
  if (override) return override;
  const title = (route.meta as any)?.title as string | undefined;
  return title ? ["首页", title] : ["首页"];
});

function go(key: string) {
  router.push(key);
}

async function focusSearch() {
  searchInputRef.value?.focus();
  searchInputRef.value?.select();
  if (app.siderCollapsed) {
    app.toggleSider();
    await nextTick();
  }
}

function onKeydown(event: KeyboardEvent) {
  const pressedSearchShortcut =
    (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k";
  if (!pressedSearchShortcut) return;
  event.preventDefault();
  void focusSearch();
}

onMounted(() => {
  window.addEventListener("keydown", onKeydown);
});

onUnmounted(() => {
  window.removeEventListener("keydown", onKeydown);
});

function onRefresh() {
  router.go(0);
}

function onUserMenu({ key }: { key: string | number }) {
  if (key === "logout") {
    auth.logout();
    router.replace("/login");
  } else if (key === "profile") {
    router.push("/profile");
  }
}

const NavItem = defineComponent({
  props: {
    item: { type: Object as () => NavLeaf, required: true },
    active: Boolean,
    isFav: Boolean,
    collapsed: Boolean,
  },
  emits: ["nav", "toggleFav"],
  setup(props, { emit }) {
    return () =>
      h(
        "div",
        {
          class: ["sider-item", { active: props.active }],
          title: props.item.label,
          onClick: () => emit("nav"),
        },
        [
          h("span", { class: "s-icon" }, [h(props.item.icon)]),
          !props.collapsed && h("span", { class: "s-label" }, props.item.label),
          !props.collapsed && props.item.badge
            ? h("span", { class: "s-badge" }, String(props.item.badge))
            : null,
          !props.collapsed &&
            h(
              "span",
              {
                class: ["s-star", { on: props.isFav }],
                onClick: (e: MouseEvent) => {
                  e.stopPropagation();
                  emit("toggleFav");
                },
              },
              [h(props.isFav ? StarFilled : StarOutlined)],
            ),
        ],
      );
  },
});
</script>

<style lang="scss" scoped>
.app-shell {
  display: grid;
  grid-template-columns: 204px minmax(0, 1fr);
  min-height: 100vh;
  background: var(--bg);
  transition: grid-template-columns 0.22s ease;

  &.collapsed {
    grid-template-columns: 64px minmax(0, 1fr);
  }
}

.sider {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  color: var(--nav-ink);
  background:
    radial-gradient(circle at 35% 92%, rgba(255, 255, 255, 0.08), transparent 10rem),
    linear-gradient(180deg, var(--nav-dark) 0%, var(--nav-dark-2) 100%);
  box-shadow: 10px 0 30px rgba(16, 24, 36, 0.08);
}

.sider-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 58px;
  padding: 0 16px;
  background: linear-gradient(135deg, var(--ruc-red-dark), var(--ruc-red));
  color: #fff;
}

.logo-mark,
.topbar-seal {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  border-radius: 999px;
  font-weight: 800;
}

.logo-mark {
  width: 34px;
  height: 34px;
  border: 2px solid rgba(255, 255, 255, 0.72);
  font-size: 16px;
}

.logo-text {
  min-width: 0;
}

.logo-text .t1 {
  color: #fff;
  font-size: 16px;
  font-weight: 800;
  line-height: 1.2;
  white-space: nowrap;
}

.logo-text .t2 {
  margin-top: 3px;
  color: rgba(255, 255, 255, 0.76);
  font-size: 12px;
  white-space: nowrap;
}

.sider-nav {
  flex: 1;
  overflow-y: auto;
  padding: 14px 8px 14px;
}

.sider-group {
  margin: 14px 8px 6px;
  color: var(--nav-muted);
  font-size: 12px;
  font-weight: 700;
}

.sider-empty {
  margin: 18px 10px 0;
  padding: 14px;
  color: var(--nav-muted);
  border: 1px dashed rgba(255, 255, 255, 0.16);
  border-radius: 10px;
}

.sider-empty-title {
  color: #fff;
  font-weight: 700;
}

.sider-empty-desc {
  margin-top: 6px;
  font-size: 12px;
  line-height: 1.6;
}

:deep(.sider-item) {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  height: 38px;
  margin-bottom: 3px;
  padding: 0 10px;
  color: var(--nav-ink);
  border-radius: 8px;
  cursor: pointer;
  transition:
    background 0.16s ease,
    color 0.16s ease,
    transform 0.16s ease;

  &:hover {
    color: #fff;
    background: rgba(255, 255, 255, 0.08);
  }

  &.active {
    color: #fff;
    background: linear-gradient(90deg, var(--ruc-red), #d7192d);
    box-shadow: 0 12px 20px rgba(176, 0, 24, 0.22);

    &::before {
      content: "";
      position: absolute;
      left: -8px;
      top: 7px;
      bottom: 7px;
      width: 4px;
      border-radius: 0 6px 6px 0;
      background: #fff;
    }
  }

  .s-icon {
    display: inline-flex;
    width: 18px;
    height: 18px;
    align-items: center;
    justify-content: center;
    font-size: 17px;
  }

  .s-label {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    font-size: 13px;
    font-weight: 600;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .s-badge {
    min-width: 18px;
    color: #ffd6dc;
    font-size: 11px;
    font-weight: 700;
    text-align: right;
  }

  .s-star {
    display: inline-flex;
    color: rgba(255, 255, 255, 0.46);
    opacity: 0;
  }

  &:hover .s-star,
  .s-star.on {
    opacity: 1;
  }

  .s-star.on {
    color: #ffd66b;
  }
}

.app-shell.collapsed :deep(.sider-item) {
  justify-content: center;
  padding: 0;
}

.sider-watermark {
  height: 88px;
  margin: 0 14px 6px;
  opacity: 0.16;
  background:
    linear-gradient(180deg, transparent, rgba(255, 255, 255, 0.06)),
    repeating-linear-gradient(90deg, transparent 0 12px, rgba(255, 255, 255, 0.24) 12px 13px);
  clip-path: polygon(0 72%, 18% 58%, 31% 66%, 44% 42%, 60% 60%, 73% 36%, 100% 65%, 100% 100%, 0 100%);
}

.sider-foot {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  padding: 0 16px 13px;
  color: var(--nav-muted);
  font-size: 12px;
}

.foot-logo {
  color: rgba(255, 255, 255, 0.7);
  font-weight: 800;
  letter-spacing: 0.8px;
}

.main {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 15;
  display: flex;
  align-items: center;
  gap: 12px;
  height: 58px;
  padding: 0 18px;
  color: #fff;
  background:
    radial-gradient(circle at 28% 10%, rgba(255, 255, 255, 0.16), transparent 16rem),
    linear-gradient(90deg, var(--ruc-red-dark), var(--ruc-red));
  box-shadow: 0 6px 16px rgba(176, 0, 24, 0.14);
}

.topbar-title {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 190px;
  font-size: 17px;
  font-weight: 800;
  white-space: nowrap;
}

.topbar-seal {
  width: 28px;
  height: 28px;
  border: 2px solid rgba(255, 255, 255, 0.72);
  font-size: 13px;
}

.topbar-search {
  display: flex;
  align-items: center;
  gap: 8px;
  width: min(410px, 34vw);
  height: 34px;
  padding: 0 12px;
  color: rgba(255, 255, 255, 0.74);
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 8px;

  input {
    min-width: 0;
    flex: 1;
    color: #fff;
    background: transparent;
    border: 0;
    outline: none;
    font: inherit;

    &::placeholder {
      color: rgba(255, 255, 255, 0.62);
    }
  }

  kbd {
    padding: 1px 7px;
    color: rgba(255, 255, 255, 0.74);
    background: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    font-size: 11px;
  }
}

.spacer {
  flex: 1;
}

.icon-btn {
  position: relative;
  display: grid;
  width: 32px;
  height: 32px;
  place-items: center;
  color: var(--text-2);
  background: transparent;
  border: 0;
  border-radius: 8px;
  cursor: pointer;

  &:hover {
    background: rgba(255, 255, 255, 0.14);
  }
}

.icon-btn.light {
  color: #fff;
}

.notif-dot {
  position: absolute;
  right: -4px;
  top: -3px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  color: #fff;
  background: #f53f3f;
  border: 2px solid var(--ruc-red);
  border-radius: 999px;
  font-size: 10px;
  font-weight: 800;
  line-height: 14px;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 140px;
  padding: 3px 8px 3px 4px;
  color: #fff;
  border-left: 1px solid rgba(255, 255, 255, 0.18);
  cursor: pointer;
}

.avatar {
  display: grid;
  width: 32px;
  height: 32px;
  place-items: center;
  color: var(--ruc-red);
  background: #fff;
  border-radius: 999px;
  font-weight: 800;
}

.u-txt {
  display: flex;
  min-width: 0;
  flex-direction: column;
  line-height: 1.2;
}

.u-name {
  overflow: hidden;
  font-size: 13px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.u-role {
  margin-top: 2px;
  color: rgba(255, 255, 255, 0.68);
  font-size: 11px;
}

.u-caret {
  color: rgba(255, 255, 255, 0.7);
  font-size: 10px;
}

.content {
  width: 100%;
  min-width: 0;
  max-width: none;
  flex: 1;
  padding: 26px 26px 36px;
}

.crumbs {
  display: none;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  color: var(--text-3);
  font-size: 13px;
}

.c-home,
.c-sep {
  display: inline-flex;
}

.c-item.current {
  color: var(--text);
  font-weight: 600;
}

/* Page Transition */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(10px);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

@media (max-width: 1180px) {
  .app-shell {
    grid-template-columns: 72px minmax(0, 1fr);
  }

  .logo-text,
  .sider-group,
  .sider-empty,
  .sider-foot span:not(.foot-logo) {
    display: none;
  }

  .topbar-title {
    min-width: auto;
  }

  .topbar-search {
    width: min(320px, 42vw);
  }
}
</style>
