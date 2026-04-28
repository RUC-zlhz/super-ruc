<template>
  <view class="container">
    <view v-if="!auth.isLoggedIn" class="login-shell">
      <view class="login-hero">
        <view class="login-brand-block">
          <text class="login-brand">中国人民大学</text>
          <text class="login-brand-en">RENMIN UNIVERSITY OF CHINA</text>
        </view>
        <view class="login-skyline">
          <view class="skyline skyline-1"></view>
          <view class="skyline skyline-2"></view>
          <view class="skyline skyline-3"></view>
          <view class="skyline skyline-4"></view>
        </view>
      </view>
      <view class="login-card">
        <view class="login-illustration">
          <view class="illustration-sheet">
            <view class="sheet-photo"></view>
            <view class="sheet-lines">
              <view class="sheet-line line-strong"></view>
              <view class="sheet-line"></view>
              <view class="sheet-line short"></view>
            </view>
          </view>
          <view class="illustration-person"></view>
          <view class="illustration-tag tag-red"></view>
          <view class="illustration-tag tag-green"></view>
        </view>
        <text class="welcome">登录后，查看你的成长画像</text>
        <text class="desc">记录成长点滴，见证更好的你</text>
        <view class="login-actions">
          <button class="primary-button" :type="UNI_BUTTON_TYPE.primary" size="default" hover-class="hover-scale" @tap="onWxLogin">
            <text class="btn-icon">❖</text> 微信一键登录
          </button>
          <text class="login-note">未绑定微信时，请先使用密码登录绑定</text>
        </view>
      </view>
    </view>

    <template v-else>
      <view class="profile-hero">
        <view class="hero-brand-row">
          <view class="hero-brand-copy">
            <text class="hero-brand-title">我的画像</text>
            <text class="hero-brand-sub">成长档案与服务入口</text>
          </view>
          <text class="hero-brand-pill">RUC</text>
        </view>
        <view class="summary-card">
          <view class="avatar-row">
            <image v-if="auth.user?.avatar_url" :src="auth.user.avatar_url" class="avatar" />
            <view v-else class="avatar fallback">
              <text>{{ (auth.user?.display_name || '学')[0] }}</text>
            </view>
            <view class="summary-text">
              <view class="summary-head">
                <text class="name">{{ auth.user?.display_name || '同学' }}</text>
                <text
                  v-if="profile?.student.enrollment_status"
                  class="summary-status"
                  :class="{ inactive: !canEditProfile }"
                >
                  {{ studentStatusLabel }}
                </text>
              </view>
              <text class="sub" v-if="profile?.student.student_no">
                学号：{{ profile?.student.student_no }}
              </text>
              <text class="summary-school">中国人民大学</text>
              <text class="summary-major" v-if="profile?.student.grade_code || profile?.student.major_code">
                {{ [profile?.student.grade_code, profile?.student.major_code].filter(Boolean).join(' · ') }}
              </text>
            </view>
          </view>
        </view>
        <view v-if="profile" class="hero-note" :class="{ readonly: !canEditProfile }">
          <view class="hero-note-dot"></view>
          <text class="hero-note-text">
            {{
              canEditProfile
                ? '若发现画像信息有误，可在下方提交纠错申诉；成长经历缺失可发起补录。'
                : readonlyHint
            }}
          </text>
        </view>
      </view>

      <view v-if="profile" class="section metric-section">
        <view class="section-head">
          <view class="section-copy">
            <text class="section-title">成长统计</text>
            <text class="section-tip">基于当前已归集的成长档案</text>
          </view>
          <text class="section-aux">共 {{ profile.facts?.length || 0 }} 条</text>
        </view>
        <view class="stat-row">
          <view v-for="(t, index) in FACT_TYPES" :key="t.code" class="stat-cell" :class="`tone-${index % 4}`">
            <view class="stat-icon">{{ factShortLabel(t.code) }}</view>
            <text class="stat-num">{{ factMetricValue(t.code) }}</text>
            <text class="stat-label">{{ t.label }}</text>
          </view>
        </view>
      </view>

      <view v-if="profile" class="section service-section">
        <view class="section-head">
          <view class="section-copy">
            <text class="section-title">功能与服务</text>
            <text class="section-tip">围绕画像查看、档案维护与进度追踪</text>
          </view>
        </view>
        <view class="service-card">
          <text class="service-icon">籍</text>
          <view class="service-copy">
            <text class="service-title">学籍信息</text>
            <text class="service-desc">查看学籍基本信息、学籍异动记录</text>
          </view>
          <text class="service-arrow">›</text>
        </view>
        <view class="info-list">
          <view class="info-row">
            <text class="info-label">姓名</text>
            <text class="info-value">{{ profile.student.full_name }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">性别</text>
            <text class="info-value">{{ profile.student.gender || '-' }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">年级</text>
            <text class="info-value">{{ profile.student.grade_code || '-' }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">专业</text>
            <text class="info-value">{{ profile.student.major_code || '-' }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">班级</text>
            <text class="info-value">{{ profile.student.class_code || '-' }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">政治面貌</text>
            <text class="info-value">{{ profile.student.political_status || '-' }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">学籍状态</text>
            <text class="info-value status-text">{{ studentStatusLabel }}</text>
          </view>
        </view>
      </view>

      <view v-if="profile && profile.facts?.length" class="section archive-section">
        <view class="section-head">
          <view class="section-copy">
            <text class="section-title">成长档案</text>
            <text class="section-tip">已沉淀的个人成长经历记录</text>
          </view>
          <text class="section-aux">{{ profile.facts.length }} 条</text>
        </view>
        <view v-for="f in profile.facts" :key="f.id" class="fact-row">
          <view class="fact-mark"></view>
          <view class="fact-body">
            <view class="fact-head">
              <text class="fact-type">{{ factLabel(f.fact_type) }}</text>
              <text class="fact-date" v-if="f.started_on">{{ f.started_on?.slice(0, 10) }}</text>
            </view>
            <text class="fact-title">{{ f.title }}</text>
            <text class="fact-desc" v-if="f.description">{{ f.description }}</text>
          </view>
        </view>
      </view>

      <view class="section">
        <view class="section-head">
          <view class="section-copy">
            <text class="section-title">我的纠错申诉</text>
            <text class="section-tip">查看申诉处理进度与审核意见</text>
          </view>
        </view>
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
        <view class="section-head">
          <view class="section-copy">
            <text class="section-title">我的成长补录</text>
            <text class="section-tip">查看补录审核状态与历史说明</text>
          </view>
        </view>
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

      <view class="section action-panel">
        <view class="section-head">
          <view class="section-copy">
            <text class="section-title">操作区</text>
            <text class="section-tip">快速发起纠错申诉、成长补录或退出账号</text>
          </view>
        </view>
        <view class="action-list">
          <view class="action-btn" :class="{ disabled: !canEditProfile }" @tap="openAppeal">
            <view class="action-copy">
              <text class="action-title">信息纠错申诉</text>
              <text class="action-desc">发起信息纠错并查看处理进度</text>
            </view>
            <text class="action-arrow">›</text>
          </view>
          <view class="action-btn" :class="{ disabled: !canEditProfile }" @tap="openGrowthSubmission">
            <view class="action-copy">
              <text class="action-title">成长补录</text>
              <text class="action-desc">补充尚未归档的成长经历记录</text>
            </view>
            <text class="action-arrow">›</text>
          </view>
          <view class="action-btn action-btn-logout" hover-class="hover-opacity" @tap="onLogout">
            <text class="action-title logout-text">退出登录</text>
          </view>
        </view>
      </view>

      <view v-if="appealVisible" class="sheet-mask" @tap="closeAppeal">
        <view class="popup-panel" @tap.stop>
          <view class="popup-handle"></view>
          <view class="popup-header">
            <text class="popup-title">纠错申诉</text>
            <text class="popup-close" @tap="closeAppeal">×</text>
          </view>
          <view class="popup-alert">
            <text class="popup-alert-icon">!</text>
            <text class="popup-alert-text">
              如发现个人画像或成长记录信息有误，可提交申诉，学校审核后统一修正。
            </text>
          </view>
          <view class="popup-form">
            <view class="form-item">
              <text class="label required">字段名</text>
              <input
                class="input"
                v-model="appealForm.field_name"
                placeholder="例如：专业名称 / 联系方式"
              />
            </view>
            <view class="form-item">
              <text class="label required">期望值</text>
              <input class="input" v-model="appealForm.proposed_value" placeholder="请填写正确值" />
            </view>
            <view class="form-item">
              <text class="label">说明</text>
              <textarea class="textarea" v-model="appealForm.reason" placeholder="请说明修改理由" />
            </view>
            <view class="upload-card" @tap="showUploadHint">
              <text class="upload-icon">凭</text>
              <view class="upload-copy">
                <text class="upload-title">上传凭证</text>
                <text class="upload-desc">支持图片、PDF 等证明材料，后端附件能力接通后可直接上传</text>
              </view>
            </view>
          </view>
          <view class="popup-footer">
            <button class="popup-cancel" size="mini" hover-class="hover-opacity" @tap="closeAppeal">取消</button>
            <button
              class="popup-submit"
              size="mini"
              :type="UNI_BUTTON_TYPE.primary"
              hover-class="hover-scale"
              :loading="appealSubmitting"
              @tap="onSubmitAppeal"
            >
              <text class="btn-icon">✓</text> 提交申诉
            </button>
          </view>
        </view>
      </view>

      <view v-if="growthVisible" class="sheet-mask" @tap="closeGrowthSubmission">
        <view class="popup-panel" @tap.stop>
          <view class="popup-handle"></view>
          <view class="popup-header">
            <text class="popup-title">成长补录</text>
            <text class="popup-close" @tap="closeGrowthSubmission">×</text>
          </view>
          <view class="popup-alert">
            <text class="popup-alert-icon">!</text>
            <text class="popup-alert-text">
              若重要成长经历尚未及时记录，可在此补录，审核通过后自动归档到个人画像。
            </text>
          </view>
          <view class="popup-form">
            <view class="form-item">
              <text class="label required">类型</text>
              <picker mode="selector" :range="factTypeLabels" :value="growthTypeIndex" @change="onGrowthTypeChange">
                <view class="picker-value">{{ factLabel(growthForm.fact_type) }}</view>
              </picker>
            </view>
            <view class="form-item">
              <text class="label required">标题</text>
              <input class="input" v-model="growthForm.title" placeholder="请输入成果标题" />
            </view>
            <view class="form-item">
              <text class="label required">内容描述</text>
              <textarea class="textarea" v-model="growthForm.description" placeholder="补充事实说明" />
            </view>
            <view class="form-item">
              <text class="label">角色/职责</text>
              <input class="input" v-model="growthForm.role_in_activity" placeholder="例如：项目负责人" />
            </view>
            <view class="double-row">
              <view class="form-item half">
                <text class="label required">开始日期</text>
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
            <view class="upload-card" @tap="showUploadHint">
              <text class="upload-icon">附</text>
              <view class="upload-copy">
                <text class="upload-title">附件上传</text>
                <text class="upload-desc">可用于佐证活动、获奖、实践等成长经历</text>
              </view>
            </view>
          </view>
          <view class="popup-footer">
            <button class="popup-cancel" size="mini" hover-class="hover-opacity" @tap="closeGrowthSubmission">取消</button>
            <button
              class="popup-submit"
              size="mini"
              :type="UNI_BUTTON_TYPE.primary"
              hover-class="hover-scale"
              :loading="growthSubmitting"
              @tap="onSubmitGrowth"
            >
              <text class="btn-icon">🚀</text> 提交补录
            </button>
          </view>
        </view>
      </view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuthStore } from '@/store/auth'
import { UNI_BUTTON_TYPE } from '@/utils/uni-button'
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

type SettledResult<T> =
  | { status: 'fulfilled'; value: T }
  | { status: 'rejected'; reason: unknown }

const auth = useAuthStore()
const profile = ref<ProfileSelfView | null>(null)
const corrections = ref<CorrectionOut[]>([])
const factSubmissions = ref<ProfileFactSubmissionOut[]>([])
const factSubmissionsSupported = ref(true)
const appealSubmitting = ref(false)
const growthSubmitting = ref(false)
const appealVisible = ref(false)
const growthVisible = ref(false)

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

function factShortLabel(type: string) {
  const label = factLabel(type)
  return label.slice(0, 1)
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

function settleAll<T extends readonly Promise<unknown>[]>(
  promises: T,
): Promise<{
  [K in keyof T]: T[K] extends Promise<infer R> ? SettledResult<R> : never
}> {
  return Promise.all(
    promises.map((promise) =>
      promise.then(
        (value) => ({ status: 'fulfilled', value }),
        (reason) => ({ status: 'rejected', reason }),
      ),
    ),
  ) as Promise<{
    [K in keyof T]: T[K] extends Promise<infer R> ? SettledResult<R> : never
  }>
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
  const [profileResp, correctionsResp, submissionsResp] = await settleAll([
    getMyProfile(),
    getMyCorrections({ page: 1, size: 10 }),
    getMyFactSubmissions({ page: 1, size: 20 }),
  ] as const)

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
  appealVisible.value = true
}

function closeAppeal() {
  appealVisible.value = false
  resetAppealForm()
}

function openGrowthSubmission() {
  if (!ensureEditable()) return
  growthVisible.value = true
}

function closeGrowthSubmission() {
  growthVisible.value = false
  resetGrowthForm()
}

function showUploadHint() {
  uni.showToast({ title: '附件上传入口已预留', icon: 'none' })
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
.container {
  min-height: 100vh;
  padding: 0 24rpx 36rpx;
  background:
    linear-gradient(180deg, #b30d1f 0, #b30d1f 360rpx, #f7f1f2 640rpx),
    #f7f1f2;
}

.login-shell {
  padding-top: 32rpx;
}

.login-hero {
  position: relative;
  min-height: 360rpx;
  padding: 34rpx 28rpx 0;
  overflow: hidden;
}

.login-brand-block {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
}

.login-brand {
  color: #fff;
  font-size: 42rpx;
  font-weight: 800;
  letter-spacing: 2rpx;
}

.login-brand-en {
  margin-top: 10rpx;
  color: rgba(255,255,255,0.84);
  font-size: 20rpx;
  letter-spacing: 2rpx;
}

.login-skyline {
  position: absolute;
  inset: auto 0 0 0;
  height: 180rpx;
}

.skyline {
  position: absolute;
  bottom: 0;
  border: 2rpx solid rgba(255,255,255,0.22);
  border-bottom: none;
  background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0));
}

.skyline-1 {
  left: 24rpx;
  width: 180rpx;
  height: 94rpx;
}

.skyline-2 {
  left: 166rpx;
  width: 120rpx;
  height: 126rpx;
}

.skyline-3 {
  right: 178rpx;
  width: 160rpx;
  height: 110rpx;
}

.skyline-4 {
  right: 34rpx;
  width: 112rpx;
  height: 154rpx;
}

.login-card {
  position: relative;
  margin: -18rpx 8rpx 0;
  background: #fff;
  border-radius: 36rpx;
  padding: 36rpx 34rpx 40rpx;
  text-align: center;
  box-shadow: 0 22rpx 56rpx rgba(103, 18, 31, 0.14);
}

.login-illustration {
  position: relative;
  width: 100%;
  height: 340rpx;
  margin: 0 auto 30rpx;
  border-radius: 30rpx;
  background:
    radial-gradient(circle at 22% 24%, rgba(255, 218, 223, 0.62), transparent 84rpx),
    radial-gradient(circle at 82% 82%, rgba(210, 227, 255, 0.9), transparent 92rpx),
    linear-gradient(180deg, #fffdfd, #fff4f5);
  overflow: hidden;
}

.illustration-sheet {
  position: absolute;
  top: 54rpx;
  right: 92rpx;
  width: 210rpx;
  height: 150rpx;
  padding: 24rpx 20rpx;
  border-radius: 24rpx;
  background: linear-gradient(180deg, #eef2ff, #ffffff);
  box-shadow: 0 18rpx 32rpx rgba(100, 113, 173, 0.14);
  display: flex;
  align-items: flex-start;
}

.sheet-photo {
  width: 52rpx;
  height: 52rpx;
  border-radius: 16rpx;
  background: linear-gradient(135deg, #ef4444, #f59e0b);
  margin-right: 16rpx;
}

.sheet-lines {
  flex: 1;
}

.sheet-line {
  height: 12rpx;
  border-radius: 999rpx;
  background: #d7def7;
  margin-top: 14rpx;
}

.line-strong {
  width: 100%;
  margin-top: 4rpx;
}

.sheet-line.short {
  width: 70%;
}

.illustration-person {
  position: absolute;
  left: 60rpx;
  bottom: 34rpx;
  width: 172rpx;
  height: 186rpx;
  border-radius: 48rpx 48rpx 28rpx 28rpx;
  background:
    radial-gradient(circle at 50% 26%, #ffe2c6 0 26rpx, transparent 28rpx),
    linear-gradient(180deg, #ef4444 0 42%, #fff 42% 56%, #c7d2fe 56% 100%);
  box-shadow: 0 16rpx 34rpx rgba(183, 15, 36, 0.14);
}

.illustration-tag {
  position: absolute;
  width: 26rpx;
  height: 26rpx;
  border-radius: 50%;
  border: 4rpx solid #fff;
}

.tag-red {
  top: 56rpx;
  right: 68rpx;
  background: #ef4444;
}

.tag-green {
  top: 132rpx;
  right: 128rpx;
  background: #22c55e;
}

.welcome {
  font-size: 38rpx;
  font-weight: 800;
  color: #202124;
  display: block;
}

.desc {
  font-size: 26rpx;
  color: #7d7b81;
  display: block;
  margin: 18rpx 0 28rpx;
}

.btn-icon {
  margin-right: 8rpx;
  font-size: 32rpx;
  vertical-align: middle;
}

.primary-button {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 20rpx;
  box-shadow: 0 14rpx 28rpx rgba(179, 13, 31, 0.18);
}

.profile-hero {
  position: relative;
  margin: 0 -24rpx 24rpx;
  padding: 28rpx 24rpx 24rpx;
  background:
    radial-gradient(circle at 84% 16%, rgba(255,255,255,0.14), transparent 130rpx),
    linear-gradient(140deg, #b30d1f 0%, #8d1020 62%, #6f0d18 100%);
  overflow: hidden;
}

.hero-brand-row {
  position: relative;
  z-index: 2;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 22rpx;
}

.hero-brand-copy {
  display: flex;
  flex-direction: column;
}

.hero-brand-title {
  font-size: 40rpx;
  font-weight: 800;
  color: #fff;
}

.hero-brand-sub {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: rgba(255,255,255,0.72);
}

.hero-brand-pill {
  min-width: 74rpx;
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  text-align: center;
  font-size: 22rpx;
  font-weight: 700;
  color: #fff;
  background: rgba(255,255,255,0.14);
  border: 1rpx solid rgba(255,255,255,0.18);
}

.summary-card {
  position: relative;
  z-index: 2;
  background: rgba(255,255,255,0.97);
  border-radius: 28rpx;
  padding: 28rpx;
  box-shadow: 0 18rpx 34rpx rgba(53, 17, 22, 0.14);
}

.avatar-row {
  display: flex;
  align-items: center;
}

.avatar {
  width: 110rpx;
  height: 110rpx;
  border-radius: 50%;
  margin-right: 22rpx;
  overflow: hidden;
  background: #f5f5f5;
  border: 4rpx solid rgba(179, 13, 31, 0.08);
}

.avatar.fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #dc3344, #b30d1f);
  color: #fff;
  font-size: 40rpx;
}

.summary-text {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.summary-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18rpx;
}

.name {
  font-size: 34rpx;
  font-weight: 800;
  color: #202124;
}

.summary-status {
  padding: 8rpx 20rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  line-height: 1;
  color: #1b8d4b;
  background: #e9f9ef;
  font-weight: 700;
}

.summary-status.inactive {
  color: #c57a0e;
  background: #fff4db;
}

.sub {
  font-size: 24rpx;
  color: #7a7c84;
  margin-top: 8rpx;
}

.summary-school,
.summary-major {
  font-size: 22rpx;
  color: #9b9da5;
  margin-top: 8rpx;
}

.hero-note {
  position: relative;
  z-index: 2;
  margin-top: 18rpx;
  padding: 18rpx 20rpx;
  border-radius: 20rpx;
  background: #fff7e6;
  border: 1rpx solid rgba(255, 214, 152, 0.8);
  display: flex;
  align-items: flex-start;
  gap: 14rpx;
}

.hero-note.readonly {
  background: rgba(255, 242, 206, 0.96);
}

.hero-note-dot {
  width: 12rpx;
  height: 12rpx;
  margin-top: 10rpx;
  border-radius: 50%;
  background: #f0a000;
  flex-shrink: 0;
}

.hero-note-text {
  flex: 1;
  font-size: 24rpx;
  line-height: 1.6;
  color: #8f5600;
}

.stat-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.stat-cell {
  position: relative;
  width: calc((100% - 24rpx) / 3);
  min-height: 164rpx;
  display: flex;
  flex-direction: column;
  justify-content: center;
  border-radius: 24rpx;
  padding: 24rpx 18rpx;
  box-sizing: border-box;
  overflow: hidden;
}

.stat-cell.tone-0 {
  background: linear-gradient(180deg, #fff3f3, #fffdfd);
}

.stat-cell.tone-1 {
  background: linear-gradient(180deg, #fff8e7, #fffdf7);
}

.stat-cell.tone-2 {
  background: linear-gradient(180deg, #eef8ff, #fbfeff);
}

.stat-cell.tone-3 {
  background: linear-gradient(180deg, #f4f1ff, #fdfcff);
}

.stat-icon {
  width: 48rpx;
  height: 48rpx;
  border-radius: 14rpx;
  background: rgba(255,255,255,0.82);
  color: #b30d1f;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  font-weight: 800;
  margin-bottom: 14rpx;
}

.stat-num {
  font-size: 40rpx;
  font-weight: 800;
  color: #202124;
  line-height: 1.1;
}

.stat-label {
  font-size: 22rpx;
  color: #6d6f78;
  margin-top: 10rpx;
  line-height: 1.4;
}

.section {
  background: #fff;
  border-radius: 28rpx;
  padding: 26rpx;
  margin-bottom: 18rpx;
  box-shadow: 0 14rpx 28rpx rgba(107, 37, 46, 0.08);
  border: 1rpx solid #f3e7ea;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16rpx;
  margin-bottom: 18rpx;
}

.section-copy {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.section-title {
  font-size: 30rpx;
  font-weight: 800;
  color: #241d1e;
  display: block;
}

.section-tip {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #9a8f92;
  line-height: 1.5;
}

.section-aux {
  font-size: 22rpx;
  color: #9a8f92;
  line-height: 1.6;
  flex-shrink: 0;
}

.service-card {
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding: 22rpx 24rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, #fff7f7, #ffffff);
  border: 1rpx solid #f5e4e6;
  margin-bottom: 18rpx;
}

.service-icon {
  width: 64rpx;
  height: 64rpx;
  border-radius: 18rpx;
  background: linear-gradient(135deg, #fff1f2, #ffe5e8);
  color: #b30d1f;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
}

.service-copy { flex: 1; }
.service-title {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
  color: #1f2937;
}

.service-desc {
  display: block;
  margin-top: 6rpx;
  font-size: 22rpx;
  color: #8a8f98;
}

.service-arrow {
  color: #c4a4ab;
  font-size: 30rpx;
  font-weight: 700;
}

.info-list {
  padding: 8rpx 0 2rpx;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18rpx;
  padding: 18rpx 0;
  font-size: 26rpx;
  color: #333;
  border-bottom: 1rpx solid #f2ecee;
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  color: #8d8a91;
}

.info-value {
  color: #2a2526;
  font-weight: 600;
  text-align: right;
}

.status-text {
  color: #b30d1f;
}

.fact-row {
  display: flex;
  gap: 18rpx;
  padding: 22rpx 0;
  border-bottom: 1rpx solid #f2ecee;
}

.fact-row:last-child {
  border-bottom: none;
}

.fact-mark {
  width: 10rpx;
  border-radius: 999rpx;
  background: linear-gradient(180deg, #c81f32, #f2b36b);
  flex-shrink: 0;
}

.fact-body {
  flex: 1;
}

.fact-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 10rpx;
}

.fact-type {
  background: #fff1f2;
  color: #b30d1f;
  font-size: 22rpx;
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  font-weight: 700;
}

.fact-date {
  font-size: 22rpx;
  color: #999;
}

.fact-title {
  font-size: 28rpx;
  color: #333;
  display: block;
  font-weight: 700;
  line-height: 1.5;
}

.fact-desc {
  font-size: 24rpx;
  color: #666;
  display: block;
  margin-top: 10rpx;
  line-height: 1.7;
}

.submission-row {
  padding: 22rpx 22rpx 18rpx;
  border-radius: 22rpx;
  background: linear-gradient(180deg, #fffdfd, #fff8f8);
  border: 1rpx solid #f5e6e8;
  margin-bottom: 16rpx;
}

.submission-row:last-child {
  margin-bottom: 0;
}

.submission-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16rpx;
}

.submission-title {
  font-size: 28rpx;
  color: #333;
  font-weight: 700;
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
  color: #8c8f98;
  margin-top: 8rpx;
  line-height: 1.6;
}

.status-chip {
  font-size: 22rpx;
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  flex-shrink: 0;
  font-weight: 700;
  border: 1rpx solid transparent;
}

.status-chip.pending {
  background: #fff7e6;
  color: #d46b08;
  border-color: #ffe1a8;
}

.status-chip.approved {
  background: #edfdf2;
  color: #1b8d4b;
  border-color: #b4ebc8;
}

.status-chip.rejected {
  background: #fff1f0;
  color: #cf1322;
  border-color: #ffc1bc;
}

.empty-inline {
  font-size: 24rpx;
  color: #999;
  padding: 36rpx 24rpx;
  text-align: center;
  border-radius: 22rpx;
  background: #fff8f8;
  border: 1rpx dashed #f0d3d8;
}

.action-list {
  margin-top: 6rpx;
}

.action-btn {
  background: linear-gradient(180deg, #fffdfd, #fff7f8);
  padding: 24rpx;
  border-radius: 24rpx;
  margin-bottom: 14rpx;
  color: #b30d1f;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1rpx solid #f1dfe3;
}

.action-btn.disabled {
  color: #bbb;
  background: #f7f7f7;
  border-color: #ededed;
}

.action-copy {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.action-title {
  font-size: 28rpx;
  font-weight: 700;
  color: inherit;
}

.action-desc {
  font-size: 22rpx;
  color: #9f9094;
  line-height: 1.5;
}

.action-arrow {
  font-size: 30rpx;
  color: #c2a0a8;
}

.action-btn-logout {
  justify-content: center;
  background: #fff6f6;
  border-color: #f3d7dc;
}

.logout-text {
  color: #c11729;
}

.sheet-mask {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: flex-end;
  background: rgba(31, 24, 27, 0.46);
}

.popup-panel {
  width: 100%;
  max-height: 82vh;
  overflow-y: auto;
  background: #fff;
  padding: 20rpx 28rpx calc(32rpx + env(safe-area-inset-bottom));
  border-radius: 34rpx 34rpx 0 0;
}

.popup-handle {
  width: 88rpx;
  height: 8rpx;
  border-radius: 999rpx;
  background: #dfd8d9;
  margin: 8rpx auto 24rpx;
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 22rpx;
}

.popup-title {
  font-size: 34rpx;
  font-weight: 800;
  color: #1f1f1f;
}

.popup-close {
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  background: #f6f2f3;
  color: #6b6365;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  line-height: 1;
}

.popup-alert {
  display: flex;
  align-items: flex-start;
  gap: 14rpx;
  padding: 18rpx 20rpx;
  border-radius: 20rpx;
  background: #fff5f5;
  color: #8a5358;
  margin-bottom: 22rpx;
}

.popup-alert-icon {
  width: 28rpx;
  height: 28rpx;
  border-radius: 50%;
  border: 1rpx solid #e9b6bc;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c11729;
  font-size: 20rpx;
  flex-shrink: 0;
}

.popup-alert-text {
  flex: 1;
  font-size: 22rpx;
  line-height: 1.6;
}

.popup-form {
  border-radius: 26rpx;
  background: #fff;
}

.upload-card {
  display: flex;
  align-items: center;
  gap: 18rpx;
  min-height: 128rpx;
  padding: 22rpx;
  border-radius: 22rpx;
  border: 2rpx dashed #ead1d6;
  background: linear-gradient(135deg, #fffafa, #fff6f7);
  margin-bottom: 18rpx;
}

.upload-icon {
  width: 58rpx;
  height: 58rpx;
  border-radius: 18rpx;
  background: #fff1f2;
  color: #b30d1f;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  font-weight: 800;
  flex-shrink: 0;
}

.upload-copy {
  flex: 1;
  min-width: 0;
}

.upload-title {
  display: block;
  color: #2a2526;
  font-size: 27rpx;
  font-weight: 800;
}

.upload-desc {
  display: block;
  margin-top: 8rpx;
  color: #9f9094;
  font-size: 22rpx;
  line-height: 1.55;
}

.form-item {
  margin-bottom: 18rpx;
}

.label {
  font-size: 24rpx;
  color: #5f5759;
  display: block;
  margin-bottom: 10rpx;
  font-weight: 700;
}

.label.required::before {
  content: '*';
  color: #d62c3d;
  margin-right: 6rpx;
}

.input,
.textarea,
.picker-value {
  background: #fbf8f8;
  border-radius: 18rpx;
  padding: 20rpx 20rpx;
  font-size: 26rpx;
  color: #333;
  border: 1rpx solid #f0e2e5;
  box-sizing: border-box;
}

.textarea {
  min-height: 180rpx;
  width: 100%;
}

.double-row {
  display: flex;
  gap: 16rpx;
}

.half { flex: 1; }

.popup-footer {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 26rpx;
}

.popup-cancel,
.popup-submit {
  height: 88rpx;
  line-height: 88rpx;
  border-radius: 22rpx;
  font-size: 28rpx;
  font-weight: 700;
  padding: 0;
}

.popup-cancel {
  width: 180rpx;
  color: #7a6d71;
  background: #f5f0f1;
}

.popup-submit {
  flex: 1;
  box-shadow: 0 14rpx 28rpx rgba(179, 13, 31, 0.18);
}
</style>
