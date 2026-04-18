<template>
  <div>
    <a-page-header title="个人信息" />

    <a-spin :spinning="loading">
      <a-descriptions v-if="user" :column="2" bordered size="small" class="mb16">
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
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const loading = ref(false)
const user = computed(() => auth.user)
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
</style>
