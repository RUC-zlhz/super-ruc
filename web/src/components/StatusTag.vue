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
  ACTIVE: { label: '进行中', color: 'processing' },
  COMPLETED: { label: '已完成', color: 'green' },
  SUSPENDED: { label: '已暂停', color: 'default' },
  PENDING: { label: '待开始', color: 'default' },
  MATERIAL_SUBMITTED: { label: '待老师确认', color: 'blue' },
  DONE: { label: '已完成', color: 'green' },
  OVERDUE: { label: '已逾期', color: 'red' },
  DEFERRED: { label: '已延期', color: 'gold' },
  MANUAL_FOLLOW_UP: { label: '人工跟进', color: 'orange' },
}

const color = computed(() => MAP[props.status]?.color ?? 'default')
const label = computed(() => MAP[props.status]?.label ?? props.status)
</script>
