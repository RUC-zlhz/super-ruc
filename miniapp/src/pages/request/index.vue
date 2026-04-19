<template>
  <view class="container">
    <scroll-view scroll-x class="tab-row">
      <view
        v-for="t in STATUS_TABS"
        :key="t.value"
        class="tab"
        :class="{ active: tab === t.value }"
        @tap="onTab(t.value)"
      >{{ t.label }}</view>
    </scroll-view>

    <view class="create-entry" @tap="goCreate">
      <text class="create-icon">＋</text>
      <text class="create-text">发起新的事务申请</text>
    </view>

    <view v-if="requests.length" class="list">
      <view
        v-for="r in requests"
        :key="r.id"
        class="req-card"
        @tap="goDetail(r.id)"
      >
        <view class="req-head">
          <text class="req-title">{{ r.title }}</text>
          <text class="req-status" :class="r.status.toLowerCase()">
            {{ statusLabel(r.status) }}
          </text>
        </view>
        <text class="req-no">编号：{{ r.request_no }}</text>
        <text class="req-type">类型：{{ r.type_code }}</text>
        <text class="req-meta">更新：{{ r.updated_at?.slice(0, 16).replace('T', ' ') }}</text>
        <view v-if="r.status === 'OFFLINE_HANDLED'" class="offline-hint">
          该事项已转线下办理，请留意老师联系方式
        </view>
      </view>
    </view>
    <view v-else-if="!loading" class="empty">暂无申请记录</view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  getMyRequests,
  getRequestStatusLabel,
  type RequestBrief,
} from '@/api/workflow'

const STATUS_TABS = [
  { label: '全部', value: '' },
  { label: '草稿', value: 'DRAFT' },
  { label: '待处理', value: 'SUBMITTED,IN_REVIEW' },
  { label: '已通过', value: 'APPROVED' },
  { label: '已驳回', value: 'REJECTED' },
  { label: '转线下办理', value: 'OFFLINE_HANDLED' },
]
const tab = ref('')

function statusLabel(status: string) {
  return getRequestStatusLabel(status)
}

const requests = ref<RequestBrief[]>([])
const loading = ref(false)

async function reload() {
  loading.value = true
  try {
    const statusParam = tab.value.includes(',') ? undefined : tab.value || undefined
    const resp = await getMyRequests({ status: statusParam, page: 1, size: 20 })
    let items = resp.data.items
    if (tab.value.includes(',')) {
      const allowed = new Set(tab.value.split(','))
      items = items.filter(r => allowed.has(r.status))
    }
    requests.value = items
  } finally {
    loading.value = false
  }
}

function onTab(v: string) { tab.value = v; reload() }

function goCreate() {
  uni.navigateTo({ url: '/pages/request/create' })
}

function goDetail(id: number) {
  uni.navigateTo({ url: `/pages/request/detail?id=${id}` })
}

onMounted(reload)
</script>

<style scoped>
.container { padding: 24rpx; }

.tab-row {
  display: flex; white-space: nowrap;
  background: #fff; border-radius: 12rpx; margin-bottom: 16rpx;
}
.tab {
  display: inline-block; padding: 20rpx 28rpx;
  font-size: 26rpx; color: #555;
}
.tab.active { color: #7f1722; border-bottom: 4rpx solid #7f1722; }

.create-entry {
  background: #fff; border-radius: 12rpx;
  padding: 28rpx; margin-bottom: 16rpx;
  display: flex; align-items: center;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06);
}
.create-icon {
  width: 56rpx; height: 56rpx; line-height: 56rpx;
  border-radius: 50%; background: #7f1722; color: #fff;
  text-align: center; font-size: 36rpx; margin-right: 16rpx;
}
.create-text { font-size: 28rpx; color: #333; }

.list {}
.req-card {
  background: #fff; padding: 24rpx; border-radius: 12rpx;
  margin-bottom: 16rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06);
}
.req-head { display: flex; justify-content: space-between; }
.req-title { font-size: 30rpx; font-weight: 600; flex: 1; }
.req-status {
  font-size: 22rpx; padding: 4rpx 14rpx; border-radius: 4rpx;
  flex-shrink: 0; margin-left: 12rpx;
}
.req-status.draft { background: #f5f5f5; color: #666; }
.req-status.submitted, .req-status.in_review { background: #e6f7ff; color: #1890ff; }
.req-status.approved { background: #f6ffed; color: #52c41a; }
.req-status.rejected { background: #fff1f0; color: #cf1322; }
.req-status.withdrawn { background: #f5f5f5; color: #999; }
.req-status.offline_handled { background: #fff7e6; color: #d46b08; }

.req-no, .req-type, .req-meta {
  display: block; font-size: 24rpx; color: #999; margin-top: 4rpx;
}
.offline-hint {
  margin-top: 12rpx; padding: 10rpx 14rpx;
  background: #fff7e6; color: #d46b08; border-radius: 6rpx;
  font-size: 24rpx;
}

.empty { text-align: center; padding: 80rpx 0; color: #999; font-size: 28rpx; }
</style>
