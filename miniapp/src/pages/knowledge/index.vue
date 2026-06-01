<template>
  <view class="container">
    <view class="search-panel">
      <view class="search-bar">
        <text class="search-icon">查</text>
        <input
          class="search-input"
          v-model="query"
          placeholder="请输入关键词/政策/制度名称"
          confirm-type="search"
          @confirm="onSearch"
        />
        <button class="search-btn" hover-class="hover-opacity" @tap="onSearch" size="mini" :type="UNI_BUTTON_TYPE.primary">
          <text class="btn-icon">搜</text> 搜索
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
          {{ matchedBy === 'retrieval' ? '检索排序' : '标题匹配' }}
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
        <text class="btn-icon">检</text>{{ aiLoading ? '检索中' : '检索匹配' }}
      </button>
    </view>

    <view class="template-panel">
      <view class="template-head">
        <view>
          <text class="template-panel-title">常用模板</text>
          <text class="template-panel-desc">直接下载已发布模板，并核对来源信息。</text>
        </view>
        <text class="template-note">{{ templateLoading ? '同步中' : '官方发布' }}</text>
      </view>

      <InlineStateNotice
        v-if="templateError && !templateItems.length"
        compact
        :tone="'warning'"
        title="模板列表未完全更新"
        :description="templateError"
        action-text="重试"
        @action="loadTemplates"
      />

      <view v-if="templateItems.length" class="template-list">
        <view
          v-for="tpl in templateItems"
          :key="tpl.id"
          class="template-item"
        >
          <view class="template-main">
            <text class="template-name">{{ tpl.template_name }}</text>
            <text class="template-meta">
              {{ [tpl.template_type, tpl.version_label, tpl.category_code].filter(Boolean).join(' · ') || '官方模板' }}
            </text>
            <text v-if="tpl.applicable_scenario" class="template-meta">{{ tpl.applicable_scenario }}</text>
          </view>
          <view class="template-side">
            <text class="template-side-note">{{ formatTemplateDate(tpl.uploaded_at) }}</text>
            <button
              class="template-download-btn"
              size="mini"
              :type="UNI_BUTTON_TYPE.primary"
              :loading="downloadingTemplateId === tpl.id"
              @tap="openTemplate(tpl.id, tpl.template_type)"
            >下载</button>
          </view>
        </view>
      </view>
      <view v-else-if="templateLoaded && !templateError && !templateLoading" class="template-empty">
        暂无可下载模板
      </view>
    </view>

    <view v-if="aiResult" class="ai-panel">
      <view class="ai-panel-head">
        <text class="ai-title">检索匹配</text>
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
        <view v-if="candidate.summary" class="ai-item-summary">{{ candidate.summary }}</view>
        <view v-if="candidate.source_name || candidate.source_url" class="source-row">
          <text class="source-label">{{ candidate.source_is_official ? '官方来源' : '来源' }}</text>
          <text class="source-name">{{ candidate.source_name || '已发布来源' }}</text>
          <text
            v-if="candidate.source_url"
            class="source-link"
            hover-class="hover-opacity"
            @tap.stop="copyUrl(candidate.source_url, '来源链接已复制')"
          >
            复制链接
          </text>
        </view>
      </view>
      <view v-if="aiResult.manual_consult_required" class="consult-card">
        {{ aiResult.manual_consult_hint || '该问题存在特殊情形，建议转人工咨询。' }}
      </view>
      <view class="ai-disclaimer">{{ aiResult.disclaimer }}</view>
    </view>

    <InlineStateNotice
      v-if="searchError"
      compact
      tone="error"
      title="知识搜索失败"
      :description="searchError"
      action-text="重试"
      @action="onSearch"
    />

    <view v-if="results.length" class="result-list">
      <view class="result-item" v-for="item in results" :key="item.id" @tap="onDetail(item)">
          <view class="result-icon">{{ resultIcon(item.category_code) }}</view>
        <view class="result-main">
          <view class="result-head">
            <text class="result-title">{{ item.title }}</text>
            <view class="result-arrow"><view class="mini-chevron" /></view>
          </view>
          <view class="result-meta" v-if="item.category_code || item.version_label">
            <text class="meta-school">校</text>
            <text class="result-category">
              {{ [item.category_code, item.version_label].filter(Boolean).join(' · ') }}
            </text>
          </view>
          <text class="result-body">{{ item.summary || '点击查看适用条件、办理步骤与正文详情' }}</text>
          <view v-if="item.source_name || item.source_url" class="source-row result-source-row">
            <text class="source-label">{{ item.source_is_official ? '官方来源' : '来源' }}</text>
            <text class="source-name">{{ item.source_name || '已发布来源' }}</text>
            <text
              v-if="item.source_url"
              class="source-link"
              hover-class="hover-opacity"
              @tap.stop="copyUrl(item.source_url, '来源链接已复制')"
            >
              复制链接
            </text>
          </view>
          <view class="tag-row" v-if="item.tags?.length">
            <text class="tag" v-for="t in item.tags" :key="t" @tap.stop="selectTag(t)">{{ t }}</text>
          </view>
        </view>
      </view>
    </view>

    <view v-else-if="searched && !searchError" class="empty">
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
        <view v-if="selected.source" class="detail-section source-section">
          <text class="detail-section-title">{{ selected.source.is_official ? '官方来源' : '来源' }}</text>
          <text class="source-main">{{ selected.source.source_name }}</text>
          <text v-if="selected.source.issuing_org" class="source-meta">发布机构：{{ selected.source.issuing_org }}</text>
          <text v-if="selected.source.version_label" class="source-meta">版本：{{ selected.source.version_label }}</text>
          <text
            v-if="selected.source.source_url"
            class="source-url"
            hover-class="hover-opacity"
            @tap="copyUrl(selected.source.source_url, '原文链接已复制')"
          >
            {{ selected.source.source_url }}
          </text>
          <text v-if="selected.source.source_url" class="source-tip">点击复制官方原文链接</text>
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
              @tap="openTemplate(tpl.template_id, tpl.template_type)"
            >打开</button>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import InlineStateNotice from '@/components/InlineStateNotice.vue'
import {
  aiMatchKnowledge,
  downloadTemplateFromUrl,
  downloadTemplateFile,
  getEntryDetail,
  getTemplateDownloadLink,
  listKnowledgeCategories,
  listStudentTemplates,
  searchKnowledge,
  type AiMatchResult,
  type KnowledgeCategory,
  type KnowledgeEntry,
  type KnowledgeEntryDetail,
  type KnowledgeTemplateItem,
} from '@/api/knowledge'
import { UNI_BUTTON_TYPE } from '@/utils/uni-button'
import { getErrorMessage } from '@/utils/error'
import { formatShanghaiDateTime } from '@/utils/datetime'

const query = ref('')
const categories = ref<KnowledgeCategory[]>([])
const templateItems = ref<KnowledgeTemplateItem[]>([])
const selectedCategory = ref<string | null>(null)
const selectedTag = ref<string | null>(null)
const results = ref<KnowledgeEntry[]>([])
const matchedBy = ref('')
const searched = ref(false)
const searchError = ref('')
const selected = ref<KnowledgeEntryDetail | null>(null)
const aiResult = ref<AiMatchResult | null>(null)
const aiLoading = ref(false)
const templateLoading = ref(false)
const templateError = ref('')
const templateLoaded = ref(false)
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
  const keyword = query.value.trim()
  searched.value = true
  searchError.value = ''
  aiResult.value = null
  try {
    const resp = await searchKnowledge({
      q: keyword || undefined,
      category: selectedCategory.value,
      tag: selectedTag.value,
      page: 1,
      size: 20,
    })
    results.value = resp.data.items
    matchedBy.value = resp.data.meta.total > 0 ? 'keyword' : ''
  } catch (error) {
    results.value = []
    matchedBy.value = ''
    searchError.value = getErrorMessage(error, '知识搜索暂不可用')
  }
}

async function onAiMatch() {
  if (aiLoading.value) return
  if (!query.value.trim()) {
    uni.showToast({ title: '请先输入检索问题', icon: 'none' })
    return
  }
  aiLoading.value = true
  try {
    const resp = await aiMatchKnowledge(query.value, 3)
    aiResult.value = resp.data
    matchedBy.value = 'retrieval'
  } catch {
    aiResult.value = null
    uni.showToast({ title: '检索匹配暂不可用', icon: 'none' })
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
    uni.showToast({ title: '知识详情打开失败', icon: 'none' })
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

async function loadTemplates() {
  templateLoading.value = true
  try {
    templateError.value = ''
    const resp = await listStudentTemplates({ page: 1, size: 8 })
    templateItems.value = resp.data.items || []
    templateLoaded.value = true
  } catch (error) {
    templateError.value = error instanceof Error ? error.message : '模板列表加载失败'
    if (!templateLoaded.value) {
      templateItems.value = []
    }
  } finally {
    templateLoading.value = false
  }
}

function templateFileType(templateType?: string | null) {
  const normalized = (templateType || '').trim().toLowerCase()
  return ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'pdf'].includes(normalized) ? normalized : undefined
}

async function openTemplate(templateId: number, templateType?: string | null) {
  if (downloadingTemplateId.value) return
  downloadingTemplateId.value = templateId
  try {
    const { tempFilePath } = await downloadTemplateWithFallback(templateId)
    openDownloadedTemplate(tempFilePath, templateType)
  } catch {
    downloadingTemplateId.value = null
    uni.showToast({ title: '模板下载失败', icon: 'none' })
  }
}

async function downloadTemplateWithFallback(templateId: number) {
  try {
    return await downloadTemplateFile(templateId)
  } catch {
    const resp = await getTemplateDownloadLink(templateId)
    return downloadTemplateFromUrl(resp.data.download_url)
  }
}

function openDownloadedTemplate(tempFilePath: string, templateType?: string | null) {
  uni.openDocument({
    filePath: tempFilePath,
    fileType: templateFileType(templateType),
    showMenu: true,
    success() {
      downloadingTemplateId.value = null
    },
    fail() {
      downloadingTemplateId.value = null
      uni.showToast({ title: '模板已下载，当前设备暂无法打开', icon: 'none' })
    },
  })
}

function copyUrl(url: string, title = '链接已复制') {
  uni.setClipboardData({
    data: url,
    success() {
      uni.showToast({ title, icon: 'none' })
    },
  })
}

function formatTemplateDate(value?: string | null) {
  return formatShanghaiDateTime(value)
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
    const [categoriesResp] = await Promise.all([
      listKnowledgeCategories(),
      loadTemplates(),
    ])
    categories.value = categoriesResp.data.filter((item) => item.is_active)
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
  left: 24rpx;
  top: 24rpx;
  width: 44rpx;
  height: 44rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  font-weight: 900;
  background: rgba(148, 163, 184, 0.14);
  border: 1rpx solid rgba(148, 163, 184, 0.26);
  color: rgba(71, 85, 105, 0.9);
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
  width: 36rpx;
  height: 36rpx;
  margin-right: 10rpx;
  border-radius: 14rpx;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
  font-weight: 900;
  background: rgba(183, 15, 36, 0.08);
  border: 1rpx solid rgba(183, 15, 36, 0.18);
}

.search-btn .btn-icon {
  background: rgba(255, 255, 255, 0.18);
  border-color: rgba(255, 255, 255, 0.28);
}

.ai-btn .btn-icon {
  background: rgba(183, 15, 36, 0.08);
  border-color: rgba(183, 15, 36, 0.18);
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

.template-panel {
  margin-top: 22rpx;
  padding: 24rpx;
  border-radius: 24rpx;
  background: #fff;
  border: 1rpx solid #f0e2e5;
  box-shadow: var(--shadow-soft);
}

.template-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16rpx;
}

.template-panel-title {
  display: block;
  font-size: 30rpx;
  font-weight: 900;
  color: #202124;
}

.template-panel-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 23rpx;
  line-height: 1.6;
  color: #6b6365;
}

.template-note {
  flex-shrink: 0;
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  background: #fff1f2;
  color: #b70f24;
  font-size: 22rpx;
}

.template-list {
  margin-top: 18rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.template-item {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 18rpx 0;
  border-top: 1rpx solid #f3e8eb;
}

.template-item:first-child {
  border-top: none;
  padding-top: 0;
}

.template-name {
  display: block;
  font-size: 27rpx;
  font-weight: 800;
  color: #202124;
}

.template-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10rpx;
}

.template-side-note {
  font-size: 20rpx;
  color: #8a8f98;
}

.template-download-btn {
  width: 112rpx;
  height: 62rpx;
  border-radius: 16rpx;
  padding: 0;
  font-size: 24rpx;
}

.template-empty {
  margin-top: 18rpx;
  padding: 24rpx 18rpx;
  border-radius: 20rpx;
  background: #f8fafc;
  color: #6b7280;
  font-size: 24rpx;
  text-align: center;
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
.ai-item-summary {
  margin-top: 10rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: #47383d;
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

.source-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 12rpx;
}

.result-source-row {
  margin-top: 12rpx;
}

.source-label {
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  background: #fff1f2;
  color: #b70f24;
  font-size: 20rpx;
  font-weight: 700;
}

.source-name {
  font-size: 22rpx;
  color: #6b6365;
  line-height: 1.5;
}

.source-link {
  font-size: 22rpx;
  color: #b70f24;
  font-weight: 700;
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
.result-arrow {
  width: 44rpx;
  height: 44rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #a6a6a6;
}
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

.meta-school {
  width: 36rpx;
  height: 36rpx;
  border-radius: 14rpx;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
  font-weight: 900;
  background: rgba(183, 15, 36, 0.08);
  border: 1rpx solid rgba(183, 15, 36, 0.16);
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
.source-section {
  margin-top: 18rpx;
}

.source-main {
  display: block;
  font-size: 28rpx;
  font-weight: 800;
  color: #1f2937;
}

.source-meta {
  display: block;
  margin-top: 8rpx;
  font-size: 23rpx;
  color: #6b7280;
  line-height: 1.6;
}

.source-url {
  display: block;
  margin-top: 12rpx;
  color: #b70f24;
  font-size: 23rpx;
  line-height: 1.6;
  word-break: break-all;
}

.source-tip {
  display: block;
  margin-top: 6rpx;
  font-size: 21rpx;
  color: #8a8f98;
}

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
