<!--
  基于 JSON Schema 的简化版动态表单（学生小程序专用）。

  支持字段形态：
  - string  + 默认文本输入
  - string  + widget="textarea"  → 多行文本域
  - string  + format="date"      → 日期 picker（YYYY-MM-DD）
  - string  + enum                → 下拉选择（picker selector）
  - number                        → 数字输入
  - boolean                       → 开关

  Schema 约定：
  {
    "type": "object",
    "required": ["a", "b"],
    "properties": {
      "<key>": { "type": "...", "title": "...", "description": "...", ... }
    }
  }

  使用方式：
    <DynamicForm v-model="formData" :schema="schema" @validate="onValidate" />
-->
<template>
  <view v-if="fields.length" class="dynamic-form">
    <view
      v-for="f in fields"
      :key="f.key"
      class="df-row"
    >
      <view class="df-label">
        <text class="df-label-text">{{ f.title }}</text>
        <text v-if="f.required" class="df-required">*</text>
      </view>
      <text v-if="f.description" class="df-desc">{{ f.description }}</text>

      <!-- textarea -->
      <textarea
        v-if="f.widget === 'textarea'"
        class="df-textarea"
        :value="modelValue[f.key]"
        :placeholder="f.placeholder || '请输入'"
        @input="onInput(f, $event)"
      />

      <!-- enum 下拉 -->
      <picker
        v-else-if="f.enum && f.enum.length"
        mode="selector"
        :range="f.enum"
        :value="pickerIndex(f)"
        @change="onEnumChange(f, $event)"
      >
        <view class="df-picker">
          <text v-if="modelValue[f.key]">{{ modelValue[f.key] }}</text>
          <text v-else class="df-placeholder">请选择</text>
        </view>
      </picker>

      <!-- 日期 picker -->
      <picker
        v-else-if="f.format === 'date'"
        mode="date"
        :value="modelValue[f.key] || ''"
        @change="onDateChange(f, $event)"
      >
        <view class="df-picker">
          <text v-if="modelValue[f.key]">{{ modelValue[f.key] }}</text>
          <text v-else class="df-placeholder">选择日期</text>
        </view>
      </picker>

      <!-- boolean 开关 -->
      <switch
        v-else-if="f.type === 'boolean'"
        :checked="!!modelValue[f.key]"
        color="#7f1722"
        @change="onBoolChange(f, $event)"
      />

      <!-- number 数字 -->
      <input
        v-else-if="f.type === 'number'"
        class="df-input"
        type="digit"
        :value="modelValue[f.key] == null ? '' : modelValue[f.key]"
        :placeholder="f.placeholder || '请输入数字'"
        @input="onNumberInput(f, $event)"
      />

      <!-- 默认文本 -->
      <input
        v-else
        class="df-input"
        :value="modelValue[f.key] || ''"
        :placeholder="f.placeholder || '请输入'"
        @input="onInput(f, $event)"
      />

      <text v-if="errors[f.key]" class="df-error">{{ errors[f.key] }}</text>
    </view>
  </view>
  <view v-else class="df-empty">
    <text>该事务无需额外填写字段</text>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue'

interface FieldSpec {
  key: string
  title: string
  type: string
  description?: string
  required: boolean
  widget?: string
  format?: string
  enum?: string[]
  placeholder?: string
}

interface SchemaObject {
  type?: string
  required?: string[]
  properties?: Record<string, any>
}

const props = defineProps<{
  modelValue: Record<string, any>
  schema?: SchemaObject | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: Record<string, any>): void
  (e: 'validate', ok: boolean, errors: Record<string, string>): void
}>()

const fields = computed<FieldSpec[]>(() => {
  const s = props.schema
  if (!s || !s.properties) return []
  const required = new Set(s.required || [])
  return Object.entries(s.properties).map(([key, raw]) => ({
    key,
    title: raw.title || key,
    type: raw.type || 'string',
    description: raw.description,
    required: required.has(key),
    widget: raw.widget,
    format: raw.format,
    enum: Array.isArray(raw.enum) ? raw.enum : undefined,
    placeholder: raw.placeholder,
  }))
})

const errors = reactive<Record<string, string>>({})

function pickerIndex(f: FieldSpec): number {
  if (!f.enum) return 0
  const idx = f.enum.indexOf(props.modelValue[f.key])
  return idx >= 0 ? idx : 0
}

function update(key: string, value: any) {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}

function onInput(f: FieldSpec, e: any) { update(f.key, e.detail.value) }
function onNumberInput(f: FieldSpec, e: any) {
  const v = e.detail.value
  update(f.key, v === '' ? null : Number(v))
}
function onBoolChange(f: FieldSpec, e: any) { update(f.key, e.detail.value) }
function onDateChange(f: FieldSpec, e: any) { update(f.key, e.detail.value) }
function onEnumChange(f: FieldSpec, e: any) {
  if (!f.enum) return
  const idx = Number(e.detail.value)
  update(f.key, f.enum[idx])
}

function validate(): { ok: boolean; errors: Record<string, string> } {
  const next: Record<string, string> = {}
  for (const f of fields.value) {
    if (!f.required) continue
    const v = props.modelValue[f.key]
    if (v == null || v === '' || (Array.isArray(v) && !v.length)) {
      next[f.key] = '该字段必填'
    }
  }
  Object.keys(errors).forEach(k => delete errors[k])
  Object.assign(errors, next)
  return { ok: !Object.keys(next).length, errors: next }
}

watch(() => props.schema, () => {
  Object.keys(errors).forEach(k => delete errors[k])
})

defineExpose({ validate })
</script>

<style scoped>
.dynamic-form {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}
.df-row {
  padding: 18rpx 0;
  border-bottom: 1rpx solid #f4e9ec;
}
.df-row:last-child {
  border-bottom: none;
}
.df-label { display: flex; align-items: center; margin-bottom: 10rpx; }
.df-label-text { font-size: 25rpx; color: #3b3134; font-weight: 700; }
.df-required { color: #c8142f; margin-left: 6rpx; font-size: 26rpx; }
.df-desc { display: block; font-size: 22rpx; color: #9a8f92; margin-bottom: 10rpx; line-height: 1.55; }

.df-input, .df-textarea, .df-picker {
  width: 100%;
  box-sizing: border-box;
  background: #fffafa;
  border: 1rpx solid #f0dfe3;
  border-radius: 18rpx;
  padding: 18rpx 20rpx;
  font-size: 26rpx;
  color: #2f2a2b;
  box-shadow: inset 0 2rpx 8rpx rgba(82, 28, 38, 0.03);
}
.df-textarea { min-height: 168rpx; }
.df-picker {
  min-height: 78rpx;
  line-height: 1.5;
  display: flex;
  align-items: center;
}
.df-placeholder { color: #b7a8ac; }
.df-error {
  display: block;
  margin-top: 10rpx;
  padding-left: 4rpx;
  font-size: 22rpx;
  color: #c8142f;
}

.df-empty {
  padding: 30rpx 0;
  text-align: center;
  font-size: 24rpx;
  color: #9a8f92;
  border-radius: 18rpx;
  background: #fffafa;
  border: 1rpx dashed #f0dfe3;
}
</style>
