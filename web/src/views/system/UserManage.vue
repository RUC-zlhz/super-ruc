<template>
  <div>
    <a-page-header title="用户管理" sub-title="FR-012 角色与权限" />

    <a-tabs v-model:activeKey="activeTab">
      <a-tab-pane key="students" tab="学生管理">
        <a-form layout="inline" class="mb16" @finish="reloadStudents">
          <a-form-item label="搜索">
            <a-input v-model:value="stuFilters.q" placeholder="学号 / 姓名" allow-clear style="width: 200px" />
          </a-form-item>
          <a-form-item label="年级">
            <a-input v-model:value="stuFilters.grade_code" placeholder="年级" allow-clear style="width: 120px" />
          </a-form-item>
          <a-form-item label="专业">
            <a-input v-model:value="stuFilters.major_code" placeholder="专业" allow-clear style="width: 120px" />
          </a-form-item>
          <a-form-item>
            <a-button type="primary" html-type="submit">查询</a-button>
          </a-form-item>
        </a-form>
        <a-table
          :columns="stuCols"
          :data-source="students"
          :loading="stuLoading"
          :pagination="stuPagination"
          row-key="id"
          @change="onStuTableChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'enrollment_status'">
              <a-tag :color="record.enrollment_status === 'ACTIVE' ? 'green' : 'default'">
                {{ record.enrollment_status }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'actions'">
              <a-button type="link" size="small" @click="onViewProfile(record.id)">画像</a-button>
              <a-button type="link" size="small" @click="onEditEnrollment(record)">学籍</a-button>
            </template>
          </template>
        </a-table>
      </a-tab-pane>

      <a-tab-pane key="roles" tab="角色策略">
        <a-table
          :columns="policyCols"
          :data-source="policies"
          :loading="policyLoading"
          row-key="id"
          size="small"
        />
      </a-tab-pane>
    </a-tabs>

    <!-- 学籍状态变更 Modal -->
    <a-modal
      v-model:open="showEnrollmentModal"
      title="变更学籍状态"
      @ok="onSubmitEnrollment"
      :confirm-loading="enrollSubmitting"
    >
      <a-form layout="vertical">
        <a-form-item label="学生">
          {{ selectedStudent?.full_name }} ({{ selectedStudent?.student_no }})
        </a-form-item>
        <a-form-item label="当前状态">
          <a-tag>{{ selectedStudent?.enrollment_status }}</a-tag>
        </a-form-item>
        <a-form-item label="新状态">
          <a-select v-model:value="enrollForm.new_status" style="width: 100%">
            <a-select-option value="ACTIVE">ACTIVE（在读）</a-select-option>
            <a-select-option value="SUSPENDED">SUSPENDED（休学）</a-select-option>
            <a-select-option value="TRANSFERRED">TRANSFERRED（转出）</a-select-option>
            <a-select-option value="GRADUATED">GRADUATED（毕业）</a-select-option>
            <a-select-option value="ARCHIVED">ARCHIVED（归档）</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="变更原因">
          <a-textarea v-model:value="enrollForm.reason" :rows="3" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { adminSearchStudents, type StudentBasic } from '@/api/profile'
import { get, post } from '@/utils/request'
import type { ApiEnvelope } from '@/utils/request'

const router = useRouter()
const activeTab = ref('students')

// ---------- 学生列表 ----------
const stuCols = [
  { title: '学号', dataIndex: 'student_no', key: 'student_no', width: 120 },
  { title: '姓名', dataIndex: 'full_name', key: 'full_name', width: 100 },
  { title: '性别', dataIndex: 'gender', key: 'gender', width: 60 },
  { title: '年级', dataIndex: 'grade_code', key: 'grade_code', width: 80 },
  { title: '专业', dataIndex: 'major_code', key: 'major_code', width: 120 },
  { title: '班级', dataIndex: 'class_code', key: 'class_code', width: 100 },
  { title: '政治面貌', dataIndex: 'political_status', key: 'political_status', width: 110 },
  { title: '学籍', key: 'enrollment_status', width: 100 },
  { title: '操作', key: 'actions', width: 140 },
]
const stuFilters = reactive<{ q?: string; grade_code?: string; major_code?: string }>({})
const students = ref<StudentBasic[]>([])
const stuLoading = ref(false)
const stuPagination = reactive({ current: 1, pageSize: 20, total: 0 })

async function reloadStudents() {
  stuLoading.value = true
  try {
    const resp = await adminSearchStudents({
      q: stuFilters.q,
      grade_code: stuFilters.grade_code,
      major_code: stuFilters.major_code,
      page: stuPagination.current,
      size: stuPagination.pageSize,
    })
    students.value = resp.data.items
    stuPagination.total = resp.data.meta.total
  } finally {
    stuLoading.value = false
  }
}

function onStuTableChange(p: any) {
  stuPagination.current = p.current
  stuPagination.pageSize = p.pageSize
  reloadStudents()
}

function onViewProfile(studentId: number) {
  router.push(`/profile/student/${studentId}`)
}

// ---------- 学籍变更 ----------
const showEnrollmentModal = ref(false)
const enrollSubmitting = ref(false)
const selectedStudent = ref<StudentBasic | null>(null)
const enrollForm = reactive({ new_status: 'ACTIVE', reason: '' })

function onEditEnrollment(stu: StudentBasic | Record<string, any>) {
  const current: StudentBasic = {
    id: stu.id,
    student_no: stu.student_no,
    full_name: stu.full_name,
    gender: stu.gender ?? null,
    grade_code: stu.grade_code ?? null,
    major_code: stu.major_code ?? null,
    class_code: stu.class_code ?? null,
    political_status: stu.political_status ?? null,
    enrollment_status: stu.enrollment_status,
  }
  selectedStudent.value = current
  enrollForm.new_status = current.enrollment_status
  enrollForm.reason = ''
  showEnrollmentModal.value = true
}

async function onSubmitEnrollment() {
  if (!selectedStudent.value) return
  enrollSubmitting.value = true
  try {
    await post<ApiEnvelope<any>>(
      `/admin/auth/students/${selectedStudent.value.id}/enrollment-status`,
      enrollForm,
    )
    message.success('学籍状态更新成功')
    showEnrollmentModal.value = false
    reloadStudents()
  } finally {
    enrollSubmitting.value = false
  }
}

// ---------- 角色策略 ----------
const policyCols = [
  { title: '角色', dataIndex: 'role_code', key: 'role_code', width: 160 },
  { title: '实体', dataIndex: 'entity_code', key: 'entity_code', width: 140 },
  { title: '字段', dataIndex: 'field_name', key: 'field_name', width: 140 },
  { title: '可见', dataIndex: 'visible', key: 'visible', width: 80 },
  { title: '可编辑', dataIndex: 'editable', key: 'editable', width: 80 },
  { title: '脱敏', dataIndex: 'mask_type', key: 'mask_type', width: 100 },
]
const policies = ref<any[]>([])
const policyLoading = ref(false)

async function loadPolicies() {
  policyLoading.value = true
  try {
    const resp = await get<ApiEnvelope<any[]>>('/admin/role-policies')
    policies.value = resp.data
  } finally {
    policyLoading.value = false
  }
}

onMounted(() => {
  reloadStudents()
  loadPolicies()
})
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
</style>
