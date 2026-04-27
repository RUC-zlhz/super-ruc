<template>
  <view class="container">
    <view v-if="!activeType" class="type-list-wrap">
      <view class="hero-card type-hero">
        <view class="hero-orb hero-orb-left" />
        <view class="hero-orb hero-orb-right" />
        <view class="hero-main">
          <view class="hero-copy">
            <view class="hero-icon-wrap">
              <text class="hero-icon">📝</text>
            </view>
            <view class="hero-text">
              <text class="hero-eyebrow">事务申请中心</text>
              <text class="hero-title">先选择类型，再完善表单与材料</text>
              <text class="hero-desc">
                支持草稿保存、附件补交和确认后提交，流程更清晰。
              </text>
            </view>
          </view>
          <view class="hero-side">
            <text class="hero-side-label">当前可发起</text>
            <text class="hero-side-value">{{ loadingTypes ? "--" : types.length }}</text>
            <text class="hero-side-note">类事务</text>
          </view>
        </view>
      </view>

      <view class="type-panel">
        <view class="panel-head">
          <view>
            <text class="section-kicker">申请类型</text>
            <text class="section-title">请选择要办理的事务</text>
          </view>
          <text class="panel-meta">{{ loadingTypes ? "加载中" : `${types.length} 类` }}</text>
        </view>

        <view v-if="loadingTypes" class="empty">加载中...</view>

        <view v-else class="type-grid">
          <view
            v-for="t in types"
            :key="t.id"
            class="type-item"
            @tap="onPickType(t)"
          >
            <view class="type-item-top">
              <view class="type-icon">{{ typeIcon(t.code, t.category) }}</view>
              <text class="type-cat">{{ categoryLabel(t.category) }}</text>
            </view>
            <text class="type-name">{{ t.name }}</text>
            <text v-if="t.description" class="type-desc">{{ t.description }}</text>
            <text class="type-meta">
              {{ t.attachment_required ? "需上传附件" : "附件可选" }}
              · 审批角色：{{ t.approver_roles }}
            </text>
            <view class="type-cta">
              <text>选择并填写</text>
              <text class="type-cta-arrow">›</text>
            </view>
          </view>
        </view>

        <view v-if="!loadingTypes && !types.length" class="empty">暂无可发起的事务</view>
      </view>
    </view>

    <view v-else class="form-wrap">
      <view class="hero-card form-hero">
        <view class="hero-orb hero-orb-left" />
        <view class="hero-orb hero-orb-right" />
        <view class="hero-main">
          <view class="hero-copy">
            <view class="hero-icon-wrap large">
              <text class="hero-icon">{{ typeIcon(activeType.code, activeType.category) }}</text>
            </view>
            <view class="hero-text">
              <text class="hero-eyebrow">{{ draftId ? "草稿已建立" : "新建申请" }}</text>
              <text class="hero-title">{{ activeType.name }}</text>
              <text class="hero-desc">
                {{ activeType.description || "先保存草稿，再补充材料并确认提交。" }}
              </text>
            </view>
          </view>
          <text class="hero-status" :class="currentStatusClass">
            {{ draftStatus ? statusLabel(draftStatus) : "未提交" }}
          </text>
        </view>
        <view class="hero-strip">
          <view class="hero-strip-item">
            <text class="hero-strip-label">当前步骤</text>
            <text class="hero-strip-value">{{ currentStepIndex }}/3</text>
          </view>
          <view class="hero-strip-item">
            <text class="hero-strip-label">附件要求</text>
            <text class="hero-strip-value">{{ activeType.attachment_required ? "必传" : "可选" }}</text>
          </view>
          <view class="hero-strip-item">
            <text class="hero-strip-label">摘要状态</text>
            <text class="hero-strip-value">{{ summaryStateLabel }}</text>
          </view>
        </view>
      </view>

      <view class="step-card">
        <view class="panel-head compact">
          <view>
            <text class="section-kicker">填写状态</text>
            <text class="section-title">办理步骤</text>
          </view>
          <text class="panel-meta">{{ currentStepIndex }}/3</text>
        </view>
        <view class="step-track">
          <view
            v-for="item in stepItems"
            :key="item.key"
            class="step-node"
            :class="item.state"
          >
            <view class="step-dot">{{ item.index }}</view>
            <view class="step-copy">
              <text class="step-label">{{ item.label }}</text>
              <text class="step-hint">{{ item.hint }}</text>
            </view>
            <text class="step-state">{{ item.stateText }}</text>
          </view>
        </view>
      </view>

      <view
        v-if="draftStatus === 'REJECTED' && draftDetail?.decision_comment"
        class="notice-card warning"
      >
        <text class="notice-title">驳回意见</text>
        <text class="notice-body">{{ draftDetail.decision_comment }}</text>
      </view>

      <view v-if="formErrors.length" class="notice-card error">
        <text class="notice-title">提交前请先处理以下问题</text>
        <text v-for="error in formErrors" :key="error" class="notice-body">{{ error }}</text>
      </view>

      <view class="field-card">
        <view class="field-head">
          <text class="field-title">标题</text>
          <text class="field-status">{{ title.trim() ? "已完成" : "待填写" }}</text>
        </view>
        <text class="field-label">申请标题 <text class="required">*</text></text>
        <input class="input" v-model="title" placeholder="请简要描述事由" />
      </view>

      <view class="field-card">
        <view class="field-head">
          <text class="field-title">动态表单</text>
          <text class="field-status">{{ dynamicFormStatusLabel }}</text>
        </view>
        <DynamicForm
          ref="dynamicFormRef"
          v-model="formData"
          :schema="activeType.form_schema || null"
        />
      </view>

      <view class="field-card">
        <view class="field-head">
          <text class="field-title">补充说明</text>
          <text class="field-status">{{ summary.trim() ? "已填写" : "选填" }}</text>
        </view>
        <textarea class="textarea" v-model="summary" placeholder="（可选）其他补充信息" />
      </view>

      <view class="section-block">
        <view class="section-head">
          <view>
            <text class="field-title">附件材料</text>
            <text class="section-hint">{{ attachmentHint }}</text>
          </view>
          <button
            class="ghost-btn"
            size="mini"
            :disabled="!draftId"
            :loading="uploading"
            @tap="onUploadAttachment"
          >
            上传附件
          </button>
        </view>

        <view v-if="attachments.length" class="attachment-list">
          <view v-for="attachment in attachments" :key="attachment.id" class="attachment-row">
            <view class="attachment-icon">📄</view>
            <view class="attachment-main">
              <text class="att-name">{{ attachment.filename }}</text>
              <text class="att-meta">{{ formatSize(attachment.file_size) }}</text>
            </view>
            <text class="attachment-state">已上传</text>
          </view>
        </view>

        <view v-else class="empty-attachment">
          <text class="empty-attachment-icon">+</text>
          <text class="empty-attachment-title">
            {{ draftId ? "暂无已上传附件" : "请先保存草稿后再上传附件" }}
          </text>
          <text class="empty-attachment-desc">
            {{ activeType.attachment_required ? "该类型提交前至少上传 1 个附件。" : "若需要补充证明材料，可在保存草稿后上传。" }}
          </text>
        </view>
      </view>

      <view class="submit-summary">
        <view class="summary-watermark">印</view>
        <text class="summary-title">提交摘要</text>
        <view class="summary-list">
          <view class="summary-row">
            <text class="summary-key">事务类型</text>
            <text class="summary-value">{{ activeType.name }}</text>
          </view>
          <view class="summary-row">
            <text class="summary-key">申请标题</text>
            <text class="summary-value">{{ title.trim() || "未填写" }}</text>
          </view>
          <view class="summary-row">
            <text class="summary-key">附件材料</text>
            <text class="summary-value">
              {{ attachments.length ? `已上传 ${attachments.length} 份` : "暂无附件" }}
            </text>
          </view>
          <view class="summary-row">
            <text class="summary-key">待处理问题</text>
            <text class="summary-value">{{ formErrors.length ? `${formErrors.length} 项待修正` : "无" }}</text>
          </view>
        </view>
      </view>

      <view class="footer-spacer" />

      <view class="footer safe-area-inset-bottom">
        <view class="footer-shell">
          <view class="footer-meta">
            <text class="footer-title">{{ draftId ? "草稿已建立，可继续补充材料" : "先保存草稿后可上传附件" }}</text>
            <text class="footer-desc">{{ footerHint }}</text>
          </view>
          <view class="footer-actions">
            <button v-if="!draftId" class="action-btn light" size="mini" @tap="onReset">重选</button>
            <button class="action-btn outline" size="mini" :loading="saving" @tap="onSave">
              {{ draftId ? "保存修改" : "保存草稿" }}
            </button>
            <button class="action-btn primary" size="mini" :loading="submitting" @tap="onSubmit">
              {{ submitButtonText }}
            </button>
          </view>
        </view>
      </view>
    </view>

    <view v-if="submitDialogVisible" class="dialog-mask" @tap="resolveSubmitDialog(false)">
      <view class="dialog-card" @tap.stop>
        <view class="dialog-icon-wrap">
          <text class="dialog-icon">✦</text>
        </view>
        <text class="dialog-title">确认提交申请？</text>
        <text class="dialog-desc">
          提交后将进入审批流程，请确认信息与附件无误。
        </text>
        <view class="dialog-summary">
          <view v-for="item in submitDialogRows" :key="item.label" class="dialog-row">
            <text class="dialog-row-label">{{ item.label }}</text>
            <text class="dialog-row-value">{{ item.value }}</text>
          </view>
        </view>
        <view class="dialog-actions">
          <button class="dialog-btn secondary" size="mini" @tap="resolveSubmitDialog(false)">
            再检查
          </button>
          <button class="dialog-btn primary" size="mini" @tap="resolveSubmitDialog(true)">
            {{ draftStatus === "REJECTED" ? "确认重提" : "确认提交" }}
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import DynamicForm from "@/components/DynamicForm.vue";
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
} from "@/api/workflow";

const types = ref<RequestType[]>([]);
const loadingTypes = ref(false);

const activeType = ref<RequestType | null>(null);
const title = ref("");
const summary = ref("");
const formData = ref<Record<string, any>>({});
const attachments = ref<RequestAttachment[]>([]);
const draftId = ref<number | null>(null);
const draftStatus = ref<RequestStatus | null>(null);
const draftDetail = ref<RequestDetail | null>(null);
const routeRequestId = ref<number | null>(null);

const dynamicFormRef = ref<InstanceType<typeof DynamicForm> | null>(null);
const saving = ref(false);
const submitting = ref(false);
const uploading = ref(false);
const formErrors = ref<string[]>([]);
const submitDialogVisible = ref(false);

let submitDialogResolver: ((value: boolean) => void) | null = null;

const attachmentStepDone = computed(() => {
  if (!activeType.value || !draftId.value) return false;
  return !activeType.value.attachment_required || attachments.value.length > 0;
});

const submitButtonText = computed(() =>
  draftStatus.value === "REJECTED" ? "重新提交申请" : "提交申请",
);

const currentStatusClass = computed(() =>
  draftStatus.value ? draftStatus.value.toLowerCase() : "draft",
);

const currentStepIndex = computed(() => {
  if (!draftId.value) return 1;
  if (!attachmentStepDone.value) return 2;
  return 3;
});

const summaryStateLabel = computed(() => {
  if (formErrors.value.length) return "待修正";
  if (!draftId.value) return "待生成";
  return "已就绪";
});

const dynamicFormStatusLabel = computed(() =>
  formErrors.value.some((item) => item.includes("动态表单")) ? "待完善" : "按要求填写",
);

const stepItems = computed(() => {
  const submitLabel = draftStatus.value === "REJECTED" ? "重新提交申请" : "提交申请";
  return [
    {
      key: "draft",
      index: 1,
      label: "保存草稿",
      hint: draftId.value ? "已建立可编辑版本" : "保存后才可上传附件",
      state: draftId.value ? "done" : "active",
      stateText: draftId.value ? "已完成" : "进行中",
    },
    {
      key: "attachment",
      index: 2,
      label: `上传附件${activeType.value?.attachment_required ? "（必填）" : "（可选）"}`,
      hint: attachmentStepDone.value
        ? `已上传 ${attachments.value.length} 份`
        : activeType.value?.attachment_required
          ? "提交前需至少上传 1 份附件"
          : "可按需补充证明材料",
      state: !draftId.value ? "pending" : attachmentStepDone.value ? "done" : "active",
      stateText: !draftId.value ? "待开始" : attachmentStepDone.value ? "已完成" : "进行中",
    },
    {
      key: "submit",
      index: 3,
      label: submitLabel,
      hint: draftStatus.value === "REJECTED" ? "确认按驳回意见修改后再重提" : "提交后将进入审批流",
      state: !draftId.value || !attachmentStepDone.value ? "pending" : "active",
      stateText: !draftId.value || !attachmentStepDone.value ? "待开始" : "待确认",
    },
  ];
});

const attachmentHint = computed(() => {
  if (!activeType.value) return "";
  if (!draftId.value) {
    return activeType.value.attachment_required
      ? "该类型需先保存草稿，再上传至少 1 个附件。"
      : "如需补充材料，请先保存草稿后再上传附件。";
  }
  if (!attachments.value.length) {
    return activeType.value.attachment_required
      ? "该类型提交前必须至少上传 1 个附件。"
      : "附件为可选项，可按需上传补充材料。";
  }
  return `当前已上传 ${attachments.value.length} 个附件。`;
});

const footerHint = computed(() => {
  if (!activeType.value) return "";
  if (!draftId.value) return "保存后可上传附件，提交前会再次确认摘要。";
  if (activeType.value.attachment_required && !attachments.value.length) {
    return "该类型必须上传附件后才能提交。";
  }
  return draftStatus.value === "REJECTED"
    ? "确认已按驳回意见修改后再重新提交。"
    : "提交后将进入审批流。";
});

const submitDialogRows = computed(() => [
  {
    label: "类型",
    value: activeType.value?.name || "-",
  },
  {
    label: "附件",
    value: attachments.value.length ? `${attachments.value.length} 份` : "无",
  },
  {
    label: "待处理",
    value: formErrors.value.length ? `${formErrors.value.length} 项` : "无",
  },
]);

function categoryLabel(category: string) {
  return getRequestCategoryLabel(category);
}

function typeIcon(code: string, category: string) {
  if (category === "CERTIFICATE" || code.includes("CERT")) return "证";
  if (code.includes("GRADE") || code.includes("SCORE")) return "绩";
  if (code.includes("SCHOLAR") || code.includes("HONOR")) return "奖";
  if (code.includes("DORM")) return "宿";
  if (code.includes("LEAVE")) return "假";
  return "事";
}

function statusLabel(status: string) {
  return getRequestStatusLabel(status);
}

function formatSize(bytes?: number | null) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  let index = 0;
  let value = bytes;
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024;
    index += 1;
  }
  return `${value.toFixed(index ? 1 : 0)} ${units[index]}`;
}

function resetDraftState() {
  title.value = "";
  summary.value = "";
  formData.value = {};
  attachments.value = [];
  draftId.value = null;
  draftStatus.value = null;
  draftDetail.value = null;
  formErrors.value = [];
}

function setFormErrors(errors: string[]) {
  formErrors.value = Array.from(new Set(errors.filter(Boolean)));
}

function syncDraftDetail(detail: RequestDetail) {
  draftId.value = detail.id;
  draftStatus.value = detail.status as RequestStatus;
  draftDetail.value = detail;
  attachments.value = [...detail.attachments];
}

async function loadTypes() {
  loadingTypes.value = true;
  try {
    const resp = await listRequestTypes();
    types.value = resp.data;
  } finally {
    loadingTypes.value = false;
  }
}

async function loadEditableDraft(id: number) {
  const resp = await getRequestDetail(id);
  const detail = resp.data;
  if (!isEditableRequestStatus(detail.status)) {
    uni.showToast({ title: "当前申请不可编辑", icon: "none" });
    uni.redirectTo({ url: `/pages/request/detail?id=${id}` });
    return;
  }
  const matchedType = types.value.find((item) => item.code === detail.type_code);
  if (!matchedType) {
    uni.showToast({ title: "当前事务类型不可继续编辑", icon: "none" });
    uni.redirectTo({ url: `/pages/request/detail?id=${id}` });
    return;
  }
  activeType.value = matchedType;
  title.value = detail.title;
  summary.value = detail.summary || "";
  formData.value = { ...detail.form_data };
  syncDraftDetail(detail);
}

function onPickType(type: RequestType) {
  resetDraftState();
  routeRequestId.value = null;
  activeType.value = type;
}

function onReset() {
  resetDraftState();
  routeRequestId.value = null;
  activeType.value = null;
}

function validateForm() {
  const errors: string[] = [];
  if (!activeType.value) return false;
  if (!title.value.trim()) {
    errors.push("请输入申请标题。");
  }
  const { ok } = dynamicFormRef.value?.validate() ?? { ok: true };
  if (!ok) {
    errors.push("请完善动态表单中的必填字段。");
  }
  setFormErrors(errors);
  if (errors.length) {
    uni.showToast({ title: errors[0], icon: "none" });
    return false;
  }
  return true;
}

function validateRequiredAttachments() {
  if (activeType.value?.attachment_required && attachments.value.length === 0) {
    setFormErrors(["请先上传该事务类型要求的必填附件。"]);
    uni.showToast({ title: "请先上传必填附件", icon: "none" });
    return false;
  }
  setFormErrors([]);
  return true;
}

function resolveSubmitDialog(value: boolean) {
  submitDialogVisible.value = false;
  const resolver = submitDialogResolver;
  submitDialogResolver = null;
  resolver?.(value);
}

function confirmSubmit() {
  if (!activeType.value) return Promise.resolve(false);
  submitDialogVisible.value = true;
  return new Promise<boolean>((resolve) => {
    submitDialogResolver = resolve;
  });
}

async function persistDraft(showSuccess: boolean) {
  if (!activeType.value || !validateForm()) return null;
  const isNewDraft = draftId.value == null;
  const payload = {
    title: title.value.trim(),
    form_data: formData.value,
    summary: summary.value.trim() || undefined,
  };
  const resp = draftId.value == null
    ? await createRequest({
      type_code: activeType.value.code,
      ...payload,
    })
    : await updateRequest(draftId.value, payload);
  syncDraftDetail(resp.data);
  setFormErrors([]);
  if (showSuccess) {
    uni.showToast({ title: isNewDraft ? "草稿已保存" : "修改已保存" });
  }
  return resp.data;
}

async function onSave() {
  saving.value = true;
  try {
    await persistDraft(true);
  } finally {
    saving.value = false;
  }
}

async function onUploadAttachment() {
  if (draftId.value == null) {
    uni.showToast({ title: "请先保存草稿", icon: "none" });
    return;
  }
  const selected = await new Promise<any>((resolve) => {
    uni.chooseMessageFile({
      count: 9,
      type: "all",
      success: resolve,
      fail: () => resolve(null),
    });
  });
  if (!selected?.tempFiles?.length) return;

  uploading.value = true;
  try {
    let uploadedCount = 0;
    for (const file of selected.tempFiles as Array<{ path?: string; tempFilePath?: string }>) {
      const filePath = file.path || file.tempFilePath;
      if (!filePath) continue;
      const attachment = await uploadRequestAttachment(draftId.value, filePath);
      attachments.value = [...attachments.value, attachment];
      uploadedCount += 1;
    }
    if (uploadedCount > 0) {
      if (draftDetail.value) {
        draftDetail.value = { ...draftDetail.value, attachments: attachments.value };
      }
      uni.showToast({
        title: uploadedCount > 1 ? `已上传${uploadedCount}个附件` : "附件已上传",
        icon: "none",
      });
    }
  } finally {
    uploading.value = false;
  }
}

async function onSubmit() {
  if (draftId.value == null) {
    setFormErrors(["请先保存草稿，再上传附件或提交申请。"]);
    uni.showToast({ title: "请先保存草稿", icon: "none" });
    return;
  }
  if (!validateRequiredAttachments()) return;
  if (!(await confirmSubmit())) return;

  submitting.value = true;
  try {
    const previousStatus = draftStatus.value;
    const detail = await persistDraft(false);
    if (!detail || !validateRequiredAttachments()) return;
    await submitRequest(detail.id);
    uni.showToast({
      title: previousStatus === "REJECTED" ? "已重新提交" : "已提交申请",
      icon: "none",
    });
    uni.redirectTo({ url: `/pages/request/detail?id=${detail.id}` });
  } finally {
    submitting.value = false;
  }
}

onMounted(async () => {
  const pages = getCurrentPages();
  const current = pages[pages.length - 1] as any;
  const options = current?.options || {};
  routeRequestId.value = options.id ? Number(options.id) : null;

  await loadTypes();
  if (routeRequestId.value != null && Number.isFinite(routeRequestId.value)) {
    await loadEditableDraft(routeRequestId.value);
  }
});
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 24rpx;
  background:
    linear-gradient(180deg, #fff7f8 0, #f7f1f2 240rpx, #f6f0f1 100%),
    #f6f0f1;
}

.type-list-wrap,
.form-wrap {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.hero-card {
  position: relative;
  overflow: hidden;
  padding: 26rpx;
  border-radius: 28rpx;
  background:
    linear-gradient(135deg, rgba(183, 15, 36, 0.95), rgba(216, 36, 56, 0.88) 58%, rgba(255, 236, 240, 0.92) 100%);
  box-shadow: 0 18rpx 42rpx rgba(146, 18, 36, 0.22);
}

.hero-orb {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.12);
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
  bottom: -94rpx;
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

.hero-icon-wrap {
  width: 92rpx;
  height: 92rpx;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.18);
  box-shadow: inset 0 0 0 1rpx rgba(255, 255, 255, 0.18);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.hero-icon-wrap.large {
  width: 98rpx;
  height: 98rpx;
}

.hero-icon {
  font-size: 46rpx;
  line-height: 1;
  color: #fff;
}

.hero-text {
  min-width: 0;
}

.hero-eyebrow {
  display: inline-flex;
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.16);
  color: rgba(255, 255, 255, 0.92);
  font-size: 20rpx;
  letter-spacing: 1rpx;
}

.hero-title {
  display: block;
  margin-top: 12rpx;
  font-size: 32rpx;
  font-weight: 800;
  line-height: 1.45;
  color: #fff;
}

.hero-desc {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: rgba(255, 245, 246, 0.82);
}

.hero-side {
  min-width: 140rpx;
  padding: 18rpx 16rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.14);
  box-shadow: inset 0 0 0 1rpx rgba(255, 255, 255, 0.12);
  text-align: center;
}

.hero-side-label,
.hero-side-note {
  display: block;
  font-size: 20rpx;
  color: rgba(255, 244, 246, 0.76);
}

.hero-side-value {
  display: block;
  margin-top: 8rpx;
  font-size: 34rpx;
  font-weight: 800;
  color: #fff;
}

.hero-status {
  flex-shrink: 0;
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
  font-size: 22rpx;
  font-weight: 700;
}

.hero-status.rejected {
  background: rgba(255, 241, 242, 0.18);
  color: #fff;
}

.hero-strip {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14rpx;
  margin-top: 20rpx;
}

.hero-strip-item {
  padding: 18rpx 16rpx;
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.12);
  box-shadow: inset 0 0 0 1rpx rgba(255, 255, 255, 0.1);
}

.hero-strip-label {
  display: block;
  font-size: 20rpx;
  color: rgba(255, 244, 246, 0.72);
}

.hero-strip-value {
  display: block;
  margin-top: 8rpx;
  font-size: 26rpx;
  font-weight: 800;
  color: #fff;
}

.type-panel,
.step-card,
.field-card,
.section-block,
.notice-card,
.submit-summary {
  background: rgba(255, 255, 255, 0.96);
  border-radius: 26rpx;
  border: 1rpx solid rgba(240, 226, 229, 0.94);
  box-shadow: 0 16rpx 36rpx rgba(41, 18, 23, 0.08);
}

.type-panel,
.step-card,
.field-card,
.section-block,
.notice-card {
  padding: 24rpx;
}

.panel-head,
.field-head,
.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16rpx;
}

.panel-head.compact {
  margin-bottom: 18rpx;
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

.panel-meta,
.field-status {
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  background: #f8fafc;
  color: #64748b;
  font-size: 22rpx;
  white-space: nowrap;
}

.type-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
}

.type-item {
  padding: 22rpx 18rpx;
  border-radius: 22rpx;
  background: linear-gradient(180deg, #fffefe, #fff7f8);
  border: 1rpx solid rgba(239, 221, 225, 0.96);
  box-shadow: 0 12rpx 28rpx rgba(41, 18, 23, 0.06);
}

.type-item-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12rpx;
}

.type-icon {
  width: 68rpx;
  height: 68rpx;
  border-radius: 20rpx;
  background: linear-gradient(135deg, #fff1f2, #ffe7ea);
  color: #b70f24;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  font-weight: 800;
  box-shadow: inset 0 0 0 1rpx rgba(183, 15, 36, 0.08);
}

.type-cat {
  padding: 6rpx 12rpx;
  border-radius: 999rpx;
  background: #fff1f2;
  font-size: 20rpx;
  color: #b70f24;
}

.type-name {
  display: block;
  margin-top: 16rpx;
  font-size: 28rpx;
  font-weight: 800;
  color: #1f2937;
  line-height: 1.5;
}

.type-desc {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  color: #64748b;
  line-height: 1.6;
}

.type-meta {
  display: block;
  margin-top: 12rpx;
  font-size: 20rpx;
  line-height: 1.6;
  color: #94a3b8;
}

.type-cta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 18rpx;
  padding-top: 16rpx;
  border-top: 1rpx solid rgba(241, 229, 232, 0.9);
  color: #b70f24;
  font-size: 22rpx;
  font-weight: 700;
}

.type-cta-arrow {
  font-size: 30rpx;
  line-height: 1;
}

.empty {
  text-align: center;
  padding: 80rpx 0;
  color: #94a3b8;
  font-size: 28rpx;
}

.step-track {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.step-node {
  display: flex;
  align-items: center;
  gap: 14rpx;
  padding: 18rpx;
  border-radius: 20rpx;
  background: #fbfcfd;
  box-shadow: inset 0 0 0 1rpx rgba(226, 232, 240, 0.66);
}

.step-node.active {
  background: linear-gradient(135deg, #fff4f5, #fff9fa);
  box-shadow: inset 0 0 0 1rpx rgba(183, 15, 36, 0.12);
}

.step-node.done {
  background: linear-gradient(135deg, #f4fff7, #fbfffc);
  box-shadow: inset 0 0 0 1rpx rgba(22, 163, 74, 0.14);
}

.step-dot {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  background: #e2e8f0;
  color: #475569;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
  font-weight: 800;
  flex-shrink: 0;
}

.step-node.active .step-dot {
  background: #b70f24;
  color: #fff;
}

.step-node.done .step-dot {
  background: #16a34a;
  color: #fff;
}

.step-copy {
  flex: 1;
  min-width: 0;
}

.step-label {
  display: block;
  font-size: 26rpx;
  font-weight: 700;
  color: #1f2937;
}

.step-hint {
  display: block;
  margin-top: 6rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #94a3b8;
}

.step-state {
  flex-shrink: 0;
  font-size: 22rpx;
  color: #64748b;
}

.step-node.active .step-state {
  color: #b70f24;
}

.step-node.done .step-state {
  color: #16a34a;
}

.notice-card.warning {
  background: linear-gradient(180deg, #fff8ef, #fffdf9);
  border-color: rgba(245, 158, 11, 0.22);
}

.notice-card.error {
  background: linear-gradient(180deg, #fff4f5, #fffdfd);
  border-color: rgba(244, 63, 94, 0.22);
}

.notice-title {
  display: block;
  font-size: 28rpx;
  font-weight: 800;
  color: #7c2d12;
}

.notice-card.error .notice-title {
  color: #9f1239;
}

.notice-body {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: #92400e;
}

.notice-card.error .notice-body {
  color: #9f1239;
}

.field-title {
  display: block;
  font-size: 28rpx;
  font-weight: 800;
  color: #1f2937;
}

.field-label {
  display: block;
  margin-top: 18rpx;
  margin-bottom: 8rpx;
  font-size: 24rpx;
  color: #334155;
}

.required {
  color: #e11d48;
  margin-left: 6rpx;
}

.input,
.textarea {
  width: 100%;
  box-sizing: border-box;
  background: #fbfcfd;
  border: 1rpx solid rgba(226, 232, 240, 0.84);
  border-radius: 18rpx;
  padding: 20rpx 18rpx;
  font-size: 26rpx;
  color: #1f2937;
  box-shadow: inset 0 2rpx 8rpx rgba(82, 28, 38, 0.03);
}

.textarea {
  min-height: 160rpx;
}

.section-hint {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #94a3b8;
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

.attachment-list {
  margin-top: 18rpx;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.attachment-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
  padding: 18rpx;
  border-radius: 18rpx;
  background: #fbfcfd;
  box-shadow: inset 0 0 0 1rpx rgba(226, 232, 240, 0.66);
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

.attachment-state {
  flex-shrink: 0;
  font-size: 22rpx;
  color: #16a34a;
}

.empty-attachment {
  margin-top: 18rpx;
  padding: 30rpx 24rpx;
  border-radius: 22rpx;
  border: 1rpx dashed rgba(183, 15, 36, 0.2);
  background: linear-gradient(180deg, #fffafb, #fffdfd);
  text-align: center;
}

.empty-attachment-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: #fff1f2;
  color: #b70f24;
  font-size: 34rpx;
  font-weight: 700;
}

.empty-attachment-title {
  display: block;
  margin-top: 14rpx;
  font-size: 26rpx;
  font-weight: 700;
  color: #1f2937;
}

.empty-attachment-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #94a3b8;
}

.submit-summary {
  position: relative;
  overflow: hidden;
  padding: 24rpx;
  background: linear-gradient(135deg, #fff8f1 0%, #fffdfc 52%, #fff2f4 100%);
  border-color: rgba(240, 213, 218, 0.96);
}

.summary-watermark {
  position: absolute;
  right: 28rpx;
  bottom: 8rpx;
  width: 150rpx;
  height: 150rpx;
  border-radius: 50%;
  border: 4rpx solid rgba(183, 15, 36, 0.08);
  color: rgba(183, 15, 36, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 68rpx;
  font-weight: 800;
}

.summary-title {
  position: relative;
  z-index: 1;
  display: block;
  font-size: 28rpx;
  font-weight: 800;
  color: #881337;
}

.summary-list {
  position: relative;
  z-index: 1;
  margin-top: 18rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  gap: 18rpx;
}

.summary-key {
  flex-shrink: 0;
  font-size: 22rpx;
  color: #9f1239;
}

.summary-value {
  flex: 1;
  text-align: right;
  font-size: 22rpx;
  line-height: 1.6;
  color: #334155;
  word-break: break-all;
}

.footer-spacer {
  height: 196rpx;
}

.footer {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 20;
  padding: 0 20rpx calc(20rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
}

.footer-shell {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  padding: 18rpx;
  border-radius: 28rpx 28rpx 0 0;
  background: rgba(255, 255, 255, 0.98);
  border-top: 1rpx solid rgba(240, 226, 229, 0.94);
  box-shadow: 0 -12rpx 30rpx rgba(41, 18, 23, 0.1);
}

.footer-meta {
  flex: 1;
  min-width: 0;
}

.footer-title {
  display: block;
  font-size: 26rpx;
  font-weight: 700;
  color: #1f2937;
}

.footer-desc {
  display: block;
  margin-top: 6rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: #94a3b8;
}

.footer-actions {
  display: flex;
  align-items: center;
  gap: 10rpx;
  flex-shrink: 0;
}

.action-btn {
  min-width: 144rpx;
  font-size: 24rpx;
  font-weight: 700;
}

.action-btn.light {
  color: #64748b;
  background: #f8fafc;
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
  padding: 74rpx 28rpx 28rpx;
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

.dialog-icon {
  color: #b70f24;
  font-size: 42rpx;
  font-weight: 800;
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

.dialog-summary {
  margin-top: 22rpx;
  border-radius: 20rpx;
  background: #fbfcfd;
  box-shadow: inset 0 0 0 1rpx rgba(226, 232, 240, 0.7);
}

.dialog-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18rpx;
  padding: 18rpx 20rpx;
  border-bottom: 1rpx solid rgba(226, 232, 240, 0.66);
}

.dialog-row:last-child {
  border-bottom: none;
}

.dialog-row-label {
  font-size: 24rpx;
  color: #64748b;
}

.dialog-row-value {
  font-size: 24rpx;
  color: #1f2937;
  font-weight: 600;
}

.dialog-actions {
  display: flex;
  gap: 16rpx;
  margin-top: 24rpx;
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
