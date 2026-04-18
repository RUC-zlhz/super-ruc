<template>
  <a-tag :color="color">{{ label }}</a-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ status: string }>()

const MAP: Record<string, { label: string; color: string }> = {
  DRAFT: { label: '草稿', color: 'default' },
  SUBMITTED: { label: '待受理', color: 'blue' },
  IN_REVIEW: { label: '审核中', color: 'processing' },
  APPROVED: { label: '已通过', color: 'green' },
  REJECTED: { label: '已驳回', color: 'red' },
  WITHDRAWN: { label: '已撤回', color: 'default' },
  OFFLINE_HANDLED: { label: '转线下', color: 'gold' },
  VALIDATED: { label: '已校验', color: 'blue' },
  COMMITTED: { label: '已提交', color: 'green' },
  FAILED: { label: '校验失败', color: 'red' },
  ROLLED_BACK: { label: '已回滚', color: 'volcano' },
}

const color = computed(() => MAP[props.status]?.color ?? 'default')
const label = computed(() => MAP[props.status]?.label ?? props.status)
</script>
