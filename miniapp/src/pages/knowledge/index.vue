<template>
  <view class="container">
    <view class="search-bar">
      <input
        class="search-input"
        v-model="query"
        placeholder="输入关键字搜索知识库..."
        confirm-type="search"
        @confirm="onSearch"
      />
      <button class="search-btn" @tap="onSearch" size="mini" type="primary">搜索</button>
    </view>

    <view v-if="matchedBy" class="match-hint">
      匹配方式：{{ matchedBy === 'ai' ? 'AI 智能匹配' : '关键词匹配' }}
    </view>

    <view v-if="results.length" class="result-list">
      <view class="result-item" v-for="item in results" :key="item.id" @tap="onDetail(item)">
        <text class="result-title">{{ item.title }}</text>
        <text class="result-category" v-if="item.category">{{ item.category }}</text>
        <text class="result-body">{{ item.body?.slice(0, 100) }}...</text>
        <view class="tag-row" v-if="item.tags?.length">
          <text class="tag" v-for="t in item.tags" :key="t">{{ t }}</text>
        </view>
      </view>
    </view>

    <view v-else-if="searched" class="empty">
      <text>未找到相关知识，请尝试调整关键字</text>
    </view>

    <!-- 详情弹窗 -->
    <uni-popup ref="detailPopup" type="bottom">
      <view class="detail-panel" v-if="selected">
        <text class="detail-title">{{ selected.title }}</text>
        <text class="detail-body">{{ selected.body }}</text>
        <view v-if="selected.source_url" class="detail-source">
          来源：{{ selected.source_url }}
        </view>
      </view>
    </uni-popup>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { searchKnowledge, type KnowledgeEntry } from '@/api/knowledge'

const query = ref('')
const results = ref<KnowledgeEntry[]>([])
const matchedBy = ref('')
const searched = ref(false)
const selected = ref<KnowledgeEntry | null>(null)

async function onSearch() {
  if (!query.value.trim()) return
  searched.value = true
  try {
    const resp = await searchKnowledge(query.value)
    results.value = resp.data.entries
    matchedBy.value = resp.data.matched_by
  } catch {
    results.value = []
  }
}

function onDetail(item: KnowledgeEntry) {
  selected.value = item
}
</script>

<style scoped>
.container { padding: 24rpx; }
.search-bar { display: flex; gap: 16rpx; margin-bottom: 24rpx; }
.search-input {
  flex: 1;
  height: 72rpx;
  border: 1rpx solid #ddd;
  border-radius: 8rpx;
  padding: 0 20rpx;
  font-size: 28rpx;
}
.search-btn { flex-shrink: 0; }
.match-hint { font-size: 24rpx; color: #7f1722; margin-bottom: 16rpx; }

.result-list { margin-top: 8rpx; }
.result-item {
  background: #fff;
  padding: 24rpx;
  border-radius: 12rpx;
  margin-bottom: 16rpx;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06);
}
.result-title { font-size: 30rpx; font-weight: 600; color: #333; display: block; }
.result-category { font-size: 24rpx; color: #7f1722; display: block; margin-top: 4rpx; }
.result-body { font-size: 26rpx; color: #666; display: block; margin-top: 8rpx; }
.tag-row { display: flex; flex-wrap: wrap; gap: 8rpx; margin-top: 12rpx; }
.tag {
  font-size: 22rpx;
  background: #f0f0f0;
  padding: 4rpx 12rpx;
  border-radius: 4rpx;
  color: #555;
}

.empty { text-align: center; padding: 80rpx 0; color: #999; font-size: 28rpx; }

.detail-panel {
  background: #fff;
  padding: 32rpx;
  border-radius: 24rpx 24rpx 0 0;
  max-height: 70vh;
  overflow-y: auto;
}
.detail-title { font-size: 34rpx; font-weight: 600; display: block; margin-bottom: 16rpx; }
.detail-body { font-size: 28rpx; color: #333; line-height: 1.7; display: block; }
.detail-source { font-size: 24rpx; color: #7f1722; margin-top: 16rpx; }
</style>
