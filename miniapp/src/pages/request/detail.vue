<template>
  <view class="container">
    <view v-if="loading" class="loading">加载中...</view>

    <template v-else-if="detail">
      <view class="head-card">
        <view class="head-row">
          <text class="title">{{ detail.title }}</text>
          <text class="status" :class="detail.status.toLowerCase()">
            {{ statusLabel(detail.status) }}
          </text>
        </view>
        <text class="meta">编号：{{ detail.request_no }}</text>
        <text class="meta">类型：{{ detail.type_name }} · {{ categoryLabel(detail.category) }}</text>
        <text class="meta" v-if="detail.submitted_at">
          提交时间：{{ fmt(detail.submitted_at) }}
        </text>
        <text class="meta">版本：v{{ detail.revision }}</text>
      </view>

      <!-- 转线下提示 -->
      <view v-if="detail.status === 'OFFLINE_HANDLED'" class="offline-card">
        <text class="offline-title">该事项已转线下办理</text>
        <text class="offline-body" v-if="detail.decision_comment">
          {{ detail.decision_comment }}
        </text>
        <text class="offline-hint">如需进一步确认，请联系老师获取后续指导。</text>
      </view>

      <!-- 表单数据 -->
      <view class="section">
        <text class="section-title">申请内容</text>
        <view v-if="detail.summary" class="summary">
          <text>{{ detail.summary }}</text>
        </view>
        <view
          v-for="row in formRows"
          :key="row.key"
          class="info-row"
        >
          <text class="info-key">{{ row.key }}</text>
          <text class="info-val">{{ row.value }}</text>
        </view>
        <view v-if="!formRows.length" class="empty-tiny">无填写内容</view>
      </view>

      <!-- 附件 -->
      <view v-if="detail.attachments?.length" class="section">
        <text class="section-title">附件</text>
        <view v-for="a in detail.attachments" :key="a.id" class="attachment-row">
          <text class="att-name">{{ a.file_name }}</text>
          <text class="att-size">{{ formatSize(a.file_size) }}</text>
        </view>
      </view>

      <!-- 审批记录 -->
      <view class="section">
        <text class="section-title">审批记录</text>
        <view v-if="!detail.approval_records?.length" class="empty-tiny">暂无审批记录</view>
        <view
          v-for="r in detail.approval_records"
          :key="r.id"
          class="record-row"
        >
          <view class="record-head">
            <text class="record-action" :class="actionClass(r.action)">
              {{ actionLabel(r.action) }}
            </text>
            <text class="record-time">{{ fmt(r.operated_at) }}</text>
          </view>
          <text class="record-comment" v-if="r.comment">{{ r.comment }}</text>
          <text class="record-operator">操作人 ID：{{ r.operator_user_id }}</text>
        </view>
      </view>

      <!-- 操作按钮 -->
      <view class="actions" v-if="canWithdraw">
        <button type="warn" size="mini" :loading="withdrawing" @tap="onWithdraw">撤回申请</button>
      </view>
    </template>

    <view v-else class="empty">未找到申请记录</view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  getRequestDetail, withdrawRequest,
  type RequestDetail,
} from '@/api/workflow'

const detail = ref<RequestDetail | null>(null)
const loading = ref(false)
const withdrawing = ref(false)
const requestId = ref<number | null>(null)

const STATUS_LABELS: Record<string, string> = {
  DRAFT: '草稿',
  SUBMITTED: '已提交',
  IN_REVIEW: '审核中',
  APPROVED: '已通过',
  REJECTED: '已驳回',
  WITHDRAWN: '已撤回',
  OFFLINE_HANDLED: '转线下',
}
function statusLabel(s: string) { return STATUS_LABELS[s] || s }

const CATEGORY_LABELS: Record<string, string> = {
  LEAVE: '请假', CERTIFICATE: '证明', STAMP: '盖章',
  REGISTRATION: '报名', MATERIAL: '材料', OTHER: '其他',
}
function categoryLabel(c: string) { return CATEGORY_LABELS[c] || c }

const ACTION_LABELS: Record<string, string> = {
  CLAIM: '受理',
  APPROVE: '通过',
  REJECT: '驳回',
  WITHDRAW: '撤回',
  OFFLINE: '转线下',
}
function actionLabel(a: string) { return ACTION_LABELS[a] || a }
function actionClass(a: string) {
  if (a === 'APPROVE') return 'approve'
  if (a === 'REJECT') return 'reject'
  if (a === 'OFFLINE') return 'offline'
  return 'info'
}

function fmt(s?: string | null) {
  if (!s) return '-'
  return s.slice(0, 16).replace('T', ' ')
}

function formatSize(bytes: number) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0; let v = bytes
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i++ }
  return `${v.toFixed(i ? 1 : 0)} ${units[i]}`
}

const formRows = computed(() => {
  if (!detail.value?.form_data) return []
  return Object.entries(detail.value.form_data).map(([k, v]) => ({
    key: k,
    value: typeof v === 'object' ? JSON.stringify(v) : String(v ?? ''),
  }))
})

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

async function onWithdraw() {
  if (requestId.value == null) return
  const confirm = await new Promise<boolean>((resolve) => {
    uni.showModal({
      title: '撤回申请',
      content: '撤回后需重新提交，确定继续吗？',
      success: (r) => resolve(r.confirm),
      fail: () => resolve(false),
    })
  })
  if (!confirm) return
  withdrawing.value = true
  try {
    await withdrawRequest(requestId.value, '学生端主动撤回')
    uni.showToast({ title: '已撤回' })
    await loadDetail()
  } finally {
    withdrawing.value = false
  }
}

onMounted(() => {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1] as any
  const opts = current?.options || {}
  requestId.value = Number(opts.id)
  loadDetail()
})
</script>

<style scoped>
.container { padding: 24rpx; }
.loading, .empty { text-align: center; padding: 80rpx 0; color: #999; font-size: 28rpx; }
.empty-tiny { text-align: center; padding: 16rpx 0; color: #bbb; font-size: 24rpx; }

.head-card {
  background: #fff; padding: 24rpx; border-radius: 12rpx;
  margin-bottom: 16rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06);
}
.head-row { display: flex; justify-content: space-between; align-items: flex-start; }
.title { font-size: 32rpx; font-weight: 600; flex: 1; }
.status { font-size: 22rpx; padding: 4rpx 14rpx; border-radius: 4rpx; flex-shrink: 0; margin-left: 12rpx; }
.status.draft { background: #f5f5f5; color: #666; }
.status.submitted, .status.in_review { background: #e6f7ff; color: #1890ff; }
.status.approved { background: #f6ffed; color: #52c41a; }
.status.rejected { background: #fff1f0; color: #cf1322; }
.status.withdrawn { background: #f5f5f5; color: #999; }
.status.offline_handled { background: #fff7e6; color: #d46b08; }
.meta { display: block; font-size: 24rpx; color: #999; margin-top: 4rpx; }

.offline-card {
  background: #fff7e6; border-left: 8rpx solid #d46b08;
  border-radius: 8rpx; padding: 20rpx;
  margin-bottom: 16rpx;
}
.offline-title { display: block; font-size: 28rpx; font-weight: 600; color: #ad6800; }
.offline-body { display: block; font-size: 26rpx; color: #333; margin-top: 8rpx; line-height: 1.6; }
.offline-hint { display: block; font-size: 24rpx; color: #999; margin-top: 8rpx; }

.section {
  background: #fff; padding: 24rpx; border-radius: 12rpx;
  margin-bottom: 16rpx;
}
.section-title { display: block; font-size: 28rpx; font-weight: 600; margin-bottom: 16rpx; }

.summary {
  background: #fafafa; padding: 16rpx; border-radius: 8rpx;
  font-size: 26rpx; color: #333; line-height: 1.6;
  margin-bottom: 16rpx;
}

.info-row {
  display: flex; justify-content: space-between;
  padding: 10rpx 0; font-size: 26rpx;
  border-bottom: 1rpx solid #f0f0f0;
}
.info-row:last-child { border-bottom: none; }
.info-key { color: #666; flex-shrink: 0; margin-right: 16rpx; }
.info-val { color: #333; text-align: right; word-break: break-all; }

.attachment-row {
  display: flex; justify-content: space-between;
  padding: 12rpx 0; font-size: 26rpx;
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
  display: block; font-size: 26rpx; color: #333;
  margin-top: 8rpx; line-height: 1.6;
}
.record-operator { display: block; font-size: 22rpx; color: #999; margin-top: 4rpx; }

.actions { margin-top: 24rpx; text-align: center; }
</style>
