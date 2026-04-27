import { get, post } from "@/utils/request";
import type { ApiEnvelope } from "@/utils/request";
import type { Paginated } from "./types";

export interface AuditArchiveSummary {
  moved: number;
  retention_days: number;
  cutoff?: number;
  has_remaining?: number;
}

export interface AuditLogOut {
  id: number;
  event_type: string;
  entity_code: string;
  entity_id?: number | null;
  actor_user_id?: number | null;
  actor_role?: string | null;
  action: string;
  result_code: string;
  ip_address?: string | null;
  detail?: unknown;
  message?: string | null;
  occurred_at: string;
  storage_scope?: "ACTIVE" | "HISTORY";
}

export function listAuditLogs(params: {
  page?: number;
  size?: number;
  event_type?: string;
  entity_code?: string;
  entity_id?: number;
  action?: string;
  actor_user_id?: number;
  since?: string;
  until?: string;
  storage_scope?: "all" | "active" | "history";
}) {
  return get<ApiEnvelope<Paginated<AuditLogOut>>>("/admin/audit-logs", {
    params,
  });
}

// v1.5 触发归档
export function archiveAuditLogs(retention_days = 180, batch_size = 1000) {
  return post<ApiEnvelope<AuditArchiveSummary>>(
    "/admin/audit-logs/archive",
    null,
    { params: { retention_days, batch_size } },
  );
}
