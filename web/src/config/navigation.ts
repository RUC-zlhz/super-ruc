import {
  DashboardOutlined,
  InboxOutlined,
  BranchesOutlined,
  BookOutlined,
  ReadOutlined,
  NotificationOutlined,
  ImportOutlined,
  TeamOutlined,
  SafetyOutlined,
  TrophyOutlined,
} from "@ant-design/icons-vue";
import { hasAnyRole } from "@/utils/permission";

export type NavLeaf = {
  key: string;
  label: string;
  icon: any;
  badge?: number | null;
  roles?: string[];
};

export type NavGroup = {
  group: string;
  items: NavLeaf[];
};

export const NAV_GROUPS: NavGroup[] = [
  {
    group: "概览",
    items: [
      {
        key: "/dashboard",
        label: "运营看板",
        icon: DashboardOutlined,
        roles: ["SUPER_ADMIN", "COLLEGE_LEADER"],
      },
    ],
  },
  {
    group: "审批",
    items: [
      { key: "/approval/workbench", label: "审批工作台", icon: InboxOutlined },
      {
        key: "/workflow/party-stage",
        label: "党团流程管理",
        icon: BranchesOutlined,
      },
    ],
  },
  {
    group: "内容",
    items: [
      { key: "/notice/list", label: "通知中心", icon: NotificationOutlined },
      { key: "/knowledge/entries", label: "知识库管理", icon: BookOutlined },
      {
        key: "/workflow/quiz-bank",
        label: "理论自测题库",
        icon: ReadOutlined,
        roles: [
          "SUPER_ADMIN",
          "COUNSELOR",
          "HEAD_TEACHER",
          "YOUTH_LEAGUE_TEACHER",
          "PARTY_BUILD_TEACHER",
        ],
      },
      { key: "/academic/curriculum", label: "培养方案管理", icon: ReadOutlined },
      { key: "/honor/list", label: "荣誉公示管理", icon: TrophyOutlined },
    ],
  },
  {
    group: "系统",
    items: [
      {
        key: "/exchange/import",
        label: "导入导出中心",
        icon: ImportOutlined,
        roles: ["SUPER_ADMIN", "COUNSELOR"],
      },
      {
        key: "/system/users",
        label: "用户管理",
        icon: TeamOutlined,
        roles: ["SUPER_ADMIN", "COLLEGE_LEADER", "COUNSELOR", "HEAD_TEACHER"],
      },
      {
        key: "/audit/log",
        label: "审计日志",
        icon: SafetyOutlined,
        roles: ["SUPER_ADMIN", "COLLEGE_LEADER"],
      },
    ],
  },
];

export function getVisibleNavGroups(userRoles: string[]): NavGroup[] {
  return NAV_GROUPS
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => hasAnyRole(userRoles, item.roles)),
    }))
    .filter((group) => group.items.length);
}

export function getDefaultRouteForRoles(userRoles: string[]): string {
  const firstVisible = getVisibleNavGroups(userRoles).flatMap((group) => group.items)[0];
  return firstVisible?.key || "/profile";
}
