<template>
  <div class="approval-detail">
    <a-page-header
      title="审批详情"
      :sub-title="detail ? `${detail.request_no} · ${detail.type_name}` : 'FR-007 / FR-008'"
      @back="$router.back()"
    />

    <a-spin :spinning="loading">
      <template v-if="detail">
        <a-card title="一、申请信息" :bordered="false" size="small" class="mb16">
          <a-alert
            type="info"
            show-icon
            class="mb16"
            :message="`当前状态：${statusMeta.label}`"
            :description="statusSummary"
          />

          <a-descriptions :column="2" bordered size="small">
            <a-descriptions-item label="单号">{{ detail.request_no }}</a-descriptions-item>
            <a-descriptions-item label="事务类型">
              {{ detail.type_name }}（{{ detail.type_code }}）
            </a-descriptions-item>
            <a-descriptions-item label="申请标题">{{ detail.title }}</a-descriptions-item>
            <a-descriptions-item label="状态">
              <a-tag :color="statusMeta.color">{{ statusMeta.label }}</a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="事务类别">{{ detail.category }}</a-descriptions-item>
            <a-descriptions-item label="当前版本">第 {{ detail.revision }} 版</a-descriptions-item>
            <a-descriptions-item label="申请人用户 ID">
              {{ detail.applicant_user_id }}
            </a-descriptions-item>
            <a-descriptions-item label="申请人学生 ID">
              {{ detail.applicant_student_id ?? '-' }}
            </a-descriptions-item>
            <a-descriptions-item label="提交时间">
              {{ formatDateTime(detail.submitted_at) }}
            </a-descriptions-item>
            <a-descriptions-item label="最近处理时间">
              {{ formatDateTime(detail.decided_at || detail.withdrawn_at) }}
            </a-descriptions-item>
            <a-descriptions-item label="审批人 ID">
              {{ detail.decided_by ?? '-' }}
            </a-descriptions-item>
            <a-descriptions-item label="撤回时间">
              {{ formatDateTime(detail.withdrawn_at) }}
            </a-descriptions-item>
            <a-descriptions-item :span="2" label="摘要说明">
              {{ detail.summary || '申请人未提供摘要。' }}
            </a-descriptions-item>
            <a-descriptions-item :span="2" label="当前意见">
              {{ detail.decision_comment || '尚未形成审批意见。' }}
            </a-descriptions-item>
          </a-descriptions>

          <div class="section-subtitle">结构化表单字段</div>
          <template v-if="formEntries.length">
            <a-descriptions :column="2" bordered size="small">
              <a-descriptions-item
                v-for="entry in formEntries"
                :key="entry.key"
                :label="entry.key"
              >
                <pre class="pre-like">{{ entry.value }}</pre>
              </a-descriptions-item>
            </a-descriptions>
          </template>
          <a-empty v-else description="当前申请未返回结构化表单字段" />
        </a-card>

        <a-card title="二、附件" :bordered="false" size="small" class="mb16">
          <div v-if="detail.attachments.length" class="attachment-list">
            <div
              v-for="attachment in detail.attachments"
              :key="attachment.id"
              class="attachment-item"
            >
              <div class="attachment-title">{{ attachment.filename }}</div>
              <div class="detail-muted">
                {{ attachment.mime_type || '未知类型' }} ·
                {{ formatFileSize(attachment.file_size) }} ·
                上传于 {{ formatDateTime(attachment.uploaded_at) }}
              </div>
            </div>
          </div>
          <a-empty v-else description="当前申请没有附件材料" />
        </a-card>

        <a-card title="三、历史流转" :bordered="false" size="small" class="mb16">
          <a-timeline v-if="approvalTimeline.length">
            <a-timeline-item
              v-for="record in approvalTimeline"
              :key="record.id"
              :color="getApprovalActionMeta(record.action).color"
            >
              <div class="timeline-title-row">
                <a-tag :color="getApprovalActionMeta(record.action).color">
                  {{ getApprovalActionMeta(record.action).label }}
                </a-tag>
                <span class="detail-muted">{{ formatDateTime(record.occurred_at) }}</span>
              </div>
              <div class="timeline-line">
                操作人：{{ formatOperator(record.operator_role, record.operator_id) }}
              </div>
              <div v-if="formatTransition(record.status_before, record.status_after)" class="timeline-line">
                状态变更：{{ formatTransition(record.status_before, record.status_after) }}
              </div>
              <div v-if="record.comment" class="timeline-comment">
                {{ record.comment }}
              </div>
            </a-timeline-item>
          </a-timeline>
          <a-empty v-else description="暂无审批流转记录" />
        </a-card>

        <a-card title="四、当前可执行动作" :bordered="false" size="small">
          <a-row :gutter="[16, 16]">
            <a-col :xs="24" :lg="14">
              <a-alert
                type="warning"
                show-icon
                class="mb16"
                :message="statusMeta.label"
                :description="statusMeta.description"
              />
              <a-descriptions :column="1" bordered size="small">
                <a-descriptions-item label="处理说明">
                  {{ detail.decision_comment || '当前尚未形成新的处理意见。' }}
                </a-descriptions-item>
                <a-descriptions-item label="审批完成时间">
                  {{ formatDateTime(detail.decided_at) }}
                </a-descriptions-item>
                <a-descriptions-item label="撤回时间">
                  {{ formatDateTime(detail.withdrawn_at) }}
                </a-descriptions-item>
              </a-descriptions>
            </a-col>

            <a-col :xs="24" :lg="10">
              <div v-if="availableActions.length" class="action-buttons">
                <a-button
                  v-for="action in availableActions"
                  :key="action.key"
                  :type="action.type"
                  :danger="action.danger"
                  :loading="action.key === 'claim' ? claiming : actionSubmitting"
                  block
                  @click="action.key === 'claim' ? onClaim() : showAction(action.key)"
                >
                  {{ ADMIN_REQUEST_ACTION_META[action.key].label }}
                </a-button>
              </div>
              <a-empty v-else description="当前状态暂无可执行的管理员动作" />
            </a-col>
          </a-row>
        </a-card>
      </template>

      <a-empty v-else-if="!loading" description="未找到审批详情" />
    </a-spin>

    <a-modal
      v-model:open="actionModal.visible"
      :title="currentActionMeta?.title"
      :confirm-loading="actionSubmitting"
      @ok="onAction"
    >
      <a-form layout="vertical">
        <a-form-item label="处理说明">
          <a-textarea
            v-model:value="actionModal.comment"
            :rows="4"
            :placeholder="actionModal.type === 'reject' ? '请填写驳回原因，便于申请人补充后重提' : '可选填处理说明'"
          />
        </a-form-item>
        <a-form-item
          v-if="actionModal.type === 'offline'"
          label="线下联系信息"
          extra="转线下办理时必填，建议填写联系人与联系方式。"
        >
          <a-input v-model:value="actionModal.contact_info" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  ADMIN_REQUEST_ACTION_META,
  approveRequest,
  claimRequest,
  getApprovalActionMeta,
  getRequestDetail,
  getRequestStatusMeta,
  markRequestOffline,
  rejectRequest,
  type RequestDetail,
} from '@/api/workflow'

type ActionModalType = 'approve' | 'reject' | 'offline' | null

interface ActionButton {
  key: 'claim' | 'approve' | 'reject' | 'offline'
  type: 'primary' | 'default'
  danger?: boolean
}

const route = useRoute()
const id = Number(route.params.id)

const detail = ref<RequestDetail | null>(null)
const loading = ref(false)
const claiming = ref(false)
const actionSubmitting = ref(false)

const actionModal = reactive({
  visible: false,
  type: null as ActionModalType,
  comment: '',
  contact_info: '',
})

const statusMeta = computed(() => getRequestStatusMeta(detail.value?.status))

const statusSummary = computed(() => {
  if (!detail.value) return statusMeta.value.description
  const chunks = [statusMeta.value.description]
  if (detail.value.decision_comment) {
    chunks.push(`当前意见：${detail.value.decision_comment}`)
  }
  return chunks.join(' ')
})

const formEntries = computed(() => {
  if (!detail.value?.form_data) return []
  return Object.entries(detail.value.form_data).map(([key, value]) => ({
    key,
    value: formatFieldValue(value),
  }))
})

const approvalTimeline = computed(() => {
  if (!detail.value?.approval_records.length) return []
  return [...detail.value.approval_records].sort(
    (left, right) => getTime(left.occurred_at) - getTime(right.occurred_at),
  )
})

const availableActions = computed<ActionButton[]>(() => {
  if (!detail.value) return []
  if (detail.value.status === 'SUBMITTED') {
    return [
      { key: 'claim', type: 'primary' },
      { key: 'approve', type: 'default' },
      { key: 'reject', type: 'default', danger: true },
      { key: 'offline', type: 'default' },
    ]
  }
  if (detail.value.status === 'IN_REVIEW') {
    return [
      { key: 'approve', type: 'primary' },
      { key: 'reject', type: 'default', danger: true },
      { key: 'offline', type: 'default' },
    ]
  }
  return []
})

const currentActionMeta = computed(() => (
  actionModal.type ? ADMIN_REQUEST_ACTION_META[actionModal.type] : null
))

function getTime(value?: string | null) {
  if (!value) return 0
  const timestamp = new Date(value).getTime()
  return Number.isNaN(timestamp) ? 0 : timestamp
}

function formatDateTime(value?: string | null) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

function formatFileSize(value?: number | null) {
  if (value == null) return '-'
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / 1024 / 1024).toFixed(1)} MB`
}

function formatFieldValue(value: unknown): string {
  if (value == null) return '-'
  if (typeof value === 'boolean') return value ? '是' : '否'
  if (typeof value === 'number') return String(value)
  if (typeof value === 'string') return value || '-'
  if (Array.isArray(value)) {
    if (!value.length) return '-'
    return value.every((item) => ['string', 'number', 'boolean'].includes(typeof item))
      ? value.map((item) => formatFieldValue(item)).join('、')
      : JSON.stringify(value, null, 2)
  }
  return JSON.stringify(value, null, 2)
}

function formatOperator(role?: string | null, operatorId?: number | null) {
  if (role && operatorId != null) return `${role} / 用户 ${operatorId}`
  if (operatorId != null) return `用户 ${operatorId}`
  if (role) return role
  return '系统'
}

function formatTransition(statusBefore?: string | null, statusAfter?: string | null) {
  if (statusBefore && statusAfter) {
    return `${getRequestStatusMeta(statusBefore).label} → ${getRequestStatusMeta(statusAfter).label}`
  }
  if (statusAfter) return getRequestStatusMeta(statusAfter).label
  return ''
}

async function loadDetail() {
  if (!Number.isFinite(id) || id <= 0) {
    detail.value = null
    return
  }
  loading.value = true
  try {
    const resp = await getRequestDetail(id)
    detail.value = resp.data
  } catch {
    detail.value = null
    message.error('审批详情加载失败')
  } finally {
    loading.value = false
  }
}

async function onClaim() {
  claiming.value = true
  try {
    await claimRequest(id)
    message.success(ADMIN_REQUEST_ACTION_META.claim.successMessage)
    await loadDetail()
  } finally {
    claiming.value = false
  }
}

function showAction(type: Exclude<ActionModalType, null>) {
  actionModal.type = type
  actionModal.comment = ''
  actionModal.contact_info = ''
  actionModal.visible = true
}

async function onAction() {
  if (!actionModal.type) return
  if (actionModal.type === 'reject' && !actionModal.comment.trim()) {
    message.warning('请填写驳回说明')
    return
  }
  if (actionModal.type === 'offline' && !actionModal.contact_info.trim()) {
    message.warning('请填写线下联系信息')
    return
  }

  actionSubmitting.value = true
  try {
    if (actionModal.type === 'approve') {
      await approveRequest(id, actionModal.comment.trim() || undefined)
    } else if (actionModal.type === 'reject') {
      await rejectRequest(id, actionModal.comment.trim())
    } else if (actionModal.type === 'offline') {
      await markRequestOffline(
        id,
        actionModal.contact_info.trim(),
        actionModal.comment.trim() || undefined,
      )
    }
    message.success(ADMIN_REQUEST_ACTION_META[actionModal.type].successMessage)
    actionModal.visible = false
    await loadDetail()
  } finally {
    actionSubmitting.value = false
  }
}

onMounted(loadDetail)
</script>

<style scoped>
.mb16 {
  margin-bottom: 16px;
}

.pre-like {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
}

.section-subtitle {
  margin-bottom: 12px;
  color: #4b5563;
  font-size: 13px;
  font-weight: 600;
}

.detail-muted {
  color: #8c8c8c;
  font-size: 12px;
}

.attachment-list {
  display: grid;
  gap: 12px;
}

.attachment-item {
  padding: 12px 14px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  background: #fafafa;
}

.attachment-title {
  margin-bottom: 4px;
  color: #262626;
  font-weight: 600;
}

.timeline-title-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-bottom: 4px;
}

.timeline-line {
  margin-top: 4px;
  line-height: 1.6;
}

.timeline-comment {
  margin-top: 8px;
  padding: 8px 12px;
  border-left: 3px solid #d9d9d9;
  background: #fafafa;
  white-space: pre-wrap;
  line-height: 1.6;
}

.action-buttons {
  display: grid;
  gap: 12px;
}
</style>
