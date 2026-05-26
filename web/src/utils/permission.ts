/**
 * 前端权限工具（C-03 强调：权限最终判定在后端；前端仅做展示与路由过滤）。
 *
 * 五级角色：
 *   L1 SUPER_ADMIN
 *   L2 COLLEGE_LEADER
 *   L3 COUNSELOR / HEAD_TEACHER / YOUTH_LEAGUE_TEACHER / PARTY_BUILD_TEACHER
 *   L4 PARTY_BRANCH_SECRETARY / YOUTH_LEAGUE_SECRETARY / CLASS_MONITOR
 *   L5 STUDENT
 */
export type RoleCode =
  | "SUPER_ADMIN"
  | "COLLEGE_LEADER"
  | "COUNSELOR"
  | "HEAD_TEACHER"
  | "YOUTH_LEAGUE_TEACHER"
  | "PARTY_BUILD_TEACHER"
  | "PARTY_BRANCH_SECRETARY"
  | "YOUTH_LEAGUE_SECRETARY"
  | "CLASS_MONITOR"
  | "YOUTH_BRANCH_SECRETARY"
  | "CLASS_LEADER"
  | "STUDENT";

export const ROLE_LEVEL: Record<RoleCode, number> = {
  SUPER_ADMIN: 1,
  COLLEGE_LEADER: 2,
  COUNSELOR: 3,
  HEAD_TEACHER: 3,
  YOUTH_LEAGUE_TEACHER: 3,
  PARTY_BUILD_TEACHER: 3,
  PARTY_BRANCH_SECRETARY: 4,
  YOUTH_LEAGUE_SECRETARY: 4,
  CLASS_MONITOR: 4,
  YOUTH_BRANCH_SECRETARY: 4,
  CLASS_LEADER: 4,
  STUDENT: 5,
};

export const COLLABORATOR_ROLES: RoleCode[] = [
  "PARTY_BRANCH_SECRETARY",
  "YOUTH_LEAGUE_SECRETARY",
  "CLASS_MONITOR",
  "YOUTH_BRANCH_SECRETARY",
  "CLASS_LEADER",
];

export const APPROVER_ROLES: RoleCode[] = [
  "SUPER_ADMIN",
  "COLLEGE_LEADER",
  "COUNSELOR",
  "HEAD_TEACHER",
  "YOUTH_LEAGUE_TEACHER",
  "PARTY_BUILD_TEACHER",
  ...COLLABORATOR_ROLES,
];

export const CONTENT_EDITOR_ROLES: RoleCode[] = [...APPROVER_ROLES];

export const CURRICULUM_ADMIN_ROLES: RoleCode[] = [
  "SUPER_ADMIN",
  "COLLEGE_LEADER",
  "COUNSELOR",
  "HEAD_TEACHER",
];

export const PROFILE_ADMIN_ROLES: RoleCode[] = [...CURRICULUM_ADMIN_ROLES];

export const REPORT_VIEWER_ROLES: RoleCode[] = [
  ...CURRICULUM_ADMIN_ROLES,
  "YOUTH_LEAGUE_TEACHER",
  "PARTY_BUILD_TEACHER",
];

export const ADMIN_USER_IMPORT_ROLES: RoleCode[] = [
  ...CURRICULUM_ADMIN_ROLES,
  "YOUTH_LEAGUE_TEACHER",
  "PARTY_BUILD_TEACHER",
];

export const SYSTEM_USER_ROLES: RoleCode[] = [...ADMIN_USER_IMPORT_ROLES];

export const AUDIT_VIEWER_ROLES: RoleCode[] = ["SUPER_ADMIN", "COLLEGE_LEADER"];

export function hasAnyRole(
  userRoles: string[],
  required: string[] | undefined,
): boolean {
  if (!required || required.length === 0) return true;
  if (!userRoles || userRoles.length === 0) return false;
  const set = new Set(userRoles);
  return required.some((r) => set.has(r));
}

export function minLevel(userRoles: string[]): number {
  if (!userRoles?.length) return 99;
  return userRoles.reduce((acc, r) => {
    const l = ROLE_LEVEL[r as RoleCode] ?? 99;
    return Math.min(acc, l);
  }, 99);
}
