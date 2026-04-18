<template>
  <div>
    <a-page-header title="审批详情" sub-title="FR-007 / FR-008" @back="$router.back()" />

    <a-spin :spinning="loading">
      <template v-if="detail">
        <a-descriptions :column="2" bordered size="small" class="mb16">
          <a-descriptions-item label="单号">{{ detail.request_no }}</a-descriptions-item>
          <a-descriptions-item label="类型">{{ detail.type_code }}</a-descriptions-item>
          <a-descriptions-item label="标题">{{ detail.title }}</a-descriptions-item>
          <a-descriptions-item label="状态">
            <StatusTag :status="detail.status" />
          </a-descriptions-item>
          <a-descriptions-item label="版本">{{ detail.revision }}</a-descriptions-item>
          <a-descriptions-item label="提交时间">{{ detail.submitted_at || '-' }}</a-descriptions-item>
          <a-descriptions-item label="申请人 ID">{{ detail.applicant_user_id }}</a-descriptions-item>
          <a-descriptions-item label="审批意见">{{ detail.decision_comment || '-' }}</a-descriptions-item>
        </a-descriptions>

        <a-card title="表单数据" :bordered="false" size="small" class="mb16">
          <pre style="white-space: pre-wrap; font-size: 13px;">{{ JSON.stringify(detail.form_data, null, 2) }}</pre>
        </a-card>

        <a-card title="附件" :bordered="false" size="small" class="mb16">
          <template v-if="detail.attachments && detail.attachments.length">
            <div v-for="att in detail.attachments" :key="att.id">
              {{ att.file_name }} ({{ att.file_size }} bytes)
            </div>
          </template>
          <a-empty v-else description="无附件" />
        </a-card>

        <a-card title="审批记录" :bordered="false" size="small" class="mb16">
          <a-timeline v-if="detail.approval_records && detail.approval_records.length">
            <a-timeline-item
              v-for="r in detail.approval_records" :key="r.id"
              :color="r.action === 'APPROVE' ? 'green' : r.action === 'REJECT' ? 'red' : 'blue'"
            >
              <strong>{{ r.action }}</strong>
              by 用户 {{ r.operator_user_id }}
              <span v-if="r.comment">— {{ r.comment }}</span>
              <br />
              <small>{{ r.operated_at }}</small>
            </a-timeline-item>
          </a-timeline>
          <a-empty v-else description="暂无审批记录" />
        </a-card>

        <!-- 操作按钮 -->
        <a-space v-if="canOperate">
          <a-button
            v-if="detail.status === 'SUBMITTED'"
            type="primary"
            @click="onClaim"
          >受理</a-button>
          <a-button
            v-if="detail.status === 'IN_REVIEW'"
            type="primary"
            @click="showAction('approve')"
          >通过</a-button>
          <a-button
            v-if="detail.status === 'IN_REVIEW'"
            danger
            @click="showAction('reject')"
          >驳回</a-button>
          <a-button
            v-if="detail.status === 'IN_REVIEW'"
            @click="showAction('offline')"
          >转线下</a-button>
        </a-space>
      </template>
    </a-spin>

    <!-- 操作 Modal -->
    <a-modal v-model:open="actionModal.visible" :title="actionModal.title" @ok="onAction">
      <a-form layout="vertical">
        <a-form-item label="审批意见">
          <a-textarea v-model:value="actionModal.comment" :rows="3" />
        </a-form-item>
        <a-form-item v-if="actionModal.type === 'offline'" label="联系方式（转线下必填）">
          <a-input v-model:value="actionModal.contact_info" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  getRequestDetail, claimRequest, approveRequest, rejectRequest, markRequestOffline,
  type RequestDetail,
} from '@/api/workflow'
import StatusTag from '@/components/StatusTag.vue'

const route = useRoute()
const id = Number(route.params.id)

const detail = ref<RequestDetail | null>(null)
const loading = ref(false)
const canOperate = ref(true) // simplified; real check is role-based

async function loadDetail() {
  loading.value = true
  try {
    const resp = await getRequestDetail(id)
    detail.value = resp.data
  } finally {
    loading.value = false
  }
}

async function onClaim() {
  await claimRequest(id)
  message.success('已受理')
  loadDetail()
}

const actionModal = reactive({
  visible: false,
  type: '' as 'approve' | 'reject' | 'offline',
  title: '',
  comment: '',
  contact_info: '',
})

function showAction(type: 'approve' | 'reject' | 'offline') {
  const titles = { approve: '通过审批', reject: '驳回', offline: '转线下处理' }
  actionModal.type = type
  actionModal.title = titles[type]
  actionModal.comment = ''
  actionModal.contact_info = ''
  actionModal.visible = true
}

async function onAction() {
  if (actionModal.type === 'approve') {
    await approveRequest(id, actionModal.comment)
    message.success('已通过')
  } else if (actionModal.type === 'reject') {
    await rejectRequest(id, actionModal.comment)
    message.success('已驳回')
  } else if (actionModal.type === 'offline') {
    await markRequestOffline(id, actionModal.contact_info, actionModal.comment)
    message.success('已转线下')
  }
  actionModal.visible = false
  loadDetail()
}

onMounted(loadDetail)
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
</style>
