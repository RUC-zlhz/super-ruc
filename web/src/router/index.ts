import {
  createRouter,
  createWebHistory,
  type RouteRecordRaw,
} from "vue-router";
import { useAuthStore } from "@/store/auth";
import { getDefaultRouteForRoles } from "@/config/navigation";
import { cancelPendingRequests, getAccessToken } from "@/utils/request";
import {
  APPROVER_ROLES,
  AUDIT_VIEWER_ROLES,
  CONTENT_EDITOR_ROLES,
  CURRICULUM_ADMIN_ROLES,
  PROFILE_ADMIN_ROLES,
  REPORT_VIEWER_ROLES,
  SYSTEM_USER_ROLES,
  hasAnyRole,
} from "@/utils/permission";

const MainLayout = () => import("@/layouts/MainLayout.vue");

const enableRequirementsPreview =
  import.meta.env.DEV || import.meta.env.VITE_ENABLE_REQUIREMENT_PREVIEW === "true";

const routes: RouteRecordRaw[] = [
  {
    path: "/login",
    component: () => import("@/views/Login.vue"),
    meta: { public: true, title: "登录" },
  },
  ...(enableRequirementsPreview
    ? [
        {
          path: "/preview/requirements",
          component: () => import("@/views/preview/RequirementsPreview.vue"),
          meta: { public: true, title: "前端预览" },
        },
      ]
    : []),
  {
    path: "/",
    component: MainLayout,
    children: [
      {
        path: "dashboard",
        name: "dashboard",
        component: () => import("@/views/dashboard/OperationDashboard.vue"),
        meta: { title: "运营看板", roles: REPORT_VIEWER_ROLES },
      },
      {
        path: "approval/workbench",
        name: "approval-workbench",
        component: () => import("@/views/approval/WorkbenchList.vue"),
        meta: { title: "审批工作台", roles: APPROVER_ROLES },
      },
      {
        path: "approval/:id",
        name: "approval-detail",
        component: () => import("@/views/approval/ApprovalDetail.vue"),
        meta: { title: "审批详情", roles: APPROVER_ROLES },
      },
      {
        path: "workflow/party-stage",
        name: "workflow-stage",
        component: () => import("@/views/workflow/PartyStageList.vue"),
        meta: {
          title: "党团流程",
          roles: CONTENT_EDITOR_ROLES,
        },
      },
      {
        path: "workflow/quiz-bank",
        name: "workflow-quiz-bank",
        component: () => import("@/views/workflow/QuizBank.vue"),
        meta: {
          title: "理论自测题库",
          roles: CONTENT_EDITOR_ROLES,
        },
      },
      {
        path: "knowledge/entries",
        name: "knowledge-entries",
        component: () => import("@/views/knowledge/EntryList.vue"),
        meta: { title: "知识条目", roles: CONTENT_EDITOR_ROLES },
      },
      {
        path: "notice/list",
        name: "notice-list",
        component: () => import("@/views/notice/NoticeList.vue"),
        meta: { title: "通知中心", roles: CONTENT_EDITOR_ROLES },
      },
      {
        path: "exchange/import",
        name: "exchange-import",
        component: () => import("@/views/exchange/ImportCenter.vue"),
        meta: { title: "导入中心", roles: CURRICULUM_ADMIN_ROLES },
      },
      {
        path: "academic/curriculum",
        name: "academic-curriculum",
        component: () => import("@/views/academic/CurriculumRules.vue"),
        meta: { title: "培养方案", roles: CURRICULUM_ADMIN_ROLES },
      },
      {
        path: "honor/list",
        name: "honor-list",
        component: () => import("@/views/honor/HonorList.vue"),
        meta: { title: "荣誉公示", roles: CONTENT_EDITOR_ROLES },
      },
      {
        path: "system/users",
        name: "system-users",
        component: () => import("@/views/system/UserManage.vue"),
        meta: {
          title: "用户管理",
          roles: SYSTEM_USER_ROLES,
        },
      },
      {
        path: "audit/log",
        name: "audit-log",
        component: () => import("@/views/audit/AuditLog.vue"),
        meta: { title: "审计日志", roles: AUDIT_VIEWER_ROLES },
      },
      {
        path: "profile",
        name: "profile",
        component: () => import("@/views/Profile.vue"),
        meta: { title: "个人信息" },
      },
      {
        path: "profile/student/:studentId",
        name: "student-profile",
        component: () => import("@/views/profile/StudentProfile.vue"),
        meta: {
          title: "学生画像",
          roles: PROFILE_ADMIN_ROLES,
        },
      },
    ],
  },
  {
    path: "/error",
    component: MainLayout,
    children: [
      {
        path: "403",
        name: "forbidden",
        component: () => import("@/views/error/Forbidden.vue"),
        meta: { public: true, title: "无权限" },
      },
    ],
  },
  { path: "/:pathMatch(.*)*", redirect: "/" },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to) => {
  // 离开当前页时取消上一页尚未返回的只读请求，避免迟到响应覆盖新页面
  cancelPendingRequests();
  const auth = useAuthStore();
  if (to.meta.public) {
    if (to.path === "/error/403" && auth.isAuthenticated && !auth.user) {
      try {
        await auth.fetchMe();
      } catch {
        auth.logout();
      }
    }
    return true;
  }

  if (!auth.isAuthenticated) {
    return { path: "/login", query: { redirect: to.fullPath } };
  }
  if (!auth.user) {
    try {
      await auth.fetchMe();
    } catch (e) {
      if (!getAccessToken()) {
        auth.logout();
        return { path: "/login", query: { redirect: to.fullPath } };
      }
      throw e;
    }
  }

  if (to.path === "/") {
    return { path: getDefaultRouteForRoles(auth.roleCodes) };
  }

  const requiredRoles = (to.meta.roles as string[] | undefined) ?? undefined;
  if (!hasAnyRole(auth.roleCodes, requiredRoles)) {
    return { path: "/error/403" };
  }
  return true;
});

// 浏览器标签标题随路由更新：标签页/历史/书签可读出当前页面
const BASE_TITLE = "信息学院管理后台";
router.afterEach((to) => {
  const pageTitle = to.meta.title as string | undefined;
  document.title = pageTitle ? `${pageTitle} · ${BASE_TITLE}` : BASE_TITLE;
});

export default router;
