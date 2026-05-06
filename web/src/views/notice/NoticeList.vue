<template>
  <div class="notice-page">
    <a-page-header title="通知中心" sub-title="统一管理通知发布、投递与触达情况" />

    <div class="metric-grid">
      <div v-for="metric in metrics" :key="metric.key" class="metric-tile">
        <span class="metric-icon"><component :is="metric.icon" /></span>
        <div class="metric-label">{{ metric.label }}</div>
        <div class="metric-value">{{ metric.value }}</div>
        <div class="metric-sub">{{ metric.sub }}</div>
      </div>
    </div>

    <a-form layout="inline" :model="filters" class="filter-card" @finish="onFilterSubmit">
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
        <a-button type="primary" html-type="submit">
          <template #icon><SearchOutlined /></template>
          查询
        </a-button>
      </a-form-item>
      <a-form-item>
        <a-button type="primary" @click="openEditor()">
          <template #icon><PlusOutlined /></template>
          新建通知
        </a-button>
      </a-form-item>
    </a-form>

    <a-table
      :columns="columns"
      :data-source="rows"
      :loading="loading"
      :pagination="pagination"
      :custom-row="noticeRowProps"
      :row-class-name="noticeRowClassName"
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
            <a-button type="link" size="small" @click="openEditor(record as NoticeBrief)">
              <template #icon><EditOutlined /></template>
              编辑
            </a-button>
            <a-button
              v-if="record.status === 'DRAFT'"
              type="link"
              size="small"
              @click="onPublish(record.id)"
            >
              <template #icon><CloudUploadOutlined /></template>
              发布
            </a-button>
            <a-button
              v-if="record.status === 'PUBLISHED'"
              type="link"
              size="small"
              @click="openDispatch(record as NoticeBrief)"
            >
              <template #icon><SendOutlined /></template>
              发送
            </a-button>
            <a-button
              v-if="record.status !== 'DRAFT'"
              type="link"
              size="small"
              @click="openBatches(record as NoticeBrief)"
            >
              <template #icon><FolderOpenOutlined /></template>
              批次
            </a-button>
            <a-button
              v-if="record.status === 'PUBLISHED'"
              type="link"
              size="small"
              @click="onArchive(record.id)"
            >
              <template #icon><InboxOutlined /></template>
              归档
            </a-button>
          </a-space>
        </template>
      </template>
    </a-table>

    <aside class="notice-side-panel">
      <div class="side-panel-head">
        <strong>通知编辑器</strong>
        <a-button type="text" size="small" :disabled="!selectedNotice" @click="clearSelectedNotice">
          <template #icon><CloseOutlined /></template>
        </a-button>
      </div>

      <div class="side-mini-stats">
        <div v-for="metric in metrics" :key="metric.key">
          <component :is="metric.icon" />
          <strong>{{ metric.value }}</strong>
          <span>{{ metric.label }}</span>
        </div>
      </div>

      <template v-if="selectedNotice">
        <a-spin :spinning="selectedNoticeLoading || selectedNoticeBatchesLoading">
          <section class="side-section notice-preview">
            <div>
              <p>当前选中通知</p>
              <h3>{{ selectedNotice.title }}</h3>
            </div>
            <a-tag :color="statusColor(selectedNotice.status)">{{ selectedNotice.status }}</a-tag>
          </section>

          <section class="side-section">
            <h3>发布信息</h3>
            <div class="side-kv">
              <span>分类</span>
              <strong>{{ selectedNotice.category || '-' }}</strong>
            </div>
            <div class="side-kv">
              <span>更新时间</span>
              <strong>{{ formatDateTime(selectedNotice.updated_at) }}</strong>
            </div>
            <div class="side-kv">
              <span>来源</span>
              <strong>{{ selectedNoticeDetail ? sourceLabel(selectedNoticeDetail.source_type) : '-' }}</strong>
            </div>
            <div class="side-kv">
              <span>渠道</span>
              <strong>{{ selectedNoticeChannelsLabel }}</strong>
            </div>
            <div class="tag-strip">
              <a-tag v-for="tag in selectedNotice.tags" :key="tag">{{ tag }}</a-tag>
              <span v-if="!selectedNotice.tags.length" class="muted">暂无标签</span>
            </div>
          </section>

          <section class="side-section">
            <h3>投递闭环</h3>
            <template v-if="selectedNotice.status === 'DRAFT'">
              <p class="side-muted">草稿通知尚未产生发送批次。</p>
            </template>
            <template v-else-if="latestSelectedBatch">
              <div class="delivery-summary-grid">
                <div>
                  <span>目标人数</span>
                  <strong>{{ latestSelectedBatch.target_count }}</strong>
                </div>
                <div>
                  <span>成功送达</span>
                  <strong>{{ latestSelectedBatch.success_count }}</strong>
                </div>
                <div>
                  <span>失败数</span>
                  <strong>{{ latestSelectedBatch.failed_count }}</strong>
                </div>
              </div>
              <p class="side-muted">
                最近批次：{{ latestSelectedBatch.batch_no }} · {{ formatDateTime(latestSelectedBatch.started_at) }}
              </p>
            </template>
            <p v-else class="side-muted">当前通知暂无发送批次，请通过“发送通知”创建首个投递批次。</p>
          </section>

          <section class="side-section">
            <h3>触达范围</h3>
            <p>{{ selectedNoticeDetail?.target_summary || '全体在读学生' }}</p>
          </section>

          <div class="side-actions">
            <a-button @click="openEditor(selectedNotice)">
              <template #icon><EditOutlined /></template>
              编辑内容
            </a-button>
            <a-button
              type="primary"
              :disabled="selectedNotice.status !== 'PUBLISHED'"
              @click="openDispatch(selectedNotice)"
            >
              <template #icon><SendOutlined /></template>
              发送通知
            </a-button>
            <a-button :disabled="selectedNotice.status === 'DRAFT'" @click="openBatches(selectedNotice)">
              <template #icon><FolderOpenOutlined /></template>
              查看批次
            </a-button>
            <a-button
              danger
              :disabled="selectedNotice.status !== 'PUBLISHED'"
              @click="onArchive(selectedNotice.id)"
            >
              <template #icon><InboxOutlined /></template>
              归档通知
            </a-button>
          </div>
        </a-spin>
      </template>
      <a-empty v-else description="请选择记录" />
    </aside>

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
                <a-form-item label="role_codes">
                  <a-select
                    v-model:value="form.target_rule.role_codes"
                    mode="tags"
                    style="width: 100%"
                    placeholder="输入后回车"
                    :disabled="editorStatus === 'ARCHIVED'"
                  />
                  <div class="muted mt8">
                    按绑定用户角色进一步过滤命中对象；为空时不按角色筛选。
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
                <template #icon><EyeOutlined /></template>
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
                <template #icon><SaveOutlined /></template>
                保存
              </a-button>
              <a-button @click="resetForm">
                <template #icon><CloseOutlined /></template>
                关闭
              </a-button>
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
                <template #icon><UnorderedListOutlined /></template>
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
            <a-button type="primary" html-type="submit">
              <template #icon><SearchOutlined /></template>
              筛选
            </a-button>
          </a-form-item>
          <a-form-item>
            <a-button @click="resetDeliveryFilters">
              <template #icon><ReloadOutlined /></template>
              重置
            </a-button>
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
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  NotificationOutlined,
  SendOutlined,
  SearchOutlined,
  PlusOutlined,
  EditOutlined,
  CloudUploadOutlined,
  FolderOpenOutlined,
  InboxOutlined,
  EyeOutlined,
  SaveOutlined,
  CloseOutlined,
  UnorderedListOutlined,
  ReloadOutlined
} from '@ant-design/icons-vue'
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
const selectedNoticeId = ref<number | null>(null)
const selectedNotice = computed(() => {
  if (selectedNoticeId.value == null) return null
  return rows.value.find((item) => item.id === selectedNoticeId.value) ?? null
})
const selectedNoticeLoading = ref(false)
const selectedNoticeDetail = ref<NoticeOut | null>(null)
const selectedNoticeBatchesLoading = ref(false)
const selectedNoticeBatches = ref<NoticeBatch[]>([])
const batchCache = new Map<number, NoticeBatch[]>()
const latestSelectedBatch = computed(() => selectedNoticeBatches.value[0] ?? null)
const selectedNoticeChannelsLabel = computed(() => {
  if (!selectedNoticeDetail.value) return '-'
  const labels = parseChannels(selectedNoticeDetail.value.channels).map((item) => channelLabel(item))
  return labels.length ? labels.join(' / ') : '-'
})

const metrics = computed(() => [
  {
    key: 'total',
    label: '通知总数',
    value: pagination.total || rows.value.length,
    sub: '当前筛选结果',
    icon: NotificationOutlined,
  },
  {
    key: 'draft',
    label: '待发布',
    value: rows.value.filter((item) => item.status === 'DRAFT').length,
    sub: '草稿通知',
    icon: ClockCircleOutlined,
  },
  {
    key: 'published',
    label: '发送中',
    value: rows.value.filter((item) => item.status === 'PUBLISHED').length,
    sub: '可投递通知',
    icon: SendOutlined,
  },
  {
    key: 'archived',
    label: '已完成',
    value: rows.value.filter((item) => item.status === 'ARCHIVED').length,
    sub: '归档通知',
    icon: CheckCircleOutlined,
  },
])

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
    syncSelectedNotice()
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

function clearSelectedNotice() {
  selectedNoticeId.value = null
  selectedNoticeDetail.value = null
  selectedNoticeBatches.value = []
  selectedNoticeLoading.value = false
  selectedNoticeBatchesLoading.value = false
}

async function loadSelectedNoticeDetail(id: number, force = false) {
  selectedNoticeLoading.value = true
  try {
    const detail = await loadNoticeDetail(id, force)
    if (selectedNoticeId.value === id) {
      selectedNoticeDetail.value = detail
    }
  } catch {
    if (selectedNoticeId.value === id) {
      selectedNoticeDetail.value = null
    }
  } finally {
    if (selectedNoticeId.value === id) {
      selectedNoticeLoading.value = false
    }
  }
}

async function loadSelectedNoticeBatches(id: number, status: NoticeStatus, force = false) {
  if (status === 'DRAFT') {
    selectedNoticeBatchesLoading.value = false
    selectedNoticeBatches.value = []
    return
  }
  if (!force && batchCache.has(id)) {
    selectedNoticeBatchesLoading.value = false
    selectedNoticeBatches.value = batchCache.get(id) ?? []
    return
  }
  selectedNoticeBatchesLoading.value = true
  try {
    const resp = await listNoticeBatches(id)
    const items = sortBatches(resp.data)
    batchCache.set(id, items)
    if (selectedNoticeId.value === id) {
      selectedNoticeBatches.value = items
    }
  } catch {
    if (selectedNoticeId.value === id) {
      selectedNoticeBatches.value = []
    }
  } finally {
    if (selectedNoticeId.value === id) {
      selectedNoticeBatchesLoading.value = false
    }
  }
}

async function selectNotice(record: NoticeBrief, force = false) {
  selectedNoticeId.value = record.id
  selectedNoticeDetail.value = force ? null : (detailCache.get(record.id) ?? null)
  selectedNoticeBatches.value = force ? [] : (batchCache.get(record.id) ?? [])
  await Promise.all([
    loadSelectedNoticeDetail(record.id, force),
    loadSelectedNoticeBatches(record.id, record.status, force),
  ])
}

function syncSelectedNotice() {
  if (selectedNoticeId.value == null) return
  const current = rows.value.find((item) => item.id === selectedNoticeId.value)
  if (!current) {
    clearSelectedNotice()
    return
  }
  void selectNotice(current, true)
}

function noticeRowProps(record: NoticeBrief) {
  return {
    class: 'selectable-notice-row',
    onClick: () => {
      void selectNotice(record)
    },
  }
}

function noticeRowClassName(record: NoticeBrief) {
  return record.id === selectedNoticeId.value
    ? 'selectable-notice-row selected-notice-row'
    : 'selectable-notice-row'
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

  selectedNoticeId.value = record.id
  editingId.value = record.id
  drawerLoading.value = true
  try {
    const detail = await loadNoticeDetail(record.id)
    currentDetail.value = detail
    editorStatus.value = detail.status
    if (selectedNoticeId.value === record.id) {
      selectedNoticeDetail.value = detail
    }
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
  batchCache.delete(id)
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
  batchCache.delete(id)
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
  selectedNoticeId.value = record.id
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
  selectedNoticeId.value = record.id
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
    batchCache.set(id, batchesDrawer.items)
    if (selectedNoticeId.value === id) {
      selectedNoticeDetail.value = detail
      selectedNoticeBatches.value = batchesDrawer.items
    }
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
.notice-page {
  padding-right: 364px;
}

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

.notice-side-panel {
  position: fixed;
  top: 58px;
  right: 0;
  bottom: 0;
  z-index: 12;
  width: 350px;
  overflow-y: auto;
  padding: 18px;
  background: #fff;
  border-left: 1px solid var(--line-soft);
  box-shadow: var(--shadow-card);
}

.side-panel-head,
.notice-preview,
.side-actions,
.side-kv {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.side-panel-head {
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--line-soft);
}

.side-panel-head strong {
  color: var(--text);
  font-size: 16px;
}

.side-panel-head :deep(.ant-btn) {
  color: var(--text-3);
}

.side-mini-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 16px;
}

.side-mini-stats div {
  min-height: 70px;
  padding: 10px;
  background: #fff7f8;
  border: 1px solid #ffe4e8;
  border-radius: 10px;
}

.side-mini-stats :deep(.anticon) {
  color: var(--ruc-red);
  font-size: 14px;
}

.side-mini-stats strong {
  display: block;
  margin-top: 6px;
  color: var(--ruc-red);
  font-family: var(--font-number);
  font-size: 22px;
  line-height: 1;
}

.side-mini-stats span {
  display: block;
  margin-top: 5px;
  color: var(--text-2);
  font-size: 12px;
}

.side-section {
  padding: 14px 0;
  border-top: 1px solid var(--line-soft);
}

.side-section h3 {
  margin: 0 0 10px;
  color: var(--text);
  font-size: 14px;
}

.notice-preview {
  align-items: flex-start;
  padding-top: 0;
  border-top: 0;
}

.notice-preview p,
.side-muted {
  margin: 0;
  color: var(--text-3);
  font-size: 12px;
  line-height: 1.7;
}

.notice-preview h3 {
  margin: 6px 0 0;
  color: var(--text);
  font-size: 16px;
  line-height: 1.45;
}

.side-kv {
  min-height: 30px;
  color: var(--text-3);
  font-size: 12px;
}

.side-kv strong {
  color: var(--text-2);
  font-weight: 600;
}

.tag-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.delivery-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 10px;
}

.delivery-summary-grid div {
  padding: 10px;
  background: #fff7f8;
  border: 1px solid #ffe4e8;
  border-radius: 10px;
}

.delivery-summary-grid span {
  display: block;
  color: var(--text-3);
  font-size: 12px;
}

.delivery-summary-grid strong {
  display: block;
  margin-top: 6px;
  color: var(--ruc-red);
  font-family: var(--font-number);
  font-size: 22px;
  line-height: 1;
}

.delivery-ring {
  display: grid;
  width: 118px;
  height: 118px;
  place-items: center;
  margin: 8px auto 12px;
  color: var(--ruc-red);
  background:
    radial-gradient(circle, #fff 0 52%, transparent 53%),
    conic-gradient(var(--ruc-red) var(--notice-progress), #edf0f5 0);
  border-radius: 999px;
}

.delivery-ring div {
  font-family: var(--font-number);
  font-size: 24px;
  font-weight: 800;
}

.side-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 16px;
}

.side-actions .ant-btn {
  width: 100%;
}

:deep(.selectable-notice-row > td) {
  cursor: pointer;
}

:deep(.selected-notice-row > td) {
  background: #fff4f5 !important;
}

@media (max-width: 1320px) {
  .notice-page {
    padding-right: 0;
  }

  .notice-side-panel {
    position: static;
    width: auto;
    margin-top: 14px;
    border: 1px solid var(--line-soft);
    border-radius: 12px;
  }

  .delivery-summary-grid,
  .side-actions {
    grid-template-columns: 1fr;
  }
}
</style>
