<template>
  <view class="container">
    <view class="honor-hero">
      <text class="hero-title">榜样力量，追光而行</text>
      <text class="hero-sub">见贤思齐 · 躬身笃行 · 不负韶华</text>
      <view class="hero-seal">RUC</view>
    </view>

    <view class="filter-bar">
      <scroll-view scroll-x class="category-scroll">
        <view
          v-for="opt in categoryChips"
          :key="opt.code || 'ALL'"
          class="chip"
          :class="{ active: filters.category_code === opt.code }"
          @tap="onCategory(opt.code)"
        >
          {{ opt.name }}
        </view>
      </scroll-view>

      <view class="control-row">
        <picker mode="selector" :range="YEAR_OPTIONS" :value="yearIdx" @change="onYearChange">
          <view class="control-pill">{{ filters.year ? `${filters.year} 年` : '全部年份' }}</view>
        </picker>
        <view class="history-toggle" :class="{ active: filters.include_archived }" @tap="onToggleHistory">
          {{ filters.include_archived ? '仅看当前' : '包含历史' }}
        </view>
      </view>
    </view>

    <view v-if="filters.include_archived" class="history-hint">
      当前结果包含历史荣誉，相关信息仅供参考
    </view>

    <view v-if="items.length" class="list">
      <view
        v-for="honor in items"
        :key="honor.id"
        class="card"
        @tap="onDetail(honor)"
      >
        <view class="honor-medal" :class="`lv-${String(honor.level).toLowerCase()}`">
          {{ medalIcon(honor.level) }}
        </view>
        <view class="honor-main">
        <view class="card-head">
          <text class="card-title">{{ honor.title }}</text>
          <text class="card-tag" :class="`lv-${String(honor.level).toLowerCase()}`">
            {{ levelLabel(honor.level) }}
          </text>
        </view>

        <view class="card-category-row">
          <text class="card-category">{{ categoryLabel(honor) }}</text>
        </view>

        <text v-if="honor.recipient_names?.length" class="card-recipients">
          获奖人：{{ honor.recipient_names.join('、') }}
        </text>
        <text class="card-meta">{{ honor.awarded_by }} · {{ formatDate(honor.announced_at) }}</text>
        <text v-if="honor.summary" class="card-summary">{{ honor.summary.slice(0, 60) }}</text>
        <text v-if="isHistoricalRecord(honor)" class="archived-mark">{{ historyReasonLabel(honor) }}</text>
        </view>
        <text class="card-arrow">›</text>
      </view>
    </view>

    <view v-else-if="!loading" class="empty">暂无荣誉记录</view>

    <view v-if="hasMore" class="load-more" @tap="loadMore">
      {{ loading ? '加载中...' : '加载更多' }}
    </view>

    <uni-popup ref="detailPopup" type="bottom">
      <view v-if="selected" class="detail-panel">
        <view class="sheet-handle" />
        <text class="detail-title">{{ selected.title }}</text>
        <view class="detail-visual" :class="`lv-${String(selected.level).toLowerCase()}`">
          {{ medalIcon(selected.level) }}
        </view>

        <view class="detail-badges">
          <text class="detail-pill">{{ categoryLabel(selected) }}</text>
          <text class="detail-pill detail-level">{{ levelLabel(selected.level) }}</text>
        </view>

        <view v-if="isHistoricalRecord(selected)" class="detail-history">
          {{ historyReasonLabel(selected) }}
        </view>

        <text class="detail-meta">{{ selected.awarded_by }} · {{ formatDate(selected.announced_at) }}</text>
        <text v-if="selected.document_no" class="detail-meta">
          文号 / 证书编号：{{ selected.document_no }}
        </text>
        <text class="detail-meta">公示日期：{{ formatDate(selected.announced_at) }}</text>

        <view v-if="selected.recipients?.length" class="detail-recipients">
          <text class="detail-section-title">获奖人</text>
          <view v-for="recipient in selected.recipients" :key="recipient.id" class="recipient-row">
            <text>{{ recipient.display_name }}</text>
            <text v-if="recipient.major_snapshot || recipient.grade_snapshot" class="recipient-meta">
              {{ [recipient.major_snapshot, recipient.grade_snapshot].filter(Boolean).join(' · ') }}
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
          <view class="detail-action secondary">查看附件</view>
          <view class="detail-action" @tap="closeDetail">分享荣誉</view>
        </view>
      </view>
    </uni-popup>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  getHonorDetail,
  listHonorCategories,
  listPublicHonors,
  type HonorCategory,
  type HonorRecordBrief,
  type HonorRecordDetail,
} from '@/api/honor'

const LEVEL_LABELS: Record<string, string> = {
  NATIONAL: '国家级',
  PROVINCIAL: '省部级',
  MINISTERIAL: '厅局级',
  SCHOOL: '校级',
}

const currentYear = new Date().getFullYear()
const YEAR_OPTIONS = ['全部年份', ...Array.from({ length: 6 }, (_, index) => String(currentYear - index))]

type HistoryLike = {
  status?: string
  effective_to?: string | null
  is_historical?: boolean | null
  history_reason?: string | null
  archive_reason?: string | null
  category_code?: string
  category_name?: string | null
}

const filters = reactive<{
  category_code: string
  year: number | null
  include_archived: boolean
}>({
  category_code: '',
  year: null,
  include_archived: false,
})

const yearIdx = ref(0)
const categories = ref<HonorCategory[]>([])
const items = ref<HonorRecordBrief[]>([])
const page = ref(1)
const size = 20
const total = ref(0)
const loading = ref(false)
const hasMore = computed(() => !loading.value && items.value.length < total.value)

const selected = ref<HonorRecordDetail | null>(null)
const detailPopup = ref<any>(null)

const categoryMap = computed(() => {
  const map = new Map<string, string>()
  for (const category of categories.value) {
    map.set(category.code, category.name)
  }
  for (const honor of items.value) {
    if (honor.category_code) {
      map.set(honor.category_code, honor.category_name || map.get(honor.category_code) || honor.category_code)
    }
  }
  if (selected.value?.category_code) {
    map.set(
      selected.value.category_code,
      selected.value.category_name || map.get(selected.value.category_code) || selected.value.category_code,
    )
  }
  return map
})

const categoryChips = computed(() => ([
  { code: '', name: '全部' },
  ...Array.from(categoryMap.value.entries()).map(([code, name]) => ({ code, name })),
]))

function levelLabel(level: string) {
  return LEVEL_LABELS[level] || level
}

function medalIcon(level: string) {
  if (level === 'NATIONAL') return '金'
  if (level === 'PROVINCIAL') return '杯'
  if (level === 'SCHOOL') return '证'
  return '奖'
}

function formatDate(value?: string | null) {
  return value ? value.slice(0, 10) : '-'
}

function categoryLabel(record: { category_code?: string; category_name?: string | null }) {
  if (record.category_name) return record.category_name
  if (record.category_code) return categoryMap.value.get(record.category_code) || record.category_code
  return '-'
}

function isPastDate(value?: string | null) {
  if (!value) return false
  const target = new Date(`${value.slice(0, 10)}T00:00:00`)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return Number.isFinite(target.getTime()) && target.getTime() < today.getTime()
}

function isHistoricalRecord(record: HistoryLike) {
  if (typeof record.is_historical === 'boolean') return record.is_historical
  if (record.status === 'ARCHIVED') return true
  if (record.status === 'REVOKED') return false
  return isPastDate(record.effective_to)
}

function historyReasonLabel(record: HistoryLike) {
  if (record.history_reason) return record.history_reason
  if (record.status === 'ARCHIVED') return record.archive_reason || '历史荣誉，仅供参考'
  if (isPastDate(record.effective_to)) return '历史荣誉 · 展示有效期已结束'
  return '历史荣誉，仅供参考'
}

function visibleItems(records: HonorRecordBrief[]) {
  return records.filter((record) => record.status !== 'REVOKED')
}

async function loadCategories() {
  try {
    const resp = await listHonorCategories()
    categories.value = resp.data
  } catch {
    // Keep chip fallback derived from returned honor items when categories are unavailable.
  }
}

async function reload(reset = true) {
  if (loading.value && !reset) return
  if (reset) {
    page.value = 1
    items.value = []
  }
  loading.value = true
  try {
    const resp = await listPublicHonors({
      category_code: filters.category_code || undefined,
      year: filters.year || undefined,
      include_archived: filters.include_archived,
      page: page.value,
      size,
    })
    const nextItems = visibleItems(resp.data.items || [])
    items.value = reset ? nextItems : [...items.value, ...nextItems]
    total.value = resp.data.meta?.total || items.value.length
  } finally {
    loading.value = false
  }
}

function onCategory(code: string) {
  filters.category_code = code
  void reload(true).catch(() => undefined)
}

function onYearChange(event: { detail: { value: string | number } }) {
  const index = Number(event.detail.value)
  yearIdx.value = index
  filters.year = index === 0 ? null : Number(YEAR_OPTIONS[index])
  void reload(true).catch(() => undefined)
}

function onToggleHistory() {
  filters.include_archived = !filters.include_archived
  void reload(true).catch(() => undefined)
}

function loadMore() {
  if (!hasMore.value) return
  page.value += 1
  void reload(false).catch(() => undefined)
}

async function onDetail(row: HonorRecordBrief) {
  if (row.status === 'REVOKED') {
    uni.showToast({ title: '已撤销荣誉不提供详情', icon: 'none' })
    return
  }
  try {
    const resp = await getHonorDetail(row.id)
    selected.value = resp.data
    detailPopup.value?.open()
  } catch {
    // request helper already handles toast
  }
}

function closeDetail() {
  detailPopup.value?.close()
  selected.value = null
}

onMounted(() => {
  void Promise.allSettled([loadCategories(), reload(true)])
})
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 0 24rpx 36rpx;
  background:
    linear-gradient(180deg, #fff4f5 0, #fff 210rpx, #f8f3f4 520rpx),
    #f8f3f4;
}

.honor-hero {
  position: relative;
  margin: 0 -24rpx 24rpx;
  min-height: 260rpx;
  padding: 56rpx 42rpx 34rpx;
  background:
    radial-gradient(circle at 86% 46%, rgba(183,15,36,0.16), transparent 150rpx),
    linear-gradient(135deg, #fff2f3, #fff 64%);
  overflow: hidden;
}

.hero-title {
  display: block;
  color: #b70f24;
  font-size: 44rpx;
  font-weight: 800;
  letter-spacing: 2rpx;
}

.hero-sub {
  display: block;
  margin-top: 14rpx;
  color: #5f4d52;
  font-size: 25rpx;
}

.hero-seal {
  position: absolute;
  right: 42rpx;
  top: 48rpx;
  width: 112rpx;
  height: 112rpx;
  border-radius: 50%;
  border: 4rpx solid rgba(183,15,36,0.28);
  color: rgba(183,15,36,0.72);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
}

.filter-bar { margin-bottom: 20rpx; }

.category-scroll {
  white-space: nowrap;
}

.chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10rpx 24rpx;
  margin-right: 12rpx;
  border-radius: 32rpx;
  border: 1rpx solid #d9b8bd;
  background: #fff;
  color: #9f1d2e;
  font-size: 26rpx;
}

.chip.active {
  background: #b70f24;
  border-color: #b70f24;
  color: #fff;
}

.control-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16rpx;
}

.control-pill,
.history-toggle {
  padding: 14rpx 28rpx;
  border-radius: 18rpx;
  background: #fff;
  color: #4b5563;
  font-size: 25rpx;
  border: 1rpx solid #f0e2e5;
}

.history-toggle.active {
  background: #fee2e2;
  color: #9f1239;
}

.history-hint {
  margin-bottom: 16rpx;
  padding: 14rpx 18rpx;
  border-radius: 16rpx;
  background: #fff7ed;
  color: #9a3412;
  font-size: 24rpx;
}

.card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 24rpx;
  margin-bottom: 18rpx;
  padding: 24rpx 30rpx 24rpx 24rpx;
  border-radius: 22rpx;
  background: #fff;
  border: 1rpx solid #f0e2e5;
  box-shadow: var(--shadow-card);
}

.honor-medal {
  flex-shrink: 0;
  width: 112rpx;
  height: 112rpx;
  border-radius: 28rpx;
  background: linear-gradient(135deg, #f5c86a, #b87916);
  color: #fff;
  font-size: 36rpx;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}

.honor-medal.lv-provincial { background: linear-gradient(135deg, #e5e7eb, #9ca3af); }
.honor-medal.lv-school { background: linear-gradient(135deg, #c44b3f, #9a1a25); }
.honor-main { flex: 1; min-width: 0; }
.card-arrow {
  position: absolute;
  right: 18rpx;
  color: #9ca3af;
  font-size: 34rpx;
}

.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.card-title {
  flex: 1;
  color: #1f2937;
  font-size: 31rpx;
  font-weight: 800;
}

.card-tag {
  flex-shrink: 0;
  margin-left: 12rpx;
  padding: 4rpx 14rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
}

.card-tag.lv-national { background: #fff1f0; color: #cf1322; }
.card-tag.lv-provincial { background: #fff7e6; color: #d46b08; }
.card-tag.lv-ministerial { background: #e6f7ff; color: #096dd9; }
.card-tag.lv-school { background: #f0f5ff; color: #2f54eb; }

.card-category-row {
  margin-top: 10rpx;
}

.card-category {
  display: inline-block;
  padding: 4rpx 14rpx;
  border-radius: 999rpx;
  background: #f3f4f6;
  color: #4b5563;
  font-size: 22rpx;
}

.card-recipients,
.card-meta,
.card-summary,
.archived-mark {
  display: block;
  margin-top: 8rpx;
}

.card-recipients {
  color: #4b5563;
  font-size: 26rpx;
}

.card-meta {
  color: #9ca3af;
  font-size: 24rpx;
}

.card-summary {
  color: #6b7280;
  font-size: 26rpx;
}

.archived-mark {
  color: #c2410c;
  font-size: 23rpx;
}

.empty {
  padding: 80rpx 0;
  text-align: center;
  color: #9ca3af;
  font-size: 28rpx;
}

.load-more {
  padding: 24rpx 0 8rpx;
  text-align: center;
  color: #7f1722;
  font-size: 26rpx;
}

.detail-panel {
  max-height: 80vh;
  overflow-y: auto;
  padding: 18rpx 32rpx 34rpx;
  border-radius: 34rpx 34rpx 0 0;
  background: #fff;
}

.sheet-handle {
  width: 72rpx;
  height: 8rpx;
  border-radius: 999rpx;
  background: #d9d9d9;
  margin: 0 auto 24rpx;
}

.detail-title {
  display: block;
  color: #1f2937;
  font-size: 34rpx;
  font-weight: 800;
}

.detail-visual {
  width: 150rpx;
  height: 150rpx;
  border-radius: 36rpx;
  margin: 24rpx auto 18rpx;
  background: linear-gradient(135deg, #f5c86a, #b87916);
  color: #fff;
  font-size: 48rpx;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 12rpx 28rpx rgba(184,121,22,0.22);
}

.detail-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 14rpx;
}

.detail-pill {
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
  background: #f3f4f6;
  color: #4b5563;
  font-size: 22rpx;
}

.detail-level {
  background: #fef3c7;
  color: #92400e;
}

.detail-history {
  margin-top: 16rpx;
  padding: 14rpx 18rpx;
  border-radius: 16rpx;
  background: #fff7ed;
  color: #9a3412;
  font-size: 24rpx;
}

.detail-meta {
  display: block;
  margin-top: 8rpx;
  color: #6b7280;
  font-size: 24rpx;
}

.detail-recipients,
.detail-block {
  margin-top: 24rpx;
}

.detail-section-title {
  display: block;
  margin-bottom: 10rpx;
  color: #1f2937;
  font-size: 28rpx;
  font-weight: 600;
}

.detail-body {
  color: #374151;
  font-size: 28rpx;
  line-height: 1.7;
}

.recipient-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8rpx 0;
  font-size: 26rpx;
  color: #374151;
}

.recipient-meta {
  color: #9ca3af;
  font-size: 24rpx;
}

.detail-footer {
  margin-top: 32rpx;
  display: flex;
  gap: 18rpx;
}

.detail-action {
  flex: 1;
  height: 76rpx;
  border-radius: 16rpx;
  background: #b70f24;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  font-weight: 700;
}

.detail-action.secondary {
  background: #fff8f9;
  color: #7f1722;
  border: 1rpx solid #f0d5da;
}
</style>
