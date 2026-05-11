<template>
  <view class="empty" :class="{ compact }">
    <view class="icon-wrap" :class="tone">
      <text class="icon">{{ icon }}</text>
    </view>
    <text class="title">{{ title }}</text>
    <text v-if="description" class="desc">{{ description }}</text>
    <button
      v-if="actionText"
      class="action"
      size="mini"
      hover-class="hover-opacity"
      @tap.stop="emit('action')"
    >
      {{ actionText }}
    </button>
  </view>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    icon?: string
    title: string
    description?: string
    actionText?: string
    tone?: 'primary' | 'muted' | 'warning' | 'danger'
    compact?: boolean
  }>(),
  {
    icon: '…',
    description: '',
    actionText: '',
    tone: 'muted',
    compact: false,
  },
)

const emit = defineEmits<{
  (e: 'action'): void
}>()
</script>

<style scoped>
.empty {
  padding: 92rpx 28rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.92);
  border: 1rpx dashed rgba(183, 15, 36, 0.18);
  text-align: center;
  box-shadow: var(--shadow-soft);
}

.empty.compact {
  padding: 68rpx 24rpx;
}

.icon-wrap {
  width: 92rpx;
  height: 92rpx;
  margin: 0 auto 18rpx;
  border-radius: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1rpx solid transparent;
}

.icon-wrap.primary {
  background: var(--primary-soft);
  border-color: rgba(183, 15, 36, 0.16);
  color: var(--primary-color);
}

.icon-wrap.muted {
  background: rgba(148, 163, 184, 0.16);
  border-color: rgba(148, 163, 184, 0.24);
  color: rgba(71, 85, 105, 0.9);
}

.icon-wrap.warning {
  background: rgba(245, 158, 11, 0.12);
  border-color: rgba(245, 158, 11, 0.22);
  color: #b45309;
}

.icon-wrap.danger {
  background: rgba(244, 63, 94, 0.1);
  border-color: rgba(244, 63, 94, 0.22);
  color: #be123c;
}

.icon {
  font-size: 34rpx;
  font-weight: 900;
}

.title {
  display: block;
  font-size: 30rpx;
  font-weight: 900;
  color: var(--text-main);
}

.desc {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.65;
  color: rgba(107, 114, 128, 0.96);
}

.action {
  margin-top: 22rpx;
  min-width: 210rpx;
  height: 70rpx;
  line-height: 70rpx;
  padding: 0 26rpx;
  border-radius: 999rpx;
  background: #fff;
  color: var(--primary-color);
  border: 1rpx solid rgba(183, 15, 36, 0.22);
  font-size: 24rpx;
  font-weight: 800;
}

.action::after {
  border: none;
}
</style>

