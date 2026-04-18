<template>
  <div>
    <a-page-header title="运营看板" sub-title="FR-016" />
    <a-row :gutter="16">
      <a-col :span="6" v-for="m in metrics" :key="m.key">
        <a-card :bordered="false">
          <a-statistic :title="m.label" :value="m.value" />
        </a-card>
      </a-col>
    </a-row>
    <a-card class="mt16" title="今日概览" :bordered="false">
      <a-empty description="数据接入后在此展示待办 / 时序趋势 / 类型占比" />
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { fetchDashboard } from '@/api/report'

interface Metric { key: string; label: string; value: number }

const metrics = ref<Metric[]>([
  { key: 'pending_requests', label: '待审事务', value: 0 },
  { key: 'overdue_nodes', label: '逾期党团节点', value: 0 },
  { key: 'active_students', label: '在校学生', value: 0 },
  { key: 'recent_notices', label: '近 7 日通知', value: 0 },
])

onMounted(async () => {
  try {
    const resp = await fetchDashboard()
    const d: any = resp.data || {}
    metrics.value = metrics.value.map((m) => ({ ...m, value: Number(d[m.key] || 0) }))
  } catch {
    /* 接口未就绪时保留占位 */
  }
})
</script>

<style scoped>
.mt16 { margin-top: 16px; }
</style>
