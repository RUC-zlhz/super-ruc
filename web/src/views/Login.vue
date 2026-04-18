<template>
  <div class="login-wrap">
    <div class="login-card">
      <div class="title">信息学院综合服务管理台</div>
      <div class="subtitle">请使用教师工号登录</div>
      <a-form
        layout="vertical"
        :model="form"
        @finish="onSubmit"
      >
        <a-form-item
          label="工号"
          name="work_no"
          :rules="[{ required: true, message: '请输入工号' }]"
        >
          <a-input v-model:value="form.work_no" autocomplete="username" />
        </a-form-item>
        <a-form-item
          label="密码"
          name="password"
          :rules="[{ required: true, message: '请输入密码' }]"
        >
          <a-input-password v-model:value="form.password" autocomplete="current-password" />
        </a-form-item>
        <a-form-item>
          <a-button type="primary" html-type="submit" :loading="loading" block>
            登录
          </a-button>
        </a-form-item>
      </a-form>
      <div class="tip">管理台仅供学院教师使用，学生端请使用微信小程序。</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const form = reactive({ work_no: '', password: '' })
const loading = ref(false)

async function onSubmit() {
  loading.value = true
  try {
    await auth.login(form.work_no, form.password)
    message.success('登录成功')
    const redirect = (route.query.redirect as string) || '/dashboard'
    router.replace(redirect)
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.login-wrap {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #7f1722 0%, #a61e2d 60%, #1e293b 120%);
}
.login-card {
  width: 380px;
  padding: 32px 28px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 18px 60px rgba(0, 0, 0, 0.2);
  .title {
    font-size: 20px;
    font-weight: 600;
    color: #7f1722;
    margin-bottom: 4px;
  }
  .subtitle {
    color: rgba(0, 0, 0, 0.55);
    margin-bottom: 24px;
  }
  .tip {
    margin-top: 12px;
    color: rgba(0, 0, 0, 0.45);
    font-size: 12px;
  }
}
</style>
