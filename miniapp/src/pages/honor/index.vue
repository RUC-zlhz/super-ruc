<template>
  <view class="container">
    <view class="honor-hero">
      <view class="hero-copy">
        <text class="hero-kicker">荣誉公示</text>
        <text class="hero-title">榜样力量，追光而行</text>
        <text class="hero-sub">见贤思齐 · 躬身笃行 · 不负韶华</text>
      </view>
      <view class="hero-art">
        <view class="hero-bird hero-bird-a"></view>
        <view class="hero-bird hero-bird-b"></view>
        <view class="hero-campus">
          <view class="campus-block campus-block-a"></view>
          <view class="campus-block campus-block-b"></view>
          <view class="campus-block campus-block-c"></view>
          <view class="campus-ground"></view>
        </view>
        <view class="hero-seal">RUC</view>
      </view>
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
          <view class="control-pill">
            <text>{{ filters.year ? `${filters.year} 年` : '全部年份' }}</text>
            <text class="control-pill-arrow">⌄</text>
          </view>
        </picker>
        <picker mode="selector" :range="LEVEL_OPTION_LABELS" :value="levelIdx" @change="onLevelChange">
          <view class="control-pill">
            <text>{{ levelFilterLabel }}</text>
            <text class="control-pill-arrow">⌄</text>
          </view>
        </picker>
        <view class="history-toggle" :class="{ active: filters.include_archived }" @tap="onToggleHistory">
          <text class="history-toggle-text">{{ filters.include_archived ? '仅看当前' : '包含历史' }}</text>
          <view class="history-switch">
            <view class="history-switch-thumb"></view>
          </view>
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
          <view class="honor-medal-core">
            <text class="honor-medal-icon">{{ medalIcon(honor.level) }}</text>
          </view>
        </view>
        <view class="honor-main">
          <view class="card-head">
            <text class="card-title">{{ honor.title }}</text>
          </view>

          <view class="card-badges">
            <text class="card-tag" :class="`lv-${String(honor.level).toLowerCase()}`">
              {{ levelLabel(honor.level) }}
            </text>
            <text class="card-category">{{ categoryLabel(honor) }}</text>
          </view>

          <view class="card-meta-row">
            <text v-if="honor.recipient_names?.length" class="card-inline-meta card-inline-recipient">
              {{ honor.recipient_names.join('、') }}
            </text>
            <text class="card-inline-meta card-inline-awarder">{{ honor.awarded_by }}</text>
          </view>
          <text class="card-inline-meta card-inline-date">{{ formatDate(honor.announced_at) }}</text>
          <text v-if="honor.summary" class="card-summary">{{ honor.summary.slice(0, 60) }}</text>
          <text v-if="isHistoricalRecord(honor)" class="archived-mark">{{ historyReasonLabel(honor) }}</text>
        </view>
        <view class="card-arrow"><view class="mini-chevron" /></view>
      </view>
    </view>

    <view v-else-if="!loading" class="empty">暂无荣誉记录</view>

    <view v-if="hasMore" class="load-more" @tap="loadMore">
      {{ loading ? '加载中...' : '加载更多' }}
    </view>

    <view v-if="selected" class="sheet-mask" @tap="closeDetail">
      <view class="detail-panel" @tap.stop>
        <view class="sheet-handle" />
        <view class="detail-sheet-head">
          <text class="detail-sheet-title">荣誉详情</text>
          <view class="detail-sheet-close" @tap="closeDetail">×</view>
        </view>
        <view class="detail-summary-card">
          <view class="detail-visual" :class="`lv-${String(selected.level).toLowerCase()}`">
            <view class="detail-visual-core">
              <text class="detail-visual-icon">{{ medalIcon(selected.level) }}</text>
            </view>
          </view>
          <view class="detail-summary-main">
            <view class="detail-summary-head">
              <text class="detail-title">{{ selected.title }}</text>
              <text class="detail-pill detail-level">{{ levelLabel(selected.level) }}</text>
            </view>

            <view class="detail-badges">
              <text class="detail-pill">{{ categoryLabel(selected) }}</text>
            </view>

            <view class="detail-facts">
              <text
                v-if="selected.recipients?.length"
                class="detail-fact detail-fact-recipient"
              >
                {{ selected.recipients.map((recipient) => recipient.display_name).join('、') }}
              </text>
              <text class="detail-fact detail-fact-awarder">{{ selected.awarded_by }}</text>
              <text class="detail-fact detail-fact-date">{{ formatDate(selected.announced_at) }}</text>
            </view>
          </view>
        </view>

        <view v-if="isHistoricalRecord(selected)" class="detail-history">
          {{ historyReasonLabel(selected) }}
        </view>

        <view class="detail-meta-block">
          <text v-if="selected.document_no" class="detail-meta">
            文号 / 证书编号：{{ selected.document_no }}
          </text>
          <text class="detail-meta">公示日期：{{ formatDate(selected.announced_at) }}</text>
        </view>

        <view v-if="selected.recipients?.length" class="detail-recipients">
          <text class="detail-section-title">获奖人</text>
          <view v-for="recipient in selected.recipients" :key="recipient.id" class="recipient-row">
            <text>{{ recipient.display_name }}</text>
            <text v-if="recipient.major_snapshot || recipient.grade_snapshot" class="recipient-meta">
              {{ [recipient.major_snapshot, recipient.grade_snapshot].filter(Boolean).join(' · ') }}
            </text>
          </view>
        </view>

        <view v-if="selected.summary" class="detail-block detail-block-highlight">
          <text class="detail-section-title">荣誉简介</text>
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
          <view class="detail-action secondary" @tap="showAttachmentHint">查看附件</view>
          <view class="detail-action" @tap="shareHonor">分享荣誉</view>
        </view>
      </view>
    </view>
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
const LEVEL_OPTIONS = [
  { label: '全部级别', value: '' },
  { label: '国家级', value: 'NATIONAL' },
  { label: '省部级', value: 'PROVINCIAL' },
  { label: '厅局级', value: 'MINISTERIAL' },
  { label: '校级', value: 'SCHOOL' },
]
const LEVEL_OPTION_LABELS = LEVEL_OPTIONS.map((item) => item.label)

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
  level: string
  year: number | null
  include_archived: boolean
}>({
  category_code: '',
  level: '',
  year: null,
  include_archived: false,
})

const yearIdx = ref(0)
const levelIdx = ref(0)
const categories = ref<HonorCategory[]>([])
const items = ref<HonorRecordBrief[]>([])
const page = ref(1)
const size = 20
const total = ref(0)
const loading = ref(false)
const hasMore = computed(() => !loading.value && items.value.length < total.value)

const selected = ref<HonorRecordDetail | null>(null)

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
const levelFilterLabel = computed(() => LEVEL_OPTIONS[levelIdx.value]?.label || '全部级别')

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
      level: filters.level || undefined,
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

function onLevelChange(event: { detail: { value: string | number } }) {
  const index = Number(event.detail.value)
  levelIdx.value = index
  filters.level = LEVEL_OPTIONS[index]?.value || ''
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
  } catch {
    // request helper already handles toast
  }
}

function closeDetail() {
  selected.value = null
}

function showAttachmentHint() {
  uni.showToast({ title: '附件查看入口已保留，请以后端附件数据为准', icon: 'none' })
}

function shareHonor() {
  if (!selected.value) {
    uni.showToast({ title: '暂无可分享荣誉', icon: 'none' })
    return
  }
  const text = `${selected.value.title}｜${selected.value.awarded_by}｜${formatDate(selected.value.announced_at)}`
  uni.setClipboardData({
    data: text,
    success() {
      uni.showToast({ title: '荣誉信息已复制', icon: 'none' })
    },
  })
}

onMounted(() => {
  void Promise.all([
    loadCategories().catch(() => undefined),
    reload(true).catch(() => undefined),
  ])
})
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 0 24rpx 40rpx;
  background:
    radial-gradient(circle at top, rgba(209, 37, 61, 0.14), transparent 320rpx),
    linear-gradient(180deg, #fff7f6 0, #fff 260rpx, #f7f2f2 640rpx),
    #f7f2f2;
}

.honor-hero {
  position: relative;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin: 0 -24rpx 22rpx;
  min-height: 298rpx;
  padding: 62rpx 34rpx 30rpx 34rpx;
  background:
    radial-gradient(circle at 88% 2%, rgba(214, 40, 64, 0.26), transparent 220rpx),
    radial-gradient(circle at 100% 100%, rgba(214, 40, 64, 0.1), transparent 240rpx),
    linear-gradient(180deg, #fff6f4 0, #fffdfa 100%);
  overflow: hidden;
}

.honor-hero::after {
  content: '';
  position: absolute;
  inset: auto 0 0;
  height: 88rpx;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0), rgba(255, 245, 244, 0.92));
}

.hero-copy {
  position: relative;
  z-index: 2;
  max-width: 430rpx;
}

.hero-kicker {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 112rpx;
  height: 42rpx;
  padding: 0 18rpx;
  border-radius: 999rpx;
  background: rgba(184, 18, 42, 0.08);
  color: #9e1124;
  font-size: 20rpx;
  font-weight: 700;
  letter-spacing: 2rpx;
}

.hero-title {
  display: block;
  margin-top: 24rpx;
  color: #a30f21;
  font-size: 54rpx;
  font-weight: 800;
  letter-spacing: 4rpx;
  line-height: 1.15;
}

.hero-sub {
  display: block;
  margin-top: 18rpx;
  color: #534343;
  font-size: 27rpx;
  letter-spacing: 1rpx;
}

.hero-art {
  position: relative;
  z-index: 1;
  flex-shrink: 0;
  width: 258rpx;
  height: 208rpx;
}

.hero-bird {
  position: absolute;
  border-top: 2rpx solid rgba(185, 74, 84, 0.22);
  border-radius: 50%;
}

.hero-bird-a {
  top: 26rpx;
  left: 24rpx;
  width: 22rpx;
  height: 10rpx;
  transform: rotate(-18deg);
}

.hero-bird-b {
  top: 44rpx;
  left: 64rpx;
  width: 18rpx;
  height: 8rpx;
  transform: rotate(12deg);
}

.hero-campus {
  position: absolute;
  inset: auto 0 0 auto;
  width: 250rpx;
  height: 124rpx;
}

.campus-block {
  position: absolute;
  bottom: 16rpx;
  border-radius: 10rpx 10rpx 0 0;
  border: 2rpx solid rgba(205, 79, 91, 0.2);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.78), rgba(244, 183, 183, 0.28));
  box-shadow: inset 0 -10rpx 18rpx rgba(220, 120, 120, 0.15);
}

.campus-block-a {
  left: 28rpx;
  width: 70rpx;
  height: 58rpx;
}

.campus-block-b {
  left: 92rpx;
  width: 78rpx;
  height: 94rpx;
}

.campus-block-c {
  right: 8rpx;
  width: 96rpx;
  height: 76rpx;
  border-radius: 20rpx 20rpx 0 0;
}

.campus-ground {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 250rpx;
  height: 34rpx;
  border-radius: 999rpx;
  background: radial-gradient(circle, rgba(202, 63, 77, 0.16), rgba(202, 63, 77, 0));
}

.hero-seal {
  position: absolute;
  right: 18rpx;
  top: 16rpx;
  width: 118rpx;
  height: 118rpx;
  border-radius: 50%;
  border: 4rpx solid rgba(176, 22, 41, 0.28);
  color: rgba(176, 22, 41, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 28rpx;
  background: rgba(255, 255, 255, 0.55);
  box-shadow: 0 16rpx 28rpx rgba(212, 67, 86, 0.08);
}

.filter-bar {
  margin-bottom: 22rpx;
}

.category-scroll {
  padding-bottom: 6rpx;
  white-space: nowrap;
}

.chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 60rpx;
  padding: 0 30rpx;
  margin-right: 14rpx;
  border-radius: 999rpx;
  border: 2rpx solid #d6a9ad;
  background: #fff;
  color: #8e1427;
  font-size: 27rpx;
  font-weight: 600;
  box-shadow: 0 10rpx 24rpx rgba(171, 24, 42, 0.04);
}

.chip.active {
  background: linear-gradient(135deg, #cf243d, #a90e22);
  border-color: #b6122b;
  color: #fff;
  box-shadow: 0 12rpx 24rpx rgba(183, 15, 36, 0.18);
}

.control-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  margin-top: 20rpx;
}

.control-pill,
.history-toggle {
  min-height: 78rpx;
  border-radius: 24rpx;
  background: #fff;
  color: #2d2d2d;
  font-size: 28rpx;
  border: 2rpx solid rgba(221, 225, 229, 0.78);
  box-shadow: 0 12rpx 28rpx rgba(37, 36, 37, 0.06);
}

.control-pill {
  display: inline-flex;
  align-items: center;
  gap: 16rpx;
  padding: 0 28rpx;
  font-weight: 600;
}

.control-pill-arrow {
  color: #707070;
  font-size: 24rpx;
  transform: translateY(-2rpx);
}

.history-toggle {
  display: inline-flex;
  align-items: center;
  gap: 20rpx;
  padding: 0 12rpx 0 28rpx;
}

.history-toggle-text {
  color: #353535;
  font-size: 28rpx;
}

.history-switch {
  position: relative;
  width: 90rpx;
  height: 48rpx;
  border-radius: 999rpx;
  background: #dddfe2;
  transition: background 0.2s ease;
}

.history-switch-thumb {
  position: absolute;
  top: 4rpx;
  left: 4rpx;
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 8rpx 16rpx rgba(31, 41, 55, 0.14);
  transition: transform 0.2s ease;
}

.history-toggle.active .history-switch {
  background: linear-gradient(135deg, #d72840, #b40f25);
}

.history-toggle.active .history-switch-thumb {
  transform: translateX(42rpx);
}

.history-hint {
  position: relative;
  margin-bottom: 18rpx;
  padding: 20rpx 22rpx 20rpx 72rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, rgba(255, 246, 244, 0.96), rgba(255, 250, 249, 0.96));
  color: #76423f;
  font-size: 25rpx;
  box-shadow: 0 12rpx 28rpx rgba(149, 73, 64, 0.06);
}

.history-hint::before {
  content: '';
  position: absolute;
  left: 24rpx;
  top: 50%;
  width: 26rpx;
  height: 26rpx;
  margin-top: -16rpx;
  border: 4rpx solid #9e2331;
  border-radius: 50%;
}

.history-hint::after {
  content: '';
  position: absolute;
  left: 37rpx;
  top: 50%;
  width: 10rpx;
  height: 10rpx;
  margin-top: -17rpx;
  border-right: 4rpx solid #9e2331;
  border-bottom: 4rpx solid #9e2331;
  transform: rotate(45deg);
}

.card {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 22rpx;
  margin-bottom: 20rpx;
  padding: 26rpx 32rpx 26rpx 26rpx;
  border-radius: 28rpx;
  background: #fff;
  border: 2rpx solid rgba(242, 233, 232, 0.92);
  box-shadow: 0 14rpx 32rpx rgba(57, 48, 49, 0.08);
  overflow: hidden;
}

.card::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 180rpx;
  height: 180rpx;
  background: radial-gradient(circle, rgba(226, 64, 81, 0.08), rgba(226, 64, 81, 0));
  transform: translate(32rpx, -48rpx);
}

.honor-medal {
  position: relative;
  flex-shrink: 0;
  width: 118rpx;
  height: 132rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.honor-medal::before,
.honor-medal::after {
  content: '';
  position: absolute;
  bottom: 6rpx;
  width: 26rpx;
  height: 40rpx;
  border-radius: 0 0 10rpx 10rpx;
  background: linear-gradient(180deg, #c4162f, #8f0d1e);
  z-index: 0;
}

.honor-medal::before {
  left: 28rpx;
  transform: skew(-8deg);
}

.honor-medal::after {
  right: 28rpx;
  transform: skew(8deg);
}

.honor-medal-core {
  position: relative;
  z-index: 1;
  width: 94rpx;
  height: 94rpx;
  border-radius: 50%;
  background: linear-gradient(180deg, #ffe6a8, #e4a93d 72%, #c07a16);
  border: 6rpx solid rgba(255, 243, 205, 0.92);
  box-shadow:
    inset 0 8rpx 16rpx rgba(255, 255, 255, 0.48),
    0 10rpx 20rpx rgba(174, 110, 18, 0.18);
  display: flex;
  align-items: center;
  justify-content: center;
}

.honor-medal-core::before {
  content: '';
  position: absolute;
  inset: 10rpx;
  border-radius: 50%;
  border: 2rpx solid rgba(191, 122, 20, 0.24);
}

.honor-medal-icon {
  color: #9b5e07;
  font-size: 34rpx;
  font-weight: 800;
}

.honor-medal.lv-provincial .honor-medal-core {
  background: linear-gradient(180deg, #fafbfc, #d0d5db 72%, #9da4ae);
  box-shadow:
    inset 0 8rpx 16rpx rgba(255, 255, 255, 0.48),
    0 10rpx 20rpx rgba(111, 123, 140, 0.16);
}

.honor-medal.lv-provincial .honor-medal-core::before {
  border-color: rgba(113, 121, 136, 0.24);
}

.honor-medal.lv-provincial .honor-medal-icon {
  color: #6d7480;
}

.honor-medal.lv-ministerial .honor-medal-core {
  background: linear-gradient(180deg, #edf5ff, #bed8fb 74%, #7fb0f2);
  box-shadow:
    inset 0 8rpx 16rpx rgba(255, 255, 255, 0.44),
    0 10rpx 20rpx rgba(50, 107, 183, 0.15);
}

.honor-medal.lv-ministerial .honor-medal-core::before {
  border-color: rgba(67, 116, 181, 0.22);
}

.honor-medal.lv-ministerial .honor-medal-icon {
  color: #2f69b1;
}

.honor-medal.lv-school .honor-medal-core {
  background: linear-gradient(180deg, #ffe6d9, #eea167 74%, #d06324);
  box-shadow:
    inset 0 8rpx 16rpx rgba(255, 255, 255, 0.42),
    0 10rpx 20rpx rgba(167, 74, 15, 0.15);
}

.honor-medal.lv-school .honor-medal-core::before {
  border-color: rgba(164, 82, 18, 0.22);
}

.honor-medal.lv-school .honor-medal-icon {
  color: #ab4d0f;
}

.honor-main {
  position: relative;
  z-index: 1;
  flex: 1;
  min-width: 0;
}

.card-arrow {
  position: absolute;
  right: 22rpx;
  top: 50%;
  width: 44rpx;
  height: 44rpx;
  margin-top: -22rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  color: #8d9096;
  box-shadow: 0 6rpx 16rpx rgba(38, 38, 38, 0.08);
}

.card-head {
  min-height: 44rpx;
}

.card-title {
  display: block;
  padding-right: 72rpx;
  color: #1f2329;
  font-size: 37rpx;
  font-weight: 800;
  line-height: 1.32;
}

.card-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 14rpx;
}

.card-tag,
.card-category {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 38rpx;
  padding: 0 16rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  font-weight: 600;
}

.card-tag.lv-national { background: #fff0f1; color: #c63b4c; }
.card-tag.lv-provincial { background: #fff8e7; color: #cd8b15; }
.card-tag.lv-ministerial { background: #edf5ff; color: #2e71c7; }
.card-tag.lv-school { background: #fff2eb; color: #bf5e22; }

.card-category {
  background: #faf4f0;
  color: #8f6057;
}

.card-meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx 18rpx;
  margin-top: 18rpx;
}

.card-inline-meta {
  position: relative;
  display: inline-flex;
  align-items: center;
  min-height: 34rpx;
  padding-left: 36rpx;
  color: #5a5f67;
  font-size: 26rpx;
}

.card-inline-meta::before,
.card-inline-meta::after {
  content: '';
  position: absolute;
  left: 0;
}

.card-inline-recipient::before {
  top: 4rpx;
  width: 18rpx;
  height: 18rpx;
  border: 2rpx solid #6d7178;
  border-radius: 50%;
}

.card-inline-recipient::after {
  bottom: 2rpx;
  width: 24rpx;
  height: 12rpx;
  border: 2rpx solid #6d7178;
  border-top: 0;
  border-radius: 0 0 14rpx 14rpx;
}

.card-inline-awarder::before {
  top: 4rpx;
  width: 22rpx;
  height: 22rpx;
  border: 2rpx solid #6d7178;
  border-bottom: 0;
}

.card-inline-awarder::after {
  top: 10rpx;
  left: 6rpx;
  width: 10rpx;
  height: 12rpx;
  border-left: 2rpx solid #6d7178;
  border-right: 2rpx solid #6d7178;
}

.card-inline-date {
  display: flex;
  margin-top: 10rpx;
  color: #707780;
}

.card-inline-date::before {
  top: 4rpx;
  width: 24rpx;
  height: 22rpx;
  border: 2rpx solid #707780;
  border-radius: 6rpx;
}

.card-inline-date::after {
  top: 0;
  left: 5rpx;
  width: 14rpx;
  height: 8rpx;
  border-top: 2rpx solid #707780;
  border-left: 2rpx solid transparent;
  border-right: 2rpx solid transparent;
}

.card-summary {
  display: block;
  margin-top: 14rpx;
  color: #6f6a67;
  font-size: 25rpx;
  line-height: 1.55;
}

.archived-mark {
  display: inline-flex;
  align-items: center;
  min-height: 40rpx;
  margin-top: 14rpx;
  padding: 0 14rpx;
  border-radius: 999rpx;
  background: #fff3ef;
  color: #b15c45;
  font-size: 22rpx;
  font-weight: 600;
}

.empty {
  padding: 100rpx 0;
  text-align: center;
  color: #9ca3af;
  font-size: 28rpx;
}

.load-more {
  padding: 30rpx 0 8rpx;
  text-align: center;
  color: #8e1226;
  font-size: 26rpx;
}

.sheet-mask {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: flex-end;
  background: rgba(31, 24, 27, 0.46);
}

.detail-panel {
  width: 100%;
  max-height: 80vh;
  overflow-y: auto;
  padding: 18rpx 30rpx calc(34rpx + env(safe-area-inset-bottom));
  border-radius: 40rpx 40rpx 0 0;
  background: #fff;
  box-shadow: 0 -18rpx 36rpx rgba(39, 28, 30, 0.08);
}

.sheet-handle {
  width: 92rpx;
  height: 8rpx;
  border-radius: 999rpx;
  background: #cfcfcf;
  margin: 0 auto 20rpx;
}

.detail-sheet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.detail-sheet-title {
  color: #1e2329;
  font-size: 42rpx;
  font-weight: 800;
}

.detail-sheet-close {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: #f7f3f3;
  color: #6c6c6c;
  font-size: 42rpx;
  line-height: 64rpx;
  text-align: center;
}

.detail-summary-card {
  display: flex;
  align-items: flex-start;
  gap: 22rpx;
  margin-top: 26rpx;
  padding: 8rpx 4rpx 0;
}

.detail-visual {
  position: relative;
  flex-shrink: 0;
  width: 150rpx;
  height: 168rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-visual::before,
.detail-visual::after {
  content: '';
  position: absolute;
  bottom: 10rpx;
  width: 30rpx;
  height: 46rpx;
  border-radius: 0 0 12rpx 12rpx;
  background: linear-gradient(180deg, #c4162f, #8f0d1e);
  z-index: 0;
}

.detail-visual::before {
  left: 34rpx;
  transform: skew(-8deg);
}

.detail-visual::after {
  right: 34rpx;
  transform: skew(8deg);
}

.detail-visual-core {
  position: relative;
  z-index: 1;
  width: 118rpx;
  height: 118rpx;
  border-radius: 50%;
  background: linear-gradient(180deg, #ffe6a8, #e4a93d 72%, #c07a16);
  border: 8rpx solid rgba(255, 243, 205, 0.92);
  box-shadow:
    inset 0 8rpx 16rpx rgba(255, 255, 255, 0.5),
    0 12rpx 24rpx rgba(176, 112, 18, 0.18);
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-visual-core::before {
  content: '';
  position: absolute;
  inset: 12rpx;
  border-radius: 50%;
  border: 2rpx solid rgba(191, 122, 20, 0.24);
}

.detail-visual-icon {
  color: #9b5e07;
  font-size: 42rpx;
  font-weight: 800;
}

.detail-visual.lv-provincial .detail-visual-core {
  background: linear-gradient(180deg, #fafbfc, #d0d5db 72%, #9da4ae);
  box-shadow:
    inset 0 8rpx 16rpx rgba(255, 255, 255, 0.48),
    0 12rpx 24rpx rgba(111, 123, 140, 0.16);
}

.detail-visual.lv-provincial .detail-visual-core::before {
  border-color: rgba(113, 121, 136, 0.24);
}

.detail-visual.lv-provincial .detail-visual-icon {
  color: #6d7480;
}

.detail-visual.lv-ministerial .detail-visual-core {
  background: linear-gradient(180deg, #edf5ff, #bed8fb 74%, #7fb0f2);
  box-shadow:
    inset 0 8rpx 16rpx rgba(255, 255, 255, 0.44),
    0 12rpx 24rpx rgba(50, 107, 183, 0.15);
}

.detail-visual.lv-ministerial .detail-visual-core::before {
  border-color: rgba(67, 116, 181, 0.22);
}

.detail-visual.lv-ministerial .detail-visual-icon {
  color: #2f69b1;
}

.detail-visual.lv-school .detail-visual-core {
  background: linear-gradient(180deg, #ffe6d9, #eea167 74%, #d06324);
  box-shadow:
    inset 0 8rpx 16rpx rgba(255, 255, 255, 0.42),
    0 12rpx 24rpx rgba(167, 74, 15, 0.15);
}

.detail-visual.lv-school .detail-visual-core::before {
  border-color: rgba(164, 82, 18, 0.22);
}

.detail-visual.lv-school .detail-visual-icon {
  color: #ab4d0f;
}

.detail-summary-main {
  flex: 1;
  min-width: 0;
  padding-top: 8rpx;
}

.detail-summary-head {
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
}

.detail-title {
  flex: 1;
  color: #1f2329;
  font-size: 38rpx;
  font-weight: 800;
  line-height: 1.32;
}

.detail-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 16rpx;
}

.detail-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40rpx;
  padding: 0 16rpx;
  border-radius: 999rpx;
  background: #faf4f0;
  color: #8f6057;
  font-size: 22rpx;
  font-weight: 600;
}

.detail-level {
  flex-shrink: 0;
  background: #fff0f1;
  color: #c63b4c;
}

.detail-history {
  margin-top: 22rpx;
  padding: 16rpx 20rpx;
  border-radius: 22rpx;
  background: #fff4ef;
  color: #a65942;
  font-size: 24rpx;
}

.detail-facts {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
  margin-top: 18rpx;
}

.detail-fact {
  position: relative;
  display: block;
  padding-left: 104rpx;
  color: #4f545d;
  font-size: 27rpx;
  line-height: 1.5;
}

.detail-fact::before {
  position: absolute;
  left: 0;
  top: 0;
  color: #2e3137;
  font-weight: 700;
}

.detail-fact-recipient::before { content: '获 奖 人'; }
.detail-fact-awarder::before { content: '授奖单位'; }
.detail-fact-date::before { content: '获奖日期'; }

.detail-meta-block {
  margin-top: 18rpx;
  padding: 18rpx 22rpx;
  border-radius: 22rpx;
  background: #fbf8f8;
}

.detail-meta {
  display: block;
  color: #6b7280;
  font-size: 24rpx;
  line-height: 1.6;
}

.detail-meta + .detail-meta {
  margin-top: 8rpx;
}

.detail-recipients,
.detail-block {
  margin-top: 24rpx;
}

.detail-section-title {
  display: block;
  margin-bottom: 12rpx;
  color: #262b31;
  font-size: 28rpx;
  font-weight: 700;
}

.detail-body {
  color: #374151;
  font-size: 28rpx;
  line-height: 1.7;
}

.detail-block-highlight {
  padding: 20rpx 22rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, #fff7f5, #fffefe);
}

.recipient-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14rpx 20rpx;
  border-radius: 20rpx;
  background: #fbf8f8;
  font-size: 26rpx;
  color: #374151;
}

.recipient-row + .recipient-row {
  margin-top: 12rpx;
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
  position: relative;
  height: 88rpx;
  border-radius: 20rpx;
  background: linear-gradient(135deg, #fff9f8, #fff6f5);
  color: #7d1c2b;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 700;
  border: 2rpx solid rgba(232, 220, 220, 0.96);
}

.detail-action::before {
  margin-right: 12rpx;
  font-size: 32rpx;
}

.detail-action.secondary::before {
  content: '⌁';
}

.detail-action:not(.secondary)::before {
  content: '⤴';
}

.detail-action.secondary {
  color: #5f5251;
  background: #fff;
}
</style>
