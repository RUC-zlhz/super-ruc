<template>
  <view class="container">
    <!-- 类型选择 -->
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
        <text class="type-desc" v-if="t.description">{{ t.description }}</text>
        <text class="type-meta">
          {{ t.attachment_required ? '需上传附件' : '无需附件' }}
          · 审批角色：{{ t.approver_roles }}
        </text>
      </view>
      <view v-if="!loadingTypes && !types.length" class="empty">暂无可发起的事务</view>
    </view>

    <!-- 表单填写 -->
    <view v-else class="form-wrap">
      <view class="form-head">
        <text class="type-name">{{ activeType.name }}</text>
        <text class="type-cat">{{ categoryLabel(activeType.category) }}</text>
      </view>
      <text class="form-hint" v-if="activeType.description">{{ activeType.description }}</text>

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

      <view class="footer">
        <button size="mini" @tap="onReset">重选类型</button>
        <button size="mini" :loading="saving" @tap="onSave">保存草稿</button>
        <button size="mini" type="primary" :loading="submitting" @tap="onSubmit">提交审核</button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import DynamicForm from '@/components/DynamicForm.vue'
import {
  listRequestTypes, createRequest, submitRequest,
  type RequestType,
} from '@/api/workflow'

const CATEGORY_LABELS: Record<string, string> = {
  LEAVE: '请假',
  CERTIFICATE: '证明',
  STAMP: '盖章',
  REGISTRATION: '报名',
  MATERIAL: '材料提交',
  OTHER: '其他',
}
function categoryLabel(c: string) { return CATEGORY_LABELS[c] || c }

const types = ref<RequestType[]>([])
const loadingTypes = ref(false)

const activeType = ref<RequestType | null>(null)
const title = ref('')
const summary = ref('')
const formData = ref<Record<string, any>>({})

const dynamicFormRef = ref<InstanceType<typeof DynamicForm> | null>(null)
const saving = ref(false)
const submitting = ref(false)

async function loadTypes() {
  loadingTypes.value = true
  try {
    const resp = await listRequestTypes()
    types.value = resp.data
  } finally {
    loadingTypes.value = false
  }
}

function onPickType(t: RequestType) {
  activeType.value = t
  title.value = ''
  summary.value = ''
  formData.value = {}
}

function onReset() {
  activeType.value = null
}

async function doCreate(): Promise<number | null> {
  if (!activeType.value) return null
  if (!title.value.trim()) {
    uni.showToast({ title: '请输入申请标题', icon: 'none' })
    return null
  }
  const { ok } = dynamicFormRef.value?.validate() ?? { ok: true }
  if (!ok) {
    uni.showToast({ title: '请完善必填字段', icon: 'none' })
    return null
  }
  const resp = await createRequest({
    type_code: activeType.value.code,
    title: title.value.trim(),
    form_data: formData.value,
    summary: summary.value?.trim() || undefined,
  })
  return resp.data.id
}

async function onSave() {
  saving.value = true
  try {
    const id = await doCreate()
    if (id != null) {
      uni.showToast({ title: '草稿已保存' })
      uni.navigateBack()
    }
  } finally {
    saving.value = false
  }
}

async function onSubmit() {
  submitting.value = true
  try {
    const id = await doCreate()
    if (id != null) {
      await submitRequest(id)
      uni.showToast({ title: '已提交审核' })
      uni.redirectTo({ url: `/pages/request/detail?id=${id}` })
    }
  } finally {
    submitting.value = false
  }
}

onMounted(loadTypes)
</script>

<style scoped>
.container { padding: 24rpx; }
.section-title { display: block; font-size: 28rpx; font-weight: 600; margin-bottom: 16rpx; }

.type-list {}
.type-item {
  background: #fff; padding: 24rpx; border-radius: 12rpx;
  margin-bottom: 16rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06);
}
.type-head { display: flex; justify-content: space-between; align-items: center; }
.type-name { font-size: 30rpx; font-weight: 600; color: #333; }
.type-cat {
  font-size: 22rpx; color: #7f1722; background: #fff1f0;
  padding: 2rpx 12rpx; border-radius: 4rpx;
}
.type-desc { display: block; font-size: 26rpx; color: #666; margin-top: 8rpx; }
.type-meta { display: block; font-size: 22rpx; color: #999; margin-top: 6rpx; }

.empty { text-align: center; padding: 80rpx 0; color: #999; font-size: 28rpx; }

.form-wrap {
  background: #fff; padding: 24rpx; border-radius: 12rpx;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06);
}
.form-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8rpx; }
.form-hint {
  display: block; font-size: 24rpx; color: #999;
  margin-bottom: 20rpx; line-height: 1.5;
}

.field { margin-bottom: 20rpx; }
.label { display: block; font-size: 26rpx; color: #333; margin-bottom: 6rpx; }
.required { color: #ff4d4f; margin-left: 6rpx; }
.input, .textarea {
  background: #f7f7f7; border-radius: 8rpx;
  padding: 14rpx 16rpx; font-size: 26rpx;
}
.textarea { min-height: 140rpx; }

.footer {
  display: flex; justify-content: flex-end;
  gap: 12rpx; margin-top: 24rpx; flex-wrap: wrap;
}
</style>
