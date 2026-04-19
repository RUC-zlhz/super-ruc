<template>
  <view class="container">
    <view v-if="!auth.isLoggedIn" class="login-card">
      <text class="welcome">欢迎使用</text>
      <text class="desc">登录后查看您的画像与申请</text>
      <button type="primary" size="default" @tap="onWxLogin">微信一键登录</button>
    </view>

    <template v-else>
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
            <text class="sub" v-if="profile?.student.enrollment_status">
              当前状态：{{ studentStatusLabel }}
            </text>
          </view>
        </view>
      </view>

      <view v-if="profile && !canEditProfile" class="readonly-card">
        <text class="readonly-title">当前仅支持只读查看</text>
        <text class="readonly-desc">{{ readonlyHint }}</text>
      </view>

      <view v-if="profile" class="stat-row">
        <view v-for="t in FACT_TYPES" :key="t.code" class="stat-cell">
          <text class="stat-num">{{ factMetricValue(t.code) }}</text>
          <text class="stat-label">{{ t.label }}</text>
        </view>
      </view>

      <view v-if="profile" class="section">
        <text class="section-title">学籍信息</text>
        <view class="info-row"><text>姓名</text><text>{{ profile.student.full_name }}</text></view>
        <view class="info-row"><text>性别</text><text>{{ profile.student.gender || '-' }}</text></view>
        <view class="info-row"><text>年级</text><text>{{ profile.student.grade_code || '-' }}</text></view>
        <view class="info-row"><text>专业</text><text>{{ profile.student.major_code || '-' }}</text></view>
        <view class="info-row"><text>班级</text><text>{{ profile.student.class_code || '-' }}</text></view>
        <view class="info-row"><text>政治面貌</text><text>{{ profile.student.political_status || '-' }}</text></view>
        <view class="info-row"><text>学籍状态</text><text>{{ studentStatusLabel }}</text></view>
      </view>

      <view v-if="profile && profile.facts?.length" class="section">
        <text class="section-title">成长档案</text>
        <view v-for="f in profile.facts" :key="f.id" class="fact-row">
          <view class="fact-head">
            <text class="fact-type">{{ factLabel(f.fact_type) }}</text>
            <text class="fact-date" v-if="f.started_on">{{ f.started_on?.slice(0, 10) }}</text>
          </view>
          <text class="fact-title">{{ f.title }}</text>
          <text class="fact-desc" v-if="f.description">{{ f.description }}</text>
        </view>
      </view>

      <view class="section">
        <text class="section-title">我的纠错申诉</text>
        <template v-if="corrections.length">
          <view v-for="c in corrections" :key="c.id" class="submission-row">
            <view class="submission-head">
              <text class="submission-title">{{ c.field_name }}</text>
              <text class="status-chip" :class="statusClass(c.status)">
                {{ correctionLabel(c.status) }}
              </text>
            </view>
            <text class="submission-desc" v-if="c.reason">{{ c.reason }}</text>
            <text class="submission-meta">提交时间：{{ formatDateTime(c.created_at) }}</text>
            <text class="submission-meta" v-if="c.handler_comment">
              处理意见：{{ c.handler_comment }}
            </text>
          </view>
        </template>
        <view v-else class="empty-inline">暂无纠错申诉记录</view>
      </view>

      <view class="section">
        <text class="section-title">我的成长补录</text>
        <template v-if="factSubmissionsSupported">
          <template v-if="factSubmissions.length">
            <view v-for="item in factSubmissions" :key="item.id" class="submission-row">
              <view class="submission-head">
                <text class="submission-title">{{ item.title }}</text>
                <text class="status-chip" :class="statusClass(item.approval_status)">
                  {{ approvalStatusLabel(item.approval_status) }}
                </text>
              </view>
              <text class="submission-meta">类型：{{ factLabel(item.fact_type) }}</text>
              <text class="submission-meta">
                提交时间：{{ formatDateTime(item.created_at || item.updated_at) }}
              </text>
              <text class="submission-desc" v-if="item.description">{{ item.description }}</text>
              <text class="submission-meta" v-if="item.review_comment">
                审核意见：{{ item.review_comment }}
              </text>
            </view>
          </template>
          <view v-else class="empty-inline">暂无成长补录记录</view>
        </template>
        <view v-else class="empty-inline">成长补录功能将在后端接口上线后自动接通</view>
      </view>

      <view class="action-list">
        <view class="action-btn" :class="{ disabled: !canEditProfile }" @tap="openAppeal">
          信息纠错申诉
        </view>
        <view class="action-btn" :class="{ disabled: !canEditProfile }" @tap="openGrowthSubmission">
          成长补录
        </view>
        <view class="action-btn" @tap="onLogout">退出登录</view>
      </view>

      <uni-popup ref="appealPopup" type="bottom">
        <view class="popup-panel">
          <text class="popup-title">提交信息纠错申诉</text>
          <view class="form-item">
            <text class="label">字段名</text>
            <input
              class="input"
              v-model="appealForm.field_name"
              placeholder="例如：专业名称 / 联系方式"
            />
          </view>
          <view class="form-item">
            <text class="label">期望值</text>
            <input class="input" v-model="appealForm.proposed_value" placeholder="请填写正确值" />
          </view>
          <view class="form-item">
            <text class="label">说明</text>
            <textarea class="textarea" v-model="appealForm.reason" placeholder="请说明修改理由" />
          </view>
          <view class="popup-footer">
            <button size="mini" @tap="closeAppeal">取消</button>
            <button size="mini" type="primary" :loading="appealSubmitting" @tap="onSubmitAppeal">
              提交
            </button>
          </view>
        </view>
      </uni-popup>

      <uni-popup ref="growthPopup" type="bottom">
        <view class="popup-panel">
          <text class="popup-title">提交成长补录</text>
          <view class="form-item">
            <text class="label">类型</text>
            <picker mode="selector" :range="factTypeLabels" :value="growthTypeIndex" @change="onGrowthTypeChange">
              <view class="picker-value">{{ factLabel(growthForm.fact_type) }}</view>
            </picker>
          </view>
          <view class="form-item">
            <text class="label">标题</text>
            <input class="input" v-model="growthForm.title" placeholder="请输入成果标题" />
          </view>
          <view class="form-item">
            <text class="label">描述</text>
            <textarea class="textarea" v-model="growthForm.description" placeholder="补充事实说明" />
          </view>
          <view class="form-item">
            <text class="label">角色/职责</text>
            <input class="input" v-model="growthForm.role_in_activity" placeholder="例如：项目负责人" />
          </view>
          <view class="double-row">
            <view class="form-item half">
              <text class="label">开始日期</text>
              <picker mode="date" :value="growthForm.started_on || ''" @change="onGrowthDateChange('started_on', $event)">
                <view class="picker-value">{{ growthForm.started_on || '请选择开始日期' }}</view>
              </picker>
            </view>
            <view class="form-item half">
              <text class="label">结束日期</text>
              <picker mode="date" :value="growthForm.ended_on || ''" @change="onGrowthDateChange('ended_on', $event)">
                <view class="picker-value">{{ growthForm.ended_on || '请选择结束日期' }}</view>
              </picker>
            </view>
          </view>
          <view class="double-row">
            <view class="form-item half">
              <text class="label">时长/学时</text>
              <input class="input" v-model="growthForm.hours" type="digit" placeholder="例如：12" />
            </view>
            <view class="form-item half">
              <text class="label">等级/名次</text>
              <input class="input" v-model="growthForm.rank_label" placeholder="例如：一等奖" />
            </view>
          </view>
          <view class="popup-footer">
            <button size="mini" @tap="closeGrowthSubmission">取消</button>
            <button size="mini" type="primary" :loading="growthSubmitting" @tap="onSubmitGrowth">
              提交
            </button>
          </view>
        </view>
      </uni-popup>
    </template>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuthStore } from '@/store/auth'
import {
  getMyCorrections,
  getMyFactSubmissions,
  getMyProfile,
  submitCorrection,
  submitMyFact,
  type CorrectionOut,
  type ProfileFactSubmissionOut,
  type ProfileSelfView,
} from '@/api/profile'

const auth = useAuthStore()
const profile = ref<ProfileSelfView | null>(null)
const corrections = ref<CorrectionOut[]>([])
const factSubmissions = ref<ProfileFactSubmissionOut[]>([])
const factSubmissionsSupported = ref(true)
const appealSubmitting = ref(false)
const growthSubmitting = ref(false)
const appealPopup = ref<any>(null)
const growthPopup = ref<any>(null)

const ACTIVE_ENROLLMENT_STATUSES = new Set(['ACTIVE', 'IN_SCHOOL'])

const FACT_TYPES = [
  { code: 'RESEARCH', label: '科研' },
  { code: 'COMPETITION', label: '竞赛' },
  { code: 'PRACTICE', label: '实践' },
  { code: 'VOLUNTEER', label: '志愿服务' },
  { code: 'LEADERSHIP', label: '学生骨干' },
  { code: 'CUSTOM', label: '自定义' },
]

const ENROLLMENT_STATUS_LABELS: Record<string, string> = {
  ACTIVE: '在读',
  IN_SCHOOL: '在校',
  SUSPENDED: '休学',
  TRANSFERRED: '转出',
  LEAVE: '离校',
  GRADUATED: '毕业',
  ARCHIVED: '归档',
}

const APPROVAL_LABELS: Record<string, string> = {
  PENDING: '待审核',
  APPROVED: '已通过',
  REJECTED: '已驳回',
}

function factLabel(type: string) {
  return FACT_TYPES.find((item) => item.code === type)?.label || type
}

const factTypeLabels = FACT_TYPES.map((item) => item.label)

function factMetricValue(code: string) {
  if (!profile.value) return 0
  if (code === 'RESEARCH') return profile.value.research_count
  if (code === 'COMPETITION') return profile.value.competition_count
  if (code === 'PRACTICE') return profile.value.practice_count
  if (code === 'VOLUNTEER') return profile.value.volunteer_hours
  if (code === 'LEADERSHIP') return profile.value.leadership_count
  return 0
}

const studentStatusLabel = computed(() => {
  const status = profile.value?.student.enrollment_status || ''
  return ENROLLMENT_STATUS_LABELS[status] || status || '未知'
})

const canEditProfile = computed(() => {
  const status = profile.value?.student.enrollment_status
  return !!status && ACTIVE_ENROLLMENT_STATUSES.has(status)
})

const readonlyHint = computed(() => {
  if (!profile.value || canEditProfile.value) return ''
  const parts = [`当前学籍状态为${studentStatusLabel.value}，仅支持查看画像和历史记录。`]
  if (profile.value.student.enrollment_status_reason) {
    parts.push(`原因：${profile.value.student.enrollment_status_reason}`)
  }
  return parts.join(' ')
})

function correctionLabel(status: string) {
  return APPROVAL_LABELS[status] || status
}

function approvalStatusLabel(status: string) {
  return APPROVAL_LABELS[status] || status
}

function statusClass(status?: string | null) {
  return (status || '').toLowerCase()
}

function formatDateTime(value?: string | null) {
  if (!value) return '-'
  const normalized = value.replace('T', ' ').replace('Z', '')
  return normalized.length >= 16 ? normalized.slice(0, 16) : normalized
}

const appealForm = reactive({
  field_name: '',
  proposed_value: '',
  reason: '',
})

const growthForm = reactive({
  fact_type: 'RESEARCH',
  title: '',
  description: '',
  role_in_activity: '',
  started_on: '',
  ended_on: '',
  hours: '',
  rank_label: '',
})

const growthTypeIndex = computed(() =>
  Math.max(FACT_TYPES.findIndex((item) => item.code === growthForm.fact_type), 0),
)

function resetAppealForm() {
  Object.assign(appealForm, {
    field_name: '',
    proposed_value: '',
    reason: '',
  })
}

function resetGrowthForm() {
  Object.assign(growthForm, {
    fact_type: 'RESEARCH',
    title: '',
    description: '',
    role_in_activity: '',
    started_on: '',
    ended_on: '',
    hours: '',
    rank_label: '',
  })
}

function ensureEditable() {
  if (canEditProfile.value) return true
  uni.showToast({ title: '当前学籍状态仅支持只读查看', icon: 'none' })
  return false
}

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
  const [profileResp, correctionsResp, submissionsResp] = await Promise.allSettled([
    getMyProfile(),
    getMyCorrections({ page: 1, size: 10 }),
    getMyFactSubmissions({ page: 1, size: 20 }),
  ])

  if (profileResp.status === 'fulfilled') {
    profile.value = profileResp.value.data
  }
  if (correctionsResp.status === 'fulfilled') {
    corrections.value = correctionsResp.value.data.items || []
  }
  if (submissionsResp.status === 'fulfilled') {
    factSubmissionsSupported.value = submissionsResp.value !== null
    factSubmissions.value = submissionsResp.value?.data.items || []
  } else {
    factSubmissionsSupported.value = false
    factSubmissions.value = []
  }
}

function openAppeal() {
  if (!ensureEditable()) return
  appealPopup.value?.open()
}

function closeAppeal() {
  appealPopup.value?.close()
  resetAppealForm()
}

function openGrowthSubmission() {
  if (!ensureEditable()) return
  growthPopup.value?.open()
}

function closeGrowthSubmission() {
  growthPopup.value?.close()
  resetGrowthForm()
}

async function onSubmitAppeal() {
  if (!ensureEditable()) return
  if (!appealForm.field_name || !appealForm.proposed_value) {
    uni.showToast({ title: '请填写字段名和期望值', icon: 'none' })
    return
  }
  appealSubmitting.value = true
  try {
    await submitCorrection({
      field_name: appealForm.field_name,
      proposed_value: appealForm.proposed_value,
      reason: appealForm.reason || undefined,
    })
    uni.showToast({ title: '已提交，等待审核', icon: 'none' })
    closeAppeal()
    await loadAll()
  } finally {
    appealSubmitting.value = false
  }
}

function onGrowthTypeChange(e: any) {
  const index = Number(e.detail.value)
  growthForm.fact_type = FACT_TYPES[index]?.code || 'RESEARCH'
}

function onGrowthDateChange(field: 'started_on' | 'ended_on', e: any) {
  growthForm[field] = e.detail.value || ''
}

async function onSubmitGrowth() {
  if (!ensureEditable()) return
  if (!growthForm.title.trim()) {
    uni.showToast({ title: '请填写成果标题', icon: 'none' })
    return
  }
  growthSubmitting.value = true
  try {
    await submitMyFact({
      fact_type: growthForm.fact_type,
      title: growthForm.title.trim(),
      description: growthForm.description || undefined,
      role_in_activity: growthForm.role_in_activity || undefined,
      started_on: growthForm.started_on || undefined,
      ended_on: growthForm.ended_on || undefined,
      hours: growthForm.hours ? Number(growthForm.hours) : undefined,
      rank_label: growthForm.rank_label || undefined,
    })
    uni.showToast({ title: '已提交成长补录', icon: 'none' })
    closeGrowthSubmission()
    await loadAll()
  } catch (error: any) {
    uni.showToast({ title: error?.message || '成长补录提交失败', icon: 'none' })
  } finally {
    growthSubmitting.value = false
  }
}

function onLogout() {
  auth.logout()
  uni.showToast({ title: '已退出', icon: 'none' })
  profile.value = null
  corrections.value = []
  factSubmissions.value = []
}

onMounted(async () => {
  if (!auth.isLoggedIn) {
    try {
      await auth.fetchMe()
    } catch {
      // ignore
    }
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
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  margin-right: 20rpx;
  overflow: hidden;
  background: #f5f5f5;
}

.avatar.fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #7f1722;
  color: #fff;
  font-size: 40rpx;
}

.summary-text { display: flex; flex-direction: column; }
.name { font-size: 32rpx; font-weight: 600; }
.sub { font-size: 24rpx; color: #999; margin-top: 4rpx; }

.readonly-card {
  background: #fff7e6;
  border: 1rpx solid #ffd591;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 16rpx;
}

.readonly-title {
  display: block;
  font-size: 28rpx;
  font-weight: 600;
  color: #d46b08;
}

.readonly-desc {
  display: block;
  font-size: 24rpx;
  color: #8c4a00;
  margin-top: 8rpx;
  line-height: 1.6;
}

.stat-row {
  display: flex;
  justify-content: space-around;
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx 0;
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
  display: flex;
  justify-content: space-between;
  padding: 12rpx 0;
  font-size: 26rpx;
  color: #333;
  border-bottom: 1rpx solid #f0f0f0;
}

.info-row:last-child { border-bottom: none; }

.fact-row { padding: 16rpx 0; border-bottom: 1rpx solid #f0f0f0; }
.fact-row:last-child { border-bottom: none; }
.fact-head { display: flex; justify-content: space-between; margin-bottom: 6rpx; }

.fact-type {
  background: #f0f5ff;
  color: #2f54eb;
  font-size: 22rpx;
  padding: 2rpx 12rpx;
  border-radius: 4rpx;
}

.fact-date { font-size: 22rpx; color: #999; }
.fact-title { font-size: 28rpx; color: #333; display: block; font-weight: 500; }
.fact-desc { font-size: 24rpx; color: #666; display: block; margin-top: 6rpx; }

.submission-row { padding: 16rpx 0; border-bottom: 1rpx solid #f0f0f0; }
.submission-row:last-child { border-bottom: none; }

.submission-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16rpx;
}

.submission-title {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
  flex: 1;
}

.submission-desc {
  display: block;
  font-size: 24rpx;
  color: #666;
  margin-top: 8rpx;
  line-height: 1.6;
}

.submission-meta {
  display: block;
  font-size: 22rpx;
  color: #999;
  margin-top: 6rpx;
}

.status-chip {
  font-size: 22rpx;
  padding: 4rpx 14rpx;
  border-radius: 999rpx;
  flex-shrink: 0;
}

.status-chip.pending { background: #fff7e6; color: #d46b08; }
.status-chip.approved { background: #f6ffed; color: #52c41a; }
.status-chip.rejected { background: #fff1f0; color: #cf1322; }

.empty-inline {
  font-size: 24rpx;
  color: #999;
  padding: 8rpx 0;
}

.action-list { margin-top: 24rpx; }

.action-btn {
  background: #fff;
  padding: 24rpx;
  border-radius: 12rpx;
  margin-bottom: 12rpx;
  text-align: center;
  font-size: 28rpx;
  color: #333;
}

.action-btn.disabled {
  color: #bbb;
  background: #f7f7f7;
}

.popup-panel {
  background: #fff;
  padding: 32rpx;
  border-radius: 24rpx 24rpx 0 0;
}

.popup-title { font-size: 32rpx; font-weight: 600; display: block; margin-bottom: 24rpx; }
.form-item { margin-bottom: 16rpx; }
.label { font-size: 24rpx; color: #666; display: block; margin-bottom: 6rpx; }

.input,
.textarea,
.picker-value {
  background: #f7f7f7;
  border-radius: 8rpx;
  padding: 14rpx 16rpx;
  font-size: 26rpx;
  color: #333;
}

.textarea { min-height: 140rpx; width: 100%; }

.double-row {
  display: flex;
  gap: 16rpx;
}

.half { flex: 1; }

.popup-footer {
  display: flex;
  justify-content: flex-end;
  gap: 16rpx;
  margin-top: 16rpx;
}
</style>
