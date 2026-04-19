<template>
  <view class="container">
    <view class="weak-hint">
      {{ result?.disclaimer || defaultDisclaimer }}
    </view>

    <view v-if="loading" class="loading">加载中...</view>

    <template v-else-if="result">
      <view class="summary-card">
        <text class="plan-name">{{ result.plan_name || `${result.student_name} 的学业缺口` }}</text>
        <view class="credit-row">
          <view class="credit-col">
            <text class="num">{{ formatCredits(result.total_credits_earned) }}</text>
            <text class="lbl">已获学分</text>
          </view>
          <view class="credit-col">
            <text class="num">{{ formatCredits(result.total_credits_required) }}</text>
            <text class="lbl">参考要求</text>
          </view>
          <view class="credit-col">
            <text class="num gap" :class="{ positive: totalGapCredits > 0 }">
              {{ formatCredits(totalGapCredits) }}
            </text>
            <text class="lbl">差额参考</text>
          </view>
        </view>
      </view>

      <view v-if="result.data_warnings?.length" class="warning-card">
        <text class="warning-title">数据提示</text>
        <text v-for="warning in result.data_warnings" :key="warning" class="warning-item">
          {{ warning }}
        </text>
      </view>

      <view class="section">
        <text class="section-title">模块完成情况（弱提示）</text>
        <view
          v-for="m in result.modules"
          :key="m.module_code"
          class="module-card"
        >
          <view class="mod-head">
            <text class="mod-name">{{ m.module_name }}</text>
            <text class="mod-tag">{{ moduleTypeLabel(m.module_type) }}</text>
          </view>
          <view class="mod-meta">
            <text>已获：{{ formatCredits(m.credits_earned) }}</text>
            <text>参考：{{ formatCredits(m.credits_required) }}</text>
            <text :class="{ positive: m.credits_gap > 0 }">差额：{{ formatCredits(m.credits_gap) }}</text>
          </view>
          <view class="progress-track">
            <view
              class="progress-fill"
              :style="{ width: Math.min(100, m.credits_required ? (m.credits_earned / m.credits_required * 100) : 0) + '%' }"
            />
          </view>
          <text v-if="m.note" class="mod-note">{{ m.note }}</text>
        </view>
        <view v-if="!result.modules.length" class="empty-tiny">暂无模块数据</view>
      </view>

      <view class="footer-hint">
        以上数据由培养方案模板与教务成绩比对生成，不代替教务毕业审核结论。
        如发现差异，请联系辅导员或教务老师核实。
      </view>
    </template>

    <view v-else class="empty">暂无学业数据</view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getMyAcademicGap, type AcademicGapResult } from '@/api/report'

const result = ref<AcademicGapResult | null>(null)
const loading = ref(false)
const defaultDisclaimer = '本结果仅为辅助提示，不构成毕业资格、课程替代或教务最终结论；请以学院/学校正式审核结果为准。'

const MODULE_TYPE_LABELS: Record<string, string> = {
  REQUIRED: '必修模块',
  ELECTIVE: '选修模块',
  GENERAL: '通识模块',
  PRACTICE: '实践模块',
}

const totalGapCredits = computed(() => {
  if (result.value?.total_credits_required == null) return null
  return Math.max(result.value.total_credits_required - result.value.total_credits_earned, 0)
})

function formatCredits(value?: number | null) {
  if (value == null) return '-'
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

function moduleTypeLabel(moduleType: string) {
  return MODULE_TYPE_LABELS[moduleType] || moduleType
}

async function reload() {
  loading.value = true
  try {
    const resp = await getMyAcademicGap()
    result.value = resp.data
  } catch {
    result.value = null
  } finally {
    loading.value = false
  }
}

onMounted(reload)
</script>

<style scoped>
.container { padding: 24rpx; }

.weak-hint {
  background: #fff7e6;
  color: #ad6800;
  font-size: 24rpx;
  line-height: 1.6;
  padding: 16rpx 20rpx;
  border-radius: 10rpx;
  border-left: 8rpx solid #faad14;
  margin-bottom: 24rpx;
}

.loading { text-align: center; padding: 80rpx 0; color: #999; font-size: 28rpx; }
.empty { text-align: center; padding: 80rpx 0; color: #999; font-size: 28rpx; }
.empty-tiny { text-align: center; padding: 16rpx 0; color: #bbb; font-size: 24rpx; }

.summary-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 32rpx 24rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06);
}
.plan-name { font-size: 30rpx; font-weight: 600; display: block; margin-bottom: 24rpx; }
.credit-row { display: flex; justify-content: space-around; }
.credit-col { display: flex; flex-direction: column; align-items: center; }
.num { font-size: 44rpx; font-weight: 600; color: #333; }
.num.gap { color: #52c41a; }
.num.gap.positive { color: #ff4d4f; }
.lbl { font-size: 22rpx; color: #999; margin-top: 4rpx; }

.warning-card {
  background: #fffbe6;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
  border: 1rpx solid #ffe58f;
}
.warning-title {
  display: block;
  font-size: 26rpx;
  font-weight: 600;
  color: #ad6800;
  margin-bottom: 8rpx;
}
.warning-item {
  display: block;
  font-size: 24rpx;
  color: #ad6800;
  line-height: 1.6;
}

.section {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
}
.section-title { font-size: 28rpx; font-weight: 600; display: block; margin-bottom: 16rpx; }

.module-card {
  padding: 16rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
}
.module-card:last-child { border-bottom: none; }
.mod-head { display: flex; justify-content: space-between; align-items: center; }
.mod-name { font-size: 28rpx; color: #333; }
.mod-tag {
  font-size: 22rpx; padding: 2rpx 12rpx; border-radius: 4rpx;
  background: #f0f0f0; color: #666;
}
.mod-meta {
  display: flex; justify-content: space-between;
  font-size: 24rpx; color: #666; margin-top: 8rpx;
}
.mod-meta .positive { color: #ff4d4f; }

.progress-track {
  margin-top: 10rpx;
  height: 10rpx;
  background: #f0f0f0;
  border-radius: 6rpx;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: #7f1722;
  transition: width .3s ease;
}
.mod-note {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  color: #999;
  line-height: 1.6;
}

.footer-hint {
  font-size: 22rpx;
  color: #999;
  line-height: 1.6;
  padding: 16rpx 0 40rpx;
  text-align: center;
}
</style>
