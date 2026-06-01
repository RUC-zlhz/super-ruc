<template>
  <view class="container">
    <view class="tab-row">
      <view
        v-for="t in TABS"
        :key="t.value"
        class="tab"
        :class="{ active: tab === t.value }"
        @tap="onTab(t.value)"
      >{{ t.label }}</view>
    </view>

    <view
      v-if="subscribeTemplates.length"
      class="subscribe-panel"
      hover-class="hover-opacity"
      @tap="onSubscribe"
    >
      <view class="subscribe-copy">
        <text class="subscribe-title">订阅微信提醒</text>
        <text class="subscribe-desc">接收党团流程提醒和申请状态更新。</text>
      </view>
      <button
        class="subscribe-button"
        size="mini"
        :loading="subscribeLoading"
        @tap.stop="onSubscribe"
      >订阅</button>
    </view>

    <InlineStateNotice
      v-if="pageError"
      :tone="notices.length ? 'warning' : 'error'"
      :title="notices.length ? '通知列表未完全更新' : '通知列表加载失败'"
      :description="notices.length ? `${pageError}，当前保留上次加载结果。` : `${pageError}，可点击重试重新同步。`"
      action-text="重试"
      @action="reload"
    />

    <EmptyState
      v-if="loading && !notices.length"
      icon="◷"
      tone="muted"
      title="通知加载中"
      description="正在同步你的通知列表，请稍候。"
      compact
    />

    <view v-else-if="visibleNotices.length" class="list">
      <view
        v-for="n in visibleNotices"
        :key="noticeKey(n)"
        class="notice-card"
        :class="{ unread: isUnread(n), pinned: n.is_pinned }"
        hover-class="hover-opacity"
        @tap="onDetail(n)"
      >
        <view class="notice-icon" :class="{ muted: !isUnread(n) }">{{ noticeIcon(n) }}</view>
        <view class="notice-main">
          <view class="notice-head">
            <view class="notice-title-wrap">
              <text class="notice-title">{{ n.title }}</text>
              <text class="pin-corner" v-if="n.is_pinned">置顶</text>
            </view>
            <view class="notice-state-flag">
              <view v-if="isUnread(n)" class="state-dot unread" />
              <text v-else class="read-mark">✓</text>
            </view>
          </view>
          <text class="notice-source">{{ noticeTag(n) }}</text>
          <text class="notice-preview" v-if="n.summary">{{ n.summary.slice(0, 80) }}</text>
          <view class="notice-footer">
            <text class="notice-date">◷ {{ formatNoticeTime(n.published_at) }}</text>
            <view class="notice-arrow"><view class="mini-chevron" /></view>
          </view>
        </view>
      </view>
    </view>

    <EmptyState
      v-else-if="!loading && !pageError"
      icon="铃"
      tone="primary"
      title="暂无通知"
      description="当前没有新的通知，可稍后下拉刷新。"
      compact
    />

    <view v-if="hasMore" class="load-more" hover-class="hover-opacity" @tap="loadMore">加载更多</view>
    <view v-else-if="!loading && notices.length" class="load-end">没有更多了</view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import InlineStateNotice from '@/components/InlineStateNotice.vue'
import EmptyState from '@/components/EmptyState.vue'
import {
  getMyNotices,
  getSubscribeConfig,
  saveSubscribeAuthorizations,
  type StudentNoticeItem,
  type WechatSubscribeAuthorizationResult,
  type WechatSubscribeTemplate,
} from '@/api/notice'
import { getErrorMessage } from '@/utils/error'
import { openNoticeDetail } from '@/utils/navigation'
import { formatShanghaiDateTime } from '@/utils/datetime'

type NoticeTab = 'all' | 'unread' | 'read'

const TABS: Array<{ label: string; value: NoticeTab }> = [
  { label: '全部', value: 'all' },
  { label: '未读', value: 'unread' },
  { label: '已读', value: 'read' },
]
const tab = ref<NoticeTab>('all')

const CATEGORY_LABELS: Record<string, string> = {
  SYSTEM: '系统通知',
  ACADEMIC: '教学通知',
  PARTY: '党团通知',
  CAMPUS: '校园通知',
}

const notices = ref<StudentNoticeItem[]>([])
const page = ref(1)
const size = 20
const total = ref(0)
const loading = ref(false)
const pageError = ref('')
const hasLoaded = ref(false)
const subscribeLoading = ref(false)
const subscribeTemplates = ref<WechatSubscribeTemplate[]>([])
const hasMore = computed(() => notices.value.length < total.value)

function isUnread(notice: StudentNoticeItem) {
  return !notice.read_at
}

function noticeKey(notice: StudentNoticeItem) {
  return notice.delivery_id == null ? notice.id : notice.delivery_id
}

function noticeTag(notice: StudentNoticeItem) {
  if (notice.is_pinned) return '置顶'
  if (notice.category) return CATEGORY_LABELS[notice.category] || notice.category
  return '通知'
}

function noticeIcon(notice: StudentNoticeItem) {
  const tag = notice.category || ''
  if (tag.includes('ACADEMIC') || tag.includes('教')) return '学'
  if (tag.includes('PARTY') || tag.includes('党')) return '党'
  if (tag.includes('SYSTEM') || tag.includes('系统')) return '⚙'
  if (tag.includes('CAMPUS') || tag.includes('校园')) return '园'
  return '铃'
}

function formatNoticeTime(value?: string | null) {
  return formatShanghaiDateTime(value)
}

const visibleNotices = computed(() => {
  if (tab.value === 'unread') return notices.value.filter(isUnread)
  if (tab.value === 'read') return notices.value.filter(n => !isUnread(n))
  return notices.value
})

async function reload(reset = true, targetPage = 1) {
  if (loading.value) return
  loading.value = true
  try {
    pageError.value = ''
    const resp = await getMyNotices({ page: targetPage, size })
    notices.value = reset ? resp.data.items : [...notices.value, ...resp.data.items]
    total.value = resp.data.meta?.total || notices.value.length
    page.value = targetPage
    hasLoaded.value = true
  } catch (error) {
    pageError.value = getErrorMessage(
      error,
      reset ? '通知列表加载失败' : '加载更多通知失败',
    )
    if (!hasLoaded.value && reset) {
      notices.value = []
      total.value = 0
    }
  } finally {
    loading.value = false
  }
}

async function loadSubscribeConfig() {
  try {
    const resp = await getSubscribeConfig()
    subscribeTemplates.value = resp.data.enabled ? resp.data.templates : []
  } catch {
    subscribeTemplates.value = []
  }
}

function normalizeSubscribeResults(
  raw: Record<string, string>,
): WechatSubscribeAuthorizationResult[] {
  const allowed = new Set(['accept', 'reject', 'ban', 'filter'])
  return subscribeTemplates.value
    .map((template) => {
      const status = raw[template.template_id]
      if (!allowed.has(status)) return null
      return {
        template_id: template.template_id,
        status: status as WechatSubscribeAuthorizationResult['status'],
      }
    })
    .filter((item): item is WechatSubscribeAuthorizationResult => !!item)
}

async function onSubscribe() {
  if (subscribeLoading.value || !subscribeTemplates.value.length) return
  subscribeLoading.value = true
  try {
    const tmplIds = subscribeTemplates.value.map((item) => item.template_id)
    const requester = (uni as any).requestSubscribeMessage
      || (globalThis as any).wx?.requestSubscribeMessage
    if (!requester) {
      uni.showToast({ title: '当前环境不支持微信订阅消息', icon: 'none' })
      return
    }
    const result = await new Promise<Record<string, string>>((resolve, reject) => {
      requester({
        tmplIds,
        success: resolve,
        fail: reject,
      })
    })
    const results = normalizeSubscribeResults(result)
    if (!results.length) {
      uni.showToast({ title: '未获得订阅结果', icon: 'none' })
      return
    }
    await saveSubscribeAuthorizations(results)
    const accepted = results.some((item) => item.status === 'accept')
    uni.showToast({ title: accepted ? '订阅已保存' : '订阅结果已记录', icon: 'none' })
  } catch {
    uni.showToast({ title: '订阅失败，请稍后重试', icon: 'none' })
  } finally {
    subscribeLoading.value = false
  }
}

function loadMore() {
  if (loading.value || !hasMore.value) return
  void reload(false, page.value + 1)
}

function onTab(v: NoticeTab) {
  tab.value = v
}

async function onDetail(notice: StudentNoticeItem) {
  try {
    await openNoticeDetail(notice.id, notice.delivery_id)
  } catch {
    uni.showToast({ title: '通知打开失败', icon: 'none' })
  }
}

onShow(() => {
  void reload()
  void loadSubscribeConfig()
})

onPullDownRefresh(async () => {
  try {
    await reload()
  } finally {
    uni.stopPullDownRefresh()
  }
})
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 24rpx 40rpx 42rpx;
  background:
    linear-gradient(0deg, rgba(183, 15, 36, 0.04) 0 2rpx, transparent 2rpx 100%),
    radial-gradient(circle at 50% 100%, rgba(183, 15, 36, 0.1), transparent 260rpx),
    linear-gradient(180deg, #fff 0, #fff 130rpx, #fbf7f7 360rpx, var(--bg-color) 100%),
    var(--bg-color);
}

.tab-row {
  display: flex;
  background: #f5f2f3;
  border-radius: 999rpx;
  padding: 8rpx;
  margin: 0 28rpx 28rpx;
  box-shadow: inset 0 0 0 1rpx rgba(183, 15, 36, 0.04);
}
.tab {
  flex: 1;
  text-align: center;
  padding: 18rpx 0;
  border-radius: 999rpx;
  font-size: 28rpx;
  color: #4b5563;
  font-weight: 600;
}
.tab.active {
  color: #fff;
  background: linear-gradient(135deg, #c8142f, #a20e20);
  font-weight: 800;
  box-shadow: 0 10rpx 22rpx rgba(183, 15, 36, 0.22);
}

.subscribe-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  margin: 0 28rpx 28rpx;
  padding: 24rpx 26rpx;
  border-radius: 18rpx;
  background: #fff;
  border: 1rpx solid #f0e2e5;
  box-shadow: var(--shadow-soft);
}
.subscribe-copy {
  min-width: 0;
  flex: 1;
}
.subscribe-title {
  display: block;
  font-size: 29rpx;
  font-weight: 800;
  color: #202124;
}
.subscribe-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  line-height: 1.45;
  color: #6b7280;
}
.subscribe-button {
  flex-shrink: 0;
  margin: 0;
  padding: 0 28rpx;
  height: 60rpx;
  line-height: 60rpx;
  border-radius: 999rpx;
  font-size: 24rpx;
  color: #fff;
  background: #b70f24;
}
.subscribe-button::after {
  border: 0;
}

.notice-card {
  display: flex;
  gap: 22rpx;
  background: var(--card-elevated);
  padding: 28rpx 26rpx;
  border-radius: 18rpx;
  margin-bottom: 22rpx;
  border: 1rpx solid #f0e2e5;
  box-shadow: var(--shadow-card);
  position: relative;
  overflow: hidden;
}
.notice-card.unread::before {
  content: '';
  position: absolute;
  top: 30rpx;
  right: 28rpx;
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: #ff4d4f;
  box-shadow: 0 0 0 8rpx rgba(255, 77, 79, 0.1);
}
.notice-card.pinned::after {
  content: '';
  position: absolute;
  right: -38rpx;
  top: -38rpx;
  width: 96rpx;
  height: 96rpx;
  background: linear-gradient(135deg, #c8142f, #a20e20);
  transform: rotate(45deg);
}
.notice-icon {
  flex-shrink: 0;
  width: 82rpx;
  height: 82rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #c83045, #a20e20);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 800;
  box-shadow: 0 14rpx 28rpx rgba(200, 48, 69, 0.2);
}
.notice-icon.muted {
  background: linear-gradient(135deg, #d7dbe1, #bcc3cd);
  box-shadow: none;
}
.notice-main { flex: 1; min-width: 0; }
.notice-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18rpx;
}
.notice-title-wrap {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
}
.notice-title {
  font-size: 31rpx;
  line-height: 1.45;
  font-weight: 800;
  color: #202124;
  flex: 1;
}
.notice-source {
  display: inline-block;
  margin-top: 12rpx;
  font-size: 23rpx;
  color: #b70f24;
  background: #fff1f2;
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
}
.pin-corner {
  color: #b70f24;
  background: #fff1f2;
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  flex-shrink: 0;
}
.notice-preview {
  display: block;
  font-size: 26rpx;
  line-height: 1.72;
  color: #5f6368;
  margin-top: 16rpx;
}
.notice-state-flag {
  width: 42rpx;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-shrink: 0;
}
.state-dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: #d4dae2;
}
.state-dot.unread {
  background: #c8142f;
}
.notice-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 18rpx;
}
.notice-date {
  font-size: 22rpx;
  color: #999;
}
.read-mark {
  font-size: 24rpx;
  color: #b8bdc5;
}
.notice-arrow {
  width: 44rpx;
  height: 44rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0a7ae;
}

.load-more {
  width: 300rpx;
  margin: 18rpx auto 0;
  text-align: center;
  padding: 20rpx 0;
  border-radius: 999rpx;
  color: #b70f24;
  background: rgba(255, 255, 255, 0.96);
  font-size: 26rpx;
  font-weight: 700;
  box-shadow: var(--shadow-soft);
}

.load-end {
  margin: 20rpx auto 0;
  text-align: center;
  color: #c1a6ac;
  font-size: 24rpx;
}
</style>
