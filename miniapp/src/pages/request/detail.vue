<template>
  <view class="container">
    <EmptyState
      v-if="loading"
      icon="◷"
      tone="muted"
      title="申请详情加载中"
      description="正在获取申请记录，请稍候。"
      compact
    />

    <template v-else-if="detail">
      <view class="hero-card">
        <view class="hero-orb hero-orb-left" />
        <view class="hero-orb hero-orb-right" />
        <view class="hero-main">
          <view class="hero-copy">
            <view class="head-icon">{{ detailIcon(detail.category) }}</view>
            <view class="hero-text">
              <text class="hero-eyebrow">申请详情</text>
              <text class="title">{{ detail.title }}</text>
              <text class="hero-desc">{{ statusNarrative(detail.status) }}</text>
            </view>
          </view>
          <text class="status" :class="detail.status.toLowerCase()">
            {{ statusLabel(detail.status) }}
          </text>
        </view>

        <view class="summary-grid">
          <view class="summary-item">
            <text class="summary-label">编号</text>
            <text class="summary-value">{{ detail.request_no }}</text>
          </view>
          <view class="summary-item">
            <text class="summary-label">类型</text>
            <text class="summary-value">{{ detail.type_name }}</text>
          </view>
          <view class="summary-item">
            <text class="summary-label">提交时间</text>
            <text class="summary-value">{{ detail.submitted_at ? fmt(detail.submitted_at) : "未提交" }}</text>
          </view>
          <view class="summary-item">
            <text class="summary-label">版本</text>
            <text class="summary-value">V{{ detail.revision }}</text>
          </view>
        </view>
      </view>

      <view v-if="detail.status === 'OFFLINE_HANDLED'" class="highlight-card offline-card">
        <view class="section-title-row compact">
          <view>
            <text class="section-kicker">转线下说明</text>
            <text class="section-title">请按线下指引继续办理</text>
          </view>
        </view>
        <text v-if="detail.decision_comment" class="highlight-body">
          {{ detail.decision_comment }}
        </text>
        <text class="highlight-hint">如需进一步确认，请联系负责老师获取后续指导。</text>
      </view>

      <view v-if="isCertificateRequest" class="section proof-section">
        <view class="section-title-row">
          <view>
            <text class="section-kicker">证明文件</text>
            <text class="section-title">PDF 预览</text>
          </view>
          <button
            class="ghost-btn"
            size="mini"
            :disabled="!canPreviewProof"
            :loading="previewing"
            hover-class="hover-opacity"
            @tap="onPreviewProof"
          >
            <text class="btn-icon">查</text>
            <text>预览 PDF</text>
          </button>
        </view>
        <view class="pdf-card">
          <view
            class="pdf-cover"
            :class="{ disabled: !canPreviewProof }"
            hover-class="hover-opacity"
            @tap="onPreviewProof"
          >
            PDF
          </view>
          <view class="pdf-copy">
            <text class="pdf-title">证明材料 PDF 预览</text>
            <text class="pdf-meta">
              {{ canPreviewProof ? "审批通过，可在线预览" : "审批通过后开放预览" }}
            </text>
          </view>
          <text class="pdf-state">{{ canPreviewProof ? "可查看" : "待开放" }}</text>
        </view>
        <text class="section-hint">{{ proofHint }}</text>
      </view>

      <view class="section">
        <view class="section-title-row">
          <view>
            <text class="section-kicker">申请内容</text>
            <text class="section-title">表单与说明</text>
          </view>
        </view>

        <view v-if="detail.summary" class="summary-box">
          <text class="summary-box-label">补充说明</text>
          <text class="summary-box-text">{{ detail.summary }}</text>
        </view>

        <view class="info-list">
          <view v-for="row in formRows" :key="row.key" class="info-row">
            <text class="info-key">{{ row.key }}</text>
            <text class="info-val">{{ row.value }}</text>
          </view>
          <view v-if="!formRows.length" class="empty-tiny">无填写内容</view>
        </view>
      </view>

      <view v-if="detail.attachments?.length" class="section">
        <view class="section-title-row">
          <view>
            <text class="section-kicker">附件</text>
            <text class="section-title">已上传 {{ detail.attachments.length }} 份材料</text>
          </view>
        </view>
        <view class="attachment-list">
          <view
            v-for="attachment in detail.attachments"
            :key="attachment.id"
            class="attachment-card"
          >
            <view class="attachment-icon">文</view>
            <view class="attachment-main">
              <text class="att-name">{{ attachment.filename }}</text>
              <text class="att-meta">
                {{ formatSize(attachment.file_size) }} · {{ fmt(attachment.uploaded_at) }}
              </text>
            </view>
            <text class="attachment-tag">{{ attachmentTag(attachment.mime_type) }}</text>
          </view>
        </view>
      </view>

      <view class="section">
        <view class="section-title-row">
          <view>
            <text class="section-kicker">审批记录</text>
            <text class="section-title">当前流转轨迹</text>
          </view>
        </view>
        <view v-if="!detail.approval_records?.length" class="empty-tiny">暂无审批记录</view>
        <view v-else class="timeline">
          <view
            v-for="(record, index) in detail.approval_records"
            :key="record.id"
            class="timeline-item"
          >
            <view class="timeline-marker">
              <view class="timeline-dot" :class="actionClass(record.action)" />
              <view
                v-if="index !== detail.approval_records.length - 1"
                class="timeline-line"
              />
            </view>
            <view class="record-card">
              <view class="record-head">
                <text class="record-action" :class="actionClass(record.action)">
                  {{ actionLabel(record.action) }}
                </text>
                <text class="record-time">{{ fmt(record.occurred_at) }}</text>
              </view>
              <text class="record-role">
                {{ record.operator_role || "待分配审批人" }}
              </text>
              <text v-if="record.comment" class="record-comment">{{ record.comment }}</text>
              <text class="record-operator">操作人 ID：{{ operatorIdLabel(record.operator_id) }}</text>
            </view>
          </view>
        </view>
      </view>

      <view v-if="canEdit || canWithdraw" class="actions safe-area-inset-bottom">
        <view class="actions-shell">
          <view class="actions-meta">
            <text class="actions-title">{{ footerTitle }}</text>
            <text class="actions-desc">{{ footerDesc }}</text>
          </view>
          <view class="actions-row">
            <button
              v-if="canWithdraw"
              class="action-btn outline"
              size="mini"
              :loading="withdrawing"
              hover-class="hover-opacity"
              @tap="onWithdraw"
            >
              <text class="btn-icon">撤</text>
              <text>撤回申请</text>
            </button>
            <button
              v-if="canEdit"
              class="action-btn primary"
              size="mini"
              hover-class="hover-scale"
              @tap="onEdit"
            >
              <text class="btn-icon">改</text>
              <text>{{ editButtonText }}</text>
            </button>
          </view>
        </view>
      </view>
      <view v-if="canEdit || canWithdraw" class="bottom-spacer" />
    </template>

    <EmptyState
      v-else
      icon="?"
      tone="danger"
      title="未找到申请记录"
      description="该申请可能已失效或无权访问，可返回列表重试。"
      action-text="返回列表"
      @action="goBack"
      compact
    />

    <view v-if="withdrawDialogVisible" class="dialog-mask" @tap="resolveWithdrawDialog(false)">
      <view class="dialog-card" @tap.stop>
        <view class="dialog-icon-wrap warning">
          <text class="dialog-icon warning">!</text>
        </view>
        <text class="dialog-title">确认撤回申请？</text>
        <text class="dialog-desc">
          撤回后当前审批流将终止，已提交内容可在草稿中修改后重新提交。
        </text>
        <view class="dialog-actions">
          <button class="dialog-btn secondary" size="mini" hover-class="hover-opacity" @tap="resolveWithdrawDialog(false)">
            取消
          </button>
          <button class="dialog-btn primary" size="mini" hover-class="hover-scale" @tap="resolveWithdrawDialog(true)">
            确认撤回
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import EmptyState from "@/components/EmptyState.vue";
import {
  getRequestActionLabel,
  getRequestDetail,
  getRequestStatusLabel,
  isEditableRequestStatus,
  previewProof,
  withdrawRequest,
  type RequestDetail,
} from "@/api/workflow";

const detail = ref<RequestDetail | null>(null);
const loading = ref(false);
const withdrawing = ref(false);
const previewing = ref(false);
const requestId = ref<number | null>(null);
const withdrawDialogVisible = ref(false);

let withdrawDialogResolver: ((value: boolean) => void) | null = null;

function goBack() {
  uni.navigateBack({ delta: 1 })
}

function statusLabel(status: string) {
  return getRequestStatusLabel(status);
}

function actionLabel(action: string) {
  return getRequestActionLabel(action);
}

function actionClass(action: string) {
  if (action === "APPROVE") return "approve";
  if (action === "REJECT") return "reject";
  if (action === "OFFLINE_HANDLE") return "offline";
  return "info";
}

function detailIcon(category: string) {
  if (category === "CERTIFICATE") return "证";
  if (category === "LEAVE") return "假";
  if (category === "STAMP") return "章";
  if (category === "REGISTRATION") return "报";
  if (category === "MATERIAL") return "材";
  return "事";
}

function statusNarrative(status: string) {
  if (status === "DRAFT") return "当前仍为草稿状态，可继续完善内容后再提交。";
  if (status === "SUBMITTED" || status === "IN_REVIEW") {
    return "申请已进入审批流，请留意后续审核结果与通知提醒。";
  }
  if (status === "APPROVED") return "申请已审批通过，可查看材料留档与后续结果。";
  if (status === "REJECTED") return "申请已被驳回，请根据意见修改后重新提交。";
  if (status === "WITHDRAWN") return "申请已撤回，如需继续办理可修改后重新提交。";
  if (status === "OFFLINE_HANDLED") return "该事项已转线下办理，请按指引提交纸质或现场材料。";
  return "可查看当前申请的完整流转记录。";
}

function attachmentTag(mimeType?: string | null) {
  if (!mimeType) return "文件";
  if (mimeType.includes("pdf")) return "PDF";
  if (mimeType.includes("image")) return "图片";
  if (mimeType.includes("word") || mimeType.includes("document")) return "DOC";
  return "文件";
}

function fmt(value?: string | null) {
  if (!value) return "-";
  return value.slice(0, 16).replace("T", " ");
}

function formatSize(bytes?: number | null) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  let index = 0;
  let size = bytes;
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024;
    index += 1;
  }
  return `${size.toFixed(index ? 1 : 0)} ${units[index]}`;
}

const formRows = computed(() => {
  if (!detail.value?.form_data) return [];
  return Object.entries(detail.value.form_data).map(([key, value]) => ({
    key,
    value: typeof value === "object" ? JSON.stringify(value) : String(value == null ? "" : value),
  }));
});

const isCertificateRequest = computed(() => detail.value?.category === "CERTIFICATE");
const canPreviewProof = computed(() =>
  !!detail.value && isCertificateRequest.value && detail.value.status === "APPROVED",
);
const proofHint = computed(() => {
  if (!detail.value) return "";
  if (detail.value.status === "OFFLINE_HANDLED") {
    return "该证明已转线下办理，不再生成线上 PDF。";
  }
  if (detail.value.status === "APPROVED") {
    return "审批通过后可直接预览系统生成的证明 PDF。";
  }
  return "证明 PDF 将在审批通过后开放预览。";
});

const canEdit = computed(() => isEditableRequestStatus(detail.value?.status));
const editButtonText = computed(() =>
  detail.value?.status === "REJECTED" ? "修改并重新提交" : "继续完善草稿",
);
const canWithdraw = computed(() =>
  !!detail.value && ["SUBMITTED", "IN_REVIEW"].includes(detail.value.status),
);
const footerTitle = computed(() => {
  if (detail.value?.status === "REJECTED") return "当前申请可修改后重新提交";
  if (canWithdraw.value) return "当前审批流仍在进行中";
  return "当前申请支持继续完善";
});
const footerDesc = computed(() => {
  if (detail.value?.status === "REJECTED") {
    return "建议先根据驳回意见调整内容与附件，再重新提交。";
  }
  if (canWithdraw.value) return "撤回后将回到草稿态，可修改后再次提交。";
  return "可继续补充草稿内容并在准备好后提交。";
});

async function loadDetail() {
  if (requestId.value == null) return;
  loading.value = true;
  try {
    const resp = await getRequestDetail(requestId.value);
    detail.value = resp.data;
  } catch {
    detail.value = null;
  } finally {
    loading.value = false;
  }
}

function onEdit() {
  if (requestId.value == null) return;
  uni.navigateTo({ url: `/pages/request/create?id=${requestId.value}` });
}

function operatorIdLabel(operatorId?: number | string | null) {
  return operatorId == null ? "-" : String(operatorId);
}

function openPdf(filePath: string) {
  return new Promise<void>((resolve, reject) => {
    uni.openDocument({
      filePath,
      fileType: "pdf",
      showMenu: true,
      success: () => resolve(),
      fail: reject,
    });
  });
}

async function onPreviewProof() {
  if (!canPreviewProof.value || requestId.value == null) return;
  previewing.value = true;
  try {
    const { tempFilePath } = await previewProof(requestId.value);
    try {
      await openPdf(tempFilePath);
    } catch {
      uni.showToast({ title: "无法打开 PDF", icon: "none" });
    }
  } catch {
    // 下载失败的提示已由现有 helper 处理
  } finally {
    previewing.value = false;
  }
}

function resolveWithdrawDialog(value: boolean) {
  withdrawDialogVisible.value = false;
  const resolver = withdrawDialogResolver;
  withdrawDialogResolver = null;
  resolver?.(value);
}

function confirmWithdraw() {
  withdrawDialogVisible.value = true;
  return new Promise<boolean>((resolve) => {
    withdrawDialogResolver = resolve;
  });
}

async function onWithdraw() {
  if (requestId.value == null) return;
  if (!(await confirmWithdraw())) return;

  withdrawing.value = true;
  try {
    await withdrawRequest(requestId.value, "学生端主动撤回");
    uni.showToast({ title: "已撤回", icon: "none" });
    await loadDetail();
  } finally {
    withdrawing.value = false;
  }
}

onMounted(() => {
  const pages = getCurrentPages();
  const current = pages[pages.length - 1] as any;
  const options = current?.options || {};
  const parsedId = Number(options.id);
  requestId.value = Number.isFinite(parsedId) ? parsedId : null;
  void loadDetail();
});
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 28rpx 24rpx;
  background:
    radial-gradient(circle at 100% 8%, rgba(183, 15, 36, 0.08), transparent 180rpx),
    linear-gradient(180deg, #fff 0, #fff6f7 220rpx, #f7f1f2 100%),
    #f6f0f1;
}

.empty-tiny {
  text-align: center;
  padding: 28rpx 0;
  color: #94a3b8;
  font-size: 24rpx;
}

.hero-card {
  position: relative;
  overflow: hidden;
  padding: 24rpx;
  border-radius: 20rpx;
  background:
    linear-gradient(180deg, rgba(255, 253, 253, 0.98), rgba(255, 248, 249, 0.98));
  border: 1rpx solid #f0c9cf;
  border-top: 6rpx solid #b70f24;
  box-shadow: 0 12rpx 30rpx rgba(146, 18, 36, 0.08);
}

.hero-orb {
  display: none;
}

.hero-orb-left {
  width: 180rpx;
  height: 180rpx;
  left: -58rpx;
  top: -60rpx;
}

.hero-orb-right {
  width: 220rpx;
  height: 220rpx;
  right: -74rpx;
  bottom: -96rpx;
}

.hero-main {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18rpx;
}

.hero-copy {
  display: flex;
  gap: 18rpx;
  align-items: center;
  flex: 1;
  min-width: 0;
}

.head-icon {
  width: 92rpx;
  height: 92rpx;
  border-radius: 26rpx;
  background: linear-gradient(135deg, #d51f35, #9f1021);
  box-shadow: 0 10rpx 20rpx rgba(183, 15, 36, 0.16);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 34rpx;
  font-weight: 800;
  flex-shrink: 0;
}

.hero-text {
  min-width: 0;
}

.hero-eyebrow {
  display: inline-flex;
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
  background: #fff1f2;
  color: #b70f24;
  font-size: 20rpx;
  letter-spacing: 1rpx;
}

.title {
  display: block;
  margin-top: 12rpx;
  font-size: 32rpx;
  font-weight: 800;
  line-height: 1.45;
  color: #1f2937;
}

.hero-desc {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: #8a7278;
}

.status {
  flex-shrink: 0;
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: #fff1f2;
  color: #b70f24;
  font-size: 22rpx;
  font-weight: 700;
}

.status.draft {
  background: rgba(241, 245, 249, 0.18);
}

.status.submitted,
.status.in_review {
  background: rgba(255, 247, 237, 0.18);
}

.status.approved {
  background: rgba(240, 253, 244, 0.18);
}

.status.rejected {
  background: rgba(255, 241, 242, 0.18);
}

.status.withdrawn {
  background: rgba(248, 250, 252, 0.16);
}

.status.offline_handled {
  background: rgba(255, 247, 237, 0.2);
}

.summary-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
  margin-top: 22rpx;
}

.summary-item {
  padding: 18rpx 16rpx;
  border-radius: 20rpx;
  background: #fff8f9;
  box-shadow: inset 0 0 0 1rpx rgba(183, 15, 36, 0.08);
}

.summary-label {
  display: block;
  font-size: 20rpx;
  color: #a88890;
}

.summary-value {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  line-height: 1.6;
  font-weight: 700;
  color: #334155;
  word-break: break-all;
}

.highlight-card,
.section {
  margin-top: 18rpx;
  padding: 24rpx;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid rgba(240, 226, 229, 0.94);
  box-shadow: 0 16rpx 36rpx rgba(41, 18, 23, 0.08);
}

.offline-card {
  background: linear-gradient(180deg, #fff8ef, #fffdf9);
  border-color: rgba(245, 158, 11, 0.22);
}

.section-title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16rpx;
}

.section-title-row.compact {
  margin-bottom: 8rpx;
}

.section-kicker {
  display: inline-flex;
  padding: 4rpx 14rpx;
  border-radius: 999rpx;
  background: #fff1f2;
  color: #b70f24;
  font-size: 20rpx;
}

.section-title {
  display: block;
  margin-top: 10rpx;
  font-size: 30rpx;
  font-weight: 800;
  color: #1f2937;
}

.highlight-body {
  display: block;
  margin-top: 14rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: #92400e;
}

.highlight-hint {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #b45309;
}

.ghost-btn,
.ghost-btn::after,
.action-btn,
.action-btn::after,
.dialog-btn,
.dialog-btn::after {
  border-radius: 999rpx;
}

.ghost-btn {
  min-width: 160rpx;
  color: #b70f24;
  background: #fff1f2;
  border: 1rpx solid rgba(183, 15, 36, 0.16);
}

.pdf-card {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 18rpx;
  padding: 18rpx;
  border-radius: 22rpx;
  background: linear-gradient(135deg, #fffafa, #fbfcfd);
  box-shadow: inset 0 0 0 1rpx rgba(240, 226, 229, 0.9);
}

.pdf-cover {
  width: 96rpx;
  height: 116rpx;
  border-radius: 18rpx;
  background: linear-gradient(135deg, #ef4444, #b70f24);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  font-weight: 800;
  flex-shrink: 0;
}

.pdf-cover.disabled {
  background: linear-gradient(135deg, #cbd5e1, #94a3b8);
  color: rgba(255, 255, 255, 0.92);
}

.pdf-copy {
  flex: 1;
  min-width: 0;
}

.pdf-title {
  display: block;
  font-size: 28rpx;
  font-weight: 800;
  color: #1f2937;
}

.pdf-meta,
.section-hint {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #94a3b8;
}

.pdf-state {
  flex-shrink: 0;
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  background: #fff1f2;
  color: #b70f24;
  font-size: 20rpx;
}

.summary-box {
  margin-top: 18rpx;
  padding: 18rpx;
  border-radius: 20rpx;
  background: linear-gradient(180deg, #fff8f9, #fffdfd);
  box-shadow: inset 0 0 0 1rpx rgba(240, 226, 229, 0.84);
}

.summary-box-label {
  display: block;
  font-size: 22rpx;
  color: #b70f24;
}

.summary-box-text {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: #334155;
}

.info-list {
  margin-top: 18rpx;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.info-row {
  display: flex;
  justify-content: space-between;
  gap: 18rpx;
  padding: 18rpx;
  border-radius: 20rpx;
  background: #fbfcfd;
  box-shadow: inset 0 0 0 1rpx rgba(226, 232, 240, 0.68);
}

.info-key {
  flex-shrink: 0;
  font-size: 22rpx;
  color: #64748b;
}

.info-val {
  flex: 1;
  text-align: right;
  font-size: 22rpx;
  line-height: 1.7;
  color: #1f2937;
  word-break: break-all;
}

.attachment-list {
  margin-top: 18rpx;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.attachment-card {
  display: flex;
  align-items: center;
  gap: 14rpx;
  padding: 18rpx;
  border-radius: 20rpx;
  background: #fbfcfd;
  box-shadow: inset 0 0 0 1rpx rgba(226, 232, 240, 0.68);
}

.attachment-icon {
  width: 60rpx;
  height: 60rpx;
  border-radius: 18rpx;
  background: #fff1f2;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  flex-shrink: 0;
}

.attachment-main {
  flex: 1;
  min-width: 0;
}

.att-name {
  display: block;
  font-size: 24rpx;
  color: #1f2937;
  word-break: break-all;
}

.att-meta {
  display: block;
  margin-top: 6rpx;
  font-size: 20rpx;
  color: #94a3b8;
}

.attachment-tag {
  flex-shrink: 0;
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  background: #fff1f2;
  color: #b70f24;
  font-size: 20rpx;
}

.timeline {
  margin-top: 18rpx;
}

.timeline-item {
  display: flex;
  gap: 16rpx;
}

.timeline-marker {
  width: 28rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
}

.timeline-dot {
  width: 20rpx;
  height: 20rpx;
  border-radius: 50%;
  background: #94a3b8;
  margin-top: 12rpx;
}

.timeline-dot.approve {
  background: #16a34a;
}

.timeline-dot.reject {
  background: #e11d48;
}

.timeline-dot.offline {
  background: #d97706;
}

.timeline-dot.info {
  background: #b70f24;
}

.timeline-line {
  width: 4rpx;
  flex: 1;
  margin-top: 8rpx;
  background: rgba(226, 232, 240, 0.92);
  border-radius: 999rpx;
}

.record-card {
  flex: 1;
  min-width: 0;
  padding: 18rpx;
  border-radius: 20rpx;
  background: #fbfcfd;
  box-shadow: inset 0 0 0 1rpx rgba(226, 232, 240, 0.68);
  margin-bottom: 14rpx;
}

.record-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14rpx;
}

.record-action {
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  font-weight: 700;
}

.record-action.approve {
  background: #f0fdf4;
  color: #15803d;
}

.record-action.reject {
  background: #fff1f2;
  color: #be123c;
}

.record-action.offline {
  background: #fff7ed;
  color: #b45309;
}

.record-action.info {
  background: #fff1f2;
  color: #b70f24;
}

.record-time,
.record-role,
.record-operator {
  display: block;
  font-size: 20rpx;
  line-height: 1.6;
  color: #94a3b8;
}

.record-role {
  margin-top: 10rpx;
}

.record-comment {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: #334155;
}

.record-operator {
  margin-top: 8rpx;
}

.actions {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 20;
  padding: 0 20rpx calc(20rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
}

.actions-shell {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  padding: 18rpx;
  border-radius: 0;
  background: rgba(255, 255, 255, 0.98);
  border-top: 1rpx solid rgba(240, 226, 229, 0.94);
  box-shadow: 0 -12rpx 30rpx rgba(41, 18, 23, 0.1);
}

.actions-meta {
  display: none;
  flex: 1;
  min-width: 0;
}

.actions-title {
  display: block;
  font-size: 26rpx;
  font-weight: 700;
  color: #1f2937;
}

.actions-desc {
  display: block;
  margin-top: 6rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #94a3b8;
}

.actions-row {
  display: flex;
  gap: 10rpx;
  flex: 1;
}

.btn-icon {
  width: 36rpx;
  height: 36rpx;
  margin-right: 10rpx;
  border-radius: 14rpx;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
  font-weight: 900;
  background: rgba(183, 15, 36, 0.08);
  border: 1rpx solid rgba(183, 15, 36, 0.18);
}

.action-btn.primary .btn-icon {
  background: rgba(255, 255, 255, 0.18);
  border-color: rgba(255, 255, 255, 0.28);
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
  flex: 1;
  height: 72rpx;
  padding: 0 24rpx;
  border-radius: 999rpx;
  font-size: 28rpx;
  font-weight: 700;
}

.action-btn::after {
  border: none;
}

.action-btn.outline {
  color: #b70f24;
  background: #fff;
  border: 1rpx solid rgba(183, 15, 36, 0.18);
}

.action-btn.primary {
  color: #fff;
  background: linear-gradient(135deg, #d51f35, #b70f24);
  box-shadow: 0 12rpx 24rpx rgba(183, 15, 36, 0.22);
}

.bottom-spacer {
  height: 188rpx;
}

.dialog-mask {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 36rpx;
  background: rgba(17, 24, 39, 0.48);
}

.dialog-card {
  width: 100%;
  max-width: 620rpx;
  position: relative;
  overflow: visible;
  padding: 76rpx 28rpx 28rpx;
  border-radius: 28rpx;
  background: #fff;
  box-shadow: 0 24rpx 48rpx rgba(15, 23, 42, 0.24);
}

.dialog-icon-wrap {
  position: absolute;
  top: -42rpx;
  left: 50%;
  transform: translateX(-50%);
  width: 104rpx;
  height: 104rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #fff5f6, #ffe8eb);
  box-shadow: 0 12rpx 26rpx rgba(183, 15, 36, 0.16);
  display: flex;
  align-items: center;
  justify-content: center;
}

.dialog-icon-wrap.warning {
  background: linear-gradient(135deg, #fff7ed, #ffedd5);
  box-shadow: 0 12rpx 26rpx rgba(217, 119, 6, 0.16);
}

.dialog-icon {
  color: #b70f24;
  font-size: 42rpx;
  font-weight: 800;
}

.dialog-icon.warning {
  color: #d97706;
}

.dialog-title {
  display: block;
  text-align: center;
  font-size: 34rpx;
  font-weight: 800;
  color: #1f2937;
}

.dialog-desc {
  display: block;
  margin-top: 12rpx;
  text-align: center;
  font-size: 24rpx;
  line-height: 1.7;
  color: #64748b;
}

.dialog-actions {
  display: flex;
  gap: 16rpx;
  margin-top: 28rpx;
}

.dialog-btn {
  flex: 1;
  font-size: 26rpx;
  font-weight: 700;
}

.dialog-btn.secondary {
  color: #475569;
  background: #f8fafc;
}

.dialog-btn.primary {
  color: #fff;
  background: linear-gradient(135deg, #d51f35, #b70f24);
}
</style>
