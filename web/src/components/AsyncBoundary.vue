<template>
  <!-- 错误态优先：加载失败时给出统一的错误结果 + 可选重试 -->
  <a-result
    v-if="showError"
    status="error"
    :title="errorTitle"
    :sub-title="errorText"
    class="async-boundary__result"
  >
    <template v-if="retry" #extra>
      <a-button type="primary" @click="retry">重试</a-button>
    </template>
  </a-result>

  <!-- 首屏骨架：仅在「加载中且尚无数据」时替代空白闪烁 -->
  <a-skeleton
    v-else-if="showSkeleton"
    active
    :paragraph="{ rows: skeletonRows }"
  />

  <!-- 常态：刷新时用 spin 覆盖既有内容；无数据时统一空态 -->
  <a-spin v-else :spinning="loading">
    <a-empty v-if="showEmpty" :description="emptyText" />
    <slot v-else />
  </a-spin>
</template>

<script setup lang="ts">
/**
 * 统一的异步内容容器：标准化「加载 / 骨架 / 空态 / 错误态」。
 *
 * 适用于详情页、卡片、自定义列表等非 a-table 内容区
 * （a-table 自带 loading 与空态，无需本组件）。
 *
 * 用法：
 *   <AsyncBoundary
 *     :loading="loading"
 *     :error="error"
 *     :empty="!loading && !error && items.length === 0"
 *     :retry="reload"
 *     skeleton
 *   >
 *     <!-- 正常内容 -->
 *   </AsyncBoundary>
 */
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    /** 是否加载中 */
    loading?: boolean
    /** 错误对象 / 文案；真值即进入错误态 */
    error?: unknown
    /** 是否无数据 */
    empty?: boolean
    /** 空态描述 */
    emptyText?: string
    /** 错误态标题 */
    errorTitle?: string
    /** 首屏是否用骨架屏（仅在加载中且 empty 时生效） */
    skeleton?: boolean
    /** 骨架段落行数 */
    skeletonRows?: number
    /** 提供时错误态显示「重试」按钮并调用之 */
    retry?: () => void
  }>(),
  {
    loading: false,
    empty: false,
    emptyText: '暂无数据',
    errorTitle: '加载失败',
    skeleton: false,
    skeletonRows: 4,
  },
)

const hasError = computed(() => Boolean(props.error))
const errorText = computed(() => {
  const e = props.error as { message?: unknown } | string | null | undefined
  if (!e) return '请稍后重试'
  if (typeof e === 'string') return e
  if (e.message) return String(e.message)
  return '请稍后重试'
})
const showError = computed(() => !props.loading && hasError.value)
const showSkeleton = computed(() => props.loading && props.skeleton && props.empty)
const showEmpty = computed(() => !props.loading && !hasError.value && props.empty)
</script>
