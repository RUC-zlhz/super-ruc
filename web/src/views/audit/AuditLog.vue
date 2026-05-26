<template>
  <div class="audit-page">
    <a-page-header title="审计日志" sub-title="记录系统关键操作行为，支持查询、分析与追溯" />

    <a-form layout="inline" :model="filters" class="filter-card" @finish="onFilterSubmit">
      <a-form-item label="事件类型">
        <a-input
          v-model:value="filters.event_type"
          placeholder="如 REQUEST / PROFILE / EXPORT"
          allow-clear
        />
      </a-form-item>
      <a-form-item label="实体">
        <a-input
          v-model:value="filters.entity_code"
          placeholder="如 REQUEST / STUDENT_PROFILE"
          allow-clear
        />
      </a-form-item>
      <a-form-item label="对象 ID">
        <a-input-number
          v-model:value="filters.entity_id"
          placeholder="对象 ID"
          :min="1"
        />
      </a-form-item>
      <a-form-item label="动作">
        <a-input
          v-model:value="filters.action"
          placeholder="如 READ_DETAIL / EXPORT_PDF"
          allow-clear
        />
      </a-form-item>
      <a-form-item label="操作人 ID">
        <a-input-number
          v-model:value="filters.actor_user_id"
          placeholder="用户 ID"
          :min="1"
        />
      </a-form-item>
      <a-form-item label="日志范围">
        <a-select v-model:value="filters.storage_scope" style="width: 140px">
          <a-select-option value="all">当前 + 历史</a-select-option>
          <a-select-option value="active">仅当前</a-select-option>
          <a-select-option value="history">仅归档</a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item label="起始">
        <a-date-picker v-model:value="filters.since" show-time />
      </a-form-item>
      <a-form-item label="截止">
        <a-date-picker v-model:value="filters.until" show-time />
      </a-form-item>
      <a-form-item>
        <a-space wrap>
          <a-button type="primary" html-type="submit">
            <template #icon><SearchOutlined /></template>
            查询
          </a-button>
          <a-button @click="resetFilters">
            <template #icon><ReloadOutlined /></template>
            重置
          </a-button>
        </a-space>
      </a-form-item>
    </a-form>

    <div class="summary-row mb16">
      <div class="summary-card">
        <div class="summary-label">当前页日志</div>
        <div class="summary-value">{{ rows.length }}</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">成功</div>
        <div class="summary-value success">{{ resultSummary.success }}</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">拒绝</div>
        <div class="summary-value warning">{{ resultSummary.denied }}</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">失败</div>
        <div class="summary-value danger">{{ resultSummary.failed }}</div>
      </div>
    </div>

    <div v-if="activeFilterSummary.length" class="filter-summary mb16">
      当前筛选：
      <span v-for="item in activeFilterSummary" :key="item" class="filter-chip">
        {{ item }}
      </span>
    </div>

    <div class="audit-workbench">
      <section class="audit-table-area">
        <a-table
          :columns="columns"
          :data-source="rows"
          :loading="loading"
          :pagination="pagination"
          row-key="id"
          @change="onTableChange"
         :scroll="{ x: 'max-content' }">
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'storage_scope'">
              <a-tag :color="auditScopeColor(record.storage_scope)">
                {{ auditScopeLabel(record.storage_scope) }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'result_code'">
              <a-tooltip :title="record.result_code">
                <a-tag :color="auditResultColor(record.result_code)">
                  {{ auditResultLabel(record.result_code) }}
                </a-tag>
              </a-tooltip>
            </template>
            <template v-else-if="column.key === 'detail'">
              <button
                v-if="auditDetailText(record)"
                class="detail-preview"
                type="button"
                @click="selectAudit(record)"
              >
                {{ auditDetailPreview(record) }}
              </button>
              <a-button v-else type="link" size="small" @click="selectAudit(record)">
                <template #icon><EyeOutlined /></template>
                查看
              </a-button>
            </template>
            <template v-else-if="column.key === 'occurred_at'">
              {{ formatDateTime(record.occurred_at) }}
            </template>
          </template>
        </a-table>
      </section>

      <aside class="audit-detail panel-card">
        <div class="detail-side-head">
          <div>
            <div class="detail-side-title">日志详情</div>
            <div class="detail-side-sub">
              {{ currentAudit ? `#${currentAudit.id}` : '选择一条日志查看上下文' }}
            </div>
          </div>
          <a-tag v-if="currentAudit" :color="auditResultColor(currentAudit.result_code)">
            {{ auditResultLabel(currentAudit.result_code) }}
          </a-tag>
        </div>

        <template v-if="currentAudit">
          <div class="detail-facts">
            <div class="detail-fact">
              <span>事件</span>
              <strong>{{ currentAudit.event_type }}</strong>
            </div>
            <div class="detail-fact">
              <span>实体</span>
              <strong>{{ currentAudit.entity_code || '-' }}</strong>
            </div>
            <div class="detail-fact">
              <span>对象 ID</span>
              <strong>{{ currentAudit.entity_id || '-' }}</strong>
            </div>
            <div class="detail-fact">
              <span>操作</span>
              <strong>{{ currentAudit.action }}</strong>
            </div>
            <div class="detail-fact">
              <span>操作人</span>
              <strong>{{ currentAudit.actor_user_id || '-' }}</strong>
            </div>
            <div class="detail-fact">
              <span>IP</span>
              <strong>{{ currentAudit.ip_address || '-' }}</strong>
            </div>
            <div class="detail-fact">
              <span>范围</span>
              <strong>{{ auditScopeLabel(currentAudit.storage_scope) }}</strong>
            </div>
            <div class="detail-fact">
              <span>时间</span>
              <strong>{{ formatDateTime(currentAudit.occurred_at) }}</strong>
            </div>
          </div>

          <div class="detail-section">
            <div class="detail-section-title">详情载荷</div>
            <pre class="detail-pre side">{{ auditDetailText(currentAudit) || '无详情' }}</pre>
          </div>
        </template>

        <a-empty v-else image="simple" description="暂无日志" />
      </aside>
    </div>

    <a-divider v-if="canArchive" />

    <a-card
      v-if="canArchive"
      title="日志归档（v1.5）"
      :bordered="false"
      size="small"
    >
      <a-space>
        <span>留存天数：</span>
        <a-input-number v-model:value="archiveDays" :min="30" :max="3650" />
        <a-popconfirm title="确定归档超期日志？" @confirm="onArchive">
          <a-button type="primary" danger>
            <template #icon><HistoryOutlined /></template>
            执行归档
          </a-button>
        </a-popconfirm>
      </a-space>
      <div v-if="archiveResult" class="mt8">
        已搬迁 <strong>{{ archiveResult.moved }}</strong> 条记录（留存
        {{ archiveResult.retention_days }} 天）
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { message } from "ant-design-vue";
import {
  FileTextOutlined,
  SearchOutlined,
  ReloadOutlined,
  EyeOutlined,
  HistoryOutlined
} from '@ant-design/icons-vue';
import { useAuthStore } from "@/store/auth";
import { hasAnyRole } from "@/utils/permission";
import {
  listAuditLogs,
  archiveAuditLogs,
  type AuditArchiveSummary,
  type AuditLogOut,
} from "@/api/audit";

const auth = useAuthStore();
const columns = [
  { title: "ID", dataIndex: "id", key: "id", width: 70 },
  {
    title: "来源",
    dataIndex: "storage_scope",
    key: "storage_scope",
    width: 90,
  },
  { title: "事件", dataIndex: "event_type", key: "event_type", width: 110 },
  { title: "实体", dataIndex: "entity_code", key: "entity_code", width: 130 },
  { title: "对象 ID", dataIndex: "entity_id", key: "entity_id", width: 90 },
  { title: "操作", dataIndex: "action", key: "action", width: 150 },
  { title: "结果", key: "result_code", width: 80 },
  {
    title: "操作人",
    dataIndex: "actor_user_id",
    key: "actor_user_id",
    width: 80,
  },
  { title: "角色", dataIndex: "actor_role", key: "actor_role", width: 120 },
  { title: "IP", dataIndex: "ip_address", key: "ip_address", width: 130 },
  { title: "详情", key: "detail" },
  { title: "时间", dataIndex: "occurred_at", key: "occurred_at", width: 180 },
];

const filters = reactive<{
  event_type?: string;
  entity_code?: string;
  entity_id?: number;
  action?: string;
  actor_user_id?: number;
  storage_scope: "all" | "active" | "history";
  since?: any;
  until?: any;
}>({ storage_scope: "all" });

const rows = ref<AuditLogOut[]>([]);
const loading = ref(false);
const pagination = reactive({ current: 1, pageSize: 20, total: 0 });
const selectedAudit = ref<AuditLogOut | null>(null);
const canArchive = computed(() => hasAnyRole(auth.roleCodes, ["SUPER_ADMIN"]));
const currentAudit = computed(() => {
  if (selectedAudit.value && rows.value.some((row) => row.id === selectedAudit.value?.id)) {
    return selectedAudit.value;
  }
  return rows.value[0] || null;
});
const resultSummary = computed(() => {
  return rows.value.reduce(
    (summary, row) => {
      const normalized = normalizeAuditResultCode(row.result_code);
      if (normalized === "SUCCESS") summary.success += 1;
      else if (normalized === "DENIED") summary.denied += 1;
      else summary.failed += 1;
      return summary;
    },
    { success: 0, denied: 0, failed: 0 },
  );
});
const activeFilterSummary = computed(() => {
  const items: string[] = [];
  if (filters.event_type) items.push(`事件=${filters.event_type}`);
  if (filters.entity_code) items.push(`实体=${filters.entity_code}`);
  if (filters.entity_id) items.push(`对象ID=${filters.entity_id}`);
  if (filters.action) items.push(`动作=${filters.action}`);
  if (filters.actor_user_id) items.push(`操作人=${filters.actor_user_id}`);
  if (filters.storage_scope !== "all") {
    items.push(
      `范围=${filters.storage_scope === "history" ? "仅归档" : "仅当前"}`,
    );
  }
  if (filters.since) {
    items.push(`起始=${formatDateTime(filters.since?.toDate?.() || filters.since)}`);
  }
  if (filters.until) {
    items.push(`截止=${formatDateTime(filters.until?.toDate?.() || filters.until)}`);
  }
  return items;
});

interface AuditDetailPayload {
  detail?: unknown;
  message?: string | null;
}

function normalizeAuditResultCode(resultCode?: string | null) {
  const normalized = resultCode?.trim().toUpperCase();
  if (!normalized) return "FAILED";
  if (normalized === "SUCCESS" || normalized === "OK") return "SUCCESS";
  if (
    normalized === "DENIED" ||
    normalized === "FORBIDDEN" ||
    normalized === "UNAUTHORIZED"
  )
    return "DENIED";
  return "FAILED";
}

function auditResultLabel(resultCode?: string | null) {
  return normalizeAuditResultCode(resultCode);
}

function auditResultColor(resultCode?: string | null) {
  const normalized = normalizeAuditResultCode(resultCode);
  if (normalized === "SUCCESS") return "green";
  if (normalized === "DENIED") return "orange";
  return "red";
}

function auditScopeLabel(storageScope?: string | null) {
  return storageScope === "HISTORY" ? "归档" : "当前";
}

function auditScopeColor(storageScope?: string | null) {
  return storageScope === "HISTORY" ? "gold" : "blue";
}

function normalizeAuditToken(value?: string | null) {
  return value?.trim().toUpperCase() || undefined;
}

function formatDateTime(value?: string | Date | null) {
  if (!value) return "-";
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return date.toLocaleString("zh-CN", { hour12: false });
}

function serializeAuditValue(value: unknown) {
  if (value == null) return "";
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function auditDetailText(record: AuditDetailPayload) {
  const detailText = serializeAuditValue(record.detail);
  if (detailText) return detailText;
  return record.message || "";
}

function auditDetailPreview(record: AuditDetailPayload) {
  const detailText = auditDetailText(record);
  if (!detailText) return "";
  return detailText.length > 96 ? `${detailText.slice(0, 96)}...` : detailText;
}

function selectAudit(record: AuditLogOut | Record<string, unknown>) {
  selectedAudit.value = record as AuditLogOut;
}

async function reload() {
  loading.value = true;
  try {
    const resp = await listAuditLogs({
      event_type: normalizeAuditToken(filters.event_type),
      entity_code: normalizeAuditToken(filters.entity_code),
      entity_id: filters.entity_id,
      action: normalizeAuditToken(filters.action),
      actor_user_id: filters.actor_user_id,
      storage_scope: filters.storage_scope,
      since: filters.since?.toISOString?.() || filters.since,
      until: filters.until?.toISOString?.() || filters.until,
      page: pagination.current,
      size: pagination.pageSize,
    });
    rows.value = resp.data.items;
    pagination.total = resp.data.meta.total;
    if (!selectedAudit.value || !rows.value.some((row) => row.id === selectedAudit.value?.id)) {
      selectedAudit.value = rows.value[0] || null;
    }
  } finally {
    loading.value = false;
  }
}

function onFilterSubmit() {
  filters.event_type = normalizeAuditToken(filters.event_type);
  filters.entity_code = normalizeAuditToken(filters.entity_code);
  filters.action = normalizeAuditToken(filters.action);
  pagination.current = 1;
  void reload();
}

function onTableChange(p: any) {
  pagination.current = p.current;
  pagination.pageSize = p.pageSize;
  reload();
}

function resetFilters() {
  filters.event_type = undefined;
  filters.entity_code = undefined;
  filters.entity_id = undefined;
  filters.action = undefined;
  filters.actor_user_id = undefined;
  filters.storage_scope = "all";
  filters.since = undefined;
  filters.until = undefined;
  pagination.current = 1;
  void reload();
}

// 归档
const archiveDays = ref(180);
const archiveResult = ref<AuditArchiveSummary | null>(null);

async function onArchive() {
  try {
    const resp = await archiveAuditLogs(archiveDays.value);
    archiveResult.value = resp.data;
    message.success(`已归档 ${resp.data.moved} 条`);
  } catch {
    message.error("归档失败");
  }
}

onMounted(reload);
</script>

<style scoped>
.mb16 {
  margin-bottom: 16px;
}
.mt8 {
  margin-top: 8px;
}
.detail-preview {
  display: inline-block;
  max-width: 320px;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--ruc-red);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
  font: inherit;
  text-align: left;
}
.detail-pre {
  margin: 0;
  max-width: 480px;
  max-height: 320px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

.detail-pre.side {
  max-width: none;
  max-height: 340px;
  padding: 12px;
  border-radius: var(--radius);
  background: #101722;
  color: rgba(255, 255, 255, 0.86);
  font-size: 12px;
  line-height: 1.65;
}

.audit-workbench {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 16px;
  align-items: start;
}

.audit-table-area {
  min-width: 0;
}

.audit-detail {
  position: sticky;
  top: 86px;
  padding: 16px;
}

.detail-side-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.detail-side-title {
  color: var(--text);
  font-size: 18px;
  font-weight: 700;
}

.detail-side-sub {
  margin-top: 4px;
  color: var(--text-3);
  font-size: 12px;
}

.detail-facts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.detail-fact {
  min-height: 66px;
  padding: 10px 12px;
  border-radius: var(--radius);
  background: #fff8f8;
  border: 1px solid var(--line-soft);
}

.detail-fact span {
  display: block;
  color: var(--text-3);
  font-size: 12px;
}

.detail-fact strong {
  display: block;
  margin-top: 7px;
  color: var(--text);
  font-size: 13px;
  word-break: break-all;
}

.detail-section {
  margin-top: 16px;
}

.detail-section-title {
  margin-bottom: 8px;
  color: var(--text);
  font-weight: 700;
}

.summary-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.summary-card {
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface);
  padding: 14px 16px;
}

.summary-label {
  color: var(--ink-3);
  font-size: 11px;
  letter-spacing: 0.8px;
  text-transform: uppercase;
}

.summary-value {
  margin-top: 8px;
  color: var(--ink);
  font-family: var(--font-serif);
  font-size: 28px;
  font-weight: 600;
  line-height: 1;
}

.summary-value.success {
  color: var(--success);
}

.summary-value.warning {
  color: var(--warning);
}

.summary-value.danger {
  color: var(--danger);
}

.filter-summary {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  color: var(--ink-3);
  font-size: 12px;
}

.filter-chip {
  display: inline-flex;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--surface-2);
  color: var(--ink-2);
}

@media (max-width: 1320px) {
  .audit-workbench {
    grid-template-columns: 1fr;
  }

  .audit-detail {
    position: static;
  }
}
</style>
