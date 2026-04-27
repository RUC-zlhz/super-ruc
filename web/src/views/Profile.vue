<template>
  <div class="profile-page">
    <a-page-header title="个人信息" sub-title="账号资料、角色范围与安全状态" />

    <a-spin :spinning="loading">
      <template v-if="user">
        <div class="profile-hero">
          <div class="avatar-card">
            <div class="avatar">{{ user.display_name.slice(0, 1) }}</div>
            <div>
              <div class="name-row">
                <h2>{{ user.display_name }}</h2>
                <a-tag color="red">教师管理员</a-tag>
                <a-tag color="green">在职</a-tag>
              </div>
              <div class="hero-meta">工号：{{ user.work_no || '-' }}</div>
              <div class="hero-meta">中国人民大学 · 信息学院</div>
            </div>
          </div>

          <div class="metric-grid hero-metrics">
            <div class="metric-tile compact">
              <span class="metric-icon"><BookOutlined /></span>
              <div class="metric-label">角色数量</div>
              <div class="metric-value">{{ user.roles.length }}</div>
              <div class="metric-sub">当前账号绑定角色</div>
            </div>
            <div class="metric-tile compact">
              <span class="metric-icon"><TeamOutlined /></span>
              <div class="metric-label">作用域</div>
              <div class="metric-value">{{ scopeCount }}</div>
              <div class="metric-sub">班级/学院等权限范围</div>
            </div>
            <div class="metric-tile compact">
              <span class="metric-icon"><MessageOutlined /></span>
              <div class="metric-label">消息提醒</div>
              <div class="metric-value">--</div>
              <div class="metric-sub">以后端消息中心为准</div>
            </div>
          </div>
        </div>

        <a-row :gutter="[18, 18]">
          <a-col :xs="24" :xl="15">
            <a-card title="基础信息" :bordered="false">
              <a-descriptions :column="2" bordered size="small">
                <a-descriptions-item label="姓名">{{ user.display_name }}</a-descriptions-item>
                <a-descriptions-item label="工号">{{ user.work_no || '-' }}</a-descriptions-item>
                <a-descriptions-item label="邮箱">{{ user.email || '-' }}</a-descriptions-item>
                <a-descriptions-item label="学号">{{ user.student_no || '-' }}</a-descriptions-item>
                <a-descriptions-item label="角色" :span="2">
                  <a-tag v-for="r in user.roles" :key="r.code">
                    {{ r.code }}<template v-if="r.scope_code">({{ r.scope_code }})</template>
                  </a-tag>
                </a-descriptions-item>
              </a-descriptions>

              <div class="login-note">
                <ClockCircleOutlined />
                <span>最后登录时间以审计日志为准，敏感操作将被记录。</span>
              </div>
            </a-card>
          </a-col>

          <a-col :xs="24" :xl="9">
            <a-card title="账号与安全" :bordered="false">
              <div class="security-list">
                <div class="security-item">
                  <LockOutlined />
                  <div>
                    <strong>修改密码</strong>
                    <span>定期修改密码可以保障账号安全</span>
                  </div>
                  <a-button>修改</a-button>
                </div>
                <div class="security-item">
                  <MobileOutlined />
                  <div>
                    <strong>绑定手机</strong>
                    <span>用于重要通知与身份校验</span>
                  </div>
                  <a-button>更换</a-button>
                </div>
                <div class="security-item">
                  <SafetyCertificateOutlined />
                  <div>
                    <strong>登录设备</strong>
                    <span>管理曾登录设备，保障账号安全</span>
                  </div>
                  <a-button>管理</a-button>
                </div>
              </div>
              <a-button danger type="primary" block class="logout-btn" @click="logout">
                退出登录
              </a-button>
            </a-card>
          </a-col>
        </a-row>
      </template>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  BookOutlined,
  ClockCircleOutlined,
  LockOutlined,
  MessageOutlined,
  MobileOutlined,
  SafetyCertificateOutlined,
  TeamOutlined,
} from '@ant-design/icons-vue'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const router = useRouter()
const loading = ref(false)
const user = computed(() => auth.user)
const scopeCount = computed(() => new Set(user.value?.roles.map((role) => role.scope_code).filter(Boolean)).size)

function logout() {
  auth.logout()
  router.replace('/login')
}
</script>

<style scoped>
.profile-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(420px, 0.9fr);
  gap: 18px;
  margin-bottom: 18px;
}

.avatar-card {
  display: flex;
  align-items: center;
  gap: 28px;
  min-height: 196px;
  padding: 34px;
  background: #fff;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.avatar {
  display: grid;
  width: 128px;
  height: 128px;
  place-items: center;
  color: #fff;
  background: linear-gradient(145deg, var(--ruc-red), #e75968);
  border-radius: 999px;
  font-size: 54px;
  font-weight: 900;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

h2 {
  margin: 0;
  color: var(--text);
  font-size: 32px;
  font-weight: 900;
}

.hero-meta {
  margin-top: 12px;
  color: var(--text-2);
  font-size: 16px;
}

.hero-metrics {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-bottom: 0;
}

.metric-tile.compact {
  min-height: 128px;
}

.login-note {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 22px;
  padding: 14px 18px;
  color: var(--ruc-red);
  background: var(--danger-soft);
  border-radius: 10px;
}

.security-list {
  display: grid;
  gap: 12px;
}

.security-item {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--line-soft);
  border-radius: 12px;
  background: #fff;
}

.security-item :deep(.anticon) {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  color: var(--ruc-red);
  background: var(--danger-soft);
  border-radius: 999px;
  font-size: 18px;
}

.security-item strong,
.security-item span {
  display: block;
}

.security-item strong {
  color: var(--text);
}

.security-item span {
  margin-top: 4px;
  color: var(--text-3);
  font-size: 12px;
}

.logout-btn {
  margin-top: 18px;
}

@media (max-width: 1180px) {
  .profile-hero {
    grid-template-columns: 1fr;
  }
}
</style>
