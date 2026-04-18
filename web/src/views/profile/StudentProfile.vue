<template>
  <div>
    <a-page-header title="学生画像" sub-title="FR-018" @back="$router.back()" />

    <a-spin :spinning="loading">
      <template v-if="profile">
        <!-- 基础信息 -->
        <a-card title="学籍信息" :bordered="false" size="small" class="mb16">
          <a-descriptions :column="3" size="small">
            <a-descriptions-item label="学号">{{ profile.student.student_no }}</a-descriptions-item>
            <a-descriptions-item label="姓名">{{ profile.student.full_name }}</a-descriptions-item>
            <a-descriptions-item label="性别">{{ profile.student.gender || '-' }}</a-descriptions-item>
            <a-descriptions-item label="年级">{{ profile.student.grade_code || '-' }}</a-descriptions-item>
            <a-descriptions-item label="专业">{{ profile.student.major_code || '-' }}</a-descriptions-item>
            <a-descriptions-item label="班级">{{ profile.student.class_code || '-' }}</a-descriptions-item>
            <a-descriptions-item label="政治面貌">{{ profile.student.political_status || '-' }}</a-descriptions-item>
            <a-descriptions-item label="学籍状态">
              <a-tag :color="profile.student.enrollment_status === 'ACTIVE' ? 'green' : 'default'">
                {{ profile.student.enrollment_status }}
              </a-tag>
            </a-descriptions-item>
          </a-descriptions>
        </a-card>

        <!-- 画像事实统计 -->
        <a-row :gutter="16" class="mb16">
          <a-col :span="4" v-for="(count, type) in profile.fact_counts" :key="type">
            <a-card :bordered="false" size="small">
              <a-statistic :title="factTypeLabel(type as string)" :value="count" />
            </a-card>
          </a-col>
          <a-col :span="4">
            <a-card :bordered="false" size="small">
              <a-statistic title="待处理申诉" :value="profile.corrections_pending" />
            </a-card>
          </a-col>
        </a-row>

        <!-- 画像事实列表 -->
        <a-card title="成长事实" :bordered="false" size="small" class="mb16">
          <template #extra>
            <a-button type="primary" size="small" @click="showFactDrawer = true">新增</a-button>
          </template>
          <a-table
            :columns="factCols"
            :data-source="profile.facts"
            row-key="id"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'verified'">
                <a-tag :color="record.verified ? 'green' : 'orange'">
                  {{ record.verified ? '已认证' : '待认证' }}
                </a-tag>
              </template>
              <template v-else-if="column.key === 'actions'">
                <a-popconfirm title="确定删除？" @confirm="onDeleteFact(record.id)">
                  <a-button type="link" size="small" danger>删除</a-button>
                </a-popconfirm>
              </template>
            </template>
          </a-table>
        </a-card>
      </template>
    </a-spin>

    <!-- 新增事实 -->
    <a-drawer :open="showFactDrawer" title="新增成长事实" width="480" @close="showFactDrawer = false">
      <a-form layout="vertical" :model="factForm" @finish="onSubmitFact">
        <a-form-item label="类型" :rules="[{ required: true }]">
          <a-select v-model:value="factForm.fact_type">
            <a-select-option value="RESEARCH">科研</a-select-option>
            <a-select-option value="COMPETITION">竞赛</a-select-option>
            <a-select-option value="PRACTICE">实践</a-select-option>
            <a-select-option value="VOLUNTEER">志愿服务</a-select-option>
            <a-select-option value="LEADERSHIP">学生骨干</a-select-option>
            <a-select-option value="CUSTOM">自定义</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="标题" :rules="[{ required: true }]">
          <a-input v-model:value="factForm.title" />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="factForm.description" :rows="3" />
        </a-form-item>
        <a-form-item label="发生日期">
          <a-date-picker v-model:value="factForm.occurred_at" style="width: 100%" />
        </a-form-item>
        <a-form-item>
          <a-button type="primary" html-type="submit" :loading="factSubmitting">保存</a-button>
        </a-form-item>
      </a-form>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { adminGetProfile, adminAddFact, adminDeleteFact, type ProfileSummary } from '@/api/profile'

const route = useRoute()
const studentId = Number(route.params.studentId)

const profile = ref<ProfileSummary | null>(null)
const loading = ref(false)

const FACT_LABELS: Record<string, string> = {
  RESEARCH: '科研',
  COMPETITION: '竞赛',
  PRACTICE: '实践',
  VOLUNTEER: '志愿服务',
  LEADERSHIP: '学生骨干',
  CUSTOM: '自定义',
}
function factTypeLabel(t: string) { return FACT_LABELS[t] || t }

async function loadProfile() {
  loading.value = true
  try {
    const resp = await adminGetProfile(studentId)
    profile.value = resp.data
  } finally {
    loading.value = false
  }
}

const factCols = [
  { title: '类型', dataIndex: 'fact_type', key: 'fact_type', width: 100, customRender: ({ text }: any) => factTypeLabel(text) },
  { title: '标题', dataIndex: 'title', key: 'title' },
  { title: '发生日期', dataIndex: 'occurred_at', key: 'occurred_at', width: 120 },
  { title: '认证', key: 'verified', width: 90 },
  { title: '操作', key: 'actions', width: 80 },
]

// 新增事实
const showFactDrawer = ref(false)
const factSubmitting = ref(false)
const factForm = reactive({ fact_type: 'RESEARCH', title: '', description: '', occurred_at: null as any })

async function onSubmitFact() {
  factSubmitting.value = true
  try {
    await adminAddFact(studentId, factForm as any)
    message.success('已添加')
    showFactDrawer.value = false
    Object.assign(factForm, { fact_type: 'RESEARCH', title: '', description: '', occurred_at: null })
    loadProfile()
  } finally {
    factSubmitting.value = false
  }
}

async function onDeleteFact(factId: number) {
  await adminDeleteFact(factId)
  message.success('已删除')
  loadProfile()
}

onMounted(loadProfile)
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
</style>
