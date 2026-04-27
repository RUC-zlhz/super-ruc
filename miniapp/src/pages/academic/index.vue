<template>
  <view class="container">
    <view class="weak-hint">
      <text class="weak-icon">i</text>
      <view class="weak-copy">
        <text class="weak-title">弱结论免责声明</text>
        <text class="weak-text">{{ result?.disclaimer || defaultDisclaimer }}</text>
      </view>
    </view>

    <view v-if="loading" class="loading">加载中...</view>

    <template v-else-if="result">
      <view class="summary-card">
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
            <text class="num gap" :class="{ positive: totalGapPositive }">
              {{ formatCredits(totalGapCredits) }}
            </text>
            <text class="lbl">差额参考</text>
          </view>
        </view>
      </view>

      <view class="warning-card">
        <text class="warning-icon">!</text>
        <view class="warning-copy">
        <text class="warning-title">数据提示</text>
        <template v-if="result.data_warnings?.length">
        <text v-for="warning in result.data_warnings" :key="warning" class="warning-item">
          {{ warning }}
        </text>
        </template>
        <text v-else class="warning-item">当前数据仅供参考，请以正式审核结果为准。</text>
        </view>
      </view>

      <view class="section">
        <view class="section-head">
          <text class="section-title">模块完成情况</text>
          <text class="plan-name">{{ result.plan_name || '培养方案' }}</text>
        </view>
        <view
          v-for="m in result.modules"
          :key="m.module_code"
          class="module-card"
        >
          <view class="module-icon">{{ moduleIcon(m.module_type) }}</view>
          <view class="module-main">
          <view class="mod-head">
            <text class="mod-name">{{ m.module_name }}</text>
            <text class="mod-tag" :class="{ done: m.credits_gap <= 0 }">
              {{ m.credits_gap <= 0 ? '已完成' : '进行中' }}
            </text>
          </view>
          <text class="mod-meta">完成 {{ formatCredits(m.credits_earned) }} / 要求 {{ formatCredits(m.credits_required) }} 学分</text>
          <view class="progress-track">
            <view
              class="progress-fill"
              :style="{ width: Math.min(100, m.credits_required ? (m.credits_earned / m.credits_required * 100) : 0) + '%' }"
            />
          </view>
          <text class="mod-percent">
            {{ Math.min(100, m.credits_required ? Math.round(m.credits_earned / m.credits_required * 100) : 0) }}%
          </text>
          <text v-if="m.note" class="mod-note">{{ m.note }}</text>
          </view>
        </view>
        <view v-if="!result.modules.length" class="empty-tiny">暂无模块数据</view>
      </view>

      <view class="footer-hint">
        <text class="footer-icon">盾</text>
        <view>
          <text class="footer-title">最终毕业资格以学校正式审核为准</text>
          <text class="footer-text">请持续关注教务通知，及时完成相关学习要求。</text>
        </view>
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

const totalGapPositive = computed(() => (totalGapCredits.value ?? 0) > 0)

function formatCredits(value?: number | null) {
  if (value == null) return '-'
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

function moduleTypeLabel(moduleType: string) {
  return MODULE_TYPE_LABELS[moduleType] || moduleType
}

function moduleIcon(moduleType: string) {
  if (moduleType === 'REQUIRED') return '书'
  if (moduleType === 'ELECTIVE') return '帽'
  if (moduleType === 'PRACTICE') return '验'
  if (moduleType === 'GENERAL') return '星'
  return '学'
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
.container {
  min-height: 100vh;
  padding: 28rpx 24rpx 36rpx;
  background: #f8f3f4;
}

.weak-hint {
  display: flex;
  gap: 18rpx;
  background: #fff8f9;
  color: #b70f24;
  padding: 26rpx 24rpx;
  border-radius: 20rpx;
  border: 2rpx solid #d43346;
  margin-bottom: 24rpx;
}
.weak-icon {
  width: 54rpx;
  height: 54rpx;
  border-radius: 50%;
  border: 4rpx solid #d43346;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  font-weight: 800;
}
.weak-copy { flex: 1; }
.weak-title {
  display: block;
  font-size: 30rpx;
  font-weight: 800;
}
.weak-text {
  display: block;
  margin-top: 8rpx;
  font-size: 26rpx;
  line-height: 1.7;
}

.loading { text-align: center; padding: 80rpx 0; color: #999; font-size: 28rpx; }
.empty { text-align: center; padding: 80rpx 0; color: #999; font-size: 28rpx; }
.empty-tiny { text-align: center; padding: 16rpx 0; color: #bbb; font-size: 24rpx; }

.summary-card {
  background: #fff;
  border-radius: 22rpx;
  padding: 34rpx 24rpx;
  margin-bottom: 22rpx;
  box-shadow: var(--shadow-card);
  border: 1rpx solid #f0e2e5;
}
.credit-row { display: flex; justify-content: space-around; }
.credit-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  border-right: 1rpx solid #f0e2e5;
}
.credit-col:last-child { border-right: none; }
.num { font-size: 54rpx; font-weight: 800; color: #b70f24; }
.num.gap { color: #16a34a; }
.num.gap.positive { color: #b70f24; }
.lbl { font-size: 25rpx; color: #6b7280; margin-top: 6rpx; }

.warning-card {
  display: flex;
  gap: 18rpx;
  background: #fffbeb;
  border-radius: 18rpx;
  padding: 22rpx;
  margin-bottom: 24rpx;
  border: 1rpx solid #f6df9f;
}
.warning-icon {
  width: 50rpx;
  height: 50rpx;
  border-radius: 50%;
  border: 4rpx solid #c98a16;
  color: #c98a16;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  font-weight: 800;
}
.warning-copy { flex: 1; }
.plan-name {
  color: #8a7b80;
  font-size: 24rpx;
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
  border-radius: 22rpx;
  padding: 24rpx;
  margin-bottom: 22rpx;
  box-shadow: var(--shadow-card);
  border: 1rpx solid #f0e2e5;
}
.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18rpx;
}
.section-title {
  font-size: 31rpx;
  font-weight: 800;
  display: block;
  padding-left: 16rpx;
  border-left: 8rpx solid #b70f24;
}

.module-card {
  display: flex;
  gap: 20rpx;
  padding: 22rpx 0;
  border-bottom: 1rpx solid #f0e2e5;
}
.module-card:last-child { border-bottom: none; }
.module-icon {
  width: 82rpx;
  height: 82rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #d51f35, #b70f24);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 800;
}
.module-main { flex: 1; min-width: 0; position: relative; }
.mod-head { display: flex; justify-content: space-between; align-items: center; }
.mod-name { font-size: 31rpx; color: #333; font-weight: 800; }
.mod-tag {
  font-size: 22rpx; padding: 6rpx 18rpx; border-radius: 999rpx;
  background: #fff1f2; color: #b70f24;
}
.mod-tag.done {
  background: #ecfdf3;
  color: #15803d;
}
.mod-meta { display: block; font-size: 25rpx; color: #6b7280; margin-top: 8rpx; }

.progress-track {
  margin-top: 18rpx;
  height: 14rpx;
  background: #edf0f3;
  border-radius: 999rpx;
  overflow: hidden;
  margin-right: 90rpx;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #fb7185, #b70f24);
  transition: width .3s ease;
}
.mod-percent {
  position: absolute;
  right: 0;
  top: 88rpx;
  color: #b70f24;
  font-size: 28rpx;
  font-weight: 800;
}
.mod-note {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  color: #999;
  line-height: 1.6;
}

.footer-hint {
  display: flex;
  gap: 20rpx;
  align-items: center;
  background: linear-gradient(135deg, #b70f24, #8b1020);
  border-radius: 20rpx;
  padding: 24rpx;
  color: #fff;
}
.footer-icon {
  width: 68rpx;
  height: 68rpx;
  border-radius: 50%;
  border: 2rpx solid rgba(255,255,255,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}
.footer-title {
  display: block;
  font-size: 28rpx;
  font-weight: 800;
}
.footer-text {
  display: block;
  margin-top: 6rpx;
  font-size: 23rpx;
  opacity: 0.88;
}
</style>
