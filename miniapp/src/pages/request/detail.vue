<template>
  <view class="container">
    <view v-if="loading" class="loading">加载中...</view>

    <template v-else-if="detail">
      <view class="head-card">
        <view class="head-row">
          <view class="head-icon">文</view>
          <view class="head-main">
          <text class="title">{{ detail.title }}</text>
          <text class="meta">编号：{{ detail.request_no }}</text>
          </view>
          <text class="status" :class="detail.status.toLowerCase()">
            {{ statusLabel(detail.status) }}
          </text>
        </view>
        <text class="meta">类型：{{ detail.type_name }} · {{ categoryLabel(detail.category) }}</text>
        <text v-if="detail.submitted_at" class="meta">
          提交时间：{{ fmt(detail.submitted_at) }}
        </text>
        <text class="meta">版本：v{{ detail.revision }}</text>
      </view>

      <view v-if="detail.status === 'OFFLINE_HANDLED'" class="offline-card">
        <text class="offline-title">该事项已转线下办理</text>
        <text v-if="detail.decision_comment" class="offline-body">
          {{ detail.decision_comment }}
        </text>
        <text class="offline-hint">如需进一步确认，请联系负责老师获取后续指导。</text>
      </view>

      <view v-if="isCertificateRequest" class="section">
        <view class="section-head">
          <text class="section-title">证明文件</text>
          <button
            size="mini"
            :type="UNI_BUTTON_TYPE.primary"
            plain
            :disabled="!canPreviewProof"
            :loading="previewing"
            @tap="onPreviewProof"
          >
            预览 PDF
          </button>
        </view>
        <view class="pdf-card">
          <view class="pdf-cover">PDF</view>
          <view class="pdf-copy">
            <text class="pdf-title">证明材料 PDF 预览</text>
            <text class="pdf-meta">{{ canPreviewProof ? '审批通过，可在线预览' : '审批通过后开放预览' }}</text>
          </view>
        </view>
        <text class="section-hint">{{ proofHint }}</text>
      </view>

      <view class="section">
        <text class="section-title">申请内容</text>
        <view v-if="detail.summary" class="summary">
          <text>{{ detail.summary }}</text>
        </view>
        <view v-for="row in formRows" :key="row.key" class="info-row">
          <text class="info-key">{{ row.key }}</text>
          <text class="info-val">{{ row.value }}</text>
        </view>
        <view v-if="!formRows.length" class="empty-tiny">无填写内容</view>
      </view>

      <view v-if="detail.attachments?.length" class="section">
        <text class="section-title">附件</text>
        <view v-for="attachment in detail.attachments" :key="attachment.id" class="attachment-row">
          <text class="att-name">{{ attachment.filename }}</text>
          <text class="att-size">{{ formatSize(attachment.file_size) }}</text>
        </view>
      </view>

      <view class="section">
        <text class="section-title">审批记录</text>
        <view v-if="!detail.approval_records?.length" class="empty-tiny">暂无审批记录</view>
        <view v-for="record in detail.approval_records" :key="record.id" class="record-row">
          <view class="record-head">
            <text class="record-action" :class="actionClass(record.action)">
              {{ actionLabel(record.action) }}
            </text>
            <text class="record-time">{{ fmt(record.occurred_at) }}</text>
          </view>
          <text v-if="record.comment" class="record-comment">{{ record.comment }}</text>
          <text class="record-operator">操作人 ID：{{ record.operator_id ?? '-' }}</text>
        </view>
      </view>

      <view v-if="canEdit || canWithdraw" class="actions">
        <button v-if="canEdit" size="mini" :type="UNI_BUTTON_TYPE.primary" plain @tap="onEdit">
          {{ editButtonText }}
        </button>
        <button
          v-if="canWithdraw"
          :type="UNI_BUTTON_TYPE.warn"
          size="mini"
          :loading="withdrawing"
          @tap="onWithdraw"
        >
          撤回申请
        </button>
      </view>
      <view v-if="canEdit || canWithdraw" class="bottom-spacer" />
    </template>

    <view v-else class="empty">未找到申请记录</view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { UNI_BUTTON_TYPE } from '@/utils/uni-button'
import {
  getRequestActionLabel,
  getRequestCategoryLabel,
  getRequestDetail,
  getRequestStatusLabel,
  isEditableRequestStatus,
  previewProof,
  withdrawRequest,
  type RequestDetail,
} from '@/api/workflow'

const detail = ref<RequestDetail | null>(null)
const loading = ref(false)
const withdrawing = ref(false)
const previewing = ref(false)
const requestId = ref<number | null>(null)

function statusLabel(status: string) {
  return getRequestStatusLabel(status)
}

function categoryLabel(category: string) {
  return getRequestCategoryLabel(category)
}

function actionLabel(action: string) {
  return getRequestActionLabel(action)
}

function actionClass(action: string) {
  if (action === 'APPROVE') return 'approve'
  if (action === 'REJECT') return 'reject'
  if (action === 'OFFLINE_HANDLE') return 'offline'
  return 'info'
}

function fmt(value?: string | null) {
  if (!value) return '-'
  return value.slice(0, 16).replace('T', ' ')
}

function formatSize(bytes?: number | null) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let index = 0
  let size = bytes
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024
    index += 1
  }
  return `${size.toFixed(index ? 1 : 0)} ${units[index]}`
}

const formRows = computed(() => {
  if (!detail.value?.form_data) return []
  return Object.entries(detail.value.form_data).map(([key, value]) => ({
    key,
    value: typeof value === 'object' ? JSON.stringify(value) : String(value ?? ''),
  }))
})

const isCertificateRequest = computed(() => detail.value?.category === 'CERTIFICATE')
const canPreviewProof = computed(() =>
  !!detail.value && isCertificateRequest.value && detail.value.status === 'APPROVED'
)
const proofHint = computed(() => {
  if (!detail.value) return ''
  if (detail.value.status === 'OFFLINE_HANDLED') {
    return '该证明已转线下办理，不再生成线上 PDF。'
  }
  if (detail.value.status === 'APPROVED') {
    return '审批通过后可直接预览系统生成的证明 PDF。'
  }
  return '证明 PDF 将在审批通过后开放预览。'
})

const canEdit = computed(() => isEditableRequestStatus(detail.value?.status))
const editButtonText = computed(() =>
  detail.value?.status === 'REJECTED' ? '修改并重新提交' : '继续完善草稿'
)
const canWithdraw = computed(() =>
  !!detail.value && ['SUBMITTED', 'IN_REVIEW'].includes(detail.value.status)
)

async function loadDetail() {
  if (requestId.value == null) return
  loading.value = true
  try {
    const resp = await getRequestDetail(requestId.value)
    detail.value = resp.data
  } catch {
    detail.value = null
  } finally {
    loading.value = false
  }
}

function onEdit() {
  if (requestId.value == null) return
  uni.navigateTo({ url: `/pages/request/create?id=${requestId.value}` })
}

function openPdf(filePath: string) {
  return new Promise<void>((resolve, reject) => {
    uni.openDocument({
      filePath,
      fileType: 'pdf',
      showMenu: true,
      success: () => resolve(),
      fail: reject,
    })
  })
}

async function onPreviewProof() {
  if (!canPreviewProof.value || requestId.value == null) return
  previewing.value = true
  try {
    const { tempFilePath } = await previewProof(requestId.value)
    try {
      await openPdf(tempFilePath)
    } catch {
      uni.showToast({ title: '无法打开 PDF', icon: 'none' })
    }
  } catch {
    // 下载失败的提示已由现有 helper 处理
  } finally {
    previewing.value = false
  }
}

async function onWithdraw() {
  if (requestId.value == null) return
  const confirm = await new Promise<boolean>((resolve) => {
    uni.showModal({
      title: '撤回申请',
      content: '撤回后可继续修改，并在准备好后重新提交。确定继续吗？',
      success: (result) => resolve(result.confirm),
      fail: () => resolve(false),
    })
  })
  if (!confirm) return

  withdrawing.value = true
  try {
    await withdrawRequest(requestId.value, '学生端主动撤回')
    uni.showToast({ title: '已撤回', icon: 'none' })
    await loadDetail()
  } finally {
    withdrawing.value = false
  }
}

onMounted(() => {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1] as any
  const options = current?.options || {}
  requestId.value = Number(options.id)
  loadDetail()
})
</script>

<style scoped>
.container { padding: 24rpx; }
.loading,
.empty { text-align: center; padding: 80rpx 0; color: #999; font-size: 28rpx; }
.empty-tiny { text-align: center; padding: 16rpx 0; color: #bbb; font-size: 24rpx; }

.head-card {
  background: #fff;
  padding: 26rpx;
  border-radius: 22rpx;
  margin-bottom: 18rpx;
  border: 1rpx solid #f0e2e5;
  box-shadow: var(--shadow-card);
}
.head-row { display: flex; justify-content: space-between; align-items: flex-start; gap: 18rpx; }
.head-icon {
  width: 64rpx;
  height: 64rpx;
  border-radius: 16rpx;
  background: #b70f24;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  font-weight: 800;
}
.head-main { flex: 1; min-width: 0; }
.title { display: block; font-size: 33rpx; font-weight: 800; flex: 1; line-height: 1.45; }
.status {
  font-size: 22rpx;
  padding: 4rpx 14rpx;
  border-radius: 999rpx;
  flex-shrink: 0;
  margin-left: 12rpx;
}
.status.draft { background: #f5f5f5; color: #666; }
.status.submitted,
.status.in_review { background: #e6f7ff; color: #1890ff; }
.status.approved { background: #f6ffed; color: #52c41a; }
.status.rejected { background: #fff1f0; color: #cf1322; }
.status.withdrawn { background: #f5f5f5; color: #999; }
.status.offline_handled { background: #fff7e6; color: #d46b08; }
.meta { display: block; font-size: 24rpx; color: #8a8f98; margin-top: 8rpx; }

.offline-card {
  background: #fff7ed;
  border: 1rpx solid #f6d7aa;
  border-left: 8rpx solid #d46b08;
  border-radius: 18rpx;
  padding: 22rpx;
  margin-bottom: 18rpx;
}
.offline-title { display: block; font-size: 28rpx; font-weight: 600; color: #ad6800; }
.offline-body { display: block; font-size: 26rpx; color: #333; margin-top: 8rpx; line-height: 1.6; }
.offline-hint { display: block; font-size: 24rpx; color: #999; margin-top: 8rpx; }

.section {
  background: #fff;
  padding: 24rpx;
  border-radius: 22rpx;
  margin-bottom: 18rpx;
  border: 1rpx solid #f0e2e5;
  box-shadow: var(--shadow-soft);
}
.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16rpx;
}
.section-title { display: block; font-size: 30rpx; font-weight: 800; margin-bottom: 16rpx; color: #b70f24; }
.section-hint {
  display: block;
  font-size: 24rpx;
  color: #999;
  line-height: 1.6;
}

.summary {
  background: #fff8f9;
  padding: 16rpx;
  border-radius: 14rpx;
  font-size: 26rpx;
  color: #333;
  line-height: 1.6;
  margin-bottom: 16rpx;
}

.pdf-card {
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding: 18rpx;
  border: 1rpx solid #f0e2e5;
  border-radius: 16rpx;
  margin-bottom: 16rpx;
}

.pdf-cover {
  width: 96rpx;
  height: 112rpx;
  border-radius: 12rpx;
  background: linear-gradient(135deg, #ef4444, #b70f24);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  font-weight: 800;
}

.pdf-copy { flex: 1; }
.pdf-title { display: block; font-size: 28rpx; font-weight: 800; color: #202124; }
.pdf-meta { display: block; margin-top: 8rpx; font-size: 23rpx; color: #8a8f98; }

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 10rpx 0;
  font-size: 26rpx;
  border-bottom: 1rpx solid #f0f0f0;
}
.info-row:last-child { border-bottom: none; }
.info-key { color: #666; flex-shrink: 0; margin-right: 16rpx; }
.info-val { color: #333; text-align: right; word-break: break-all; }

.attachment-row {
  display: flex;
  justify-content: space-between;
  padding: 12rpx 0;
  font-size: 26rpx;
  border-bottom: 1rpx solid #f0f0f0;
}
.attachment-row:last-child { border-bottom: none; }
.att-name { color: #333; flex: 1; }
.att-size { color: #999; font-size: 22rpx; }

.record-row { padding: 12rpx 0; border-bottom: 1rpx solid #f0f0f0; }
.record-row:last-child { border-bottom: none; }
.record-head { display: flex; justify-content: space-between; align-items: center; }
.record-action { font-size: 26rpx; padding: 4rpx 14rpx; border-radius: 4rpx; }
.record-action.approve { background: #f6ffed; color: #52c41a; }
.record-action.reject { background: #fff1f0; color: #cf1322; }
.record-action.offline { background: #fff7e6; color: #d46b08; }
.record-action.info { background: #e6f7ff; color: #1890ff; }
.record-time { font-size: 22rpx; color: #999; }
.record-comment {
  display: block;
  font-size: 26rpx;
  color: #333;
  margin-top: 8rpx;
  line-height: 1.6;
}
.record-operator { display: block; font-size: 22rpx; color: #999; margin-top: 4rpx; }

.actions {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 20;
  margin-top: 0;
  padding: 18rpx 24rpx calc(18rpx + env(safe-area-inset-bottom));
  background: rgba(255,255,255,0.98);
  border-top: 1rpx solid #f0e2e5;
  display: flex;
  justify-content: center;
  gap: 16rpx;
  flex-wrap: wrap;
  box-shadow: 0 -8rpx 28rpx rgba(82,28,38,0.08);
}

.actions button {
  flex: 1;
  min-width: 220rpx;
  border-radius: 999rpx;
}

.bottom-spacer { height: 132rpx; }
</style>
