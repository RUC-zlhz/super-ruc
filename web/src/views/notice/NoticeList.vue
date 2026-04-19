<template>
  <div>
    <a-page-header title="通知中心" sub-title="FR-010 / FR-011" />

    <a-form layout="inline" :model="filters" class="mb16" @finish="onFilterSubmit">
      <a-form-item label="关键字">
        <a-input v-model:value="filters.q" placeholder="标题" allow-clear style="width: 200px" />
      </a-form-item>
      <a-form-item label="状态">
        <a-select v-model:value="filters.status" style="width: 140px" allow-clear>
          <a-select-option value="DRAFT">草稿</a-select-option>
          <a-select-option value="PUBLISHED">已发布</a-select-option>
          <a-select-option value="ARCHIVED">已归档</a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item>
        <a-button type="primary" html-type="submit">查询</a-button>
      </a-form-item>
      <a-form-item>
        <a-button type="primary" @click="openEditor()">新建通知</a-button>
      </a-form-item>
    </a-form>

    <a-table
      :columns="columns"
      :data-source="rows"
      :loading="loading"
      :pagination="pagination"
      row-key="id"
      @change="onTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'title'">
          <div class="table-title">{{ record.title }}</div>
          <div class="table-secondary">
            <a-tag v-if="record.category" size="small">{{ record.category }}</a-tag>
            <span v-if="record.summary">{{ record.summary }}</span>
            <span v-else class="muted">无摘要</span>
          </div>
        </template>
        <template v-else-if="column.key === 'status'">
          <a-tag :color="statusColor(record.status)">{{ record.status }}</a-tag>
        </template>
        <template v-else-if="column.key === 'tags'">
          <a-tag v-for="tag in record.tags" :key="tag" size="small">{{ tag }}</a-tag>
          <span v-if="!record.tags.length" class="muted">-</span>
        </template>
        <template v-else-if="column.key === 'published_at'">
          {{ formatDateTime(record.published_at) }}
        </template>
        <template v-else-if="column.key === 'updated_at'">
          {{ formatDateTime(record.updated_at) }}
        </template>
        <template v-else-if="column.key === 'actions'">
          <a-space size="small" wrap>
            <a-button type="link" size="small" @click="openEditor(record as NoticeBrief)">编辑</a-button>
            <a-button
              v-if="record.status === 'DRAFT'"
              type="link"
              size="small"
              @click="onPublish(record.id)"
            >
              发布
            </a-button>
            <a-button
              v-if="record.status === 'PUBLISHED'"
              type="link"
              size="small"
              @click="openDispatch(record as NoticeBrief)"
            >
              发送
            </a-button>
            <a-button
              v-if="record.status !== 'DRAFT'"
              type="link"
              size="small"
              @click="openBatches(record as NoticeBrief)"
            >
              批次
            </a-button>
            <a-button
              v-if="record.status === 'PUBLISHED'"
              type="link"
              size="small"
              @click="onArchive(record.id)"
            >
              归档
            </a-button>
          </a-space>
        </template>
      </template>
    </a-table>

    <a-drawer
      :open="showDrawer"
      :title="editingId ? '通知详情 / 编辑' : '新建通知'"
      width="760"
      @close="resetForm"
    >
      <a-spin :spinning="drawerLoading">
        <a-alert
          v-if="editorStatus === 'ARCHIVED'"
          type="warning"
          show-icon
          class="mb16"
          message="已归档通知只读"
          description="当前通知已归档，可查看治理信息，但不可再次保存。"
        />

        <a-form layout="vertical" :model="form" @finish="onSubmit">
          <a-card title="基础信息" size="small" class="mb16">
            <a-row :gutter="16">
              <a-col :span="16">
                <a-form-item label="标题" :rules="[{ required: true }]">
                  <a-input v-model:value="form.title" :disabled="editorStatus === 'ARCHIVED'" />
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="分类">
                  <a-input v-model:value="form.category" :disabled="editorStatus === 'ARCHIVED'" />
                </a-form-item>
              </a-col>
            </a-row>

            <a-form-item label="摘要">
              <a-textarea
                v-model:value="form.summary"
                :rows="2"
                :disabled="editorStatus === 'ARCHIVED'"
              />
            </a-form-item>

            <a-form-item label="标签">
              <a-select
                v-model:value="form.tags"
                mode="tags"
                style="width: 100%"
                placeholder="输入后回车，可录入多个标签"
                :disabled="editorStatus === 'ARCHIVED'"
              />
            </a-form-item>

            <a-form-item>
              <a-checkbox v-model:checked="form.is_pinned" :disabled="editorStatus === 'ARCHIVED'">
                置顶通知
              </a-checkbox>
            </a-form-item>
          </a-card>

          <a-card title="内容与治理信息" size="small" class="mb16">
            <a-row :gutter="16">
              <a-col :span="8">
                <a-form-item label="source_type">
                  <a-select v-model:value="form.source_type" :disabled="editorStatus === 'ARCHIVED'">
                    <a-select-option value="MANUAL">手工录入</a-select-option>
                    <a-select-option value="CRAWL">受控抓取</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :span="16">
                <a-form-item label="source_url">
                  <a-input
                    v-model:value="form.source_url"
                    placeholder="可选"
                    :disabled="editorStatus === 'ARCHIVED'"
                  />
                </a-form-item>
              </a-col>
            </a-row>

            <a-form-item label="channels">
              <a-checkbox-group
                v-model:value="form.channels"
                :options="CHANNEL_OPTIONS"
                :disabled="editorStatus === 'ARCHIVED'"
              />
            </a-form-item>

            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="生效开始">
                  <a-date-picker
                    v-model:value="form.effective_start"
                    value-format="YYYY-MM-DD"
                    style="width: 100%"
                    :disabled="editorStatus === 'ARCHIVED'"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="生效结束">
                  <a-date-picker
                    v-model:value="form.effective_end"
                    value-format="YYYY-MM-DD"
                    style="width: 100%"
                    :disabled="editorStatus === 'ARCHIVED'"
                  />
                </a-form-item>
              </a-col>
            </a-row>

            <a-form-item label="正文（body_md / Markdown）" :rules="[{ required: true }]">
              <a-textarea
                v-model:value="form.body_md"
                :rows="10"
                :disabled="editorStatus === 'ARCHIVED'"
              />
            </a-form-item>
          </a-card>

          <a-card title="目标人群与命中预览" size="small" class="mb16">
            <a-form-item label="target_summary">
              <a-input
                v-model:value="form.target_summary"
                placeholder="例如：2022 级 CS 党员"
                :disabled="editorStatus === 'ARCHIVED'"
              />
            </a-form-item>

            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="grade_codes">
                  <a-select
                    v-model:value="form.target_rule.grade_codes"
                    mode="tags"
                    style="width: 100%"
                    placeholder="输入后回车"
                    :disabled="editorStatus === 'ARCHIVED'"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="major_codes">
                  <a-select
                    v-model:value="form.target_rule.major_codes"
                    mode="tags"
                    style="width: 100%"
                    placeholder="输入后回车"
                    :disabled="editorStatus === 'ARCHIVED'"
                  />
                </a-form-item>
              </a-col>
            </a-row>

            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="class_codes">
                  <a-select
                    v-model:value="form.target_rule.class_codes"
                    mode="tags"
                    style="width: 100%"
                    placeholder="输入后回车"
                    :disabled="editorStatus === 'ARCHIVED'"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="political_status">
                  <a-select
                    v-model:value="form.target_rule.political_status"
                    mode="tags"
                    style="width: 100%"
                    placeholder="输入后回车"
                    :disabled="editorStatus === 'ARCHIVED'"
                  />
                </a-form-item>
              </a-col>
            </a-row>

            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="role_codes（保留字段）">
                  <a-select
                    v-model:value="form.target_rule.role_codes"
                    mode="tags"
                    style="width: 100%"
                    placeholder="输入后回车"
                    :disabled="editorStatus === 'ARCHIVED'"
                  />
                  <div class="muted mt8">
                    当前后端 contract 保留该字段，但 target-preview 暂未按 role_codes 命中。
                  </div>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="圈人规则">
                  <a-checkbox
                    v-model:checked="form.target_rule.exclude_graduated"
                    :disabled="editorStatus === 'ARCHIVED'"
                  >
                    排除已毕业学生
                  </a-checkbox>
                </a-form-item>
              </a-col>
            </a-row>

            <div class="drawer-actions">
              <a-button
                :loading="previewLoading"
                :disabled="editorStatus === 'ARCHIVED'"
                @click="onPreviewTarget"
              >
                命中预览
              </a-button>
              <span class="muted">修改规则后需重新点击预览，结果不会自动刷新。</span>
            </div>

            <a-alert
              v-if="previewResult"
              class="mt12"
              type="info"
              show-icon
              :message="`target_count：${previewResult.target_count}`"
            >
              <template #description>
                <div v-if="previewResult.sample_student_nos.length" class="preview-samples">
                  <span class="muted">sample_student_nos：</span>
                  <a-tag
                    v-for="studentNo in previewResult.sample_student_nos"
                    :key="studentNo"
                    size="small"
                  >
                    {{ studentNo }}
                  </a-tag>
                </div>
                <span v-else class="muted">当前无命中样本。</span>
              </template>
            </a-alert>
          </a-card>

          <a-card v-if="currentDetail" title="当前治理视图" size="small" class="mb16">
            <a-descriptions :column="2" bordered size="small">
              <a-descriptions-item label="状态">
                <a-tag :color="statusColor(currentDetail.status)">{{ currentDetail.status }}</a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="source_type">
                {{ sourceLabel(currentDetail.source_type) }}
              </a-descriptions-item>
              <a-descriptions-item label="channels" :span="2">
                <a-tag
                  v-for="channel in parseChannels(currentDetail.channels)"
                  :key="channel"
                  size="small"
                >
                  {{ channelLabel(channel) }}
                </a-tag>
                <span v-if="!parseChannels(currentDetail.channels).length" class="muted">-</span>
              </a-descriptions-item>
              <a-descriptions-item label="target_summary">
                {{ currentDetail.target_summary || '全体在读学生' }}
              </a-descriptions-item>
              <a-descriptions-item label="source_url">
                {{ currentDetail.source_url || '-' }}
              </a-descriptions-item>
              <a-descriptions-item label="published_at">
                {{ formatDateTime(currentDetail.published_at) }}
              </a-descriptions-item>
              <a-descriptions-item label="updated_at">
                {{ formatDateTime(currentDetail.updated_at) }}
              </a-descriptions-item>
            </a-descriptions>
          </a-card>

          <a-form-item>
            <a-space>
              <a-button
                type="primary"
                html-type="submit"
                :loading="submitting"
                :disabled="editorStatus === 'ARCHIVED'"
              >
                保存
              </a-button>
              <a-button @click="resetForm">关闭</a-button>
            </a-space>
          </a-form-item>
        </a-form>
      </a-spin>
    </a-drawer>

    <a-modal
      v-model:open="dispatchModal.open"
      title="发送通知"
      :confirm-loading="dispatchModal.submitting"
      @ok="onDispatchSubmit"
      @cancel="resetDispatchModal"
    >
      <a-spin :spinning="dispatchModal.loading">
        <a-descriptions v-if="dispatchModal.detail" :column="1" bordered size="small" class="mb16">
          <a-descriptions-item label="标题">{{ dispatchModal.detail.title }}</a-descriptions-item>
          <a-descriptions-item label="source_type">
            {{ sourceLabel(dispatchModal.detail.source_type) }}
          </a-descriptions-item>
          <a-descriptions-item label="channels">
            <a-tag
              v-for="channel in parseChannels(dispatchModal.detail.channels)"
              :key="channel"
              size="small"
            >
              {{ channelLabel(channel) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="target_summary">
            {{ dispatchModal.detail.target_summary || '全体在读学生' }}
          </a-descriptions-item>
        </a-descriptions>

        <a-form layout="vertical">
          <a-form-item label="发送渠道">
            <a-checkbox-group v-model:value="dispatchModal.channels" :options="CHANNEL_OPTIONS" />
          </a-form-item>
          <a-form-item label="批次备注">
            <a-textarea
              v-model:value="dispatchModal.note"
              :rows="3"
              placeholder="可选，便于回看批次用途"
            />
          </a-form-item>
        </a-form>
      </a-spin>
    </a-modal>

    <a-drawer
      :open="batchesDrawer.open"
      title="发送批次"
      width="960"
      @close="closeBatchesDrawer"
    >
      <a-spin :spinning="batchesDrawer.loading">
        <a-descriptions
          v-if="batchesDrawer.notice"
          :column="2"
          bordered
          size="small"
          class="mb16"
        >
          <a-descriptions-item label="标题">{{ batchesDrawer.notice.title }}</a-descriptions-item>
          <a-descriptions-item label="状态">
            <a-tag :color="statusColor(batchesDrawer.notice.status)">{{ batchesDrawer.notice.status }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="source_type">
            {{ sourceLabel(batchesDrawer.notice.source_type) }}
          </a-descriptions-item>
          <a-descriptions-item label="channels">
            <a-tag
              v-for="channel in parseChannels(batchesDrawer.notice.channels)"
              :key="channel"
              size="small"
            >
              {{ channelLabel(channel) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="target_summary">
            {{ batchesDrawer.notice.target_summary || '全体在读学生' }}
          </a-descriptions-item>
          <a-descriptions-item label="published_at">
            {{ formatDateTime(batchesDrawer.notice.published_at) }}
          </a-descriptions-item>
        </a-descriptions>

        <a-table
          :columns="batchColumns"
          :data-source="batchesDrawer.items"
          :pagination="false"
          row-key="id"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'channels'">
              <a-tag v-for="channel in parseChannels(record.channels)" :key="channel" size="small">
                {{ channelLabel(channel) }}
              </a-tag>
              <span v-if="!parseChannels(record.channels).length" class="muted">-</span>
            </template>
            <template v-else-if="column.key === 'batch_status'">
              <a-tag :color="batchStatusColor(record.status)">{{ record.status }}</a-tag>
            </template>
            <template v-else-if="column.key === 'started_at'">
              {{ formatDateTime(record.started_at) }}
            </template>
            <template v-else-if="column.key === 'finished_at'">
              {{ formatDateTime(record.finished_at) }}
            </template>
            <template v-else-if="column.key === 'actions'">
              <a-button type="link" size="small" @click="openDeliveries(record as NoticeBatch)">
                投递明细
              </a-button>
            </template>
          </template>
        </a-table>

        <a-empty v-if="!batchesDrawer.items.length && !batchesDrawer.loading" description="暂无发送批次" />
      </a-spin>
    </a-drawer>

    <a-drawer
      :open="deliveriesDrawer.open"
      title="投递明细"
      width="1120"
      @close="closeDeliveriesDrawer"
    >
      <a-spin :spinning="deliveriesDrawer.loading">
        <a-descriptions
          v-if="deliveriesDrawer.batch"
          :column="3"
          bordered
          size="small"
          class="mb16"
        >
          <a-descriptions-item label="batch_no">
            {{ deliveriesDrawer.batch.batch_no }}
          </a-descriptions-item>
          <a-descriptions-item label="batch_status">
            <a-tag :color="batchStatusColor(deliveriesDrawer.batch.status)">
              {{ deliveriesDrawer.batch.status }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="channels">
            <a-tag
              v-for="channel in parseChannels(deliveriesDrawer.batch.channels)"
              :key="channel"
              size="small"
            >
              {{ channelLabel(channel) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="target_count">
            {{ deliveriesDrawer.batch.target_count }}
          </a-descriptions-item>
          <a-descriptions-item label="success_count">
            {{ deliveriesDrawer.batch.success_count }}
          </a-descriptions-item>
          <a-descriptions-item label="failed_count">
            {{ deliveriesDrawer.batch.failed_count }}
          </a-descriptions-item>
          <a-descriptions-item label="note" :span="3">
            {{ deliveriesDrawer.batch.note || '-' }}
          </a-descriptions-item>
        </a-descriptions>

        <a-form layout="inline" :model="deliveryFilters" class="mb16" @finish="reloadDeliveries">
          <a-form-item label="投递状态">
            <a-select v-model:value="deliveryFilters.status" allow-clear style="width: 160px">
              <a-select-option value="SENT">SENT</a-select-option>
              <a-select-option value="READ">READ</a-select-option>
              <a-select-option value="SKIPPED">SKIPPED</a-select-option>
              <a-select-option value="FAILED">FAILED</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="渠道">
            <a-select v-model:value="deliveryFilters.channel" allow-clear style="width: 160px">
              <a-select-option value="IN_APP">IN_APP</a-select-option>
              <a-select-option value="EMAIL">EMAIL</a-select-option>
              <a-select-option value="SMS">SMS</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item>
            <a-button type="primary" html-type="submit">筛选</a-button>
          </a-form-item>
          <a-form-item>
            <a-button @click="resetDeliveryFilters">重置</a-button>
          </a-form-item>
        </a-form>

        <a-table
          :columns="deliveryColumns"
          :data-source="deliveriesDrawer.items"
          :loading="deliveriesDrawer.loading"
          :pagination="deliveryPagination"
          row-key="id"
          size="small"
          @change="onDeliveryTableChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'channel'">
              <a-tag>{{ channelLabel(record.channel) }}</a-tag>
            </template>
            <template v-else-if="column.key === 'status'">
              <a-tag :color="deliveryStatusColor(record.status)">{{ record.status }}</a-tag>
            </template>
            <template v-else-if="column.key === 'sent_at'">
              {{ formatDateTime(record.sent_at) }}
            </template>
            <template v-else-if="column.key === 'read_at'">
              {{ formatDateTime(record.read_at) }}
            </template>
            <template v-else-if="column.key === 'error_code'">
              {{ record.error_code || '-' }}
            </template>
            <template v-else-if="column.key === 'error_message'">
              <span :class="{ muted: !record.error_message }">{{ record.error_message || '-' }}</span>
            </template>
          </template>
        </a-table>
      </a-spin>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import {
  archiveNotice,
  createNotice,
  dispatchNotice,
  getNoticeDetail,
  listBatchDeliveries,
  listNoticeBatches,
  listNotices,
  previewNoticeTarget,
  publishNotice,
  updateNotice,
  type NoticeBatch,
  type NoticeBatchStatus,
  type NoticeBrief,
  type NoticeChannel,
  type NoticeDelivery,
  type NoticeDeliveryStatus,
  type NoticeInput,
  type NoticeOut,
  type NoticeStatus,
  type NoticeTargetPreviewResult,
  type NoticeTargetRule,
} from '@/api/notice'

interface NoticeTargetRuleForm {
  grade_codes: string[]
  major_codes: string[]
  class_codes: string[]
  political_status: string[]
  role_codes: string[]
  exclude_graduated: boolean
}

interface NoticeFormState {
  title: string
  body_md: string
  summary: string
  category: string
  tags: string[]
  target_rule: NoticeTargetRuleForm
  target_summary: string
  channels: NoticeChannel[]
  effective_start?: string
  effective_end?: string
  is_pinned: boolean
  source_type: string
  source_url: string
}

const CHANNEL_OPTIONS: Array<{ label: string; value: NoticeChannel }> = [
  { label: '站内信 (IN_APP)', value: 'IN_APP' },
  { label: '邮件 (EMAIL)', value: 'EMAIL' },
  { label: '短信 (SMS)', value: 'SMS' },
]

const SOURCE_LABELS: Record<string, string> = {
  MANUAL: '手工录入',
  CRAWL: '受控抓取',
}

const columns = [
  { title: '通知', dataIndex: 'title', key: 'title' },
  { title: '标签', key: 'tags', width: 220 },
  { title: '状态', key: 'status', width: 110 },
  { title: '发布时间', dataIndex: 'published_at', key: 'published_at', width: 170 },
  { title: '更新时间', dataIndex: 'updated_at', key: 'updated_at', width: 170 },
  { title: '操作', key: 'actions', width: 260 },
]

const batchColumns = [
  { title: 'batch_no', dataIndex: 'batch_no', key: 'batch_no', width: 220 },
  { title: 'channels', key: 'channels', width: 180 },
  { title: 'target_count', dataIndex: 'target_count', key: 'target_count', width: 110 },
  { title: 'success_count', dataIndex: 'success_count', key: 'success_count', width: 110 },
  { title: 'failed_count', dataIndex: 'failed_count', key: 'failed_count', width: 110 },
  { title: 'batch_status', key: 'batch_status', width: 130 },
  { title: 'started_at', dataIndex: 'started_at', key: 'started_at', width: 170 },
  { title: 'finished_at', dataIndex: 'finished_at', key: 'finished_at', width: 170 },
  { title: '操作', key: 'actions', width: 120 },
]

const deliveryColumns = [
  { title: 'student_id', dataIndex: 'student_id', key: 'student_id', width: 110 },
  { title: 'user_id', dataIndex: 'user_id', key: 'user_id', width: 110 },
  { title: 'channel', key: 'channel', width: 110 },
  { title: 'status', key: 'status', width: 110 },
  { title: 'sent_at', dataIndex: 'sent_at', key: 'sent_at', width: 170 },
  { title: 'read_at', dataIndex: 'read_at', key: 'read_at', width: 170 },
  { title: 'error_code', key: 'error_code', width: 150 },
  { title: 'error_message', key: 'error_message' },
]

function sourceLabel(sourceType: string) {
  return SOURCE_LABELS[sourceType] ?? sourceType
}

function channelLabel(channel: string) {
  return channel === 'IN_APP' ? '站内信' : channel === 'EMAIL' ? '邮件' : channel === 'SMS' ? '短信' : channel
}

function statusColor(status: NoticeStatus) {
  return status === 'PUBLISHED' ? 'green' : status === 'ARCHIVED' ? 'default' : 'blue'
}

function batchStatusColor(status: NoticeBatchStatus | string) {
  if (status === 'COMPLETED') return 'green'
  if (status === 'FAILED') return 'red'
  if (status === 'PARTIAL') return 'orange'
  return 'blue'
}

function deliveryStatusColor(status: NoticeDeliveryStatus | string) {
  if (status === 'READ') return 'green'
  if (status === 'SENT') return 'blue'
  if (status === 'FAILED') return 'red'
  return 'default'
}

function formatDateTime(value?: string | null) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false, timeZone: 'Asia/Shanghai' })
}

function normalizeStringList(items?: string[] | null) {
  if (!items?.length) return []
  return Array.from(
    new Set(
      items
        .map((item) => item.trim())
        .filter(Boolean),
    ),
  )
}

function normalizeChannels(items?: NoticeChannel[] | null) {
  const next = normalizeStringList(items as string[]) as NoticeChannel[]
  return next.length ? next : (['IN_APP'] as NoticeChannel[])
}

function parseChannels(channels?: string | null) {
  if (!channels) return [] as NoticeChannel[]
  return normalizeStringList(channels.split(',')) as NoticeChannel[]
}

function createEmptyTargetRuleForm(): NoticeTargetRuleForm {
  return {
    grade_codes: [],
    major_codes: [],
    class_codes: [],
    political_status: [],
    role_codes: [],
    exclude_graduated: true,
  }
}

function normalizeTargetRule(rule: NoticeTargetRuleForm): NoticeTargetRule | null {
  const targetRule: NoticeTargetRule = {
    grade_codes: normalizeStringList(rule.grade_codes),
    major_codes: normalizeStringList(rule.major_codes),
    class_codes: normalizeStringList(rule.class_codes),
    political_status: normalizeStringList(rule.political_status),
    role_codes: normalizeStringList(rule.role_codes),
    exclude_graduated: rule.exclude_graduated,
  }

  const hasExplicitFilters = Boolean(
    targetRule.grade_codes?.length ||
      targetRule.major_codes?.length ||
      targetRule.class_codes?.length ||
      targetRule.political_status?.length ||
      targetRule.role_codes?.length,
  )

  if (!hasExplicitFilters && targetRule.exclude_graduated !== false) {
    return null
  }

  return targetRule
}

function createEmptyForm(): NoticeFormState {
  return {
    title: '',
    body_md: '',
    summary: '',
    category: '',
    tags: [],
    target_rule: createEmptyTargetRuleForm(),
    target_summary: '',
    channels: ['IN_APP'],
    effective_start: undefined,
    effective_end: undefined,
    is_pinned: false,
    source_type: 'MANUAL',
    source_url: '',
  }
}

function buildFormFromNotice(detail: NoticeOut): NoticeFormState {
  return {
    title: detail.title,
    body_md: detail.body_md,
    summary: detail.summary ?? '',
    category: detail.category ?? '',
    tags: normalizeStringList(detail.tags),
    target_rule: {
      grade_codes: normalizeStringList(detail.target_rule?.grade_codes),
      major_codes: normalizeStringList(detail.target_rule?.major_codes),
      class_codes: normalizeStringList(detail.target_rule?.class_codes),
      political_status: normalizeStringList(detail.target_rule?.political_status),
      role_codes: normalizeStringList(detail.target_rule?.role_codes),
      exclude_graduated: detail.target_rule?.exclude_graduated ?? true,
    },
    target_summary: detail.target_summary ?? '',
    channels: parseChannels(detail.channels),
    effective_start: detail.effective_start ?? undefined,
    effective_end: detail.effective_end ?? undefined,
    is_pinned: detail.is_pinned,
    source_type: detail.source_type,
    source_url: detail.source_url ?? '',
  }
}

function buildPayload(): NoticeInput {
  return {
    title: form.title.trim(),
    body_md: form.body_md.trim(),
    summary: form.summary.trim() || null,
    category: form.category.trim() || null,
    tags: normalizeStringList(form.tags),
    target_rule: normalizeTargetRule(form.target_rule),
    target_summary: form.target_summary.trim() || null,
    channels: normalizeChannels(form.channels),
    effective_start: form.effective_start || null,
    effective_end: form.effective_end || null,
    is_pinned: form.is_pinned,
    source_type: form.source_type.trim() || 'MANUAL',
    source_url: form.source_url.trim() || null,
  }
}

function assignForm(next: NoticeFormState) {
  Object.assign(form, createEmptyForm(), next)
}

const detailCache = new Map<number, NoticeOut>()

async function loadNoticeDetail(id: number, force = false) {
  if (!force && detailCache.has(id)) {
    return detailCache.get(id) as NoticeOut
  }
  const resp = await getNoticeDetail(id)
  detailCache.set(id, resp.data)
  return resp.data
}

const filters = reactive<{ q?: string; status?: NoticeStatus }>({})
const rows = ref<NoticeBrief[]>([])
const loading = ref(false)
const pagination = reactive({ current: 1, pageSize: 20, total: 0 })

async function reload() {
  loading.value = true
  try {
    const resp = await listNotices({
      q: filters.q,
      status: filters.status,
      page: pagination.current,
      size: pagination.pageSize,
    })
    rows.value = resp.data.items
    pagination.total = resp.data.meta.total
  } finally {
    loading.value = false
  }
}

async function onFilterSubmit() {
  pagination.current = 1
  await reload()
}

function onTableChange(p: { current?: number; pageSize?: number }) {
  pagination.current = p.current ?? pagination.current
  pagination.pageSize = p.pageSize ?? pagination.pageSize
  reload()
}

const showDrawer = ref(false)
const drawerLoading = ref(false)
const submitting = ref(false)
const editingId = ref<number | null>(null)
const editorStatus = ref<NoticeStatus>('DRAFT')
const currentDetail = ref<NoticeOut | null>(null)
const previewLoading = ref(false)
const previewResult = ref<NoticeTargetPreviewResult | null>(null)
const form = reactive<NoticeFormState>(createEmptyForm())

async function openEditor(record?: NoticeBrief) {
  showDrawer.value = true
  previewResult.value = null

  if (!record) {
    editingId.value = null
    editorStatus.value = 'DRAFT'
    currentDetail.value = null
    assignForm(createEmptyForm())
    return
  }

  editingId.value = record.id
  drawerLoading.value = true
  try {
    const detail = await loadNoticeDetail(record.id)
    currentDetail.value = detail
    editorStatus.value = detail.status
    assignForm(buildFormFromNotice(detail))
  } finally {
    drawerLoading.value = false
  }
}

function resetForm() {
  showDrawer.value = false
  drawerLoading.value = false
  submitting.value = false
  editingId.value = null
  editorStatus.value = 'DRAFT'
  currentDetail.value = null
  previewResult.value = null
  assignForm(createEmptyForm())
}

async function onPreviewTarget() {
  previewLoading.value = true
  try {
    const resp = await previewNoticeTarget({ target_rule: buildPayload().target_rule })
    previewResult.value = resp.data
  } finally {
    previewLoading.value = false
  }
}

async function onSubmit() {
  const payload = buildPayload()
  if (!payload.title) {
    message.warning('请填写标题')
    return
  }
  if (!payload.body_md) {
    message.warning('请填写正文')
    return
  }

  submitting.value = true
  try {
    const resp = editingId.value
      ? await updateNotice(editingId.value, payload)
      : await createNotice(payload)
    detailCache.set(resp.data.id, resp.data)
    message.success('保存成功')
    resetForm()
    await reload()
  } finally {
    submitting.value = false
  }
}

async function onPublish(id: number) {
  const resp = await publishNotice(id)
  detailCache.set(resp.data.id, resp.data)
  if (editingId.value === id) {
    currentDetail.value = resp.data
    editorStatus.value = resp.data.status
  }
  message.success('已发布')
  await reload()
}

async function onArchive(id: number) {
  const resp = await archiveNotice(id)
  detailCache.set(resp.data.id, resp.data)
  if (editingId.value === id) {
    currentDetail.value = resp.data
    editorStatus.value = resp.data.status
  }
  message.success('已归档')
  await reload()
}

const dispatchModal = reactive({
  open: false,
  loading: false,
  submitting: false,
  noticeId: 0,
  channels: ['IN_APP'] as NoticeChannel[],
  note: '',
  detail: null as NoticeOut | null,
})

async function openDispatch(record: NoticeBrief) {
  dispatchModal.open = true
  dispatchModal.loading = true
  dispatchModal.noticeId = record.id
  dispatchModal.note = ''
  try {
    const detail = await loadNoticeDetail(record.id)
    dispatchModal.detail = detail
    dispatchModal.channels = normalizeChannels(parseChannels(detail.channels))
  } finally {
    dispatchModal.loading = false
  }
}

function resetDispatchModal() {
  dispatchModal.open = false
  dispatchModal.loading = false
  dispatchModal.submitting = false
  dispatchModal.noticeId = 0
  dispatchModal.channels = ['IN_APP']
  dispatchModal.note = ''
  dispatchModal.detail = null
}

async function onDispatchSubmit() {
  if (!dispatchModal.noticeId) return
  if (!dispatchModal.channels.length) {
    message.warning('至少选择一个发送渠道')
    return
  }

  dispatchModal.submitting = true
  try {
    await dispatchNotice(dispatchModal.noticeId, {
      channels: normalizeChannels(dispatchModal.channels),
      note: dispatchModal.note.trim() || null,
    })
    const noticeId = dispatchModal.noticeId
    const title = dispatchModal.detail?.title || '通知'
    message.success('发送成功')
    resetDispatchModal()
    await reload()
    await openBatchesForNotice(noticeId, title)
  } finally {
    dispatchModal.submitting = false
  }
}

const batchesDrawer = reactive({
  open: false,
  loading: false,
  noticeId: 0,
  title: '',
  notice: null as NoticeOut | null,
  items: [] as NoticeBatch[],
})

function sortBatches(items: NoticeBatch[]) {
  return [...items].sort((left, right) => {
    return new Date(right.started_at).getTime() - new Date(left.started_at).getTime()
  })
}

async function openBatches(record: NoticeBrief) {
  await openBatchesForNotice(record.id, record.title)
}

async function openBatchesForNotice(id: number, title: string) {
  batchesDrawer.open = true
  batchesDrawer.loading = true
  batchesDrawer.noticeId = id
  batchesDrawer.title = title
  try {
    const [detail, batchesResp] = await Promise.all([loadNoticeDetail(id), listNoticeBatches(id)])
    batchesDrawer.notice = detail
    batchesDrawer.items = sortBatches(batchesResp.data)
  } finally {
    batchesDrawer.loading = false
  }
}

function closeBatchesDrawer() {
  batchesDrawer.open = false
  batchesDrawer.loading = false
  batchesDrawer.noticeId = 0
  batchesDrawer.title = ''
  batchesDrawer.notice = null
  batchesDrawer.items = []
  closeDeliveriesDrawer()
}

const deliveryFilters = reactive<{
  status?: NoticeDeliveryStatus
  channel?: NoticeChannel
}>({})

const deliveriesDrawer = reactive({
  open: false,
  loading: false,
  batch: null as NoticeBatch | null,
  items: [] as NoticeDelivery[],
})

const deliveryPagination = reactive({
  current: 1,
  pageSize: 50,
  total: 0,
})

async function openDeliveries(batch: NoticeBatch) {
  deliveriesDrawer.open = true
  deliveriesDrawer.batch = batch
  deliveryPagination.current = 1
  deliveryPagination.pageSize = 50
  deliveryFilters.status = undefined
  deliveryFilters.channel = undefined
  await reloadDeliveries()
}

async function reloadDeliveries() {
  if (!deliveriesDrawer.batch) return
  deliveriesDrawer.loading = true
  try {
    const resp = await listBatchDeliveries(deliveriesDrawer.batch.id, {
      status: deliveryFilters.status,
      channel: deliveryFilters.channel,
      page: deliveryPagination.current,
      size: deliveryPagination.pageSize,
    })
    deliveriesDrawer.items = resp.data.items
    deliveryPagination.total = resp.data.meta.total
  } finally {
    deliveriesDrawer.loading = false
  }
}

function onDeliveryTableChange(p: { current?: number; pageSize?: number }) {
  deliveryPagination.current = p.current ?? deliveryPagination.current
  deliveryPagination.pageSize = p.pageSize ?? deliveryPagination.pageSize
  reloadDeliveries()
}

function resetDeliveryFilters() {
  deliveryFilters.status = undefined
  deliveryFilters.channel = undefined
  deliveryPagination.current = 1
  reloadDeliveries()
}

function closeDeliveriesDrawer() {
  deliveriesDrawer.open = false
  deliveriesDrawer.loading = false
  deliveriesDrawer.batch = null
  deliveriesDrawer.items = []
  deliveryPagination.current = 1
  deliveryPagination.pageSize = 50
  deliveryPagination.total = 0
  deliveryFilters.status = undefined
  deliveryFilters.channel = undefined
}

onMounted(reload)
</script>

<style scoped>
.mb16 {
  margin-bottom: 16px;
}

.mt12 {
  margin-top: 12px;
}

.mt8 {
  margin-top: 8px;
}

.table-title {
  font-weight: 600;
  line-height: 22px;
}

.table-secondary {
  color: rgba(0, 0, 0, 0.45);
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  line-height: 20px;
  margin-top: 4px;
}

.drawer-actions {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.preview-samples {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.muted {
  color: rgba(0, 0, 0, 0.45);
}
</style>
