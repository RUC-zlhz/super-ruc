<template>
  <div class="user-page">
    <a-page-header title="用户管理" sub-title="学生信息与字段权限矩阵" />

    <a-tabs v-model:activeKey="activeTab">
      <a-tab-pane key="students" tab="学生管理">
        <div class="metric-grid">
          <div v-for="metric in metrics" :key="metric.key" class="metric-tile">
            <span class="metric-icon"><component :is="metric.icon" /></span>
            <div class="metric-label">{{ metric.label }}</div>
            <div class="metric-value">{{ metric.value }}</div>
            <div class="metric-sub">{{ metric.sub }}</div>
          </div>
        </div>

        <a-form layout="inline" class="filter-card" @finish="onStudentSearch">
          <a-form-item label="搜索">
            <a-input
              v-model:value="stuFilters.q"
              placeholder="学号 / 姓名"
              allow-clear
              style="width: 200px"
            />
          </a-form-item>
          <a-form-item label="年级">
            <a-input
              v-model:value="stuFilters.grade_code"
              placeholder="年级"
              allow-clear
              style="width: 120px"
            />
          </a-form-item>
          <a-form-item label="专业">
            <a-input
              v-model:value="stuFilters.major_code"
              placeholder="专业"
              allow-clear
              style="width: 120px"
            />
          </a-form-item>
          <a-form-item label="班级">
            <a-input
              v-model:value="stuFilters.class_code"
              placeholder="班级"
              allow-clear
              style="width: 120px"
            />
          </a-form-item>
          <a-form-item>
            <a-button type="primary" html-type="submit">查询</a-button>
          </a-form-item>
          <a-form-item>
            <a-button @click="resetStudentFilters">重置</a-button>
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
              <a-tag :color="enrollmentStatusColor(record.enrollment_status)">
                {{ enrollmentStatusLabel(record.enrollment_status) }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'actions'">
              <a-button
                type="link"
                size="small"
                @click="onViewProfile(record.id)"
                >画像</a-button
              >
              <a-button
                v-if="canEditEnrollment"
                type="link"
                size="small"
                @click="onEditEnrollment(record)"
                >学籍</a-button
              >
            </template>
          </template>
        </a-table>
      </a-tab-pane>

      <a-tab-pane v-if="canViewPolicies" key="roles" tab="角色策略">
        <a-table
          :columns="policyCols"
          :data-source="policies"
          :loading="policyLoading"
          row-key="id"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'can_read'">
              <a-tag :color="record.can_read ? 'green' : 'default'">
                {{ record.can_read ? "允许" : "禁止" }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'can_write'">
              <a-tag :color="record.can_write ? 'blue' : 'default'">
                {{ record.can_write ? "允许" : "禁止" }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'mask_strategy'">
              {{ maskStrategyLabel(record.mask_strategy) }}
            </template>
          </template>
        </a-table>
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
          <a-tag
            :color="enrollmentStatusColor(selectedStudent?.enrollment_status)"
          >
            {{ enrollmentStatusLabel(selectedStudent?.enrollment_status) }}
          </a-tag>
        </a-form-item>
        <a-form-item label="新状态">
          <a-select v-model:value="enrollForm.new_status" style="width: 100%">
            <a-select-option value="ACTIVE">ACTIVE（在读）</a-select-option>
            <a-select-option value="SUSPENDED"
              >SUSPENDED（休学）</a-select-option
            >
            <a-select-option value="TRANSFERRED"
              >TRANSFERRED（转出）</a-select-option
            >
            <a-select-option value="GRADUATED"
              >GRADUATED（毕业）</a-select-option
            >
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
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { message } from "ant-design-vue";
import {
  PauseCircleOutlined,
  TeamOutlined,
  UserDeleteOutlined,
  UserSwitchOutlined,
} from "@ant-design/icons-vue";
import { updateEnrollmentStatus } from "@/api/auth";
import { adminSearchStudents, type StudentBasic } from "@/api/profile";
import { useAuthStore } from "@/store/auth";
import { hasAnyRole } from "@/utils/permission";
import { get } from "@/utils/request";
import type { ApiEnvelope } from "@/utils/request";

const router = useRouter();
const auth = useAuthStore();
const activeTab = ref("students");
const canViewPolicies = computed(() =>
  hasAnyRole(auth.roleCodes, ["SUPER_ADMIN"]),
);
const canEditEnrollment = computed(() =>
  hasAnyRole(auth.roleCodes, ["SUPER_ADMIN", "COLLEGE_LEADER", "COUNSELOR"]),
);

const ENROLLMENT_STATUS_LABELS: Record<string, string> = {
  ACTIVE: "在读",
  SUSPENDED: "休学",
  TRANSFERRED: "转出",
  GRADUATED: "毕业",
  ARCHIVED: "归档",
  IN_SCHOOL: "在校",
  LEAVE: "离校",
};

function enrollmentStatusLabel(status?: string | null) {
  if (!status) return "-";
  return ENROLLMENT_STATUS_LABELS[status] || status;
}

function enrollmentStatusColor(status?: string | null) {
  if (status === "ACTIVE" || status === "IN_SCHOOL") return "green";
  if (status === "SUSPENDED") return "gold";
  if (status === "TRANSFERRED" || status === "LEAVE") return "orange";
  if (status === "GRADUATED") return "blue";
  return "default";
}

// ---------- 学生列表 ----------
const stuCols = [
  { title: "学号", dataIndex: "student_no", key: "student_no", width: 120 },
  { title: "姓名", dataIndex: "full_name", key: "full_name", width: 100 },
  { title: "性别", dataIndex: "gender", key: "gender", width: 60 },
  { title: "年级", dataIndex: "grade_code", key: "grade_code", width: 80 },
  { title: "专业", dataIndex: "major_code", key: "major_code", width: 120 },
  { title: "班级", dataIndex: "class_code", key: "class_code", width: 100 },
  {
    title: "政治面貌",
    dataIndex: "political_status",
    key: "political_status",
    width: 110,
  },
  { title: "学籍状态", key: "enrollment_status", width: 110 },
  { title: "操作", key: "actions", width: 140 },
];
const stuFilters = reactive<{
  q?: string;
  grade_code?: string;
  major_code?: string;
  class_code?: string;
}>({});
const students = ref<StudentBasic[]>([]);
const stuLoading = ref(false);
const stuPagination = reactive({ current: 1, pageSize: 20, total: 0 });
const metrics = computed(() => [
  {
    key: "total",
    label: "总人数",
    value: stuPagination.total || students.value.length,
    sub: "当前筛选结果",
    icon: TeamOutlined,
  },
  {
    key: "active",
    label: "在籍",
    value: students.value.filter((item) =>
      ["ACTIVE", "IN_SCHOOL"].includes(item.enrollment_status || item.status || ""),
    ).length,
    sub: "当前页在读",
    icon: UserSwitchOutlined,
  },
  {
    key: "suspended",
    label: "休学",
    value: students.value.filter((item) => item.enrollment_status === "SUSPENDED").length,
    sub: "当前页休学",
    icon: PauseCircleOutlined,
  },
  {
    key: "graduated",
    label: "毕业/归档",
    value: students.value.filter((item) =>
      ["GRADUATED", "ARCHIVED"].includes(item.enrollment_status || ""),
    ).length,
    sub: "只读治理对象",
    icon: UserDeleteOutlined,
  },
]);

async function reloadStudents() {
  stuLoading.value = true;
  try {
    const resp = await adminSearchStudents({
      q: stuFilters.q,
      grade_code: stuFilters.grade_code,
      major_code: stuFilters.major_code,
      class_code: stuFilters.class_code,
      page: stuPagination.current,
      size: stuPagination.pageSize,
    });
    students.value = resp.data.items;
    stuPagination.total = resp.data.meta.total;
  } finally {
    stuLoading.value = false;
  }
}

function onStudentSearch() {
  stuPagination.current = 1;
  void reloadStudents();
}

function onStuTableChange(p: any) {
  stuPagination.current = p.current;
  stuPagination.pageSize = p.pageSize;
  reloadStudents();
}

function resetStudentFilters() {
  stuFilters.q = undefined;
  stuFilters.grade_code = undefined;
  stuFilters.major_code = undefined;
  stuFilters.class_code = undefined;
  stuPagination.current = 1;
  void reloadStudents();
}

function onViewProfile(studentId: number) {
  router.push(`/profile/student/${studentId}`);
}

// ---------- 学籍变更 ----------
const showEnrollmentModal = ref(false);
const enrollSubmitting = ref(false);
const selectedStudent = ref<StudentBasic | null>(null);
const enrollForm = reactive({ new_status: "ACTIVE", reason: "" });

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
    enrollment_year: stu.enrollment_year ?? null,
    expected_graduation_year: stu.expected_graduation_year ?? null,
    status: stu.status ?? stu.enrollment_status ?? "ACTIVE",
    enrollment_status: stu.enrollment_status ?? stu.status ?? "ACTIVE",
    enrollment_status_reason: stu.enrollment_status_reason ?? null,
    enrollment_status_updated_at: stu.enrollment_status_updated_at ?? null,
  };
  selectedStudent.value = current;
  enrollForm.new_status = current.enrollment_status;
  enrollForm.reason = "";
  showEnrollmentModal.value = true;
}

async function onSubmitEnrollment() {
  if (!selectedStudent.value) return;
  enrollSubmitting.value = true;
  try {
    await updateEnrollmentStatus(selectedStudent.value.id, {
      status: enrollForm.new_status as
        | "ACTIVE"
        | "SUSPENDED"
        | "TRANSFERRED"
        | "GRADUATED"
        | "ARCHIVED",
      reason: enrollForm.reason || undefined,
    });
    message.success("学籍状态更新成功");
    showEnrollmentModal.value = false;
    await reloadStudents();
  } finally {
    enrollSubmitting.value = false;
  }
}

// ---------- 角色策略 ----------
const policyCols = [
  { title: "角色", dataIndex: "role_code", key: "role_code", width: 160 },
  { title: "实体", dataIndex: "entity_code", key: "entity_code", width: 140 },
  { title: "字段", dataIndex: "field_name", key: "field_name", width: 140 },
  { title: "可读", dataIndex: "can_read", key: "can_read", width: 80 },
  { title: "可写", dataIndex: "can_write", key: "can_write", width: 80 },
  {
    title: "脱敏策略",
    dataIndex: "mask_strategy",
    key: "mask_strategy",
    width: 110,
  },
];
interface RoleFieldPolicy {
  id: number;
  role_code: string;
  entity_code: string;
  field_name: string;
  can_read: boolean;
  can_write: boolean;
  mask_strategy?: string | null;
}

const policies = ref<RoleFieldPolicy[]>([]);
const policyLoading = ref(false);
const policyLoaded = ref(false);

function maskStrategyLabel(maskStrategy?: string | null) {
  if (!maskStrategy) return "-";
  if (maskStrategy === "partial") return "部分脱敏";
  if (maskStrategy === "full") return "完全脱敏";
  if (maskStrategy === "none") return "无遮盖";
  return maskStrategy;
}

async function loadPolicies() {
  if (!canViewPolicies.value || policyLoaded.value) return;
  policyLoading.value = true;
  try {
    const resp = await get<ApiEnvelope<RoleFieldPolicy[]>>(
      "/admin/role-policies",
    );
    policies.value = resp.data;
    policyLoaded.value = true;
  } finally {
    policyLoading.value = false;
  }
}

onMounted(() => {
  reloadStudents();
});

watch(activeTab, (tab) => {
  if (tab === "roles") {
    void loadPolicies();
  }
});
</script>

<style scoped></style>
