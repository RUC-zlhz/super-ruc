<template>
  <view class="container">
    <view class="filter-bar">
      <scroll-view scroll-x class="level-scroll">
        <view
          v-for="opt in LEVEL_OPTIONS"
          :key="opt.value"
          class="chip"
          :class="{ active: filters.level === opt.value }"
          @tap="onLevel(opt.value)"
        >{{ opt.label }}</view>
      </scroll-view>
      <view class="year-picker">
        <picker mode="selector" :range="YEAR_OPTIONS" :value="yearIdx" @change="onYearChange">
          <view class="year-text">{{ filters.year ? `${filters.year} 学年` : '全部学年' }}</view>
        </picker>
        <view class="history-toggle" @tap="onToggleHistory">
          {{ filters.include_archived ? '返回公示' : '历史荣誉' }}
        </view>
      </view>
    </view>

    <view v-if="filters.include_archived" class="history-hint">
      当前为归档视图 · 仅供参考
    </view>

    <view v-if="items.length" class="list">
      <view
        v-for="h in items"
        :key="h.id"
        class="card"
        @tap="onDetail(h)"
      >
        <view class="card-head">
          <text class="card-title">{{ h.title }}</text>
          <text class="card-tag" :class="`lv-${h.level.toLowerCase()}`">{{ levelLabel(h.level) }}</text>
        </view>
        <text class="card-recipients" v-if="h.recipient_names?.length">
          获奖人：{{ h.recipient_names.join('、') }}
        </text>
        <text class="card-meta">{{ h.awarded_by }} · {{ h.announced_at?.slice(0, 10) }}</text>
        <text class="card-summary" v-if="h.summary">{{ h.summary.slice(0, 60) }}</text>
        <text v-if="h.status !== 'ACTIVE'" class="archived-mark">历史荣誉，仅供参考</text>
      </view>
    </view>

    <view v-else-if="!loading" class="empty">暂无荣誉记录</view>

    <view v-if="hasMore" class="load-more" @tap="loadMore">加载更多</view>

    <!-- 详情弹窗 -->
    <uni-popup ref="detailPopup" type="bottom">
      <view class="detail-panel" v-if="selected">
        <text class="detail-title">{{ selected.title }}</text>
        <text class="detail-meta">
          {{ levelLabel(selected.level) }} · {{ selected.awarded_by }}
        </text>
        <text class="detail-meta" v-if="selected.document_no">
          文号 / 证书编号：{{ selected.document_no }}
        </text>
        <text class="detail-meta">公示日期：{{ selected.announced_at?.slice(0, 10) }}</text>
        <view class="detail-recipients" v-if="selected.recipients?.length">
          <text class="detail-section-title">获奖人</text>
          <view v-for="r in selected.recipients" :key="r.id" class="recipient-row">
            <text>{{ r.display_name }}</text>
            <text class="recipient-meta" v-if="r.major_snapshot || r.grade_snapshot">
              {{ [r.major_snapshot, r.grade_snapshot].filter(Boolean).join(' · ') }}
            </text>
          </view>
        </view>
        <view v-if="selected.summary" class="detail-block">
          <text class="detail-section-title">事迹摘要</text>
          <text class="detail-body">{{ selected.summary }}</text>
        </view>
        <view v-if="selected.story_md" class="detail-block">
          <text class="detail-section-title">完整事迹</text>
          <text class="detail-body">{{ selected.story_md }}</text>
        </view>
        <view v-if="selected.acceptance_speech" class="detail-block">
          <text class="detail-section-title">获奖感言</text>
          <text class="detail-body">{{ selected.acceptance_speech }}</text>
        </view>
        <view class="detail-footer">
          <button size="mini" @tap="closeDetail">返回榜单</button>
        </view>
      </view>
    </uni-popup>
  </view>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted, computed } from 'vue'
import { listPublicHonors, getHonorDetail, type HonorRecordBrief } from '@/api/honor'

const LEVEL_OPTIONS = [
  { label: '全部', value: '' },
  { label: '国家级', value: 'NATIONAL' },
  { label: '省部级', value: 'PROVINCIAL' },
  { label: '厅局级', value: 'MINISTERIAL' },
  { label: '校级', value: 'SCHOOL' },
]

const LEVEL_LABELS: Record<string, string> = {
  NATIONAL: '国家级',
  PROVINCIAL: '省部级',
  MINISTERIAL: '厅局级',
  SCHOOL: '校级',
}
function levelLabel(v: string) { return LEVEL_LABELS[v] || v }

const currentYear = new Date().getFullYear()
const YEAR_OPTIONS = ['全部学年', ...Array.from({ length: 6 }).map((_, i) => String(currentYear - i))]

const filters = reactive<{
  level: string
  year: number | null
  include_archived: boolean
}>({ level: '', year: null, include_archived: false })

const yearIdx = ref(0)
const items = ref<HonorRecordBrief[]>([])
const page = ref(1)
const size = 20
const total = ref(0)
const loading = ref(false)
const hasMore = computed(() => items.value.length < total.value)

const selected = ref<any | null>(null)
const detailPopup = ref<any>(null)

async function reload(reset = true) {
  if (reset) { page.value = 1; items.value = [] }
  loading.value = true
  try {
    const resp = await listPublicHonors({
      level: filters.level || undefined,
      year: filters.year || undefined,
      include_archived: filters.include_archived,
      page: page.value,
      size,
    })
    items.value = reset ? resp.data.items : [...items.value, ...resp.data.items]
    total.value = resp.data.meta?.total || items.value.length
  } finally {
    loading.value = false
  }
}

function loadMore() {
  page.value += 1
  reload(false)
}

function onLevel(v: string) {
  filters.level = v
  reload()
}

function onYearChange(e: any) {
  const idx = Number(e.detail.value)
  yearIdx.value = idx
  filters.year = idx === 0 ? null : Number(YEAR_OPTIONS[idx])
  reload()
}

function onToggleHistory() {
  filters.include_archived = !filters.include_archived
  reload()
}

async function onDetail(row: HonorRecordBrief) {
  try {
    const resp = await getHonorDetail(row.id)
    selected.value = resp.data
    detailPopup.value?.open()
  } catch { /* ok */ }
}

function closeDetail() {
  detailPopup.value?.close()
  selected.value = null
}

onMounted(() => reload())
</script>

<style scoped>
.container { padding: 24rpx; }

.filter-bar { margin-bottom: 16rpx; }
.level-scroll { white-space: nowrap; }
.chip {
  display: inline-block;
  padding: 10rpx 24rpx;
  margin-right: 12rpx;
  background: #fff;
  border: 1rpx solid #ddd;
  border-radius: 32rpx;
  font-size: 26rpx;
  color: #555;
}
.chip.active { background: #7f1722; color: #fff; border-color: #7f1722; }

.year-picker {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 16rpx; font-size: 26rpx;
}
.year-text { color: #333; }
.history-toggle { color: #7f1722; }

.history-hint {
  font-size: 24rpx; color: #999; padding: 8rpx 0 16rpx;
}

.list {}
.card {
  background: #fff; padding: 24rpx; border-radius: 12rpx;
  margin-bottom: 16rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06);
}
.card-head { display: flex; justify-content: space-between; align-items: flex-start; }
.card-title { font-size: 30rpx; font-weight: 600; color: #333; flex: 1; }
.card-tag {
  flex-shrink: 0; font-size: 22rpx; padding: 4rpx 14rpx;
  border-radius: 4rpx; margin-left: 12rpx;
}
.card-tag.lv-national { background: #fff1f0; color: #cf1322; }
.card-tag.lv-provincial { background: #fff7e6; color: #d46b08; }
.card-tag.lv-ministerial { background: #e6f7ff; color: #096dd9; }
.card-tag.lv-school { background: #f0f5ff; color: #2f54eb; }

.card-recipients { display: block; font-size: 26rpx; color: #555; margin-top: 8rpx; }
.card-meta { display: block; font-size: 24rpx; color: #999; margin-top: 4rpx; }
.card-summary { display: block; font-size: 26rpx; color: #666; margin-top: 8rpx; }
.archived-mark { display: block; font-size: 22rpx; color: #999; margin-top: 8rpx; }

.empty { text-align: center; padding: 80rpx 0; color: #999; font-size: 28rpx; }
.load-more { text-align: center; padding: 24rpx 0; color: #7f1722; font-size: 26rpx; }

.detail-panel {
  background: #fff; padding: 32rpx;
  border-radius: 24rpx 24rpx 0 0;
  max-height: 80vh; overflow-y: auto;
}
.detail-title { font-size: 34rpx; font-weight: 600; display: block; margin-bottom: 12rpx; }
.detail-meta { display: block; font-size: 24rpx; color: #666; margin-top: 4rpx; }
.detail-block { margin-top: 24rpx; }
.detail-section-title { font-size: 28rpx; font-weight: 600; color: #333; display: block; margin-bottom: 8rpx; }
.detail-body { font-size: 28rpx; line-height: 1.7; color: #333; }
.detail-recipients { margin-top: 24rpx; }
.recipient-row { display: flex; justify-content: space-between; padding: 8rpx 0; font-size: 26rpx; }
.recipient-meta { color: #999; font-size: 24rpx; }
.detail-footer { text-align: center; margin-top: 32rpx; }
</style>
