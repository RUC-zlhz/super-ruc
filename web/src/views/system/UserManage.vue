<template>
  <div class="user-page" :class="{ 'user-page--with-policy': canViewPolicies }">
    <a-page-header title="用户管理" sub-title="学生信息、后台账号批量创建与字段权限矩阵" />

    <a-tabs v-model:activeKey="activeTab">
      <a-tab-pane v-if="canManageStudents" key="students" tab="学生管理">
        <a-form layout="inline" class="filter-card user-filter">
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
          <a-form-item label="学籍">
            <a-select v-model:value="stuFilters.enrollment_status" allow-clear style="width: 140px">
              <a-select-option value="ACTIVE">在读</a-select-option>
              <a-select-option value="SUSPENDED">休学</a-select-option>
              <a-select-option value="TRANSFERRED">转出</a-select-option>
              <a-select-option value="GRADUATED">毕业</a-select-option>
              <a-select-option value="ARCHIVED">归档</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item>
            <a-checkbox v-model:checked="stuFilters.include_non_active">包含非在读</a-checkbox>
          </a-form-item>
          <a-form-item>
            <a-space wrap>
              <a-button type="primary" @click="onStudentSearch">
                <template #icon><SearchOutlined /></template>
                查询
              </a-button>
              <a-button v-if="canEditStudents" type="primary" @click="openStudentEditor()">
                <template #icon><UserAddOutlined /></template>
                新增学生
              </a-button>
              <a-button @click="resetStudentFilters">
                <template #icon><ReloadOutlined /></template>
                重置
              </a-button>
            </a-space>
          </a-form-item>
        </a-form>

        <div class="metric-grid user-metrics">
          <div v-for="metric in metrics" :key="metric.key" class="metric-tile">
            <span class="metric-icon"><component :is="metric.icon" /></span>
            <div class="metric-label">{{ metric.label }}</div>
            <div class="metric-value">{{ metric.value }}</div>
            <div class="metric-sub">{{ metric.sub }}</div>
          </div>
        </div>

        <div class="user-workspace">
          <section class="user-main">
            <a-table
              :columns="stuCols"
              :data-source="students"
              :loading="stuLoading"
              :pagination="stuPagination"
              row-key="id"
              size="small"
              @change="onStuTableChange"
             :scroll="{ x: 'max-content' }">
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
                    @click="onEditStudent(record)"
                  >
                    <template #icon><EditOutlined /></template>
                    主档
                  </a-button>
                  <a-button
                    type="link"
                    size="small"
                    @click="onOpenWechatBinding(record)"
                  >
                    <template #icon><SyncOutlined /></template>
                    微信
                  </a-button>
                  <a-button
                    type="link"
                    size="small"
                    @click="onViewProfile(record.id)"
                  >
                    <template #icon><IdcardOutlined /></template>
                    画像
                  </a-button>
                  <a-button
                    v-if="canEditEnrollment"
                    type="link"
                    size="small"
                    @click="onEditEnrollment(record)"
                  >
                    <template #icon><EditOutlined /></template>
                    学籍
                  </a-button>
                </template>
              </template>
            </a-table>
          </section>

          <aside v-if="canViewPolicies" class="policy-side-panel">
            <div class="policy-title-row">
              <strong>字段权限矩阵</strong>
              <span>×</span>
            </div>
            <div class="policy-hint">
              设置字段级权限，精细化控制数据的可见与操作范围
            </div>
            <div class="policy-matrix">
              <div class="policy-grid policy-grid-head">
                <span>字段名称</span>
                <span>可见</span>
                <span>可编辑</span>
                <span>仅管理员</span>
                <span>导出权限</span>
              </div>
              <div
                v-for="policy in policyMatrixRows"
                :key="policyRowKey(policy)"
                class="policy-grid"
              >
                <span>{{ policyFieldName(policy) }}</span>
                <a-checkbox :checked="policyCanRead(policy)" disabled />
                <a-checkbox :checked="policyCanWrite(policy)" disabled />
                <a-checkbox :checked="policyAdminOnly(policy)" disabled />
                <a-checkbox :checked="policyCanExport(policy)" disabled />
              </div>
            </div>
            <div class="preset-block">
              <div class="preset-title">预设模板</div>
              <a-select :value="policyPresetName" style="width: 100%" disabled>
                <a-select-option :value="policyPresetName">{{ policyPresetName }}</a-select-option>
              </a-select>
              <div class="preset-actions">
                <a-button size="small" type="primary" @click="refreshPolicies" :loading="policyLoading">
                  <template #icon><ReloadOutlined /></template>
                  刷新策略
                </a-button>
                <a-button size="small" @click="onViewAllPolicies">
                  <template #icon><IdcardOutlined /></template>
                  查看全部
                </a-button>
              </div>
            </div>
          </aside>
        </div>
      </a-tab-pane>

      <a-tab-pane v-if="canImportAdminUsers" key="admin-import" tab="批量创建账号">
        <div class="admin-import-toolbar">
          <a-space wrap>
            <a-button @click="onDownloadAdminTemplate('xlsx')">
              <template #icon><DownloadOutlined /></template>
              下载 XLSX 模板
            </a-button>
            <a-button @click="onDownloadAdminTemplate('csv')">
              <template #icon><DownloadOutlined /></template>
              下载 CSV 模板
            </a-button>
            <a-button @click="openSingleAdminModal">
              <template #icon><UserAddOutlined /></template>
              新增单个账号
            </a-button>
            <a-upload
              :show-upload-list="false"
              accept=".xlsx,.csv"
              :before-upload="beforeAdminImportUpload"
            >
              <a-button type="primary" :loading="adminImportLoading">
                <template #icon><UploadOutlined /></template>
                上传并预检
              </a-button>
            </a-upload>
            <a-button
              type="primary"
              danger
              :disabled="!canCommitAdminImport"
              :loading="adminCommitLoading"
              @click="onCommitAdminImport"
            >
              <template #icon><UserAddOutlined /></template>
              确认导入
            </a-button>
            <a-button
              :disabled="!adminPreview"
              @click="onDownloadCurrentErrorReport"
            >
              <template #icon><FileExcelOutlined /></template>
              下载错误报告
            </a-button>
          </a-space>
        </div>

        <div class="metric-grid user-metrics">
          <div v-for="metric in adminImportMetrics" :key="metric.key" class="metric-tile">
            <span class="metric-icon"><component :is="metric.icon" /></span>
            <div class="metric-label">{{ metric.label }}</div>
            <div class="metric-value">{{ metric.value }}</div>
            <div class="metric-sub">{{ metric.sub }}</div>
          </div>
        </div>

        <a-alert
          v-if="adminCredentials.length"
          class="admin-import-alert"
          type="warning"
          show-icon
          message="初始密码仅本次可见"
          description="请立即下载或复制本次结果；刷新页面后将无法再次获取明文初始密码。"
        />

        <section v-if="adminCredentials.length" class="admin-import-section">
          <div class="section-title-row">
            <strong>本次新账号初始密码</strong>
            <a-button size="small" type="primary" @click="downloadAdminCredentialsExcel">
              <template #icon><FileExcelOutlined /></template>
              下载本次结果
            </a-button>
          </div>
          <a-table
            :columns="adminCredentialCols"
            :data-source="adminCredentials"
            row-key="work_no"
            size="small"
            :pagination="false"
           :scroll="{ x: 'max-content' }" />
        </section>

        <section class="admin-import-section">
          <div class="section-title-row">
            <strong>预检 / 提交行结果</strong>
            <span v-if="adminPreview" class="section-hint">
              批次 {{ adminPreview.batch.batch_no }} · {{ adminPreview.batch.status }}
            </span>
          </div>
          <a-empty v-if="!adminPreview" description="请先上传模板文件进行预检" />
          <a-table
            v-else
            :columns="adminImportRowCols"
            :data-source="adminPreview.rows"
            row-key="id"
            size="small"
            :pagination="{ pageSize: 10 }"
           :scroll="{ x: 'max-content' }">
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'severity'">
                <a-tag :color="adminSeverityColor(record.severity)">
                  {{ record.severity }}
                </a-tag>
              </template>
              <template v-else-if="column.key === 'message'">
                <span>{{ record.message || "-" }}</span>
              </template>
            </template>
          </a-table>
        </section>

        <section class="admin-import-section">
          <div class="section-title-row">
            <strong>历史批次</strong>
            <a-button size="small" @click="reloadAdminImportHistory">
              <template #icon><ReloadOutlined /></template>
              刷新
            </a-button>
          </div>
          <a-table
            :columns="adminImportHistoryCols"
            :data-source="adminImportHistory"
            :loading="adminHistoryLoading"
            :pagination="adminHistoryPagination"
            row-key="id"
            size="small"
            @change="onAdminHistoryTableChange"
           :scroll="{ x: 'max-content' }">
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-tag :color="adminBatchStatusColor(record.status)">
                  {{ record.status }}
                </a-tag>
              </template>
              <template v-else-if="column.key === 'actions'">
                <a-space>
                  <a-button type="link" size="small" @click="onViewAdminImport(record.id)">
                    查看
                  </a-button>
                  <a-button
                    type="link"
                    size="small"
                    @click="downloadAdminUserImportErrorReport(record.id, record.batch_no)"
                  >
                    错误报告
                  </a-button>
                </a-space>
              </template>
            </template>
          </a-table>
        </section>
      </a-tab-pane>

      <a-tab-pane v-if="canViewPolicies" key="roles" tab="角色策略">
        <a-table
          :columns="policyCols"
          :data-source="policies"
          :loading="policyLoading"
          :row-key="policyRowKey"
          size="small"
         :scroll="{ x: 'max-content' }">
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

    <a-modal
      v-model:open="studentEditorOpen"
      :title="studentEditorTitle"
      :confirm-loading="studentEditorSubmitting"
      @ok="onSubmitStudentEditor"
      @cancel="closeStudentEditor"
    >
      <a-form layout="vertical">
        <a-form-item label="学号" required>
          <a-input v-model:value="studentEditorForm.student_no" />
        </a-form-item>
        <a-form-item label="姓名" required>
          <a-input v-model:value="studentEditorForm.full_name" />
        </a-form-item>
        <a-form-item label="性别">
          <a-input v-model:value="studentEditorForm.gender" placeholder="男 / 女" />
        </a-form-item>
        <a-form-item label="年级">
          <a-input v-model:value="studentEditorForm.grade_code" placeholder="如 2024" />
        </a-form-item>
        <a-form-item label="专业">
          <a-input v-model:value="studentEditorForm.major_code" placeholder="专业代码或名称" />
        </a-form-item>
        <a-form-item label="班级">
          <a-input v-model:value="studentEditorForm.class_code" placeholder="如 CS2401" />
        </a-form-item>
        <a-form-item label="政治面貌">
          <a-input v-model:value="studentEditorForm.political_status" />
        </a-form-item>
        <a-form-item label="入学年份">
          <a-input-number
            v-model:value="studentEditorForm.enrollment_year"
            :min="2000"
            :max="2100"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="预计毕业年份">
          <a-input-number
            v-model:value="studentEditorForm.expected_graduation_year"
            :min="2000"
            :max="2100"
            style="width: 100%"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="wechatBindingOpen"
      title="微信登录绑定"
      :confirm-loading="wechatBindingLoading"
      @ok="closeWechatBinding"
      @cancel="closeWechatBinding"
    >
      <a-spin :spinning="wechatBindingLoading">
        <a-descriptions :column="1" size="small" bordered>
          <a-descriptions-item label="学生">
            {{ wechatBindingStudent?.full_name }} ({{ wechatBindingStudent?.student_no }})
          </a-descriptions-item>
          <a-descriptions-item label="绑定状态">
            <a-tag :color="wechatBinding?.bound ? 'green' : 'default'">
              {{ wechatBinding?.bound ? '已绑定' : '未绑定' }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item v-if="wechatBinding?.bound" label="账号 ID">
            {{ wechatBinding.user_id }}
          </a-descriptions-item>
          <a-descriptions-item v-if="wechatBinding?.bound" label="账号名称">
            {{ wechatBinding.display_name || '-' }}
          </a-descriptions-item>
          <a-descriptions-item v-if="wechatBinding?.bound" label="OpenID">
            {{ wechatBinding.openid_masked || '-' }}
          </a-descriptions-item>
          <a-descriptions-item v-if="wechatBinding?.bound" label="UnionID">
            {{ wechatBinding.unionid_masked || '-' }}
          </a-descriptions-item>
          <a-descriptions-item v-if="wechatBinding?.bound" label="最近登录">
            {{ wechatBinding.last_login_at || '-' }}
          </a-descriptions-item>
          <a-descriptions-item v-if="wechatBinding?.bound" label="角色">
            {{ wechatBinding.roles.join(', ') || '-' }}
          </a-descriptions-item>
        </a-descriptions>
        <div v-if="wechatBinding?.bound" class="wechat-actions">
          <a-button danger :loading="wechatUnbinding" @click="onUnbindWechat">
            解绑微信
          </a-button>
        </div>
      </a-spin>
    </a-modal>

    <a-modal
      v-model:open="singleAdminModalOpen"
      title="新增后台账号"
      :confirm-loading="singleAdminSubmitting"
      @ok="onSubmitSingleAdmin"
      @cancel="closeSingleAdminModal"
    >
      <a-form layout="vertical">
        <a-form-item label="工号" required>
          <a-input v-model:value="singleAdminForm.work_no" placeholder="如 T2026001" />
        </a-form-item>
        <a-form-item label="姓名" required>
          <a-input v-model:value="singleAdminForm.display_name" />
        </a-form-item>
        <a-form-item label="邮箱">
          <a-input v-model:value="singleAdminForm.email" />
        </a-form-item>
        <a-form-item label="角色" required>
          <a-select v-model:value="singleAdminForm.role_code">
            <a-select-option
              v-for="option in singleAdminRoleOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="范围类型">
          <a-select v-model:value="singleAdminForm.scope_type">
            <a-select-option value="GLOBAL">GLOBAL（全局）</a-select-option>
            <a-select-option value="GRADE">GRADE（年级）</a-select-option>
            <a-select-option value="MAJOR">MAJOR（专业）</a-select-option>
            <a-select-option value="CLASS">CLASS（班级）</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="范围编码">
          <a-input
            v-model:value="singleAdminForm.scope_code"
            :disabled="singleAdminForm.scope_type === 'GLOBAL'"
            placeholder="如 2024 / 信息安全 / CS2401"
          />
        </a-form-item>
        <a-form-item label="状态">
          <a-switch v-model:checked="singleAdminForm.is_active" checked-children="启用" un-checked-children="停用" />
        </a-form-item>
        <a-alert
          type="info"
          show-icon
          message="该操作复用批量创建账号的预检与提交流程，初始密码只在提交结果中显示一次。"
        />
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { message, Modal } from "ant-design-vue";
import {
  CheckCircleOutlined,
  DownloadOutlined,
  ExclamationCircleOutlined,
  FileExcelOutlined,
  PauseCircleOutlined,
  TeamOutlined,
  UserDeleteOutlined,
  UserAddOutlined,
  UserSwitchOutlined,
  IdcardOutlined,
  SearchOutlined,
  SyncOutlined,
  ReloadOutlined,
  EditOutlined,
  UploadOutlined,
} from "@ant-design/icons-vue";
import {
  commitAdminUserImport,
  downloadAdminUserImportErrorReport,
  downloadAdminUserImportTemplate,
  getAdminUserImport,
  listAdminUserImports,
  previewAdminUserImport,
  type AdminUserCredential,
  type AdminUserImportBatch,
  type AdminUserImportPreviewResult,
} from "@/api/adminUsers";
import { updateEnrollmentStatus } from "@/api/auth";
import {
  adminCreateStudent,
  adminGetStudentWechatBinding,
  adminSearchStudents,
  adminUnbindStudentWechat,
  adminUpdateStudentAcademicInfo,
  type StudentBasic,
  type StudentWechatBinding,
} from "@/api/profile";
import { useAuthStore } from "@/store/auth";
import { ADMIN_USER_IMPORT_ROLES, CURRICULUM_ADMIN_ROLES, hasAnyRole } from "@/utils/permission";
import { get } from "@/utils/request";
import type { ApiEnvelope } from "@/utils/request";

const router = useRouter();
const auth = useAuthStore();
const activeTab = ref("students");
const canManageStudents = computed(() =>
  hasAnyRole(auth.roleCodes, CURRICULUM_ADMIN_ROLES),
);
const canImportAdminUsers = computed(() =>
  hasAnyRole(auth.roleCodes, ADMIN_USER_IMPORT_ROLES),
);
const canViewPolicies = computed(() =>
  hasAnyRole(auth.roleCodes, ["SUPER_ADMIN"]),
);
const canEditEnrollment = computed(() =>
  hasAnyRole(auth.roleCodes, ["SUPER_ADMIN", "COLLEGE_LEADER", "COUNSELOR"]),
);
const canEditStudents = computed(() =>
  hasAnyRole(auth.roleCodes, ["SUPER_ADMIN", "COLLEGE_LEADER", "COUNSELOR", "HEAD_TEACHER"]),
);

const ROLE_LABELS: Record<string, string> = {
  COLLEGE_LEADER: "学院领导",
  COUNSELOR: "辅导员",
  HEAD_TEACHER: "班主任",
  YOUTH_LEAGUE_TEACHER: "团委老师",
  PARTY_BUILD_TEACHER: "党建老师",
  PARTY_BRANCH_SECRETARY: "党支部书记",
  YOUTH_LEAGUE_SECRETARY: "团支书",
  CLASS_MONITOR: "班长",
  YOUTH_BRANCH_SECRETARY: "团支部书记",
  CLASS_LEADER: "班委",
};

const L3_ROLE_CODES = [
  "COUNSELOR",
  "HEAD_TEACHER",
  "YOUTH_LEAGUE_TEACHER",
  "PARTY_BUILD_TEACHER",
];
const L4_ROLE_CODES = [
  "PARTY_BRANCH_SECRETARY",
  "YOUTH_LEAGUE_SECRETARY",
  "CLASS_MONITOR",
  "YOUTH_BRANCH_SECRETARY",
  "CLASS_LEADER",
];

const singleAdminRoleOptions = computed(() => {
  let roleCodes: string[] = [];
  if (auth.roleCodes.includes("SUPER_ADMIN")) {
    roleCodes = ["COLLEGE_LEADER", ...L3_ROLE_CODES, ...L4_ROLE_CODES];
  } else if (auth.roleCodes.includes("COLLEGE_LEADER")) {
    roleCodes = [...L3_ROLE_CODES, ...L4_ROLE_CODES];
  } else if (auth.roleCodes.some((role) => L3_ROLE_CODES.includes(role))) {
    roleCodes = [...L4_ROLE_CODES];
  }
  return roleCodes.map((value) => ({ value, label: `${value}（${ROLE_LABELS[value] || value}）` }));
});

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
  { title: "操作", key: "actions", width: 250 },
];
const stuFilters = reactive<{
  q?: string;
  grade_code?: string;
  major_code?: string;
  class_code?: string;
  include_non_active?: boolean;
  enrollment_status?: string;
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
  if (!canManageStudents.value) return;
  stuLoading.value = true;
  try {
    const resp = await adminSearchStudents({
      q: stuFilters.q,
      grade_code: stuFilters.grade_code,
      major_code: stuFilters.major_code,
      class_code: stuFilters.class_code,
      include_non_active: stuFilters.include_non_active,
      enrollment_status: stuFilters.enrollment_status,
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
  stuFilters.include_non_active = false;
  stuFilters.enrollment_status = undefined;
  stuPagination.current = 1;
  void reloadStudents();
}

function onViewProfile(studentId: number) {
  router.push(`/profile/student/${studentId}`);
}

function toStudentBasic(stu: StudentBasic | Record<string, any>): StudentBasic {
  return {
    id: Number(stu.id),
    student_no: String(stu.student_no || ""),
    full_name: String(stu.full_name || ""),
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
}

// ---------- 学生主档新增 / 修改 ----------
const studentEditorOpen = ref(false);
const studentEditorSubmitting = ref(false);
const editingStudent = ref<StudentBasic | null>(null);
const studentEditorForm = reactive<{
  student_no: string;
  full_name: string;
  gender: string;
  grade_code: string;
  major_code: string;
  class_code: string;
  political_status: string;
  enrollment_year: number | undefined;
  expected_graduation_year: number | undefined;
}>({
  student_no: "",
  full_name: "",
  gender: "",
  grade_code: "",
  major_code: "",
  class_code: "",
  political_status: "",
  enrollment_year: undefined,
  expected_graduation_year: undefined,
});
const studentEditorTitle = computed(() => (editingStudent.value ? "修改学生主档" : "新增学生"));

function normalizeOptionalText(value: string) {
  const trimmed = value.trim();
  return trimmed || null;
}

function resetStudentEditorForm(stu?: StudentBasic | null) {
  studentEditorForm.student_no = stu?.student_no || "";
  studentEditorForm.full_name = stu?.full_name || "";
  studentEditorForm.gender = stu?.gender || "";
  studentEditorForm.grade_code = stu?.grade_code || "";
  studentEditorForm.major_code = stu?.major_code || "";
  studentEditorForm.class_code = stu?.class_code || "";
  studentEditorForm.political_status = stu?.political_status || "";
  studentEditorForm.enrollment_year = stu?.enrollment_year ?? undefined;
  studentEditorForm.expected_graduation_year = stu?.expected_graduation_year ?? undefined;
}

function openStudentEditor(stu?: StudentBasic) {
  editingStudent.value = stu || null;
  resetStudentEditorForm(stu || null);
  studentEditorOpen.value = true;
}

function closeStudentEditor() {
  studentEditorOpen.value = false;
}

function onEditStudent(stu: StudentBasic | Record<string, any>) {
  openStudentEditor(toStudentBasic(stu));
}

async function onSubmitStudentEditor() {
  const studentNo = studentEditorForm.student_no.trim();
  const fullName = studentEditorForm.full_name.trim();
  if (!studentNo || !fullName) {
    message.warning("请填写学号和姓名");
    return;
  }
  const payload = {
    student_no: studentNo,
    full_name: fullName,
    gender: normalizeOptionalText(studentEditorForm.gender),
    grade_code: normalizeOptionalText(studentEditorForm.grade_code),
    major_code: normalizeOptionalText(studentEditorForm.major_code),
    class_code: normalizeOptionalText(studentEditorForm.class_code),
    political_status: normalizeOptionalText(studentEditorForm.political_status),
    enrollment_year: studentEditorForm.enrollment_year ?? null,
    expected_graduation_year: studentEditorForm.expected_graduation_year ?? null,
  };
  studentEditorSubmitting.value = true;
  try {
    if (editingStudent.value) {
      await adminUpdateStudentAcademicInfo(editingStudent.value.id, payload);
      message.success("学生主档已更新");
    } else {
      await adminCreateStudent(payload);
      message.success("学生已新增");
    }
    closeStudentEditor();
    await reloadStudents();
  } finally {
    studentEditorSubmitting.value = false;
  }
}

// ---------- 微信登录绑定 ----------
const wechatBindingOpen = ref(false);
const wechatBindingLoading = ref(false);
const wechatUnbinding = ref(false);
const wechatBindingStudent = ref<StudentBasic | null>(null);
const wechatBinding = ref<StudentWechatBinding | null>(null);

async function loadWechatBinding(studentId: number) {
  wechatBindingLoading.value = true;
  try {
    const resp = await adminGetStudentWechatBinding(studentId);
    wechatBinding.value = resp.data;
  } finally {
    wechatBindingLoading.value = false;
  }
}

function onOpenWechatBinding(stu: StudentBasic | Record<string, any>) {
  wechatBindingStudent.value = toStudentBasic(stu);
  wechatBinding.value = null;
  wechatBindingOpen.value = true;
  void loadWechatBinding(wechatBindingStudent.value.id);
}

function closeWechatBinding() {
  wechatBindingOpen.value = false;
}

function onUnbindWechat() {
  if (!wechatBindingStudent.value || !wechatBinding.value?.bound) return;
  const student = wechatBindingStudent.value;
  Modal.confirm({
    title: "解绑微信登录绑定",
    content: `确认解绑 ${student.full_name} (${student.student_no}) 的微信登录绑定？`,
    okText: "解绑",
    okType: "danger",
    cancelText: "取消",
    async onOk() {
      wechatUnbinding.value = true;
      try {
        const resp = await adminUnbindStudentWechat(student.id);
        wechatBinding.value = resp.data;
        message.success("微信绑定已解绑");
      } finally {
        wechatUnbinding.value = false;
      }
    },
  });
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

// ---------- 后台账号批量创建 ----------
const adminPreview = ref<AdminUserImportPreviewResult | null>(null);
const adminCredentials = ref<AdminUserCredential[]>([]);
const adminImportLoading = ref(false);
const adminCommitLoading = ref(false);
const adminHistoryLoading = ref(false);
const adminImportHistory = ref<AdminUserImportBatch[]>([]);
const adminHistoryPagination = reactive({ current: 1, pageSize: 10, total: 0 });
const singleAdminModalOpen = ref(false);
const singleAdminSubmitting = ref(false);
const singleAdminForm = reactive({
  work_no: "",
  display_name: "",
  email: "",
  role_code: "",
  scope_type: "GLOBAL",
  scope_code: "",
  is_active: true,
});

const adminImportMetrics = computed(() => {
  const batch = adminPreview.value?.batch;
  return [
    {
      key: "total",
      label: "预检行数",
      value: batch?.total_rows ?? 0,
      sub: batch ? `批次 ${batch.batch_no}` : "等待上传",
      icon: FileExcelOutlined,
    },
    {
      key: "fatal",
      label: "致命错误",
      value: batch?.fatal_rows ?? 0,
      sub: "为 0 才允许提交",
      icon: ExclamationCircleOutlined,
    },
    {
      key: "warn",
      label: "警告",
      value: batch?.warn_rows ?? 0,
      sub: "通常为幂等账号",
      icon: SyncOutlined,
    },
    {
      key: "created",
      label: "已创建",
      value: batch?.created_rows ?? 0,
      sub: "提交后统计",
      icon: CheckCircleOutlined,
    },
  ];
});

const canCommitAdminImport = computed(() => {
  const batch = adminPreview.value?.batch;
  return Boolean(batch && batch.status === "VALIDATED" && batch.fatal_rows === 0);
});

const adminImportRowCols = [
  { title: "行号", dataIndex: "row_no", key: "row_no", width: 80 },
  { title: "工号", dataIndex: "work_no", key: "work_no", width: 120 },
  { title: "角色", dataIndex: "role_code", key: "role_code", width: 160 },
  { title: "范围", dataIndex: "scope_code", key: "scope_code", width: 150 },
  { title: "级别", dataIndex: "severity", key: "severity", width: 90 },
  { title: "结果", dataIndex: "result", key: "result", width: 130 },
  { title: "字段", dataIndex: "field_name", key: "field_name", width: 110 },
  { title: "说明", dataIndex: "message", key: "message" },
];

const adminCredentialCols = [
  { title: "工号", dataIndex: "work_no", key: "work_no", width: 120 },
  { title: "姓名", dataIndex: "display_name", key: "display_name", width: 120 },
  { title: "角色", dataIndex: "role_code", key: "role_code", width: 180 },
  { title: "范围", dataIndex: "scope_code", key: "scope_code", width: 160 },
  { title: "初始密码", dataIndex: "initial_password", key: "initial_password", width: 180 },
];

const adminImportHistoryCols = [
  { title: "批次", dataIndex: "batch_no", key: "batch_no", width: 190 },
  { title: "文件", dataIndex: "filename", key: "filename", width: 180 },
  { title: "状态", dataIndex: "status", key: "status", width: 110 },
  { title: "行数", dataIndex: "total_rows", key: "total_rows", width: 90 },
  { title: "错误", dataIndex: "fatal_rows", key: "fatal_rows", width: 90 },
  { title: "新建", dataIndex: "created_rows", key: "created_rows", width: 90 },
  { title: "已存在", dataIndex: "existing_rows", key: "existing_rows", width: 90 },
  { title: "操作", key: "actions", width: 150 },
];

function adminSeverityColor(severity: string) {
  if (severity === "FATAL") return "red";
  if (severity === "WARN") return "gold";
  return "green";
}

function adminBatchStatusColor(status: string) {
  if (status === "COMMITTED") return "green";
  if (status === "FAILED") return "red";
  if (status === "VALIDATED") return "blue";
  return "default";
}

function resetSingleAdminForm() {
  singleAdminForm.work_no = "";
  singleAdminForm.display_name = "";
  singleAdminForm.email = "";
  singleAdminForm.role_code = singleAdminRoleOptions.value[0]?.value || "";
  singleAdminForm.scope_type = "GLOBAL";
  singleAdminForm.scope_code = "";
  singleAdminForm.is_active = true;
}

function openSingleAdminModal() {
  resetSingleAdminForm();
  singleAdminModalOpen.value = true;
}

function closeSingleAdminModal() {
  singleAdminModalOpen.value = false;
}

function csvCell(value: unknown) {
  const text = String(value ?? "");
  return `"${text.replace(/"/g, '""')}"`;
}

function buildSingleAdminCsv() {
  const scopeType = singleAdminForm.scope_type;
  const scopeCode = scopeType === "GLOBAL" ? "" : singleAdminForm.scope_code.trim();
  const rows = [
    ["work_no", "display_name", "email", "role_code", "scope_type", "scope_code", "is_active"],
    [
      singleAdminForm.work_no.trim(),
      singleAdminForm.display_name.trim(),
      singleAdminForm.email.trim(),
      singleAdminForm.role_code,
      scopeType,
      scopeCode,
      singleAdminForm.is_active ? "true" : "false",
    ],
  ];
  return `\ufeff${rows.map((row) => row.map(csvCell).join(",")).join("\n")}\n`;
}

async function onSubmitSingleAdmin() {
  if (!singleAdminForm.work_no.trim() || !singleAdminForm.display_name.trim() || !singleAdminForm.role_code) {
    message.warning("请填写工号、姓名和角色");
    return;
  }
  if (singleAdminForm.scope_type !== "GLOBAL" && !singleAdminForm.scope_code.trim()) {
    message.warning("非 GLOBAL 范围必须填写范围编码");
    return;
  }
  singleAdminSubmitting.value = true;
  adminCredentials.value = [];
  try {
    const file = new File([buildSingleAdminCsv()], "single-admin-user.csv", {
      type: "text/csv;charset=utf-8",
    });
    const preview = await previewAdminUserImport(file);
    adminPreview.value = preview.data;
    activeTab.value = "admin-import";
    if (preview.data.batch.fatal_rows > 0) {
      message.warning("预检失败，请查看下方错误行或下载错误报告");
      return;
    }
    const committed = await commitAdminUserImport(preview.data.batch.id);
    adminPreview.value = { batch: committed.data.batch, rows: committed.data.rows };
    adminCredentials.value = committed.data.credentials;
    message.success("账号已创建，初始密码只在本次结果中显示");
    closeSingleAdminModal();
    await reloadAdminImportHistory();
  } finally {
    singleAdminSubmitting.value = false;
  }
}

async function onDownloadAdminTemplate(format: "xlsx" | "csv") {
  await downloadAdminUserImportTemplate(format);
}

function beforeAdminImportUpload(file: File) {
  void onPreviewAdminImport(file);
  return false;
}

async function onPreviewAdminImport(file: File) {
  adminImportLoading.value = true;
  adminCredentials.value = [];
  try {
    const resp = await previewAdminUserImport(file);
    adminPreview.value = resp.data;
    if (resp.data.batch.fatal_rows > 0) {
      message.warning("预检完成，存在致命错误，请下载错误报告修正后重传");
    } else {
      message.success("预检通过，可以确认导入");
    }
    await reloadAdminImportHistory();
  } finally {
    adminImportLoading.value = false;
  }
}

async function onCommitAdminImport() {
  const batch = adminPreview.value?.batch;
  if (!batch) return;
  adminCommitLoading.value = true;
  try {
    const resp = await commitAdminUserImport(batch.id);
    adminPreview.value = { batch: resp.data.batch, rows: resp.data.rows };
    adminCredentials.value = resp.data.credentials;
    message.success(`导入完成，新建 ${resp.data.credentials.length} 个账号`);
    await reloadAdminImportHistory();
  } finally {
    adminCommitLoading.value = false;
  }
}

async function reloadAdminImportHistory() {
  if (!canImportAdminUsers.value) return;
  adminHistoryLoading.value = true;
  try {
    const resp = await listAdminUserImports({
      page: adminHistoryPagination.current,
      size: adminHistoryPagination.pageSize,
    });
    adminImportHistory.value = resp.data.items;
    adminHistoryPagination.total = resp.data.meta.total;
  } finally {
    adminHistoryLoading.value = false;
  }
}

function onAdminHistoryTableChange(p: any) {
  adminHistoryPagination.current = p.current;
  adminHistoryPagination.pageSize = p.pageSize;
  void reloadAdminImportHistory();
}

async function onViewAdminImport(batchId: number) {
  const resp = await getAdminUserImport(batchId);
  adminPreview.value = resp.data;
  adminCredentials.value = [];
  activeTab.value = "admin-import";
}

async function onDownloadCurrentErrorReport() {
  const batch = adminPreview.value?.batch;
  if (!batch) return;
  await downloadAdminUserImportErrorReport(batch.id, batch.batch_no);
}

function downloadAdminCredentialsExcel() {
  if (!adminCredentials.value.length) return;
  const batchNo = adminPreview.value?.batch.batch_no || "current";
  const rows = [
    ["work_no", "display_name", "role_code", "scope_code", "initial_password"],
    ...adminCredentials.value.map((item) => [
      item.work_no,
      item.display_name,
      item.role_code,
      item.scope_code || "",
      item.initial_password,
    ]),
  ];
  const xlsxData = buildXlsx(rows);
  const xlsxBuffer = xlsxData.buffer.slice(
    xlsxData.byteOffset,
    xlsxData.byteOffset + xlsxData.byteLength,
  ) as ArrayBuffer;
  const blob = new Blob([xlsxBuffer], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `admin-user-initial-passwords-${batchNo}.xlsx`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function buildXlsx(rows: string[][]): Uint8Array {
  const sheetXml = buildWorksheetXml(rows);
  return buildZip([
    {
      name: "[Content_Types].xml",
      text: `<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>`,
    },
    {
      name: "_rels/.rels",
      text: `<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>`,
    },
    {
      name: "xl/workbook.xml",
      text: `<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="credentials" sheetId="1" r:id="rId1"/></sheets>
</workbook>`,
    },
    {
      name: "xl/_rels/workbook.xml.rels",
      text: `<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>`,
    },
    { name: "xl/worksheets/sheet1.xml", text: sheetXml },
  ]);
}

function buildWorksheetXml(rows: string[][]) {
  const body = rows
    .map((row, rowIndex) => {
      const rowNo = rowIndex + 1;
      const cells = row
        .map((value, colIndex) => {
          const ref = `${xlsxColumnName(colIndex)}${rowNo}`;
          return `<c r="${ref}" t="inlineStr"><is><t>${escapeXml(value)}</t></is></c>`;
        })
        .join("");
      return `<row r="${rowNo}">${cells}</row>`;
    })
    .join("");
  const lastCell = `${xlsxColumnName(Math.max(rows[0]?.length || 1, 1) - 1)}${Math.max(rows.length, 1)}`;
  return `<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <dimension ref="A1:${lastCell}"/>
  <sheetData>${body}</sheetData>
</worksheet>`;
}

function xlsxColumnName(index: number) {
  let name = "";
  let value = index + 1;
  while (value > 0) {
    const mod = (value - 1) % 26;
    name = String.fromCharCode(65 + mod) + name;
    value = Math.floor((value - mod) / 26);
  }
  return name;
}

function escapeXml(value: unknown) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function buildZip(files: Array<{ name: string; text: string }>): Uint8Array {
  const encoder = new TextEncoder();
  const localParts: Uint8Array[] = [];
  const centralParts: Uint8Array[] = [];
  let offset = 0;
  const { time, date } = zipDosDateTime(new Date());
  for (const file of files) {
    const nameBytes = encoder.encode(file.name);
    const data = encoder.encode(file.text);
    const crc = crc32(data);
    const local = new Uint8Array(30 + nameBytes.length);
    const localView = new DataView(local.buffer);
    localView.setUint32(0, 0x04034b50, true);
    localView.setUint16(4, 20, true);
    localView.setUint16(8, 0, true);
    localView.setUint16(10, time, true);
    localView.setUint16(12, date, true);
    localView.setUint32(14, crc, true);
    localView.setUint32(18, data.length, true);
    localView.setUint32(22, data.length, true);
    localView.setUint16(26, nameBytes.length, true);
    local.set(nameBytes, 30);
    localParts.push(local, data);

    const central = new Uint8Array(46 + nameBytes.length);
    const centralView = new DataView(central.buffer);
    centralView.setUint32(0, 0x02014b50, true);
    centralView.setUint16(4, 20, true);
    centralView.setUint16(6, 20, true);
    centralView.setUint16(10, 0, true);
    centralView.setUint16(12, time, true);
    centralView.setUint16(14, date, true);
    centralView.setUint32(16, crc, true);
    centralView.setUint32(20, data.length, true);
    centralView.setUint32(24, data.length, true);
    centralView.setUint16(28, nameBytes.length, true);
    centralView.setUint32(42, offset, true);
    central.set(nameBytes, 46);
    centralParts.push(central);
    offset += local.length + data.length;
  }
  const centralOffset = offset;
  const centralSize = centralParts.reduce((sum, item) => sum + item.length, 0);
  const end = new Uint8Array(22);
  const endView = new DataView(end.buffer);
  endView.setUint32(0, 0x06054b50, true);
  endView.setUint16(8, files.length, true);
  endView.setUint16(10, files.length, true);
  endView.setUint32(12, centralSize, true);
  endView.setUint32(16, centralOffset, true);
  return concatUint8Arrays([...localParts, ...centralParts, end]);
}

function zipDosDateTime(value: Date) {
  const year = Math.max(value.getFullYear(), 1980);
  return {
    time: (value.getHours() << 11) | (value.getMinutes() << 5) | Math.floor(value.getSeconds() / 2),
    date: ((year - 1980) << 9) | ((value.getMonth() + 1) << 5) | value.getDate(),
  };
}

function concatUint8Arrays(parts: Uint8Array[]) {
  const total = parts.reduce((sum, item) => sum + item.length, 0);
  const out = new Uint8Array(total);
  let offset = 0;
  for (const part of parts) {
    out.set(part, offset);
    offset += part.length;
  }
  return out;
}

function crc32(data: Uint8Array) {
  let crc = 0xffffffff;
  for (const byte of data) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit += 1) {
      crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
    }
  }
  return (crc ^ 0xffffffff) >>> 0;
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
  id?: number;
  role_code?: string;
  entity_code?: string;
  field_name?: string;
  field?: string;
  action?: string;
  effect?: string;
  can_read?: boolean;
  can_write?: boolean;
  can_export?: boolean;
  mask_strategy?: string | null;
}

const policies = ref<RoleFieldPolicy[]>([]);
const policyLoading = ref(false);
const policyLoaded = ref(false);
const policyMatrixRows = computed(() => policies.value.slice(0, 6));
const policyPresetName = computed(() =>
  policyLoaded.value ? "学生信息管理（标准）" : "权限策略加载中",
);

function policyRowKey(record: RoleFieldPolicy) {
  return (
    record.id ??
    `${record.role_code || "role"}-${record.entity_code || "entity"}-${policyFieldName(record)}-${record.action || "policy"}`
  );
}

function policyFieldName(record: RoleFieldPolicy) {
  return record.field_name || record.field || "-";
}

function policyCanRead(record: RoleFieldPolicy) {
  if (typeof record.can_read === "boolean") return record.can_read;
  if (record.action === "READ") return record.effect !== "DENY";
  return record.effect === "ALLOW";
}

function policyCanWrite(record: RoleFieldPolicy) {
  if (typeof record.can_write === "boolean") return record.can_write;
  if (record.action === "WRITE") return record.effect === "ALLOW";
  return false;
}

function policyAdminOnly(record: RoleFieldPolicy) {
  return record.role_code === "SUPER_ADMIN" && !policyCanWrite(record);
}

function policyCanExport(record: RoleFieldPolicy) {
  if (typeof record.can_export === "boolean") return record.can_export;
  return record.role_code === "SUPER_ADMIN" && policyCanRead(record);
}

function maskStrategyLabel(maskStrategy?: string | null) {
  if (!maskStrategy) return "-";
  if (maskStrategy === "partial") return "部分脱敏";
  if (maskStrategy === "full") return "完全脱敏";
  if (maskStrategy === "none") return "无遮盖";
  return maskStrategy;
}

async function loadPolicies(force = false) {
  if (!canViewPolicies.value || (!force && policyLoaded.value)) return;
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

function refreshPolicies() {
  void loadPolicies(true);
}

function onViewAllPolicies() {
  activeTab.value = "roles";
  void loadPolicies();
}

onMounted(() => {
  if (!canManageStudents.value && canImportAdminUsers.value) {
    activeTab.value = "admin-import";
  }
  void reloadStudents();
  void reloadAdminImportHistory();
  void loadPolicies();
});

watch(activeTab, (tab) => {
  if (tab === "students") {
    void reloadStudents();
  }
  if (tab === "admin-import") {
    void reloadAdminImportHistory();
  }
  if (tab === "roles") {
    void loadPolicies();
  }
});
</script>

<style scoped>
.user-filter {
  margin-bottom: 12px;
}

.user-page--with-policy {
  padding-right: 364px;
}

.user-metrics {
  margin-bottom: 14px;
}

.user-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 14px;
  align-items: start;
}

.user-main {
  min-width: 0;
}

.admin-import-toolbar {
  margin-bottom: 14px;
}

.admin-import-alert {
  margin-bottom: 14px;
}

.admin-import-section {
  margin-top: 16px;
}

.wechat-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.section-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.section-title-row strong {
  color: var(--text);
  font-size: 15px;
}

.section-hint {
  color: var(--text-3);
  font-size: 12px;
}

.policy-side-panel {
  position: fixed;
  top: 58px;
  right: 0;
  bottom: 0;
  z-index: 12;
  width: 350px;
  overflow-y: auto;
  padding: 18px;
  background: #fff;
  border: 1px solid var(--line-soft);
  border-top: 0;
  border-right: 0;
  border-bottom: 0;
  border-radius: 0;
  box-shadow: var(--shadow-card);
}

.policy-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.policy-title-row strong {
  color: var(--text);
  font-size: 16px;
}

.policy-title-row span {
  color: var(--text-3);
  font-size: 18px;
}

.policy-hint {
  margin-bottom: 14px;
  padding: 10px 12px;
  color: #9a6400;
  background: #fff7e8;
  border: 1px solid #ffe5b5;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.6;
}

.policy-matrix {
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 10px;
}

.policy-grid {
  display: grid;
  grid-template-columns: 1.35fr repeat(4, 0.82fr);
  min-height: 54px;
  border-top: 1px solid var(--line-soft);
}

.policy-grid:first-child {
  border-top: 0;
}

.policy-grid > span,
.policy-grid > label {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
  padding: 0 8px;
  border-left: 1px solid var(--line-soft);
  color: var(--text-2);
  font-size: 12px;
}

.policy-grid > span:first-child {
  justify-content: flex-start;
  border-left: 0;
  color: var(--text);
  font-weight: 600;
}

.policy-grid-head {
  min-height: 42px;
  background: #f7f8fa;
}

.policy-grid-head > span {
  color: var(--text);
  font-weight: 700;
}

.preset-block {
  margin-top: 18px;
}

.preset-title {
  margin-bottom: 10px;
  color: var(--text);
  font-weight: 700;
}

.preset-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
}

@media (max-width: 1320px) {
  .user-page--with-policy {
    padding-right: 0;
  }

  .user-workspace {
    grid-template-columns: 1fr;
  }

  .policy-side-panel {
    position: static;
    width: auto;
    border: 1px solid var(--line-soft);
    border-radius: 12px;
  }
}
</style>
