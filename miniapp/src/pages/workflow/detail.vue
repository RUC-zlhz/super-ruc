<template>
  <view class="container">
    <view v-if="loading" class="loading">加载中...</view>

    <template v-else-if="workflow">
      <view class="head-card">
        <view class="head-row">
          <text class="title">{{ workflow.template_name }}</text>
          <text class="status" :class="workflow.status.toLowerCase()">
            {{ statusLabel(workflow.status) }}
          </text>
        </view>
        <text class="meta">模板编码：{{ workflow.template_code }}</text>
        <text class="meta" v-if="workflow.started_at">
          开始时间：{{ fmt(workflow.started_at) }}
        </text>
        <text class="meta" v-if="workflow.current_node_name">
          当前节点：{{ workflow.current_node_name }}
        </text>
      </view>

      <view class="section">
        <text class="section-title">流程节点</text>
        <view v-if="!nodes.length" class="empty-tiny">暂无节点记录</view>
        <view class="timeline" v-else>
          <view
            v-for="(n, idx) in nodes"
            :key="n.id"
            class="node-row"
          >
            <view class="node-rail">
              <view class="node-dot" :class="nodeDotClass(n.status)" />
              <view v-if="idx < nodes.length - 1" class="node-line" />
            </view>
            <view class="node-body">
              <view class="node-head">
                <text class="node-name">{{ n.node_name }}</text>
                <text class="node-status" :class="n.status.toLowerCase()">
                  {{ nodeStatusLabel(n.status) }}
                </text>
              </view>
              <text class="node-code">节点编码：{{ n.node_code }}</text>
              <text class="node-time" v-if="n.completed_at">
                完成时间：{{ fmt(n.completed_at) }}
              </text>
            </view>
          </view>
        </view>
      </view>
    </template>

    <view v-else class="empty">未找到流程记录</view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  getWorkflowDetail,
  type StudentWorkflow,
  type StudentWorkflowNode,
} from '@/api/workflow'

const workflow = ref<StudentWorkflow | null>(null)
const nodes = ref<StudentWorkflowNode[]>([])
const loading = ref(false)
const workflowId = ref<number | null>(null)

const STATUS_LABELS: Record<string, string> = {
  ACTIVE: '进行中',
  COMPLETED: '已完成',
  SUSPENDED: '已暂停',
  IN_PROGRESS: '进行中',
  CANCELLED: '已取消',
}
function statusLabel(s: string) { return STATUS_LABELS[s] || s }

const NODE_STATUS_LABELS: Record<string, string> = {
  PENDING: '待开始',
  DONE: '已完成',
  OVERDUE: '已逾期',
  DEFERRED: '已延期',
  MANUAL_FOLLOW_UP: '人工跟进',
}
function nodeStatusLabel(s: string) { return NODE_STATUS_LABELS[s] || s }

function nodeDotClass(s: string) {
  if (s === 'DONE') return 'completed'
  if (s === 'OVERDUE') return 'overdue'
  if (s === 'DEFERRED' || s === 'MANUAL_FOLLOW_UP') return 'manual'
  return 'pending'
}

function fmt(s?: string | null) {
  if (!s) return '-'
  return s.slice(0, 16).replace('T', ' ')
}

async function loadDetail() {
  if (workflowId.value == null) return
  loading.value = true
  try {
    const resp = await getWorkflowDetail(workflowId.value)
    workflow.value = resp.data
    nodes.value = resp.data.nodes || []
  } catch {
    workflow.value = null
    nodes.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1] as any
  const opts = current?.options || {}
  workflowId.value = Number(opts.id)
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
.status.active, .status.in_progress { background: #e6f7ff; color: #1890ff; }
.status.completed { background: #f6ffed; color: #52c41a; }
.status.suspended, .status.cancelled { background: #f5f5f5; color: #999; }
.meta { display: block; font-size: 24rpx; color: #999; margin-top: 6rpx; }

.section {
  background: #fff; padding: 24rpx; border-radius: 12rpx;
  margin-bottom: 16rpx;
}
.section-title { display: block; font-size: 28rpx; font-weight: 600; margin-bottom: 20rpx; }

.timeline {}
.node-row {
  display: flex; align-items: stretch; position: relative;
}
.node-rail {
  width: 40rpx; flex-shrink: 0; display: flex; flex-direction: column;
  align-items: center;
}
.node-dot {
  width: 20rpx; height: 20rpx; border-radius: 50%;
  margin-top: 6rpx; flex-shrink: 0; border: 2rpx solid #d9d9d9;
  background: #fff;
}
.node-dot.completed { background: #52c41a; border-color: #52c41a; }
.node-dot.overdue { background: #ff4d4f; border-color: #ff4d4f; }
.node-dot.manual { background: #faad14; border-color: #faad14; }
.node-dot.pending { background: #fff; border-color: #d9d9d9; }
.node-line {
  width: 2rpx; flex: 1; background: #f0f0f0;
  margin-top: 4rpx; min-height: 40rpx;
}
.node-body {
  flex: 1; padding: 0 0 28rpx 12rpx;
}
.node-head { display: flex; justify-content: space-between; align-items: center; }
.node-name { font-size: 28rpx; font-weight: 600; color: #333; }
.node-status {
  font-size: 22rpx; padding: 4rpx 12rpx; border-radius: 4rpx;
}
.node-status.done { background: #f6ffed; color: #52c41a; }
.node-status.overdue { background: #fff1f0; color: #cf1322; }
.node-status.deferred, .node-status.manual_follow_up { background: #fff7e6; color: #d46b08; }
.node-status.pending { background: #fafafa; color: #bfbfbf; }
.node-code { display: block; font-size: 22rpx; color: #999; margin-top: 4rpx; }
.node-time { display: block; font-size: 22rpx; color: #999; margin-top: 4rpx; }
</style>
