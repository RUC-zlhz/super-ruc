import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { hasAnyRole } from '@/utils/permission'

const MainLayout = () => import('@/layouts/MainLayout.vue')
const BlankLayout = () => import('@/layouts/BlankLayout.vue')

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true, title: '登录' },
  },
  {
    path: '/',
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/views/dashboard/OperationDashboard.vue'),
        meta: { title: '运营看板', roles: ['SUPER_ADMIN', 'COLLEGE_LEADER'] },
      },
      {
        path: 'approval/workbench',
        name: 'approval-workbench',
        component: () => import('@/views/approval/WorkbenchList.vue'),
        meta: { title: '审批工作台' },
      },
      {
        path: 'approval/:id',
        name: 'approval-detail',
        component: () => import('@/views/approval/ApprovalDetail.vue'),
        meta: { title: '审批详情' },
      },
      {
        path: 'workflow/party-stage',
        name: 'workflow-stage',
        component: () => import('@/views/workflow/PartyStageList.vue'),
        meta: { title: '党团流程' },
      },
      {
        path: 'knowledge/entries',
        name: 'knowledge-entries',
        component: () => import('@/views/knowledge/EntryList.vue'),
        meta: { title: '知识条目' },
      },
      {
        path: 'notice/list',
        name: 'notice-list',
        component: () => import('@/views/notice/NoticeList.vue'),
        meta: { title: '通知中心' },
      },
      {
        path: 'exchange/import',
        name: 'exchange-import',
        component: () => import('@/views/exchange/ImportCenter.vue'),
        meta: { title: '导入中心', roles: ['SUPER_ADMIN', 'COUNSELOR'] },
      },
      {
        path: 'academic/curriculum',
        name: 'academic-curriculum',
        component: () => import('@/views/academic/CurriculumRules.vue'),
        meta: { title: '培养方案' },
      },
      {
        path: 'honor/list',
        name: 'honor-list',
        component: () => import('@/views/honor/HonorList.vue'),
        meta: { title: '荣誉公示' },
      },
      {
        path: 'system/users',
        name: 'system-users',
        component: () => import('@/views/system/UserManage.vue'),
        meta: { title: '用户管理', roles: ['SUPER_ADMIN'] },
      },
      {
        path: 'audit/log',
        name: 'audit-log',
        component: () => import('@/views/audit/AuditLog.vue'),
        meta: { title: '审计日志', roles: ['SUPER_ADMIN', 'COLLEGE_LEADER'] },
      },
      {
        path: 'profile',
        name: 'profile',
        component: () => import('@/views/Profile.vue'),
        meta: { title: '个人信息' },
      },
      {
        path: 'profile/student/:studentId',
        name: 'student-profile',
        component: () => import('@/views/profile/StudentProfile.vue'),
        meta: { title: '学生画像', roles: ['SUPER_ADMIN', 'COLLEGE_LEADER', 'COUNSELOR', 'HEAD_TEACHER'] },
      },
    ],
  },
  {
    path: '/error',
    component: BlankLayout,
    children: [
      {
        path: '403',
        name: 'forbidden',
        component: () => import('@/views/error/Forbidden.vue'),
        meta: { public: true, title: '无权限' },
      },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.meta.public) return true

  if (!auth.isAuthenticated) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (!auth.user) {
    try {
      await auth.fetchMe()
    } catch {
      auth.logout()
      return { path: '/login', query: { redirect: to.fullPath } }
    }
  }
  const requiredRoles = (to.meta.roles as string[] | undefined) ?? undefined
  if (!hasAnyRole(auth.roleCodes, requiredRoles)) {
    return { path: '/error/403' }
  }
  return true
})

export default router
