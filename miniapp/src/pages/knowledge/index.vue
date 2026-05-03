<template>
  <view class="container">
    <view class="search-panel">
      <view class="search-bar">
        <text class="search-icon">⌕</text>
        <input
          class="search-input"
          v-model="query"
          placeholder="请输入关键词/政策/制度名称"
          confirm-type="search"
          @confirm="onSearch"
        />
        <button class="search-btn" hover-class="hover-opacity" @tap="onSearch" size="mini" :type="UNI_BUTTON_TYPE.primary">
          <text class="btn-icon">🔍</text> 搜索
        </button>
      </view>

      <scroll-view v-if="categories.length" scroll-x class="category-scroll">
        <view class="category-row">
          <text
            class="filter-chip"
            :class="{ active: !selectedCategory }"
            @tap="selectCategory(null)"
          >全部</text>
          <text
            v-for="category in categories"
            :key="category.code"
            class="filter-chip"
            :class="{ active: selectedCategory === category.code }"
            @tap="selectCategory(category.code)"
          >{{ category.name }}</text>
        </view>
      </scroll-view>

      <view class="match-hint">
        <text class="hint-label">匹配方式提示：</text>
        <text class="hint-chip" :class="{ active: matchedBy }">
          {{ matchedBy === 'ai' ? '智能匹配' : '标题匹配' }}
        </text>
        <text class="hint-chip">全文匹配</text>
        <text class="hint-chip">标签匹配</text>
        <text v-if="selectedTag" class="hint-chip active" @tap="selectTag(null)">
          #{{ selectedTag }} ×
        </text>
      </view>

      <button
        class="ai-btn"
        hover-class="hover-opacity"
        size="mini"
        :disabled="aiLoading"
        @tap="onAiMatch"
      >
        <text class="btn-icon">✨</text>{{ aiLoading ? '匹配中' : '智能匹配' }}
      </button>
    </view>

    <view v-if="aiResult" class="ai-panel">
      <view class="ai-panel-head">
        <text class="ai-title">智能匹配</text>
        <text class="ai-engine">{{ aiResult.engine }}</text>
      </view>
      <view
        v-for="candidate in aiResult.candidates"
        :key="candidate.entry_id"
        class="ai-item"
        @tap="onDetailById(candidate.entry_id)"
      >
        <view class="ai-item-title">{{ candidate.title }}</view>
        <view class="ai-item-reason">
          {{ candidate.reason || '基于已发布知识条目匹配' }} · {{ Math.round(candidate.score * 100) }}%
        </view>
      </view>
      <view v-if="aiResult.manual_consult_required" class="consult-card">
        {{ aiResult.manual_consult_hint || '该问题存在特殊情形，建议转人工咨询。' }}
      </view>
      <view class="ai-disclaimer">{{ aiResult.disclaimer }}</view>
    </view>

    <view v-if="results.length" class="result-list">
      <view class="result-item" v-for="item in results" :key="item.id" @tap="onDetail(item)">
          <view class="result-icon">{{ resultIcon(item.category_code) }}</view>
        <view class="result-main">
          <view class="result-head">
            <text class="result-title">{{ item.title }}</text>
            <text class="result-arrow">›</text>
          </view>
          <view class="result-meta" v-if="item.category_code || item.version_label">
            <text class="meta-school">🏛</text>
            <text class="result-category">
              {{ [item.category_code, item.version_label].filter(Boolean).join(' · ') }}
            </text>
          </view>
          <text class="result-body">{{ item.summary || '点击查看适用条件、办理步骤与正文详情' }}</text>
          <view class="tag-row" v-if="item.tags?.length">
            <text class="tag" v-for="t in item.tags" :key="t" @tap.stop="selectTag(t)">{{ t }}</text>
          </view>
        </view>
      </view>
    </view>

    <view v-else-if="searched" class="empty">
      <text>未找到相关知识，请尝试调整关键字</text>
    </view>

    <!-- 详情弹窗 -->
    <view v-if="selected" class="sheet-mask" @tap="closeDetail">
      <view class="detail-panel" @tap.stop>
        <view class="sheet-handle" />
        <view class="detail-sheet-head">
          <text class="detail-sheet-label">知识详情</text>
          <view class="detail-sheet-close" @tap="closeDetail">×</view>
        </view>
        <view class="detail-head">
          <view class="detail-icon">{{ resultIcon(selected.category_code) }}</view>
          <view class="detail-head-main">
        <text class="detail-title">{{ selected.title }}</text>
        <view class="detail-meta-row">
          <text class="detail-tag" v-if="selected.category_code">{{ selected.category_code }}</text>
          <text class="detail-date">{{ selected.version_label || '知识库条目' }}</text>
        </view>
          </view>
        </view>
        <view class="detail-section">
          <text class="detail-section-title">正文内容</text>
          <text class="detail-body">{{ detailBody }}</text>
        </view>
        <view v-if="selected.tags?.length" class="tag-row detail-tags">
          <text class="tag" v-for="t in selected.tags" :key="t" @tap="selectTag(t)">{{ t }}</text>
        </view>
        <view v-if="selected.ambiguity_flag || selected.manual_consult_hint" class="consult-card detail-consult">
          {{ selected.manual_consult_hint || '该条目存在适用条件或特殊情形，建议转人工咨询确认。' }}
        </view>
        <view v-if="selected.templates?.length" class="template-section">
          <text class="detail-section-title">相关模板</text>
          <view
            v-for="tpl in selected.templates"
            :key="tpl.template_id"
            class="template-row"
          >
            <view class="template-main">
              <text class="template-title">{{ tpl.template_name }}</text>
              <text class="template-meta">{{ [tpl.template_type, tpl.version_label].filter(Boolean).join(' · ') }}</text>
            </view>
            <button
              class="template-btn"
              size="mini"
              :type="UNI_BUTTON_TYPE.primary"
              :loading="downloadingTemplateId === tpl.template_id"
              @tap="openTemplate(tpl.template_id)"
            >打开</button>
          </view>
        </view>
        <view v-if="selected.source" class="detail-source">
          来源：{{ selected.source.source_name }}
        </view>
        <view class="detail-action" @tap="openSource">查看原文</view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  aiMatchKnowledge,
  getEntryDetail,
  getTemplateDownloadLink,
  listKnowledgeCategories,
  searchKnowledge,
  type AiMatchResult,
  type KnowledgeCategory,
  type KnowledgeEntry,
  type KnowledgeEntryDetail,
} from '@/api/knowledge'
import { UNI_BUTTON_TYPE } from '@/utils/uni-button'

const query = ref('')
const categories = ref<KnowledgeCategory[]>([])
const selectedCategory = ref<string | null>(null)
const selectedTag = ref<string | null>(null)
const results = ref<KnowledgeEntry[]>([])
const matchedBy = ref('')
const searched = ref(false)
const selected = ref<KnowledgeEntryDetail | null>(null)
const aiResult = ref<AiMatchResult | null>(null)
const aiLoading = ref(false)
const downloadingTemplateId = ref<number | null>(null)
const detailBody = computed(() => {
  if (!selected.value) return ''
  return [
    selected.value.applicable_condition ? `适用条件：${selected.value.applicable_condition}` : '',
    selected.value.required_materials ? `所需材料：${selected.value.required_materials}` : '',
    selected.value.process_steps ? `办理步骤：${selected.value.process_steps}` : '',
    selected.value.body_md || selected.value.summary || '',
    selected.value.manual_consult_hint ? `人工咨询提示：${selected.value.manual_consult_hint}` : '',
  ].filter(Boolean).join('\n\n')
})

async function onSearch() {
  if (!query.value.trim()) return
  searched.value = true
  aiResult.value = null
  try {
    const resp = await searchKnowledge({
      q: query.value,
      category: selectedCategory.value,
      tag: selectedTag.value,
      page: 1,
      size: 20,
    })
    results.value = resp.data.items
    matchedBy.value = resp.data.meta.total > 0 ? 'keyword' : ''
  } catch {
    results.value = []
  }
}

async function onAiMatch() {
  if (!query.value.trim() || aiLoading.value) return
  aiLoading.value = true
  try {
    const resp = await aiMatchKnowledge(query.value, 3)
    aiResult.value = resp.data
    matchedBy.value = 'ai'
  } catch {
    aiResult.value = null
    uni.showToast({ title: '智能匹配暂不可用', icon: 'none' })
  } finally {
    aiLoading.value = false
  }
}

async function onDetail(item: KnowledgeEntry) {
  await onDetailById(item.id)
}

async function onDetailById(id: number) {
  try {
    const resp = await getEntryDetail(id)
    selected.value = resp.data
  } catch {
    selected.value = null
  }
}

function closeDetail() {
  selected.value = null
}

async function selectCategory(code: string | null) {
  selectedCategory.value = code
  await onSearch()
}

async function selectTag(tag: string | null) {
  selectedTag.value = tag
  if (tag) closeDetail()
  await onSearch()
}

async function openTemplate(templateId: number) {
  if (downloadingTemplateId.value) return
  downloadingTemplateId.value = templateId
  try {
    const resp = await getTemplateDownloadLink(templateId)
    uni.downloadFile({
      url: resp.data.download_url,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          uni.openDocument({
            filePath: res.tempFilePath,
            showMenu: true,
            fail() {
              uni.showToast({ title: '模板已下载，暂无法打开', icon: 'none' })
            },
          })
        } else {
          uni.showToast({ title: '模板下载失败', icon: 'none' })
        }
      },
      fail() {
        uni.showToast({ title: '模板下载失败', icon: 'none' })
      },
      complete() {
        downloadingTemplateId.value = null
      },
    })
  } catch {
    downloadingTemplateId.value = null
    uni.showToast({ title: '模板下载链接生成失败', icon: 'none' })
  }
}

function openSource() {
  if (!selected.value?.source?.source_url) {
    uni.showToast({ title: '暂无原文链接', icon: 'none' })
    return
  }
  uni.setClipboardData({
    data: selected.value.source.source_url,
    success() {
      uni.showToast({ title: '原文链接已复制', icon: 'none' })
    },
  })
}

function resultIcon(category?: string | null) {
  if (!category) return '册'
  if (category.includes('奖')) return '奖'
  if (category.includes('卡')) return '卡'
  if (category.includes('教')) return '教'
  return '规'
}

onMounted(async () => {
  try {
    const resp = await listKnowledgeCategories()
    categories.value = resp.data.filter((item) => item.is_active)
  } catch {
    categories.value = []
  }
})
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 36rpx 36rpx 36rpx;
  background:
    radial-gradient(circle at 100% 8%, rgba(183, 15, 36, 0.08), transparent 180rpx),
    linear-gradient(180deg, #fff 0, #fff6f7 220rpx, #f7f1f2 100%),
    #f7f1f2;
}

.search-panel {
  position: relative;
  z-index: 2;
  padding: 0;
  border-radius: 0;
  background: transparent;
  border: none;
  box-shadow: none;
}
.search-bar {
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.search-icon {
  position: absolute;
  z-index: 1;
  margin-left: 24rpx;
  font-size: 36rpx;
  color: #9aa0a6;
}
.search-input {
  flex: 1;
  height: 92rpx;
  border: 1rpx solid #eadde0;
  border-radius: 999rpx;
  padding: 0 28rpx 0 76rpx;
  font-size: 28rpx;
  background: #fff;
}
.btn-icon {
  margin-right: 6rpx;
  font-size: 26rpx;
  vertical-align: middle;
}

.search-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 140rpx;
  height: 92rpx;
  border-radius: 18rpx;
  background: linear-gradient(135deg, #b70f24, #8b1020);
  color: #fff;
  font-size: 28rpx;
  font-weight: 700;
  padding: 0;
}
.match-hint {
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex-wrap: wrap;
  margin-top: 22rpx;
  font-size: 24rpx;
}
.category-scroll {
  width: 100%;
  margin-top: 20rpx;
  white-space: nowrap;
}
.category-row {
  display: inline-flex;
  gap: 12rpx;
}
.filter-chip {
  display: inline-flex;
  align-items: center;
  height: 54rpx;
  padding: 0 24rpx;
  border-radius: 999rpx;
  background: #fff;
  border: 1rpx solid #eadde0;
  color: #6b6365;
  font-size: 24rpx;
}
.filter-chip.active {
  background: #b70f24;
  color: #fff;
  border-color: #b70f24;
}
.hint-label {
  color: #8a6b45;
}
.hint-chip {
  padding: 8rpx 20rpx;
  border-radius: 999rpx;
  color: #b70f24;
  background: rgba(255, 241, 242, 0.9);
}
.hint-chip.active {
  background: #b70f24;
  color: #fff;
}
.ai-btn {
  margin-top: 18rpx;
  height: 70rpx;
  border-radius: 18rpx;
  background: #fff;
  color: #b70f24;
  border: 1rpx solid #f0d8dd;
  font-size: 26rpx;
  font-weight: 700;
}
.ai-panel {
  margin-top: 22rpx;
  padding: 24rpx;
  border-radius: 24rpx;
  background: #fff;
  border: 1rpx solid #f0e2e5;
  box-shadow: var(--shadow-soft);
}
.ai-panel-head,
.ai-item {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
}
.ai-title {
  font-size: 30rpx;
  font-weight: 900;
  color: #202124;
}
.ai-engine,
.ai-disclaimer {
  font-size: 22rpx;
  color: #8a8f98;
}
.ai-item {
  display: block;
  margin-top: 18rpx;
  padding: 18rpx;
  border-radius: 18rpx;
  background: #fff8f9;
}
.ai-item-title {
  font-size: 27rpx;
  font-weight: 800;
  color: #1f2937;
}
.ai-item-reason {
  margin-top: 6rpx;
  font-size: 23rpx;
  color: #6b6365;
}
.consult-card {
  margin-top: 16rpx;
  padding: 18rpx 20rpx;
  border-radius: 18rpx;
  background: #fff7e6;
  color: #8a5b00;
  font-size: 24rpx;
  line-height: 1.6;
}
.detail-consult {
  margin-top: 22rpx;
}

.result-list { margin-top: 24rpx; }
.result-item {
  position: relative;
  display: flex;
  gap: 20rpx;
  background: #fff;
  padding: 32rpx 26rpx;
  border-radius: 24rpx;
  margin-bottom: 20rpx;
  border: 1rpx solid #f0e2e5;
  box-shadow: var(--shadow-card);
  overflow: hidden;
}
.result-icon {
  width: 86rpx;
  height: 86rpx;
  border-radius: 50%;
  background: #fff1f2;
  color: #b70f24;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 800;
}
.result-main { flex: 1; min-width: 0; }
.result-head {
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
}
.result-title {
  flex: 1;
  font-size: 32rpx;
  line-height: 1.45;
  font-weight: 800;
  color: #202124;
  display: block;
}
.result-arrow { color: #a6a6a6; font-size: 34rpx; }
.result-meta {
  display: flex;
  align-items: center;
  gap: 10rpx;
  margin-top: 8rpx;
}
.meta-school,
.result-category {
  font-size: 23rpx;
  color: #b70f24;
}
.result-body {
  font-size: 25rpx;
  color: #5f6368;
  display: block;
  margin-top: 10rpx;
  line-height: 1.7;
}
.tag-row { display: flex; flex-wrap: wrap; gap: 8rpx; margin-top: 12rpx; }
.tag {
  font-size: 22rpx;
  background: #fff1f2;
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
  color: #b70f24;
}

.empty {
  margin-top: 28rpx;
  padding: 76rpx 28rpx;
  border-radius: 26rpx;
  background: #fff;
  text-align: center;
  color: #999;
  font-size: 28rpx;
  box-shadow: var(--shadow-soft);
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
  background: #fff;
  padding: 18rpx 32rpx calc(34rpx + env(safe-area-inset-bottom));
  border-radius: 34rpx 34rpx 0 0;
  max-height: 78vh;
  overflow-y: auto;
  box-shadow: 0 -14rpx 40rpx rgba(82,28,38,0.12);
}
.sheet-handle {
  width: 72rpx;
  height: 8rpx;
  border-radius: 999rpx;
  background: #d9d9d9;
  margin: 0 auto 24rpx;
}
.detail-sheet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18rpx;
}
.detail-sheet-label {
  font-size: 32rpx;
  font-weight: 900;
  color: #1f2937;
}
.detail-sheet-close {
  width: 58rpx;
  height: 58rpx;
  border-radius: 50%;
  background: #f8f3f4;
  color: #6b6365;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
  line-height: 1;
}
.detail-head {
  display: flex;
  align-items: flex-start;
  gap: 18rpx;
}
.detail-icon {
  width: 82rpx;
  height: 82rpx;
  border-radius: 50%;
  background: #fff1f2;
  color: #b70f24;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 900;
  flex-shrink: 0;
}
.detail-head-main { flex: 1; min-width: 0; }
.detail-title { font-size: 34rpx; line-height: 1.45; font-weight: 900; display: block; margin-bottom: 16rpx; }
.detail-meta-row {
  display: flex;
  gap: 16rpx;
  align-items: center;
  margin-bottom: 22rpx;
}
.detail-tag {
  padding: 6rpx 18rpx;
  border-radius: 999rpx;
  color: #b70f24;
  background: #fff1f2;
  font-size: 23rpx;
}
.detail-date { color: #8a8f98; font-size: 23rpx; }
.detail-section {
  margin-top: 8rpx;
  padding: 22rpx;
  border-radius: 22rpx;
  background: #fff8f9;
}
.detail-section-title {
  display: block;
  color: #b70f24;
  font-size: 28rpx;
  font-weight: 800;
  margin-bottom: 14rpx;
}
.detail-body { font-size: 28rpx; color: #333; line-height: 1.8; display: block; white-space: pre-wrap; }
.detail-tags { margin-top: 22rpx; }
.detail-source { font-size: 24rpx; color: #7f1722; margin-top: 16rpx; }
.template-section {
  margin-top: 22rpx;
  padding: 22rpx;
  border-radius: 22rpx;
  background: #f8fafc;
}
.template-row {
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding: 18rpx 0;
  border-top: 1rpx solid #edf0f3;
}
.template-row:first-of-type {
  border-top: none;
}
.template-main {
  flex: 1;
  min-width: 0;
}
.template-title {
  display: block;
  font-size: 27rpx;
  font-weight: 800;
  color: #202124;
}
.template-meta {
  display: block;
  margin-top: 6rpx;
  font-size: 22rpx;
  color: #8a8f98;
}
.template-btn {
  width: 112rpx;
  height: 62rpx;
  border-radius: 16rpx;
  font-size: 24rpx;
  padding: 0;
}
.detail-action {
  margin-top: 26rpx;
  height: 86rpx;
  border-radius: 22rpx;
  background: linear-gradient(135deg, #b70f24, #8b1020);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 700;
}
</style>
