<template>
  <view class="notice" :class="[tone, { compact }]">
    <view class="notice-copy">
      <text class="notice-title">{{ title }}</text>
      <text v-if="description" class="notice-desc">{{ description }}</text>
    </view>
    <button
      v-if="actionText"
      class="notice-action"
      size="mini"
      hover-class="hover-opacity"
      @tap.stop="emit('action')"
    >
      {{ actionText }}
    </button>
  </view>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  title: string
  description?: string
  actionText?: string
  tone?: 'error' | 'warning' | 'info'
  compact?: boolean
}>(), {
  description: '',
  actionText: '',
  tone: 'info',
  compact: false,
})

const emit = defineEmits<{
  (e: 'action'): void
}>()
</script>

<style scoped>
.notice {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  padding: 22rpx 24rpx;
  border-radius: 18rpx;
  border: 1rpx solid transparent;
}

.notice.compact {
  padding: 18rpx 20rpx;
}

.notice.info {
  background: #fff7f7;
  border-color: #f0dfe3;
}

.notice.warning {
  background: #fff8ef;
  border-color: rgba(245, 158, 11, 0.24);
}

.notice.error {
  background: #fff4f5;
  border-color: rgba(244, 63, 94, 0.24);
}

.notice-copy {
  flex: 1;
  min-width: 0;
}

.notice-title {
  display: block;
  font-size: 26rpx;
  font-weight: 700;
  color: #1f2937;
}

.notice.info .notice-title {
  color: #9f1239;
}

.notice.warning .notice-title {
  color: #b45309;
}

.notice.error .notice-title {
  color: #be123c;
}

.notice-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.65;
  color: #6b7280;
}

.notice.info .notice-desc {
  color: #7f1d1d;
}

.notice.warning .notice-desc {
  color: #92400e;
}

.notice.error .notice-desc {
  color: #9f1239;
}

.notice-action {
  flex-shrink: 0;
  min-width: 132rpx;
  height: 60rpx;
  line-height: 60rpx;
  padding: 0 22rpx;
  border-radius: 999rpx;
  background: #ffffff;
  color: #b70f24;
  font-size: 22rpx;
  font-weight: 700;
}

.notice.warning .notice-action {
  color: #b45309;
}

.notice.error .notice-action {
  color: #be123c;
}

.notice-action::after {
  border: none;
}
</style>
