<template>
  <view class="container">
    <!-- 未登录态 -->
    <view v-if="!auth.isLoggedIn" class="login-card">
      <text class="welcome">欢迎使用</text>
      <text class="desc">登录后查看您的画像与申请</text>
      <button type="primary" size="default" @tap="onWxLogin">微信一键登录</button>
    </view>

    <!-- 已登录 -->
    <template v-else>
      <!-- 身份摘要 -->
      <view class="summary-card">
        <view class="avatar-row">
          <image v-if="auth.user?.avatar_url" :src="auth.user.avatar_url" class="avatar" />
          <view v-else class="avatar fallback">
            <text>{{ (auth.user?.display_name || '学')[0] }}</text>
          </view>
          <view class="summary-text">
            <text class="name">{{ auth.user?.display_name || '同学' }}</text>
            <text class="sub" v-if="profile?.student.student_no">
              学号：{{ profile?.student.student_no }}
            </text>
            <text class="sub" v-if="enrollmentReadonly">
              学籍状态：{{ enrollmentLabel }}（只读）
            </text>
          </view>
        </view>
      </view>

      <!-- 画像统计 -->
      <view v-if="profile" class="stat-row">
        <view v-for="t in FACT_TYPES" :key="t.code" class="stat-cell">
          <text class="stat-num">{{ profile.fact_counts?.[t.code] || 0 }}</text>
          <text class="stat-label">{{ t.label }}</text>
        </view>
      </view>

      <!-- 静态学籍信息 -->
      <view v-if="profile" class="section">
        <text class="section-title">学籍信息</text>
        <view class="info-row"><text>姓名</text><text>{{ profile.student.full_name }}</text></view>
        <view class="info-row"><text>性别</text><text>{{ profile.student.gender || '-' }}</text></view>
        <view class="info-row"><text>年级</text><text>{{ profile.student.grade_code || '-' }}</text></view>
        <view class="info-row"><text>专业</text><text>{{ profile.student.major_code || '-' }}</text></view>
        <view class="info-row"><text>班级</text><text>{{ profile.student.class_code || '-' }}</text></view>
        <view class="info-row"><text>政治面貌</text><text>{{ profile.student.political_status || '-' }}</text></view>
      </view>

      <!-- 动态成长事实 -->
      <view v-if="profile && profile.facts?.length" class="section">
        <text class="section-title">成长档案</text>
        <view
          v-for="f in profile.facts"
          :key="f.id"
          class="fact-row"
        >
          <view class="fact-head">
            <text class="fact-type">{{ factLabel(f.fact_type) }}</text>
            <text class="fact-date" v-if="f.started_on">{{ f.started_on?.slice(0, 10) }}</text>
          </view>
          <text class="fact-title">{{ f.title }}</text>
          <text class="fact-desc" v-if="f.description">{{ f.description }}</text>
        </view>
      </view>

      <!-- 我的申诉 -->
      <view v-if="corrections.length" class="section">
        <text class="section-title">我的纠错申诉</text>
        <view v-for="c in corrections" :key="c.id" class="correction-row">
          <view class="correction-head">
            <text class="correction-field">{{ c.field_name }}</text>
            <text class="correction-status" :class="c.status.toLowerCase()">
              {{ correctionLabel(c.status) }}
            </text>
          </view>
          <text class="correction-reason" v-if="c.reason">{{ c.reason }}</text>
        </view>
      </view>

      <!-- 操作入口 -->
      <view class="action-list">
        <view
          v-if="!enrollmentReadonly"
          class="action-btn"
          @tap="showAppeal = true"
        >信息纠错申诉</view>
        <view
          v-else
          class="action-btn disabled"
        >信息纠错申诉（当前学籍不可提交）</view>
        <view class="action-btn" @tap="onLogout">退出登录</view>
      </view>

      <!-- 申诉表单 -->
      <uni-popup ref="appealPopup" type="bottom" v-if="showAppeal">
        <view class="appeal-panel">
          <text class="appeal-title">提交信息纠错申诉</text>
          <view class="form-item">
            <text class="label">字段名</text>
            <input
              class="input"
              v-model="appealForm.field_name"
              placeholder="例如：专业名称 / 联系方式"
            />
          </view>
          <view class="form-item">
            <text class="label">当前值</text>
            <input class="input" v-model="appealForm.current_value" placeholder="（可选）当前系统中的值" />
          </view>
          <view class="form-item">
            <text class="label">期望值</text>
            <input class="input" v-model="appealForm.proposed_value" placeholder="请填写正确值" />
          </view>
          <view class="form-item">
            <text class="label">说明</text>
            <textarea class="textarea" v-model="appealForm.reason" placeholder="请说明修改理由" />
          </view>
          <view class="appeal-footer">
            <button size="mini" @tap="closeAppeal">取消</button>
            <button size="mini" type="primary" :loading="submitting" @tap="onSubmitAppeal">提交</button>
          </view>
        </view>
      </uni-popup>
    </template>
  </view>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, computed } from 'vue'
import { useAuthStore } from '@/store/auth'
import { getMyProfile, submitCorrection, getMyCorrections, type ProfileSelfView } from '@/api/profile'

const auth = useAuthStore()
const profile = ref<ProfileSelfView | null>(null)
const corrections = ref<any[]>([])
const showAppeal = ref(false)
const submitting = ref(false)
const appealPopup = ref<any>(null)

const FACT_TYPES = [
  { code: 'RESEARCH', label: '科研' },
  { code: 'COMPETITION', label: '竞赛' },
  { code: 'PRACTICE', label: '实践' },
  { code: 'VOLUNTEER', label: '志愿' },
  { code: 'LEADERSHIP', label: '干部' },
]
function factLabel(t: string) {
  return FACT_TYPES.find(x => x.code === t)?.label || t
}

const ENROLLMENT_LABELS: Record<string, string> = {
  ACTIVE: '在读',
  SUSPENDED: '休学',
  TRANSFERRED: '转出',
  GRADUATED: '毕业',
  ARCHIVED: '归档',
}
const enrollmentLabel = computed(() =>
  ENROLLMENT_LABELS[profile.value?.student.enrollment_status || ''] || '未知'
)
const enrollmentReadonly = computed(() =>
  !!profile.value && profile.value.student.enrollment_status !== 'ACTIVE'
)

const CORRECTION_LABELS: Record<string, string> = {
  PENDING: '待处理',
  APPROVED: '已通过',
  REJECTED: '已驳回',
}
function correctionLabel(s: string) { return CORRECTION_LABELS[s] || s }

const appealForm = reactive({
  field_name: '',
  current_value: '',
  proposed_value: '',
  reason: '',
})

async function onWxLogin() {
  try {
    const loginRes = await uni.login({ provider: 'weixin' })
    await auth.wxLogin((loginRes as any).code)
    await loadAll()
  } catch {
    uni.showToast({ title: '登录失败', icon: 'none' })
  }
}

async function loadAll() {
  try {
    const [pRes, cRes] = await Promise.all([
      getMyProfile(),
      getMyCorrections({ page: 1, size: 10 }),
    ])
    profile.value = pRes.data
    corrections.value = cRes.data.items || []
  } catch { /* ok */ }
}

function closeAppeal() {
  showAppeal.value = false
  Object.assign(appealForm, { field_name: '', current_value: '', proposed_value: '', reason: '' })
}

async function onSubmitAppeal() {
  if (!appealForm.field_name || !appealForm.proposed_value) {
    uni.showToast({ title: '请填写字段名和期望值', icon: 'none' })
    return
  }
  submitting.value = true
  try {
    await submitCorrection({
      field_name: appealForm.field_name,
      current_value: appealForm.current_value || undefined,
      proposed_value: appealForm.proposed_value,
      reason: appealForm.reason || undefined,
    })
    uni.showToast({ title: '已提交，等待审核' })
    closeAppeal()
    await loadAll()
  } finally {
    submitting.value = false
  }
}

function onLogout() {
  auth.logout()
  uni.showToast({ title: '已退出' })
  profile.value = null
  corrections.value = []
}

onMounted(async () => {
  if (!auth.isLoggedIn) {
    try { await auth.fetchMe() } catch { /* not logged in */ }
  }
  if (auth.isLoggedIn) await loadAll()
})
</script>

<style scoped>
.container { padding: 24rpx; }

.login-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 60rpx 40rpx;
  text-align: center;
}
.welcome { font-size: 40rpx; font-weight: 600; color: #7f1722; display: block; }
.desc { font-size: 26rpx; color: #666; display: block; margin: 16rpx 0 24rpx; }

.summary-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 32rpx;
  margin-bottom: 16rpx;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06);
}
.avatar-row { display: flex; align-items: center; }
.avatar {
  width: 100rpx; height: 100rpx; border-radius: 50%;
  margin-right: 20rpx; overflow: hidden; background: #f5f5f5;
}
.avatar.fallback {
  display: flex; align-items: center; justify-content: center;
  background: #7f1722; color: #fff; font-size: 40rpx;
}
.summary-text { display: flex; flex-direction: column; }
.name { font-size: 32rpx; font-weight: 600; }
.sub { font-size: 24rpx; color: #999; margin-top: 4rpx; }

.stat-row {
  display: flex; justify-content: space-around;
  background: #fff; border-radius: 16rpx; padding: 24rpx 0;
  margin-bottom: 16rpx;
}
.stat-cell { display: flex; flex-direction: column; align-items: center; }
.stat-num { font-size: 34rpx; font-weight: 600; color: #7f1722; }
.stat-label { font-size: 22rpx; color: #666; margin-top: 4rpx; }

.section {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 16rpx;
}
.section-title { font-size: 28rpx; font-weight: 600; display: block; margin-bottom: 16rpx; }
.info-row {
  display: flex; justify-content: space-between;
  padding: 12rpx 0; font-size: 26rpx; color: #333;
  border-bottom: 1rpx solid #f0f0f0;
}
.info-row:last-child { border-bottom: none; }

.fact-row { padding: 16rpx 0; border-bottom: 1rpx solid #f0f0f0; }
.fact-row:last-child { border-bottom: none; }
.fact-head { display: flex; justify-content: space-between; margin-bottom: 6rpx; }
.fact-type {
  background: #f0f5ff; color: #2f54eb;
  font-size: 22rpx; padding: 2rpx 12rpx; border-radius: 4rpx;
}
.fact-date { font-size: 22rpx; color: #999; }
.fact-title { font-size: 28rpx; color: #333; display: block; font-weight: 500; }
.fact-desc { font-size: 24rpx; color: #666; display: block; margin-top: 6rpx; }

.correction-row { padding: 14rpx 0; border-bottom: 1rpx solid #f0f0f0; }
.correction-row:last-child { border-bottom: none; }
.correction-head { display: flex; justify-content: space-between; align-items: center; }
.correction-field { font-size: 26rpx; color: #333; }
.correction-status { font-size: 22rpx; padding: 2rpx 12rpx; border-radius: 4rpx; }
.correction-status.pending { background: #fff7e6; color: #d46b08; }
.correction-status.approved { background: #f6ffed; color: #52c41a; }
.correction-status.rejected { background: #fff1f0; color: #cf1322; }
.correction-reason { font-size: 24rpx; color: #666; display: block; margin-top: 6rpx; }

.action-list { margin-top: 24rpx; }
.action-btn {
  background: #fff; padding: 24rpx; border-radius: 12rpx;
  margin-bottom: 12rpx; text-align: center; font-size: 28rpx; color: #333;
}
.action-btn.disabled { color: #bbb; }

.appeal-panel {
  background: #fff; padding: 32rpx;
  border-radius: 24rpx 24rpx 0 0;
}
.appeal-title { font-size: 32rpx; font-weight: 600; display: block; margin-bottom: 24rpx; }
.form-item { margin-bottom: 16rpx; }
.label { font-size: 24rpx; color: #666; display: block; margin-bottom: 6rpx; }
.input, .textarea {
  background: #f7f7f7; border-radius: 8rpx;
  padding: 14rpx 16rpx; font-size: 26rpx;
}
.textarea { min-height: 140rpx; }
.appeal-footer { display: flex; justify-content: flex-end; gap: 16rpx; margin-top: 16rpx; }
</style>
