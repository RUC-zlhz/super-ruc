<template>
  <div class="login-wrap">
    <div class="brand-block">
      <div class="brand-seal">R</div>
      <div>
        <div class="brand-title">信息学院管理后台</div>
        <div class="brand-sub">中国人民大学</div>
      </div>
    </div>

    <div class="login-column">
      <section class="login-card">
        <div class="card-heading">
          <h1>欢迎登录</h1>
          <div class="heading-line">
            <span />
            <p>信息学院管理后台</p>
            <span />
          </div>
        </div>

        <a-form layout="vertical" :model="form" @finish="onSubmit">
          <a-form-item
            name="work_no"
            :rules="[{ required: true, message: '请输入工号' }]"
          >
            <a-input
              v-model:value="form.work_no"
              autocomplete="username"
              placeholder="教师工号"
              size="large"
            >
              <template #prefix><UserOutlined /></template>
            </a-input>
          </a-form-item>

          <a-form-item
            name="password"
            :rules="[{ required: true, message: '请输入密码' }]"
          >
            <a-input-password
              v-model:value="form.password"
              autocomplete="current-password"
              placeholder="密码"
              size="large"
            >
              <template #prefix><LockOutlined /></template>
            </a-input-password>
          </a-form-item>

          <a-form-item>
            <a-button type="primary" html-type="submit" :loading="loading" block size="large">
              登录
            </a-button>
          </a-form-item>
        </a-form>

        <div class="security-tip">
          <SafetyCertificateOutlined />
          <span>安全登录，保护账户信息</span>
        </div>
      </section>

      <div class="login-support">
        <div class="student-tip">
          <MobileOutlined />
          <span>学生端请使用小程序登录访问</span>
        </div>

        <div v-if="showPreviewEntry" class="preview-entry">
          <div class="preview-title">开发预览</div>
          <a-button block @click="openRequirementsPreview">
            直接预览班团骨干权限与请假提示
          </a-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  LockOutlined,
  MobileOutlined,
  SafetyCertificateOutlined,
  UserOutlined,
} from '@ant-design/icons-vue'
import { getDefaultRouteForRoles } from '@/config/navigation'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const form = reactive({ work_no: '', password: '' })
const loading = ref(false)
const showPreviewEntry = import.meta.env.DEV || import.meta.env.VITE_ENABLE_REQUIREMENT_PREVIEW === 'true'

async function onSubmit() {
  loading.value = true
  try {
    await auth.login(form.work_no, form.password)
    message.success('登录成功')
    const redirect = (route.query.redirect as string) || getDefaultRouteForRoles(auth.roleCodes)
    if (auth.user?.must_change_password) {
      Modal.confirm({
        title: '请尽快修改初始密码',
        content: '当前账号仍在使用初始密码 admin123。为避免账号被共用，建议登录后立即修改密码。',
        okText: '立即修改',
        cancelText: '稍后处理',
        async onOk() {
          await router.replace({ path: '/profile', query: { changePassword: '1' } })
        },
        async onCancel() {
          await router.replace(redirect)
        },
      })
      return
    }
    router.replace(redirect)
  } finally {
    loading.value = false
  }
}

function openRequirementsPreview() {
  void router.push('/preview/requirements')
}
</script>

<style lang="scss" scoped>
.login-wrap {
  position: relative;
  display: grid;
  min-height: 100vh;
  place-items: center;
  overflow: hidden;
  background:
    radial-gradient(circle at 86% 12%, rgba(176, 0, 24, 0.05), transparent 20rem),
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(247, 248, 250, 0.96));
}

.login-wrap::before {
  content: "";
  position: absolute;
  left: 5vw;
  bottom: 12vh;
  width: 38vw;
  height: 34vh;
  opacity: 0.12;
  background:
    linear-gradient(180deg, transparent 56%, #4e5969 57% 61%, transparent 62%),
    repeating-linear-gradient(90deg, transparent 0 28px, #4e5969 28px 30px);
  clip-path: polygon(0 74%, 12% 62%, 24% 68%, 34% 48%, 51% 63%, 68% 34%, 100% 68%, 100% 100%, 0 100%);
}

.login-wrap::after {
  content: "";
  position: absolute;
  right: -8vw;
  bottom: -16vh;
  width: 76vw;
  height: 36vh;
  background:
    linear-gradient(160deg, #e51b33, var(--ruc-red) 62%, #9d0014),
    var(--ruc-red);
  border-radius: 55% 0 0 0;
  box-shadow: inset 0 18px 42px rgba(255, 255, 255, 0.12);
}

.brand-block {
  position: absolute;
  left: 60px;
  top: 54px;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 18px;
}

.brand-seal {
  display: grid;
  width: 64px;
  height: 64px;
  place-items: center;
  color: #fff;
  background: var(--ruc-red);
  border: 4px solid #fff;
  border-radius: 999px;
  box-shadow: 0 12px 30px rgba(176, 0, 24, 0.18);
  font-size: 26px;
  font-weight: 900;
}

.brand-title {
  color: var(--text);
  font-size: 34px;
  font-weight: 900;
  letter-spacing: -0.8px;
}

.brand-sub {
  margin-top: 6px;
  color: var(--text-2);
  font-size: 18px;
}

.login-column {
  z-index: 1;
  display: flex;
  flex-direction: column;
  width: min(560px, calc(100vw - 36px));
  gap: 14px;
  transform: translateY(-18px);
}

.login-card {
  width: 100%;
  padding: 56px 56px 42px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(176, 0, 24, 0.16);
  border-radius: 18px;
  box-shadow: 0 26px 70px rgba(31, 35, 41, 0.13);
  backdrop-filter: blur(12px);
}

.card-heading {
  margin-bottom: 34px;
  text-align: center;
}

.card-heading h1 {
  margin: 0;
  color: var(--ruc-red);
  font-size: 34px;
  font-weight: 900;
  letter-spacing: 1px;
}

.heading-line {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 12px;
  color: var(--text-2);
  font-size: 16px;
}

.heading-line p {
  margin: 0;
}

.heading-line span {
  width: 42px;
  height: 1px;
  background: var(--line);
}

.security-tip,
.student-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--text-3);
}

.security-tip {
  margin-top: 8px;
}

.login-support {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 12px;
}

.student-tip {
  align-self: center;
  max-width: 100%;
  padding: 8px 18px;
  color: var(--text-2);
  background: rgba(255, 255, 255, 0.72);
  border-radius: 999px;
  box-shadow: 0 10px 26px rgba(31, 35, 41, 0.08);
  font-size: 16px;
  backdrop-filter: blur(6px);
}

.preview-entry {
  padding: 16px 18px 18px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(176, 0, 24, 0.14);
  border-radius: 16px;
  box-shadow: 0 16px 42px rgba(31, 35, 41, 0.08);
  backdrop-filter: blur(8px);
}

.preview-title {
  margin-bottom: 10px;
  color: var(--text-2);
  font-size: 13px;
  text-align: center;
}

.student-tip :deep(.anticon) {
  color: var(--ruc-red);
}

.preview-entry :deep(.ant-btn) {
  height: 44px;
  border-radius: 10px;
  font-weight: 700;
}

:deep(.ant-input-affix-wrapper-lg) {
  height: 58px;
  padding-inline: 18px;
  border-radius: 10px !important;
}

:deep(.ant-btn-lg) {
  height: 58px;
  margin-top: 4px;
  border-radius: 10px !important;
  font-size: 18px;
  font-weight: 800 !important;
}

@media (max-width: 760px) {
  .brand-block {
    left: 24px;
    top: 28px;
  }

  .brand-title {
    font-size: 24px;
  }

  .brand-sub {
    font-size: 14px;
  }

  .login-column {
    width: calc(100vw - 36px);
    transform: none;
  }

  .login-card {
    padding: 42px 26px 32px;
  }

  .student-tip {
    font-size: 14px;
  }
}
</style>
