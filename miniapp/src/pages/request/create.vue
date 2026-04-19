<template>
  <view class="container">
    <view v-if="!activeType" class="type-list">
      <text class="section-title">选择事务类型</text>
      <view v-if="loadingTypes" class="empty">加载中...</view>
      <view
        v-else
        v-for="t in types"
        :key="t.id"
        class="type-item"
        @tap="onPickType(t)"
      >
        <view class="type-head">
          <text class="type-name">{{ t.name }}</text>
          <text class="type-cat">{{ categoryLabel(t.category) }}</text>
        </view>
        <text v-if="t.description" class="type-desc">{{ t.description }}</text>
        <text class="type-meta">
          {{ t.attachment_required ? '需上传附件' : '附件可选' }}
          · 审批角色：{{ t.approver_roles }}
        </text>
      </view>
      <view v-if="!loadingTypes && !types.length" class="empty">暂无可发起的事务</view>
    </view>

    <view v-else class="form-wrap">
      <view class="form-head">
        <view class="form-head-main">
          <text class="type-name">{{ activeType.name }}</text>
          <text class="type-cat">{{ categoryLabel(activeType.category) }}</text>
        </view>
        <text v-if="draftStatus" class="status-chip" :class="draftStatus.toLowerCase()">
          {{ statusLabel(draftStatus) }}
        </text>
      </view>
      <text v-if="activeType.description" class="form-hint">{{ activeType.description }}</text>

      <view class="step-card">
        <text class="section-title">办理步骤</text>
        <text class="step-item" :class="{ done: !!draftId }">1. 保存草稿</text>
        <text class="step-item" :class="{ done: attachmentStepDone }">
          2. 上传附件{{ activeType.attachment_required ? '（必填）' : '（可选）' }}
        </text>
        <text class="step-item">3. {{ draftStatus === 'REJECTED' ? '重新提交申请' : '提交申请' }}</text>
      </view>

      <view
        v-if="draftStatus === 'REJECTED' && draftDetail?.decision_comment"
        class="notice-card warning"
      >
        <text class="notice-title">该申请已被驳回，请根据意见修改后重新提交</text>
        <text class="notice-body">{{ draftDetail.decision_comment }}</text>
      </view>

      <view class="field">
        <text class="label">申请标题 <text class="required">*</text></text>
        <input class="input" v-model="title" placeholder="请简要描述事由" />
      </view>

      <DynamicForm
        ref="dynamicFormRef"
        v-model="formData"
        :schema="activeType.form_schema || null"
      />

      <view class="field">
        <text class="label">补充说明</text>
        <textarea class="textarea" v-model="summary" placeholder="（可选）其他补充信息" />
      </view>

      <view class="section-block">
        <view class="section-head">
          <text class="section-title">附件材料</text>
          <button
            size="mini"
            type="primary"
            plain
            :disabled="!draftId"
            :loading="uploading"
            @tap="onUploadAttachment"
          >
            上传附件
          </button>
        </view>
        <text class="section-hint">{{ attachmentHint }}</text>
        <view v-if="attachments.length">
          <view v-for="attachment in attachments" :key="attachment.id" class="attachment-row">
            <text class="att-name">{{ attachment.filename }}</text>
            <text class="att-meta">{{ formatSize(attachment.file_size) }}</text>
          </view>
        </view>
        <view v-else class="empty-tiny">
          {{ draftId ? '暂无已上传附件' : '请先保存草稿后再上传附件' }}
        </view>
      </view>

      <view class="footer">
        <button v-if="!draftId" size="mini" @tap="onReset">重选类型</button>
        <button size="mini" :loading="saving" @tap="onSave">
          {{ draftId ? '保存修改' : '保存草稿' }}
        </button>
        <button size="mini" type="primary" :loading="submitting" @tap="onSubmit">
          {{ submitButtonText }}
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import DynamicForm from '@/components/DynamicForm.vue'
import {
  createRequest,
  getRequestCategoryLabel,
  getRequestDetail,
  getRequestStatusLabel,
  isEditableRequestStatus,
  listRequestTypes,
  submitRequest,
  updateRequest,
  uploadRequestAttachment,
  type RequestAttachment,
  type RequestDetail,
  type RequestStatus,
  type RequestType,
} from '@/api/workflow'

const types = ref<RequestType[]>([])
const loadingTypes = ref(false)

const activeType = ref<RequestType | null>(null)
const title = ref('')
const summary = ref('')
const formData = ref<Record<string, any>>({})
const attachments = ref<RequestAttachment[]>([])
const draftId = ref<number | null>(null)
const draftStatus = ref<RequestStatus | null>(null)
const draftDetail = ref<RequestDetail | null>(null)
const routeRequestId = ref<number | null>(null)

const dynamicFormRef = ref<InstanceType<typeof DynamicForm> | null>(null)
const saving = ref(false)
const submitting = ref(false)
const uploading = ref(false)

const attachmentStepDone = computed(() => {
  if (!activeType.value || !draftId.value) return false
  return !activeType.value.attachment_required || attachments.value.length > 0
})

const submitButtonText = computed(() =>
  draftStatus.value === 'REJECTED' ? '重新提交申请' : '提交申请'
)

const attachmentHint = computed(() => {
  if (!activeType.value) return ''
  if (!draftId.value) {
    return activeType.value.attachment_required
      ? '该类型需先保存草稿，再上传至少 1 个附件。'
      : '如需补充材料，请先保存草稿后再上传附件。'
  }
  if (!attachments.value.length) {
    return activeType.value.attachment_required
      ? '该类型提交前必须至少上传 1 个附件。'
      : '附件为可选项，可按需上传补充材料。'
  }
  return `当前已上传 ${attachments.value.length} 个附件。`
})

function categoryLabel(category: string) {
  return getRequestCategoryLabel(category)
}

function statusLabel(status: string) {
  return getRequestStatusLabel(status)
}

function formatSize(bytes?: number | null) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let index = 0
  let value = bytes
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024
    index += 1
  }
  return `${value.toFixed(index ? 1 : 0)} ${units[index]}`
}

function resetDraftState() {
  title.value = ''
  summary.value = ''
  formData.value = {}
  attachments.value = []
  draftId.value = null
  draftStatus.value = null
  draftDetail.value = null
}

function syncDraftDetail(detail: RequestDetail) {
  draftId.value = detail.id
  draftStatus.value = detail.status as RequestStatus
  draftDetail.value = detail
  attachments.value = [...detail.attachments]
}

async function loadTypes() {
  loadingTypes.value = true
  try {
    const resp = await listRequestTypes()
    types.value = resp.data
  } finally {
    loadingTypes.value = false
  }
}

async function loadEditableDraft(id: number) {
  const resp = await getRequestDetail(id)
  const detail = resp.data
  if (!isEditableRequestStatus(detail.status)) {
    uni.showToast({ title: '当前申请不可编辑', icon: 'none' })
    uni.redirectTo({ url: `/pages/request/detail?id=${id}` })
    return
  }
  const matchedType = types.value.find((item) => item.code === detail.type_code)
  if (!matchedType) {
    uni.showToast({ title: '当前事务类型不可继续编辑', icon: 'none' })
    uni.redirectTo({ url: `/pages/request/detail?id=${id}` })
    return
  }
  activeType.value = matchedType
  title.value = detail.title
  summary.value = detail.summary || ''
  formData.value = { ...detail.form_data }
  syncDraftDetail(detail)
}

function onPickType(type: RequestType) {
  resetDraftState()
  routeRequestId.value = null
  activeType.value = type
}

function onReset() {
  resetDraftState()
  routeRequestId.value = null
  activeType.value = null
}

function validateForm() {
  if (!activeType.value) return false
  if (!title.value.trim()) {
    uni.showToast({ title: '请输入申请标题', icon: 'none' })
    return false
  }
  const { ok } = dynamicFormRef.value?.validate() ?? { ok: true }
  if (!ok) {
    uni.showToast({ title: '请完善必填字段', icon: 'none' })
    return false
  }
  return true
}

function validateRequiredAttachments() {
  if (activeType.value?.attachment_required && attachments.value.length === 0) {
    uni.showToast({ title: '请先上传必填附件', icon: 'none' })
    return false
  }
  return true
}

async function persistDraft(showSuccess: boolean) {
  if (!activeType.value || !validateForm()) return null
  const isNewDraft = draftId.value == null
  const payload = {
    title: title.value.trim(),
    form_data: formData.value,
    summary: summary.value.trim() || undefined,
  }
  const resp = draftId.value == null
    ? await createRequest({
      type_code: activeType.value.code,
      ...payload,
    })
    : await updateRequest(draftId.value, payload)
  syncDraftDetail(resp.data)
  if (showSuccess) {
    uni.showToast({ title: isNewDraft ? '草稿已保存' : '修改已保存' })
  }
  return resp.data
}

async function onSave() {
  saving.value = true
  try {
    await persistDraft(true)
  } finally {
    saving.value = false
  }
}

async function onUploadAttachment() {
  if (draftId.value == null) {
    uni.showToast({ title: '请先保存草稿', icon: 'none' })
    return
  }
  const selected = await new Promise<any>((resolve) => {
    uni.chooseMessageFile({
      count: 9,
      type: 'all',
      success: resolve,
      fail: () => resolve(null),
    })
  })
  if (!selected?.tempFiles?.length) return

  uploading.value = true
  try {
    let uploadedCount = 0
    for (const file of selected.tempFiles as Array<{ path?: string; tempFilePath?: string }>) {
      const filePath = file.path || file.tempFilePath
      if (!filePath) continue
      const attachment = await uploadRequestAttachment(draftId.value, filePath)
      attachments.value = [...attachments.value, attachment]
      uploadedCount += 1
    }
    if (uploadedCount > 0) {
      if (draftDetail.value) {
        draftDetail.value = { ...draftDetail.value, attachments: attachments.value }
      }
      uni.showToast({
        title: uploadedCount > 1 ? `已上传${uploadedCount}个附件` : '附件已上传',
        icon: 'none',
      })
    }
  } finally {
    uploading.value = false
  }
}

async function onSubmit() {
  if (draftId.value == null) {
    uni.showToast({ title: '请先保存草稿', icon: 'none' })
    return
  }
  if (!validateRequiredAttachments()) return

  submitting.value = true
  try {
    const previousStatus = draftStatus.value
    const detail = await persistDraft(false)
    if (!detail || !validateRequiredAttachments()) return
    await submitRequest(detail.id)
    uni.showToast({
      title: previousStatus === 'REJECTED' ? '已重新提交' : '已提交申请',
      icon: 'none',
    })
    uni.redirectTo({ url: `/pages/request/detail?id=${detail.id}` })
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1] as any
  const options = current?.options || {}
  routeRequestId.value = options.id ? Number(options.id) : null

  await loadTypes()
  if (routeRequestId.value != null && Number.isFinite(routeRequestId.value)) {
    await loadEditableDraft(routeRequestId.value)
  }
})
</script>

<style scoped>
.container { padding: 24rpx; }
.section-title { display: block; font-size: 28rpx; font-weight: 600; margin-bottom: 16rpx; }

.type-item {
  background: #fff;
  padding: 24rpx;
  border-radius: 12rpx;
  margin-bottom: 16rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.06);
}
.type-head { display: flex; justify-content: space-between; align-items: center; }
.type-name { font-size: 30rpx; font-weight: 600; color: #333; }
.type-cat {
  font-size: 22rpx;
  color: #7f1722;
  background: #fff1f0;
  padding: 2rpx 12rpx;
  border-radius: 4rpx;
}
.type-desc { display: block; font-size: 26rpx; color: #666; margin-top: 8rpx; }
.type-meta { display: block; font-size: 22rpx; color: #999; margin-top: 6rpx; }

.empty { text-align: center; padding: 80rpx 0; color: #999; font-size: 28rpx; }
.empty-tiny { text-align: center; padding: 24rpx 0; color: #bbb; font-size: 24rpx; }

.form-wrap {
  background: #fff;
  padding: 24rpx;
  border-radius: 12rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.06);
}
.form-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16rpx;
  margin-bottom: 8rpx;
}
.form-head-main { flex: 1; }
.status-chip {
  font-size: 22rpx;
  padding: 4rpx 14rpx;
  border-radius: 4rpx;
  flex-shrink: 0;
}
.status-chip.draft { background: #f5f5f5; color: #666; }
.status-chip.submitted,
.status-chip.in_review { background: #e6f7ff; color: #1890ff; }
.status-chip.approved { background: #f6ffed; color: #52c41a; }
.status-chip.rejected { background: #fff1f0; color: #cf1322; }
.status-chip.withdrawn { background: #f5f5f5; color: #999; }
.status-chip.offline_handled { background: #fff7e6; color: #d46b08; }
.form-hint {
  display: block;
  font-size: 24rpx;
  color: #999;
  margin-bottom: 20rpx;
  line-height: 1.5;
}

.step-card,
.section-block,
.notice-card {
  background: #fafafa;
  border-radius: 10rpx;
  padding: 20rpx;
  margin-bottom: 20rpx;
}
.step-item {
  display: block;
  font-size: 24rpx;
  color: #999;
  line-height: 1.8;
}
.step-item.done { color: #237804; }

.notice-card.warning {
  background: #fff7e6;
  border-left: 8rpx solid #d46b08;
}
.notice-title { display: block; font-size: 26rpx; color: #ad6800; font-weight: 600; }
.notice-body { display: block; font-size: 24rpx; color: #8c8c8c; margin-top: 8rpx; line-height: 1.6; }

.field { margin-bottom: 20rpx; }
.label { display: block; font-size: 26rpx; color: #333; margin-bottom: 6rpx; }
.required { color: #ff4d4f; margin-left: 6rpx; }
.input,
.textarea {
  background: #f7f7f7;
  border-radius: 8rpx;
  padding: 14rpx 16rpx;
  font-size: 26rpx;
}
.textarea { min-height: 140rpx; }

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16rpx;
}
.section-hint {
  display: block;
  font-size: 24rpx;
  color: #999;
  margin-bottom: 12rpx;
  line-height: 1.6;
}
.attachment-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
  font-size: 26rpx;
}
.attachment-row:last-child { border-bottom: none; }
.att-name {
  flex: 1;
  color: #333;
  margin-right: 16rpx;
  word-break: break-all;
}
.att-meta { color: #999; font-size: 22rpx; }

.footer {
  display: flex;
  justify-content: flex-end;
  gap: 12rpx;
  margin-top: 24rpx;
  flex-wrap: wrap;
}
</style>
