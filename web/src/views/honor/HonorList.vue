<template>
  <div class="honor-page">
    <a-page-header title="荣誉公示管理" sub-title="维护学生荣誉记录、公示状态与历史记录" />

    <div class="metric-grid">
      <div v-for="metric in metrics" :key="metric.key" class="metric-tile">
        <span class="metric-icon"><component :is="metric.icon" /></span>
        <div class="metric-label">{{ metric.label }}</div>
        <div class="metric-value">{{ metric.value }}</div>
        <div class="metric-sub">{{ metric.sub }}</div>
      </div>
    </div>

    <div class="honor-workbench">
      <section class="honor-main">
        <a-card :bordered="false" class="mb16">
          <a-form layout="inline" :model="filters" @finish="onSearch">
            <a-form-item label="关键字">
              <a-input
                v-model:value="filters.q"
                placeholder="标题 / 授奖单位 / 获奖人"
                allow-clear
                style="width: 220px"
              />
            </a-form-item>
            <a-form-item label="类别">
              <a-select
                v-model:value="filters.category_code"
                :options="categorySelectOptions"
                allow-clear
                show-search
                placeholder="全部类别"
                style="width: 200px"
                :filter-option="filterSelectOption"
              />
            </a-form-item>
            <a-form-item label="年份">
              <a-select
                v-model:value="filters.year"
                allow-clear
                placeholder="全部年份"
                style="width: 140px"
              >
                <a-select-option
                  v-for="year in YEAR_OPTIONS"
                  :key="year"
                  :value="year"
                >
                  {{ year }} 年
                </a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item label="级别">
              <a-select v-model:value="filters.level" style="width: 140px" allow-clear>
                <a-select-option value="NATIONAL">国家级</a-select-option>
                <a-select-option value="PROVINCIAL">省部级</a-select-option>
                <a-select-option value="MINISTERIAL">厅局级</a-select-option>
                <a-select-option value="SCHOOL">校级</a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item label="状态">
              <a-select v-model:value="filters.status" style="width: 140px" allow-clear>
                <a-select-option value="ACTIVE">生效</a-select-option>
                <a-select-option value="ARCHIVED">归档</a-select-option>
                <a-select-option value="REVOKED">撤销</a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item label="类型">
              <a-select
                v-model:value="filters.honor_type"
                style="width: 130px"
                allow-clear
              >
                <a-select-option value="PERSONAL">个人</a-select-option>
                <a-select-option value="COLLECTIVE">集体</a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item>
              <a-space wrap>
      <a-button type="primary" html-type="submit">
        <template #icon><SearchOutlined /></template>
        查询
      </a-button>
      <a-button @click="onResetFilters">
        <template #icon><ReloadOutlined /></template>
        重置
      </a-button>
      <a-button @click="openCategoryManager">
        <template #icon><SettingOutlined /></template>
        类别维护
      </a-button>
      <a-button @click="openImportModal">
        <template #icon><ImportOutlined /></template>
        批量导入
      </a-button>
      <a-button type="primary" @click="openEditor()">
        <template #icon><PlusOutlined /></template>
        新增荣誉
      </a-button>
    </a-space>
            </a-form-item>
          </a-form>
        </a-card>

        <a-table
          :columns="columns"
          :data-source="rows"
          :loading="loading"
          :pagination="pagination"
          :scroll="{ x: 1610 }"
          row-key="id"
          @change="onTableChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'title'">
              <div class="title-cell">
                <div class="title-main">{{ record.title }}</div>
                <div v-if="isHistoricalRecord(record) || record.summary" class="cell-subtle">
                  <a-tag v-if="isHistoricalRecord(record)" color="orange">历史荣誉</a-tag>
                  <span>{{ historyReasonText(record) || record.summary }}</span>
                </div>
              </div>
            </template>

            <template v-else-if="column.key === 'category'">
              <div class="category-cell">
                <span>{{ categoryLabel(record) }}</span>
                <a-tag
                  v-if="categoryMap.get(record.category_code)?.is_active === false"
                  class="mt4"
                >
                  已停用
                </a-tag>
              </div>
            </template>

            <template v-else-if="column.key === 'level'">
              {{ levelLabel(record.level) }}
            </template>

            <template v-else-if="column.key === 'honor_type'">
              <a-tag :color="record.is_collective ? 'blue' : 'purple'">
                {{ record.is_collective ? '集体' : '个人' }}
              </a-tag>
            </template>

            <template v-else-if="column.key === 'recipients'">
              {{ (record.recipient_names || []).join('、') || '-' }}
            </template>

            <template v-else-if="column.key === 'status'">
              <div class="status-cell">
                <a-tag :color="statusColor(record.status)">{{ statusLabel(record.status) }}</a-tag>
                <a-tag
                  v-if="isHistoricalRecord(record) && record.status === 'ACTIVE'"
                  color="orange"
                >
                  历史荣誉
                </a-tag>
              </div>
            </template>

            <template v-else-if="column.key === 'maintenance'">
              <div class="maintenance-cell">
                <div>{{ record.updated_by_name || '-' }}</div>
                <div class="cell-subtle">{{ formatDateTime(record.updated_at) }}</div>
              </div>
            </template>

            <template v-else-if="column.key === 'actions'">
              <a-space size="small">
                <a-button type="link" size="small" @click="openEditor(record as HonorRecordBrief)">
                  <template #icon><EditOutlined /></template>
                  编辑
                </a-button>
                <a-popconfirm
                  v-if="record.status === 'ACTIVE'"
                  title="确定将该荣誉归档为历史荣誉？"
                  @confirm="onArchive(record.id, 'ARCHIVED')"
                >
                  <a-button type="link" size="small">
                    <template #icon><InboxOutlined /></template>
                    归档
                  </a-button>
                </a-popconfirm>
                <a-popconfirm
                  v-if="record.status !== 'REVOKED'"
                  title="确定撤销该荣誉展示？"
                  @confirm="onArchive(record.id, 'REVOKED')"
                >
                  <a-button type="link" size="small" danger>
                    <template #icon><RollbackOutlined /></template>
                    撤销
                  </a-button>
                </a-popconfirm>
              </a-space>
            </template>
          </template>
        </a-table>
      </section>

      <aside class="honor-side panel-card">
        <div class="side-head">
          <div>
            <div class="side-title">公示治理</div>
            <div class="side-sub">类别、导入和状态分布</div>
          </div>
          <a-button type="primary" size="small" @click="openEditor()">
            <template #icon><PlusOutlined /></template>
            新增
          </a-button>
        </div>

        <div class="status-stack">
          <div v-for="item in statusSummary" :key="item.key" class="status-row">
            <span :class="['status-dot', item.key]"></span>
            <span class="status-name">{{ item.label }}</span>
            <strong>{{ item.count }}</strong>
          </div>
        </div>

        <div class="side-section">
          <div class="side-section-title">类别维护</div>
          <div class="category-chip-list">
            <span
              v-for="category in categoryRows.slice(0, 8)"
              :key="category.code"
              class="side-category-chip"
              :class="{ inactive: !category.is_active }"
            >
              {{ category.name }}
            </span>
          </div>
          <a-button block class="mt12" @click="openCategoryManager">打开类别维护</a-button>
        </div>

        <div class="side-section">
          <div class="side-section-title">批量导入</div>
          <div class="side-hint">
            导入前会先完成校验预览；存在致命错误时不能正式提交。
          </div>
          <a-button block type="primary" ghost @click="openImportModal">进入导入</a-button>
        </div>
      </aside>
    </div>

    <a-drawer
      :open="showDrawer"
      :title="editingId ? '编辑荣誉记录' : '新增荣誉记录'"
      width="720"
      @close="resetForm"
    >
      <a-spin :spinning="drawerLoading">
        <a-alert
          v-if="currentDetail && isHistoricalRecord(currentDetail)"
          class="mb16"
          type="warning"
          show-icon
          message="当前记录按历史荣誉展示"
          :description="historyReasonText(currentDetail)"
        />

        <a-descriptions
          v-if="currentDetail"
          :column="1"
          size="small"
          class="mb16"
        >
          <a-descriptions-item label="当前状态">
            {{ statusLabel(currentDetail.status) }}
          </a-descriptions-item>
          <a-descriptions-item label="最近维护人">
            {{ currentDetail.updated_by_name || '-' }}
          </a-descriptions-item>
          <a-descriptions-item label="最近维护时间">
            {{ formatDateTime(currentDetail.updated_at) }}
          </a-descriptions-item>
          <a-descriptions-item v-if="currentDetail.archive_reason" label="归档/撤销原因">
            {{ currentDetail.archive_reason }}
          </a-descriptions-item>
        </a-descriptions>

        <a-form layout="vertical" :model="form" @finish="onSubmit">
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="标题" :rules="[{ required: true }]">
                <a-input v-model:value="form.title" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="荣誉类别" :rules="[{ required: true }]">
                <a-select
                  v-model:value="form.category_code"
                  :options="categorySelectOptions"
                  show-search
                  placeholder="请选择类别"
                  :filter-option="filterSelectOption"
                />
              </a-form-item>
            </a-col>
          </a-row>

          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="级别" :rules="[{ required: true }]">
                <a-select v-model:value="form.level">
                  <a-select-option value="NATIONAL">国家级</a-select-option>
                  <a-select-option value="PROVINCIAL">省部级</a-select-option>
                  <a-select-option value="MINISTERIAL">厅局级</a-select-option>
                  <a-select-option value="SCHOOL">校级</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="授奖单位" :rules="[{ required: true }]">
                <a-input v-model:value="form.awarded_by" />
              </a-form-item>
            </a-col>
          </a-row>

          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="公布日期" :rules="[{ required: true }]">
                <a-date-picker
                  v-model:value="form.announced_at"
                  value-format="YYYY-MM-DD"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="文号 / 证书编号">
                <a-input v-model:value="form.document_no" />
              </a-form-item>
            </a-col>
          </a-row>

          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="生效开始">
                <a-date-picker
                  v-model:value="form.effective_from"
                  value-format="YYYY-MM-DD"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="展示有效期截止">
                <a-date-picker
                  v-model:value="form.effective_to"
                  value-format="YYYY-MM-DD"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
          </a-row>

          <a-form-item label="简介">
            <a-textarea v-model:value="form.summary" :rows="3" />
          </a-form-item>
          <a-form-item label="榜样风采（Markdown）">
            <a-textarea v-model:value="form.story_md" :rows="5" />
          </a-form-item>
          <a-form-item label="获奖感言">
            <a-textarea v-model:value="form.acceptance_speech" :rows="3" />
          </a-form-item>

          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="展示顺序">
                <a-input-number
                  v-model:value="form.display_order"
                  :min="0"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="封面图片 URL">
                <a-input
                  v-model:value="form.cover_image_url"
                  placeholder="用于榜样宣传卡片展示"
                />
              </a-form-item>
            </a-col>
          </a-row>

          <a-form-item label="媒体 JSON">
            <a-textarea
              v-model:value="form.media_text"
              :rows="3"
              placeholder='如 {"photos":["https://..."],"videos":[]}'
            />
          </a-form-item>

          <a-form-item label="获奖人 / 集体成员" required>
            <div class="recipient-editor">
              <div
                v-for="(recipient, index) in form.recipients"
                :key="index"
                class="recipient-row-editor"
              >
                <a-input
                  v-model:value="recipient.display_name"
                  placeholder="姓名或集体名称"
                />
                <a-input
                  v-model:value="recipient.student_no_snapshot"
                  placeholder="学号"
                />
                <a-input
                  v-model:value="recipient.major_snapshot"
                  placeholder="专业"
                />
                <a-input
                  v-model:value="recipient.grade_snapshot"
                  placeholder="年级"
                />
                <a-input
                  v-model:value="recipient.class_snapshot"
                  placeholder="班级"
                />
                <a-input
                  v-model:value="recipient.role_in_collective"
                  placeholder="集体角色"
                />
                <a-button
                  danger
                  :disabled="form.recipients.length <= 1"
                  @click="removeRecipient(index)"
                >
                  删除
                </a-button>
              </div>
              <a-button block @click="addRecipient">新增获奖人 / 成员</a-button>
            </div>
          </a-form-item>

          <a-space direction="vertical" style="width: 100%">
            <a-checkbox v-model:checked="form.is_collective">集体荣誉</a-checkbox>
            <a-checkbox v-model:checked="form.consent_flag">已获获奖人同意展示</a-checkbox>
          </a-space>

          <div class="drawer-actions">
          <a-space>
            <a-button type="primary" html-type="submit" :loading="submitting">
              <template #icon><SaveOutlined /></template>
              保存
            </a-button>
            <a-button @click="resetForm">
              <template #icon><CloseOutlined /></template>
              取消
            </a-button>
          </a-space>
        </div>
        </a-form>
      </a-spin>
    </a-drawer>

    <a-modal
      :open="showCategoryModal"
      title="荣誉类别维护"
      width="980"
      :footer="null"
      @cancel="closeCategoryManager"
    >
      <a-alert
        class="mb16"
        type="info"
        show-icon
        message="类别编码建议一经启用后保持稳定"
        description="当前后端以类别编码作为 upsert 键。编辑现有类别时保留编码不变，可避免生成重复类别。"
      />

      <a-row :gutter="16">
        <a-col :span="14">
          <a-table
            :columns="categoryColumns"
            :data-source="categoryRows"
            :loading="categoryLoading"
            row-key="code"
            :pagination="false"
            size="small"
           :scroll="{ x: 'max-content' }">
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'active'">
                <a-tag :color="record.is_active ? 'green' : 'default'">
                  {{ record.is_active ? '启用中' : '已停用' }}
                </a-tag>
              </template>
              <template v-else-if="column.key === 'actions'">
                <a-button type="link" size="small" @click="onEditCategory(record as HonorCategoryOut)">
                  编辑
                </a-button>
              </template>
            </template>
          </a-table>
        </a-col>

        <a-col :span="10">
          <a-card :bordered="false" class="category-form-card">
            <div class="section-title">
              {{ editingCategoryCode ? '编辑类别' : '新增类别' }}
            </div>
            <a-form layout="vertical" :model="categoryForm" @finish="onSubmitCategory">
              <a-form-item label="类别编码" :rules="[{ required: true }]">
                <a-input
                  v-model:value="categoryForm.code"
                  :disabled="Boolean(editingCategoryCode)"
                  placeholder="如：NATIONAL_SCHOLARSHIP"
                />
              </a-form-item>
              <a-form-item label="类别名称" :rules="[{ required: true }]">
                <a-input v-model:value="categoryForm.name" placeholder="如：国家奖学金" />
              </a-form-item>
              <a-form-item label="排序">
                <a-input-number v-model:value="categoryForm.sort_order" :min="0" style="width: 100%" />
              </a-form-item>
              <a-form-item label="说明">
                <a-textarea v-model:value="categoryForm.description" :rows="4" />
              </a-form-item>
              <a-form-item label="是否启用">
                <a-switch v-model:checked="categoryForm.is_active" checked-children="启用" un-checked-children="停用" />
              </a-form-item>

              <a-space>
                <a-button type="primary" html-type="submit" :loading="categorySubmitting">
                  <template #icon><SaveOutlined /></template>
                  保存类别
                </a-button>
                <a-button @click="resetCategoryForm">
                  <template #icon><PlusOutlined /></template>
                  新建一条
                </a-button>
              </a-space>
            </a-form>
          </a-card>
        </a-col>
      </a-row>
    </a-modal>

    <a-modal
      :open="showImportModal"
      title="荣誉批量导入"
      width="1080"
      :footer="null"
      @cancel="closeImportModal"
    >
      <a-alert
        class="mb16"
        type="info"
        show-icon
        message="导入流程沿用校验预览、整批提交、错误报告下载的模式"
        description="当前导入接口已接入校验预览、整批提交和错误报告下载，可直接选择 Excel 文件发起校验。"
      />

      <template>
        <a-card :bordered="false" class="mb16">
          <a-space>
            <a-upload :show-upload-list="false" :before-upload="onBeforeHonorImport">
              <a-button type="primary" :loading="importLoading">选择 Excel 文件</a-button>
            </a-upload>
            <span class="cell-subtle">建议使用最终公示名单对应的标准导入模板。</span>
          </a-space>
        </a-card>

        <a-card v-if="importPreview" :bordered="false" class="mb16">
          <a-descriptions title="校验结果" :column="4" size="small">
            <a-descriptions-item label="批次号">{{ importPreview.batch.batch_no }}</a-descriptions-item>
            <a-descriptions-item label="文件名">{{ importPreview.batch.filename }}</a-descriptions-item>
            <a-descriptions-item label="总行数">{{ importPreview.batch.total_rows }}</a-descriptions-item>
            <a-descriptions-item label="状态">
              <a-tag :color="importStatusColor(importPreview.batch.status)">
                {{ importPreview.batch.status }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="正常">
              <span style="color: #389e0d">{{ importPreview.batch.ok_rows }}</span>
            </a-descriptions-item>
            <a-descriptions-item label="警告">
              <span style="color: #d48806">{{ importPreview.batch.warn_rows }}</span>
            </a-descriptions-item>
            <a-descriptions-item label="致命">
              <span style="color: #cf1322">{{ importPreview.batch.fatal_rows }}</span>
            </a-descriptions-item>
          </a-descriptions>

          <a-table
            :columns="importRowColumns"
            :data-source="importPreview.rows"
            row-key="id"
            size="small"
            :pagination="{ pageSize: 10 }"
            class="mt8"
           :scroll="{ x: 'max-content' }">
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'severity'">
                <a-tag :color="severityColor(record.severity)">{{ record.severity }}</a-tag>
              </template>
            </template>
          </a-table>

          <a-space class="mt8">
            <a-button
              type="primary"
              :loading="importLoading"
              :disabled="importPreview.batch.fatal_rows > 0"
              @click="onCommitHonorImport"
            >
              <template #icon><UploadOutlined /></template>
              {{ importPreview.batch.fatal_rows > 0 ? '存在致命错误，暂不能提交' : '正式提交' }}
            </a-button>
            <a-button @click="onDownloadImportErrors(importPreview.batch.id)">
              <template #icon><DownloadOutlined /></template>
              下载错误报告
            </a-button>
          </a-space>
        </a-card>

        <a-card title="历史批次" :bordered="false">
          <a-table
            :columns="importBatchColumns"
            :data-source="importBatches"
            :loading="importBatchLoading"
            :pagination="importBatchPagination"
            row-key="id"
            size="small"
            @change="onImportTableChange"
           :scroll="{ x: 'max-content' }">
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-tag :color="importStatusColor(record.status)">{{ record.status }}</a-tag>
              </template>
              <template v-else-if="column.key === 'actions'">
                <a-space size="small">
                  <a-button type="link" size="small" @click="onOpenImportBatch(record.id)">查看</a-button>
                  <a-button type="link" size="small" @click="onDownloadImportErrors(record.id)">错误报告</a-button>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-card>
      </template>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  InboxOutlined,
  TrophyOutlined,
  SearchOutlined,
  ReloadOutlined,
  SettingOutlined,
  ImportOutlined,
  PlusOutlined,
  EditOutlined,
  RollbackOutlined,
  SaveOutlined,
  CloseOutlined,
  UploadOutlined,
  DownloadOutlined
} from '@ant-design/icons-vue'
import {
  adminArchiveRecord,
  adminCreateRecord,
  adminGetRecord,
  adminListCategories,
  adminListRecords,
  adminUpdateRecord,
  adminUpsertCategory,
  commitHonorImport,
  downloadHonorImportErrorReport,
  getHonorImport,
  listHonorImports,
  uploadHonorImport,
  type HonorCategoryOut,
  type HonorImportBatchBrief,
  type HonorImportPreviewResult,
  type HonorLevel,
  type HonorRecordBrief,
  type HonorRecordDetail,
  type HonorRecordIn,
  type HonorStatus,
} from '@/api/honor'

const YEAR_OPTIONS = Array.from({ length: 10 }, (_, index) => new Date().getFullYear() - index)

const columns = [
  { title: '荣誉信息', dataIndex: 'title', key: 'title', width: 280 },
  { title: '类别', key: 'category', width: 170 },
  { title: '级别', dataIndex: 'level', key: 'level', width: 100 },
  { title: '类型', key: 'honor_type', width: 90 },
  { title: '授奖单位', dataIndex: 'awarded_by', key: 'awarded_by', width: 180 },
  { title: '获奖人', key: 'recipients', width: 220 },
  { title: '公布日期', dataIndex: 'announced_at', key: 'announced_at', width: 120 },
  { title: '状态', key: 'status', width: 150 },
  { title: '维护信息', key: 'maintenance', width: 180 },
  { title: '操作', key: 'actions', width: 190, fixed: 'right' as const },
]

const categoryColumns = [
  { title: '编码', dataIndex: 'code', key: 'code', width: 170 },
  { title: '名称', dataIndex: 'name', key: 'name', width: 180 },
  { title: '排序', dataIndex: 'sort_order', key: 'sort_order', width: 80 },
  { title: '状态', key: 'active', width: 90 },
  { title: '说明', dataIndex: 'description', key: 'description' },
  { title: '操作', key: 'actions', width: 80 },
]

const importRowColumns = [
  { title: '行号', dataIndex: 'row_no', key: 'row_no', width: 70 },
  { title: '级别', key: 'severity', width: 80 },
  { title: '字段', dataIndex: 'field_name', key: 'field_name', width: 120 },
  { title: '结果', dataIndex: 'result', key: 'result', width: 80 },
  { title: '消息', dataIndex: 'message', key: 'message' },
]

const importBatchColumns = [
  { title: '批次号', dataIndex: 'batch_no', key: 'batch_no', width: 160 },
  { title: '文件名', dataIndex: 'filename', key: 'filename' },
  { title: '状态', key: 'status', width: 120 },
  {
    title: '总行/正常/警告/致命',
    key: 'counts',
    width: 180,
    customRender: ({ record }: { record: HonorImportBatchBrief }) =>
      `${record.total_rows} / ${record.ok_rows} / ${record.warn_rows} / ${record.fatal_rows}`,
  },
  { title: '开始时间', dataIndex: 'started_at', key: 'started_at', width: 180 },
  { title: '操作', key: 'actions', width: 140 },
]

const filters = reactive<{
  q?: string
  category_code?: string
  year?: number
  level?: HonorLevel
  status?: HonorStatus
  honor_type?: 'PERSONAL' | 'COLLECTIVE'
}>({})

const rows = ref<HonorRecordBrief[]>([])
const loading = ref(false)
const pagination = reactive({ current: 1, pageSize: 20, total: 0 })
const metrics = computed(() => [
  {
    key: 'total',
    label: '总数',
    value: pagination.total || rows.value.length,
    sub: '当前筛选结果',
    icon: TrophyOutlined,
  },
  {
    key: 'active',
    label: '待公示/生效',
    value: rows.value.filter((item) => item.status === 'ACTIVE').length,
    sub: '当前页生效',
    icon: CheckCircleOutlined,
  },
  {
    key: 'archived',
    label: '已归档',
    value: rows.value.filter((item) => item.status === 'ARCHIVED').length,
    sub: '历史荣誉',
    icon: InboxOutlined,
  },
  {
    key: 'categories',
    label: '类别数',
    value: categoryRows.value.length,
    sub: '类别维护',
    icon: ClockCircleOutlined,
  },
])
const statusSummary = computed(() => [
  {
    key: 'active',
    label: '生效 / 待公示',
    count: rows.value.filter((item) => item.status === 'ACTIVE').length,
  },
  {
    key: 'archived',
    label: '历史归档',
    count: rows.value.filter((item) => item.status === 'ARCHIVED').length,
  },
  {
    key: 'revoked',
    label: '撤销记录',
    count: rows.value.filter((item) => item.status === 'REVOKED').length,
  },
])

const categoryRows = ref<HonorCategoryOut[]>([])
const categoryLoading = ref(false)
const lastTouchedCategory = ref<HonorCategoryOut | null>(null)

const categoryMap = computed(() => {
  const map = new Map<string, HonorCategoryOut>()
  for (const category of categoryRows.value) {
    map.set(category.code, category)
  }
  return map
})

const categorySelectOptions = computed(() => {
  const merged = new Map<string, string>()
  for (const category of categoryRows.value) {
    merged.set(category.code, category.name)
  }
  for (const record of rows.value) {
    if (record.category_code) {
      merged.set(record.category_code, record.category_name || merged.get(record.category_code) || record.category_code)
    }
  }
  if (currentDetail.value?.category_code) {
    merged.set(
      currentDetail.value.category_code,
      currentDetail.value.category_name || merged.get(currentDetail.value.category_code) || currentDetail.value.category_code,
    )
  }
  if (form.category_code) {
    merged.set(form.category_code, merged.get(form.category_code) || form.category_code)
  }
  return Array.from(merged.entries()).map(([value, label]) => ({ value, label }))
})

type HistoricalLike = {
  status?: string
  effective_to?: string | null
  is_historical?: boolean | null
  history_reason?: string | null
  archive_reason?: string | null
  category_code?: string
  category_name?: string | null
}

function filterSelectOption(input: string, option?: { label?: unknown }) {
  return String(option?.label ?? '').toLowerCase().includes(input.trim().toLowerCase())
}

function levelLabel(level: HonorLevel) {
  return {
    NATIONAL: '国家级',
    PROVINCIAL: '省部级',
    MINISTERIAL: '厅局级',
    SCHOOL: '校级',
  }[level] || level
}

function statusLabel(status: HonorStatus | string) {
  return {
    ACTIVE: '生效',
    ARCHIVED: '归档',
    REVOKED: '撤销',
  }[status as HonorStatus] || status
}

function statusColor(status: HonorStatus | string) {
  return status === 'ACTIVE' ? 'green' : status === 'REVOKED' ? 'red' : 'default'
}

function importStatusColor(status: string) {
  return status === 'COMPLETED' || status === 'COMMITTED'
    ? 'green'
    : status === 'FAILED' || status === 'ROLLBACK'
      ? 'red'
      : status === 'VALIDATED'
        ? 'blue'
        : 'default'
}

function severityColor(severity: string) {
  return severity === 'FATAL' ? 'red' : severity === 'WARN' ? 'orange' : 'green'
}

function formatDate(value?: string | null) {
  return value ? value.slice(0, 10) : '-'
}

function formatDateTime(value?: string | null) {
  if (!value) return '-'
  return value.replace('T', ' ').slice(0, 16)
}

function isPastDate(value?: string | null) {
  if (!value) return false
  const target = new Date(`${value.slice(0, 10)}T00:00:00`)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return Number.isFinite(target.getTime()) && target.getTime() < today.getTime()
}

function isHistoricalRecord(record: HistoricalLike) {
  if (typeof record.is_historical === 'boolean') return record.is_historical
  if (record.status === 'ARCHIVED') return true
  if (record.status === 'REVOKED') return false
  return isPastDate(record.effective_to)
}

function historyReasonText(record: HistoricalLike) {
  if (record.history_reason) return record.history_reason
  if (record.status === 'ARCHIVED') return record.archive_reason || '已归档'
  if (isPastDate(record.effective_to)) return `展示有效期已于 ${formatDate(record.effective_to)} 结束`
  return ''
}

function categoryLabel(record: HistoricalLike) {
  return record.category_name || categoryMap.value.get(record.category_code || '')?.name || record.category_code || '-'
}

function mergeCategories(categories: HonorCategoryOut[], extra?: HonorCategoryOut | null) {
  const map = new Map<string, HonorCategoryOut>()
  for (const category of categories) {
    map.set(category.code, category)
  }
  if (extra && !map.has(extra.code)) {
    map.set(extra.code, extra)
  }
  return Array.from(map.values()).sort((left, right) => {
    if (left.sort_order !== right.sort_order) return left.sort_order - right.sort_order
    return left.id - right.id
  })
}

async function loadCategories() {
  categoryLoading.value = true
  try {
    const resp = await adminListCategories()
    categoryRows.value = mergeCategories(resp.data, lastTouchedCategory.value)
  } finally {
    categoryLoading.value = false
  }
}

async function reload(resetPage = false) {
  if (resetPage) pagination.current = 1
  loading.value = true
  try {
    const resp = await adminListRecords({
      q: filters.q?.trim() || undefined,
      category_code: filters.category_code,
      year: filters.year,
      level: filters.level,
      status: filters.status,
      is_collective: filters.honor_type === 'COLLECTIVE'
        ? true
        : filters.honor_type === 'PERSONAL'
          ? false
          : undefined,
      page: pagination.current,
      size: pagination.pageSize,
    })
    rows.value = resp.data.items
    pagination.total = resp.data.meta.total
  } finally {
    loading.value = false
  }
}

function onSearch() {
  void reload(true).catch(() => undefined)
}

function onResetFilters() {
  filters.q = undefined
  filters.category_code = undefined
  filters.year = undefined
  filters.level = undefined
  filters.status = undefined
  filters.honor_type = undefined
  void reload(true).catch(() => undefined)
}

function onTableChange(p: { current?: number; pageSize?: number }) {
  pagination.current = p.current ?? pagination.current
  pagination.pageSize = p.pageSize ?? pagination.pageSize
  void reload().catch(() => undefined)
}

interface HonorRecipientForm {
  student_id: number | null
  student_no_snapshot: string
  display_name: string
  major_snapshot: string
  grade_snapshot: string
  class_snapshot: string
  role_in_collective: string
}

interface HonorFormState {
  category_code: string
  title: string
  level: HonorLevel
  awarded_by: string
  document_no: string
  announced_at?: string
  effective_from?: string
  effective_to?: string
  is_collective: boolean
  summary: string
  display_order: number
  story_md: string
  acceptance_speech: string
  cover_image_url: string
  media_text: string
  consent_flag: boolean
  recipients: HonorRecipientForm[]
}

interface CategoryFormState {
  id?: number | null
  code: string
  name: string
  description: string
  sort_order: number
  is_active: boolean
}

function createEmptyForm(): HonorFormState {
  return {
    category_code: '',
    title: '',
    level: 'SCHOOL',
    awarded_by: '',
    document_no: '',
    announced_at: undefined,
    effective_from: undefined,
    effective_to: undefined,
    is_collective: false,
    summary: '',
    display_order: 0,
    story_md: '',
    acceptance_speech: '',
    cover_image_url: '',
    media_text: '',
    consent_flag: false,
    recipients: [createEmptyRecipient()],
  }
}

function createEmptyRecipient(): HonorRecipientForm {
  return {
    student_id: null,
    student_no_snapshot: '',
    display_name: '',
    major_snapshot: '',
    grade_snapshot: '',
    class_snapshot: '',
    role_in_collective: '',
  }
}

function buildFormFromDetail(detail: HonorRecordDetail): HonorFormState {
  return {
    category_code: detail.category_code,
    title: detail.title,
    level: detail.level,
    awarded_by: detail.awarded_by,
    document_no: detail.document_no || '',
    announced_at: detail.announced_at,
    effective_from: detail.effective_from || undefined,
    effective_to: detail.effective_to || undefined,
    is_collective: detail.is_collective,
    summary: detail.summary || '',
    display_order: detail.display_order || 0,
    story_md: detail.story_md || '',
    acceptance_speech: detail.acceptance_speech || '',
    cover_image_url: detail.cover_image_url || '',
    media_text: detail.media ? JSON.stringify(detail.media, null, 2) : '',
    consent_flag: detail.consent_flag,
    recipients: (detail.recipients.length ? detail.recipients : [createEmptyRecipient()]).map((recipient) => ({
      student_id: recipient.student_id ?? null,
      student_no_snapshot: recipient.student_no_snapshot ?? '',
      display_name: recipient.display_name,
      major_snapshot: recipient.major_snapshot ?? '',
      grade_snapshot: recipient.grade_snapshot ?? '',
      class_snapshot: recipient.class_snapshot ?? '',
      role_in_collective: recipient.role_in_collective ?? '',
    })),
  }
}

const showDrawer = ref(false)
const drawerLoading = ref(false)
const submitting = ref(false)
const editingId = ref<number | null>(null)
const currentDetail = ref<HonorRecordDetail | null>(null)
const form = reactive<HonorFormState>(createEmptyForm())

function assignForm(next: HonorFormState) {
  Object.assign(form, createEmptyForm(), next)
}

function parseMediaText(): Record<string, unknown> | null | undefined {
  const text = form.media_text.trim()
  if (!text) return null
  try {
    const parsed = JSON.parse(text)
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      message.warning('媒体 JSON 必须是对象')
      return undefined
    }
    return parsed as Record<string, unknown>
  } catch {
    message.warning('媒体 JSON 格式不正确')
    return undefined
  }
}

function normalizedRecipients() {
  return form.recipients
    .map((recipient) => ({
      student_id: recipient.student_id ?? null,
      student_no_snapshot: recipient.student_no_snapshot?.trim() || null,
      display_name: recipient.display_name.trim(),
      major_snapshot: recipient.major_snapshot?.trim() || null,
      grade_snapshot: recipient.grade_snapshot?.trim() || null,
      class_snapshot: recipient.class_snapshot?.trim() || null,
      role_in_collective: recipient.role_in_collective?.trim() || null,
    }))
    .filter((recipient) => recipient.display_name)
}

function buildPayload(media: Record<string, unknown> | null): HonorRecordIn {
  return {
    category_code: form.category_code,
    title: form.title.trim(),
    level: form.level,
    awarded_by: form.awarded_by.trim(),
    document_no: form.document_no.trim() || undefined,
    announced_at: form.announced_at || '',
    effective_from: form.effective_from,
    effective_to: form.effective_to,
    is_collective: form.is_collective,
    summary: form.summary.trim() || undefined,
    display_order: Number(form.display_order || 0),
    story_md: form.story_md.trim() || undefined,
    acceptance_speech: form.acceptance_speech.trim() || undefined,
    cover_image_url: form.cover_image_url.trim() || undefined,
    media,
    consent_flag: form.consent_flag,
    recipients: normalizedRecipients(),
  }
}

function addRecipient() {
  form.recipients.push(createEmptyRecipient())
}

function removeRecipient(index: number) {
  if (form.recipients.length <= 1) return
  form.recipients.splice(index, 1)
}

async function openEditor(record?: HonorRecordBrief | Record<string, unknown>) {
  showDrawer.value = true
  currentDetail.value = null
  if (!categoryRows.value.length) {
    await loadCategories()
  }
  if (!record) {
    editingId.value = null
    assignForm(createEmptyForm())
    return
  }

  editingId.value = Number(record.id)
  drawerLoading.value = true
  try {
    const resp = await adminGetRecord(Number(record.id))
    currentDetail.value = resp.data
    assignForm(buildFormFromDetail(resp.data))
  } finally {
    drawerLoading.value = false
  }
}

function resetForm() {
  showDrawer.value = false
  drawerLoading.value = false
  editingId.value = null
  currentDetail.value = null
  assignForm(createEmptyForm())
}

async function onSubmit() {
  if (!form.title.trim() || !form.category_code || !form.awarded_by.trim() || !form.announced_at) {
    message.warning('请补全标题、荣誉类别、授奖单位和公布日期')
    return
  }
  if (!normalizedRecipients().length) {
    message.warning('请至少填写一位获奖人或一个获奖集体')
    return
  }
  const media = parseMediaText()
  if (media === undefined) return

  submitting.value = true
  try {
    const payload = buildPayload(media)
    if (editingId.value) {
      const resp = await adminUpdateRecord(editingId.value, payload)
      currentDetail.value = resp.data
    } else {
      const resp = await adminCreateRecord(payload)
      currentDetail.value = resp.data
    }
    message.success('保存成功')
    resetForm()
    await reload(true)
  } finally {
    submitting.value = false
  }
}

async function onArchive(id: number, newStatus: HonorStatus) {
  await adminArchiveRecord(id, undefined, newStatus)
  message.success(newStatus === 'REVOKED' ? '已撤销' : '已归档')
  await reload()
}

function createEmptyCategoryForm(): CategoryFormState {
  return {
    code: '',
    name: '',
    description: '',
    sort_order: 0,
    is_active: true,
  }
}

const showCategoryModal = ref(false)
const categorySubmitting = ref(false)
const editingCategoryCode = ref<string | null>(null)
const categoryForm = reactive<CategoryFormState>(createEmptyCategoryForm())

function resetCategoryForm() {
  editingCategoryCode.value = null
  Object.assign(categoryForm, createEmptyCategoryForm())
}

function openCategoryManager() {
  showCategoryModal.value = true
  resetCategoryForm()
  void loadCategories().catch(() => undefined)
}

function closeCategoryManager() {
  showCategoryModal.value = false
  resetCategoryForm()
}

function onEditCategory(record: HonorCategoryOut) {
  editingCategoryCode.value = record.code
  Object.assign(categoryForm, {
    id: record.id,
    code: record.code,
    name: record.name,
    description: record.description || '',
    sort_order: record.sort_order,
    is_active: record.is_active,
  })
}

async function onSubmitCategory() {
  const normalizedCode = categoryForm.code.trim().toUpperCase()
  const normalizedName = categoryForm.name.trim()
  if (!normalizedCode || !normalizedName) {
    message.warning('请补全类别编码和类别名称')
    return
  }

  categorySubmitting.value = true
  try {
    const resp = await adminUpsertCategory({
      ...categoryForm,
      code: normalizedCode,
      name: normalizedName,
      sort_order: Number(categoryForm.sort_order || 0),
      description: categoryForm.description?.trim() || null,
    })
    lastTouchedCategory.value = resp.data
    message.success(editingCategoryCode.value ? '类别已更新' : '类别已新增')
    resetCategoryForm()
    await loadCategories()
  } finally {
    categorySubmitting.value = false
  }
}

const showImportModal = ref(false)
const importLoading = ref(false)
const importPreview = ref<HonorImportPreviewResult | null>(null)
const importBatches = ref<HonorImportBatchBrief[]>([])
const importBatchLoading = ref(false)
const importBatchPagination = reactive({ current: 1, pageSize: 10, total: 0 })

async function loadImportBatches() {
  importBatchLoading.value = true
  try {
    const resp = await listHonorImports({
      page: importBatchPagination.current,
      size: importBatchPagination.pageSize,
    })
    importBatches.value = resp.data.items
    importBatchPagination.total = resp.data.meta.total
  } finally {
    importBatchLoading.value = false
  }
}

function openImportModal() {
  showImportModal.value = true
  importPreview.value = null
  void loadImportBatches().catch(() => undefined)
}

function closeImportModal() {
  showImportModal.value = false
  importPreview.value = null
}

async function onBeforeHonorImport(file: File) {
  importLoading.value = true
  try {
    const resp = await uploadHonorImport(file)
    importPreview.value = resp.data
    message.success('荣誉导入校验完成')
    await loadImportBatches()
  } catch {
    return false
  } finally {
    importLoading.value = false
  }
  return false
}

async function onCommitHonorImport() {
  if (!importPreview.value) return
  importLoading.value = true
  try {
    await commitHonorImport(importPreview.value.batch.id)
    message.success('荣誉导入已提交')
    importPreview.value = null
    await Promise.all([loadImportBatches(), reload(true)])
  } finally {
    importLoading.value = false
  }
}

function onDownloadImportErrors(batchId: number) {
  void downloadHonorImportErrorReport(batchId)
}

async function onOpenImportBatch(batchId: number) {
  importLoading.value = true
  try {
    const resp = await getHonorImport(batchId)
    importPreview.value = resp.data
  } finally {
    importLoading.value = false
  }
}

function onImportTableChange(p: { current?: number; pageSize?: number }) {
  importBatchPagination.current = p.current ?? importBatchPagination.current
  importBatchPagination.pageSize = p.pageSize ?? importBatchPagination.pageSize
  void loadImportBatches().catch(() => undefined)
}

onMounted(() => {
  void Promise.allSettled([loadCategories(), reload()])
})
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }
.mt4 { margin-top: 4px; }
.mt8 { margin-top: 8px; }

.title-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.title-main {
  font-weight: 600;
  color: #1f2937;
}

.cell-subtle {
  color: #6b7280;
  font-size: 12px;
  line-height: 1.6;
}

.category-cell,
.maintenance-cell,
.status-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.drawer-actions {
  margin-top: 24px;
}

.recipient-editor {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.recipient-row-editor {
  display: grid;
  grid-template-columns: minmax(120px, 1.2fr) repeat(5, minmax(90px, 1fr)) auto;
  gap: 8px;
  align-items: center;
}

.section-title {
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.category-form-card {
  background: #fafafa;
}

.honor-workbench {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 16px;
  align-items: start;
}

.honor-main {
  min-width: 0;
}

.honor-side {
  position: sticky;
  top: 86px;
  padding: 16px;
}

.side-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.side-title {
  color: var(--text);
  font-size: 18px;
  font-weight: 700;
}

.side-sub,
.side-hint {
  color: var(--text-3);
  font-size: 12px;
  line-height: 1.6;
}

.side-sub {
  margin-top: 4px;
}

.status-stack {
  padding: 10px 12px;
  border-radius: var(--radius);
  background: linear-gradient(135deg, #fff8f8, #fff);
  border: 1px solid var(--line-soft);
}

.status-row {
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
  min-height: 30px;
  color: var(--text-2);
  font-size: 13px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--text-3);
}

.status-dot.active {
  background: var(--success);
}

.status-dot.archived {
  background: var(--warning);
}

.status-dot.revoked {
  background: var(--danger);
}

.side-section {
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid var(--line-soft);
}

.side-section-title {
  margin-bottom: 10px;
  color: var(--text);
  font-weight: 700;
}

.category-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.side-category-chip {
  display: inline-flex;
  min-height: 28px;
  align-items: center;
  padding: 0 10px;
  border-radius: 999px;
  background: var(--danger-soft);
  color: var(--ruc-red);
  font-size: 12px;
  font-weight: 600;
}

.side-category-chip.inactive {
  color: var(--text-3);
  background: #f4f5f7;
}

@media (max-width: 1320px) {
  .honor-workbench {
    grid-template-columns: 1fr;
  }

  .honor-side {
    position: static;
  }
}
</style>
