<template>
  <div class="preview-page">
    <a-page-header
      title="需求实现前端预览"
      sub-title="不依赖后端账号，直接验证班团骨干菜单范围和请假边界提示"
      @back="router.push('/login')"
    />

    <a-alert
      class="mb16"
      type="info"
      show-icon
      message="当前为开发预览页"
      description="这里直接复用前端权限配置来展示班团骨干可见入口，并用静态样例展示请假提示文案，适合快速验收，不需要先造测试账号。"
    />

    <a-card title="角色切换" size="small" class="mb16">
      <a-radio-group v-model:value="selectedRole" button-style="solid">
        <a-radio-button
          v-for="role in PREVIEW_CADRE_ROLES"
          :key="role.code"
          :value="role.code"
        >
          {{ role.label }}
        </a-radio-button>
      </a-radio-group>
    </a-card>

    <a-row :gutter="[16, 16]" class="mb16">
      <a-col :xs="24" :xl="14">
        <a-card title="该角色可见菜单" size="small" class="full-height">
          <div class="group-list">
            <div v-for="group in visibleGroups" :key="group.group" class="group-card">
              <div class="group-title">{{ group.group }}</div>
              <div class="tag-list">
                <a-tag v-for="item in group.items" :key="item.key" color="processing">
                  {{ item.label }}
                </a-tag>
              </div>
            </div>
          </div>
        </a-card>
      </a-col>

      <a-col :xs="24" :xl="10">
        <a-card title="仍然不会开放的高权限入口" size="small" class="full-height">
          <div class="tag-list">
            <a-tag v-for="item in hiddenHighPrivilegeItems" :key="item.key" color="default">
              {{ item.label }}
            </a-tag>
          </div>
          <a-alert
            class="mt16"
            type="warning"
            show-icon
            message="设计边界"
            description="班团骨干现在是“协同管理者”，可以进入审批、通知、知识库、党团流程等入口，但不会获得导入中心、用户管理、审计日志等高权限能力。"
          />
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="[16, 16]">
      <a-col :xs="24" :xl="12">
        <a-card title="审批工作台中的请假提示" size="small" class="full-height">
          <a-alert
            type="warning"
            show-icon
            :message="LEAVE_WORKBENCH_ALERT.message"
            :description="LEAVE_WORKBENCH_ALERT.description"
          />
          <a-table
            class="mt16"
            :columns="previewColumns"
            :data-source="[PREVIEW_LEAVE_REQUEST_BRIEF]"
            :pagination="false"
            row-key="id"
            size="small"
          />
        </a-card>
      </a-col>

      <a-col :xs="24" :xl="12">
        <a-card title="请假详情中的正式渠道提示" size="small" class="full-height">
          <a-alert
            v-if="isLeaveRequestPreview(PREVIEW_LEAVE_REQUEST_DETAIL)"
            type="warning"
            show-icon
            :message="LEAVE_DETAIL_ALERT.message"
            :description="LEAVE_DETAIL_ALERT.description"
          />

          <a-descriptions class="mt16" :column="1" bordered size="small">
            <a-descriptions-item label="单号">
              {{ PREVIEW_LEAVE_REQUEST_DETAIL.request_no }}
            </a-descriptions-item>
            <a-descriptions-item label="事务类型">
              {{ PREVIEW_LEAVE_REQUEST_DETAIL.type_name }} ({{ PREVIEW_LEAVE_REQUEST_DETAIL.type_code }})
            </a-descriptions-item>
            <a-descriptions-item label="状态">
              {{ PREVIEW_LEAVE_REQUEST_DETAIL.status }}
            </a-descriptions-item>
            <a-descriptions-item label="摘要">
              {{ PREVIEW_LEAVE_REQUEST_DETAIL.summary }}
            </a-descriptions-item>
            <a-descriptions-item label="处理说明">
              {{ PREVIEW_LEAVE_REQUEST_DETAIL.decision_comment }}
            </a-descriptions-item>
          </a-descriptions>
        </a-card>
      </a-col>
    </a-row>

    <div class="action-row">
      <a-space wrap>
        <a-button type="primary" @click="router.push('/login')">返回登录</a-button>
        <a-button @click="copyPreviewPath">复制预览地址</a-button>
      </a-space>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import { NAV_GROUPS, getVisibleNavGroups } from '@/config/navigation'
import {
  LEAVE_DETAIL_ALERT,
  LEAVE_WORKBENCH_ALERT,
  PREVIEW_CADRE_ROLES,
  PREVIEW_HIDDEN_MENU_LABELS,
  PREVIEW_LEAVE_REQUEST_BRIEF,
  PREVIEW_LEAVE_REQUEST_DETAIL,
  isLeaveRequestPreview,
} from '@/features/approval/preview'

const router = useRouter()
const selectedRole = ref<(typeof PREVIEW_CADRE_ROLES)[number]['code']>('YOUTH_LEAGUE_SECRETARY')

const visibleGroups = computed(() => getVisibleNavGroups([selectedRole.value]))

const hiddenHighPrivilegeItems = computed(() => {
  return NAV_GROUPS.flatMap((group) => group.items).filter((item) => {
    if (!PREVIEW_HIDDEN_MENU_LABELS.includes(item.label)) return false
    return !visibleGroups.value.some((visibleGroup) =>
      visibleGroup.items.some((visibleItem) => visibleItem.key === item.key),
    )
  })
})

const previewColumns = [
  { title: '单号', dataIndex: 'request_no', key: 'request_no' },
  { title: '类型', dataIndex: 'type_code', key: 'type_code' },
  { title: '标题', dataIndex: 'title', key: 'title' },
  { title: '状态', dataIndex: 'status', key: 'status' },
]

async function copyPreviewPath() {
  const text = `${location.origin}/preview/requirements`
  try {
    await navigator.clipboard.writeText(text)
    message.success('预览地址已复制')
  } catch {
    message.warning(text)
  }
}
</script>

<style scoped>
.preview-page {
  min-height: 100vh;
  padding: 28px;
  background:
    radial-gradient(circle at top right, rgba(176, 0, 24, 0.08), transparent 24rem),
    linear-gradient(180deg, #fafbfc, #f4f6f8);
}

.mb16 {
  margin-bottom: 16px;
}

.mt16 {
  margin-top: 16px;
}

.full-height {
  height: 100%;
}

.group-list {
  display: grid;
  gap: 12px;
}

.group-card {
  padding: 14px;
  background: #fafafa;
  border: 1px solid var(--line-soft);
  border-radius: 12px;
}

.group-title {
  margin-bottom: 10px;
  color: var(--text);
  font-weight: 700;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.action-row {
  margin-top: 20px;
}
</style>
