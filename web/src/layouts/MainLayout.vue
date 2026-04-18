<template>
  <a-layout class="main-layout">
    <a-layout-sider
      v-model:collapsed="app.siderCollapsed"
      :trigger="null"
      collapsible
      :width="230"
      class="app-sider"
    >
      <div class="app-logo">
        <span v-if="!app.siderCollapsed">信息学院 · 综合服务</span>
        <span v-else>SIP</span>
      </div>
      <a-menu
        v-model:selectedKeys="selectedKeys"
        v-model:openKeys="openKeys"
        mode="inline"
        theme="dark"
        :items="menuItems"
        @click="onMenuClick"
      />
    </a-layout-sider>

    <a-layout>
      <a-layout-header class="app-header">
        <a-button type="text" class="collapse-btn" @click="app.toggleSider">
          <menu-fold-outlined v-if="!app.siderCollapsed" />
          <menu-unfold-outlined v-else />
        </a-button>
        <div class="header-spacer" />
        <a-dropdown>
          <span class="user-chip">
            <a-avatar size="small">{{ initials }}</a-avatar>
            <span class="nick">{{ auth.user?.display_name || '未登录' }}</span>
          </span>
          <template #overlay>
            <a-menu @click="onUserMenu">
              <a-menu-item key="profile">个人信息</a-menu-item>
              <a-menu-item key="logout">退出登录</a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </a-layout-header>

      <a-layout-content class="app-content">
        <router-view />
      </a-layout-content>

      <a-layout-footer class="app-footer">
        © {{ year }} 信息学院 · Student Integrated Platform
      </a-layout-footer>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { computed, h, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DashboardOutlined,
  SolutionOutlined,
  ReadOutlined,
  NotificationOutlined,
  ImportOutlined,
  TeamOutlined,
  AuditOutlined,
  TrophyOutlined,
  BranchesOutlined,
} from '@ant-design/icons-vue'
import type { ItemType } from 'ant-design-vue'
import { useAuthStore } from '@/store/auth'
import { useAppStore } from '@/store/app'
import { hasAnyRole } from '@/utils/permission'

const auth = useAuthStore()
const app = useAppStore()
const route = useRoute()
const router = useRouter()

const year = new Date().getFullYear()
const initials = computed(() => (auth.user?.display_name || '?').slice(0, 1))

type Item = ItemType & { roles?: string[] }

const rawMenu: Item[] = [
  { key: '/dashboard', icon: () => h(DashboardOutlined), label: '运营看板', roles: ['SUPER_ADMIN', 'COLLEGE_LEADER'] },
  { key: '/approval/workbench', icon: () => h(SolutionOutlined), label: '审批工作台' },
  { key: '/workflow/party-stage', icon: () => h(BranchesOutlined), label: '党团流程' },
  {
    key: '/workflow/quiz-bank',
    icon: () => h(ReadOutlined),
    label: '理论自测题库',
    roles: ['SUPER_ADMIN', 'COUNSELOR', 'HEAD_TEACHER', 'YOUTH_LEAGUE_TEACHER', 'PARTY_BUILD_TEACHER'],
  },
  { key: '/knowledge/entries', icon: () => h(ReadOutlined), label: '知识库管理' },
  { key: '/notice/list', icon: () => h(NotificationOutlined), label: '通知中心' },
  { key: '/exchange/import', icon: () => h(ImportOutlined), label: '导入导出', roles: ['SUPER_ADMIN', 'COUNSELOR'] },
  { key: '/academic/curriculum', icon: () => h(ReadOutlined), label: '培养方案' },
  { key: '/honor/list', icon: () => h(TrophyOutlined), label: '荣誉公示' },
  { key: '/system/users', icon: () => h(TeamOutlined), label: '用户管理', roles: ['SUPER_ADMIN'] },
  { key: '/audit/log', icon: () => h(AuditOutlined), label: '审计日志', roles: ['SUPER_ADMIN', 'COLLEGE_LEADER'] },
]

const menuItems = computed<ItemType[]>(() =>
  rawMenu.filter((m) => hasAnyRole(auth.roleCodes, (m as Item).roles)) as ItemType[],
)

const selectedKeys = ref<string[]>([route.path])
const openKeys = ref<string[]>([])

watch(
  () => route.path,
  (p) => {
    const match = rawMenu.find((m) => p.startsWith(String(m.key)))
    if (match) selectedKeys.value = [String(match.key)]
  },
  { immediate: true },
)

function onMenuClick({ key }: { key: string }) {
  router.push(key)
}

function onUserMenu({ key }: { key: string }) {
  if (key === 'logout') {
    auth.logout()
    router.replace('/login')
  } else if (key === 'profile') {
    router.push('/profile')
  }
}
</script>

<style lang="scss" scoped>
.main-layout {
  min-height: 100vh;
}
.app-sider {
  background: #1e293b !important;
}
.app-logo {
  color: #fff;
  font-weight: 600;
  letter-spacing: 1px;
  text-align: center;
  padding: 18px 8px;
  background: #0f172a;
}
.app-header {
  background: #fff;
  padding: 0 16px;
  display: flex;
  align-items: center;
  box-shadow: 0 1px 0 rgba(0, 0, 0, 0.06);
  .collapse-btn {
    font-size: 18px;
  }
  .header-spacer {
    flex: 1;
  }
  .user-chip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    .nick {
      color: rgba(0, 0, 0, 0.72);
    }
  }
}
.app-content {
  margin: 16px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  min-height: 280px;
}
.app-footer {
  text-align: center;
  background: transparent;
  color: rgba(0, 0, 0, 0.45);
}
</style>
