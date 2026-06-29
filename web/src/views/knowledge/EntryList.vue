<template>
  <div class="knowledge-page">
    <a-page-header title="知识库管理" sub-title="知识条目、模板与版本治理" />

    <a-tabs v-model:active-key="activeTab">
      <a-tab-pane key="entries" tab="知识条目">
        <div class="knowledge-workspace">
          <section class="knowledge-main">
            <a-form layout="inline" :model="filters" class="filter-card knowledge-filter" @finish="onFilterSubmit">
              <a-form-item label="关键字">
                <a-input v-model:value="filters.q" placeholder="搜索知识条目标题、标签、内容摘要..." allow-clear style="width: 320px" />
              </a-form-item>
              <a-form-item label="状态">
                <a-select v-model:value="filters.status" style="width: 120px" allow-clear>
                  <a-select-option value="DRAFT">草稿</a-select-option>
                  <a-select-option value="PUBLISHED">已发布</a-select-option>
                  <a-select-option value="DEPRECATED">已停用</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item>
                <a-button html-type="submit">筛选</a-button>
              </a-form-item>
              <a-form-item>
                <a-button type="primary" @click="openEntryEditor()">新增知识条目</a-button>
              </a-form-item>
            </a-form>

            <a-alert
              class="mb16 compact-alert"
              type="info"
              show-icon
              message="知识条目需先保存为草稿再发布；模板文件上传为可用后会直接进入学生端“常用模板”，也可继续关联到具体知识条目。"
            />

            <a-table
              :columns="entryColumns"
              :data-source="entries"
              :loading="entryLoading"
              :pagination="entryPagination"
              :custom-row="entryRowProps"
              :row-class-name="entryRowClassName"
              row-key="id"
              size="small"
              @change="onEntryTableChange"
             :scroll="{ x: 'max-content' }">
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'title'">
                  <div class="table-title">{{ record.title }}</div>
                  <div class="table-secondary">
                    <span>{{ record.slug }}</span>
                    <a-tag v-if="record.category_code" size="small">{{ record.category_code }}</a-tag>
                    <a-tag v-if="record.ambiguity_flag" color="orange" size="small">需人工兜底</a-tag>
                  </div>
                </template>
                <template v-else-if="column.key === 'status'">
                  <a-tag :color="entryStatusColor(record.status)">{{ entryStatusLabel(record.status) }}</a-tag>
                </template>
                <template v-else-if="column.key === 'tags'">
                  <a-tag v-for="tag in record.tags" :key="tag" size="small">{{ tag }}</a-tag>
                  <span v-if="!record.tags.length" class="muted">-</span>
                </template>
                <template v-else-if="column.key === 'source'">
                  <div class="table-title">
                    {{ record.source_name || '未绑定来源' }}
                    <a-tag v-if="record.source_is_official" color="green" size="small">官方</a-tag>
                  </div>
                  <a
                    v-if="record.source_url"
                    class="table-link"
                    :href="record.source_url"
                    target="_blank"
                    rel="noreferrer noopener"
                    @click.stop
                  >
                    {{ record.source_url }}
                  </a>
                  <span v-else class="muted">未填写来源链接</span>
                </template>
                <template v-else-if="column.key === 'updated_at'">
                  {{ formatDateTime(record.updated_at) }}
                </template>
                <template v-else-if="column.key === 'actions'">
                  <a-space size="small" wrap>
                    <a-button type="link" size="small" @click="openEntryEditor(record.id)">编辑</a-button>
                    <a-button
                      v-if="record.status !== 'PUBLISHED'"
                      type="link"
                      size="small"
                      @click="onPublishEntry(record.id)"
                    >
                      发布
                    </a-button>
                    <a-button
                      v-if="record.status !== 'DEPRECATED'"
                      type="link"
                      size="small"
                      danger
                      @click="onDeprecateEntry(record.id)"
                    >
                      停用
                    </a-button>
                    <a-button type="link" size="small" @click="openRevisions(record.id)">版本</a-button>
                  </a-space>
                </template>
              </template>
            </a-table>

            <a-card class="template-preview-card" :title="selectedEntry ? '关联模板' : '请选择知识条目'" :bordered="false">
              <a-table
                :columns="templatePreviewColumns"
                :data-source="selectedEntryTemplateRows"
                :loading="selectedEntryLoading"
                row-key="template_id"
                size="small"
                :pagination="false"
               :scroll="{ x: 'max-content' }">
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'template_name'">
                    <div class="table-title">{{ record.template_name }}</div>
                    <div class="table-secondary">{{ record.applicable_scenario || '未填写适用场景' }}</div>
                  </template>
                  <template v-else-if="column.key === 'status'">
                    <a-tag color="blue">已关联</a-tag>
                  </template>
                  <template v-else-if="column.key === 'version_label'">
                    {{ record.version_label || '-' }}
                  </template>
                  <template v-else-if="column.key === 'actions'">
                    <a-button type="link" size="small" @click="onDownloadTemplate(record.template_id, record.template_name)">
                      下载
                    </a-button>
                  </template>
                </template>
              </a-table>
              <a-empty v-if="!selectedEntry && !selectedEntryLoading" description="请选择记录" />
              <a-empty v-else-if="selectedEntry && !selectedEntryTemplateRows.length && !selectedEntryLoading" description="当前条目未关联模板" />
            </a-card>
          </section>

          <aside class="knowledge-editor-panel">
            <div class="editor-panel-head">
              <strong>编辑知识条目</strong>
              <a-button type="text" size="small" :disabled="!selectedEntry" @click="clearSelectedEntry">
                <template #icon><CloseOutlined /></template>
              </a-button>
            </div>
            <div class="mini-metrics">
              <div v-for="metric in metrics" :key="metric.key">
                <component :is="metric.icon" />
                <strong>{{ metric.value }}</strong>
                <span>{{ metric.label }}</span>
              </div>
            </div>
            <template v-if="selectedEntry">
              <a-spin :spinning="selectedEntryLoading">
              <label class="panel-field">
                <span>标题</span>
                <div>{{ selectedEntry.title }}</div>
              </label>
              <label class="panel-field">
                <span>分类</span>
                <div>{{ selectedEntry.category_code || '-' }}</div>
              </label>
              <label class="panel-field">
                <span>标签</span>
                <div class="panel-tags">
                  <a-tag v-for="tag in selectedEntry.tags" :key="tag">{{ tag }}</a-tag>
                  <span v-if="!selectedEntry.tags.length" class="muted">-</span>
                </div>
              </label>
              <label class="panel-field">
                <span>摘要</span>
                <p>{{ selectedEntry.summary || '暂无摘要' }}</p>
              </label>
              <label class="panel-field">
                <span>状态</span>
                <div class="panel-status">
                  <a-tag :color="entryStatusColor(selectedEntry.status)">{{ entryStatusLabel(selectedEntry.status) }}</a-tag>
                  <em>{{ selectedEntryDetail?.published_at ? `发布于 ${formatDateTime(selectedEntryDetail.published_at)}` : '尚未发布到学生端' }}</em>
                </div>
              </label>
              <label class="panel-field">
                <span>来源</span>
                <p v-if="selectedEntryDetail?.source">
                  <strong class="source-name">{{ selectedEntryDetail.source.source_name }}</strong>
                  <a-tag v-if="selectedEntryDetail.source.is_official" color="green" size="small">官方来源</a-tag>
                  <a
                    v-if="selectedEntryDetail.source.source_url"
                    class="table-link"
                    :href="selectedEntryDetail.source.source_url"
                    target="_blank"
                    rel="noreferrer noopener"
                    @click.stop
                  >
                    {{ selectedEntryDetail.source.source_url }}
                  </a>
                </p>
                <p v-else>未绑定来源</p>
              </label>
              <label class="panel-field">
                <span>备注</span>
                <p>版本 {{ selectedEntry.version_label || '-' }} · {{ formatDateTime(selectedEntry.updated_at) }}</p>
              </label>
              <label class="panel-field">
                <span>人工咨询提示</span>
                <p>{{ selectedEntryDetail?.manual_consult_hint || '当前未配置人工咨询提示' }}</p>
              </label>
              <div class="panel-actions">
                <a-button @click="openEntryEditor(selectedEntry.id)">编辑条目</a-button>
                <a-button type="primary" @click="openRevisions(selectedEntry.id)">查看版本</a-button>
                <a-button
                  v-if="selectedEntry.status !== 'PUBLISHED'"
                  @click="onPublishEntry(selectedEntry.id)"
                >
                  发布条目
                </a-button>
                <a-button
                  v-if="selectedEntry.status !== 'DEPRECATED'"
                  danger
                  @click="onDeprecateEntry(selectedEntry.id)"
                >
                  停用条目
                </a-button>
              </div>
              </a-spin>
            </template>
            <a-empty v-else description="请选择记录" />
          </aside>
        </div>
      </a-tab-pane>

      <a-tab-pane key="sources" tab="来源管理">
        <a-form layout="inline" class="filter-card">
          <a-form-item>
            <a-button type="primary" @click="openSourceDrawer()">新增来源</a-button>
          </a-form-item>
        </a-form>

        <a-table
          :columns="sourceColumns"
          :data-source="sources"
          :loading="sourceLoading"
          row-key="id"
          size="small"
          :pagination="false"
         :scroll="{ x: 'max-content' }">
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'source_name'">
              <div class="table-title">
                {{ record.source_name }}
                <a-tag v-if="record.is_official" color="green" size="small">官方</a-tag>
                <a-tag v-else color="default" size="small">可信待核</a-tag>
              </div>
              <a
                v-if="record.source_url"
                class="table-link"
                :href="record.source_url"
                target="_blank"
                rel="noreferrer noopener"
              >
                {{ record.source_url }}
              </a>
              <span v-else class="muted">未填写来源链接</span>
            </template>
            <template v-else-if="column.key === 'status'">
              <a-tag :color="record.is_active ? 'green' : 'default'">
                {{ record.is_active ? '启用' : '停用' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'updated_at'">
              {{ formatDateTime(record.updated_at) }}
            </template>
            <template v-else-if="column.key === 'actions'">
              <a-space size="small" wrap>
                <a-button type="link" size="small" @click="openSourceDrawer(record)">编辑</a-button>
                <a-button type="link" size="small" @click="onToggleSourceOfficial(record)">
                  {{ record.is_official ? '取消官方' : '标记官方' }}
                </a-button>
                <a-button type="link" size="small" @click="onToggleSourceActive(record)">
                  {{ record.is_active ? '停用' : '启用' }}
                </a-button>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-tab-pane>

      <a-tab-pane key="templates" tab="模板文件">
        <a-form layout="inline" :model="templateFilters" class="filter-card" @finish="reloadTemplates">
          <a-form-item label="关键字">
            <a-input v-model:value="templateFilters.q" placeholder="模板名称" allow-clear style="width: 220px" />
          </a-form-item>
          <a-form-item label="分类">
            <a-input v-model:value="templateFilters.category" placeholder="分类编码" allow-clear style="width: 160px" />
          </a-form-item>
          <a-form-item>
            <a-checkbox v-model:checked="templateFilters.include_deprecated">含停用</a-checkbox>
          </a-form-item>
          <a-form-item>
            <a-button type="primary" html-type="submit">查询</a-button>
          </a-form-item>
          <a-form-item>
            <a-button type="primary" @click="openTemplateDrawer">上传模板</a-button>
          </a-form-item>
        </a-form>

        <a-table
          :columns="templateColumns"
          :data-source="templates"
          :loading="templateLoading"
          :pagination="templatePagination"
          row-key="id"
          @change="onTemplateTableChange"
         :scroll="{ x: 'max-content' }">
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'template_name'">
              <div class="table-title">{{ record.template_name }}</div>
              <div class="table-secondary">
                <span>{{ record.applicable_scenario || '未填写适用场景' }}</span>
              </div>
            </template>
            <template v-else-if="column.key === 'status'">
              <a-tag :color="record.status === 'ACTIVE' ? 'green' : 'default'">
                {{ record.status === 'ACTIVE' ? '可用' : '已停用' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'file_size'">
              {{ formatSize(record.file_size) }}
            </template>
            <template v-else-if="column.key === 'tags'">
              <a-tag v-for="tag in record.tags || []" :key="tag" size="small">{{ tag }}</a-tag>
              <span v-if="!record.tags?.length" class="muted">-</span>
            </template>
            <template v-else-if="column.key === 'uploaded_at'">
              {{ formatDateTime(record.uploaded_at) }}
            </template>
            <template v-else-if="column.key === 'actions'">
              <a-space size="small" wrap>
                <a-button type="link" size="small" @click="onDownloadTemplate(record.id, record.template_name)">
                  下载
                </a-button>
                <a-popconfirm title="确定停用该模板？" @confirm="onDeprecateTemplate(record.id)">
                  <a-button v-if="record.status === 'ACTIVE'" type="link" size="small" danger>停用</a-button>
                </a-popconfirm>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-tab-pane>
    </a-tabs>

    <a-drawer
      :open="entryDrawerOpen"
      :title="editingEntryId ? '编辑知识条目' : '新增知识条目'"
      width="760"
      @close="resetEntryForm"
    >
      <a-spin :spinning="entryDrawerLoading">
      <a-form layout="vertical" :model="entryForm" @finish="onSubmitEntry">
        <a-row :gutter="16">
          <a-col :span="10">
            <a-form-item label="Slug" name="slug" :rules="[{ required: !editingEntryId, message: '请输入 slug' }]">
              <a-input v-model:value="entryForm.slug" :disabled="!!editingEntryId" placeholder="sick-leave-procedure" />
            </a-form-item>
          </a-col>
          <a-col :span="14">
            <a-form-item label="标题" name="title" :rules="[{ required: true, message: '请输入标题' }]">
              <a-input v-model:value="entryForm.title" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="8"><a-form-item label="分类"><a-input v-model:value="entryForm.category_code" /></a-form-item></a-col>
          <a-col :span="8"><a-form-item label="版本"><a-input v-model:value="entryForm.version_label" /></a-form-item></a-col>
          <a-col :span="8">
            <a-form-item label="来源" name="source_id" :rules="[{ required: true, message: '请选择来源' }]">
              <a-select v-model:value="entryForm.source_id" allow-clear show-search option-filter-prop="label">
                <a-select-option v-for="source in activeSources" :key="source.id" :value="source.id" :label="source.source_name">
                  {{ source.source_name }}{{ source.is_official ? '（官方）' : '' }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="摘要"><a-textarea v-model:value="entryForm.summary" :rows="2" /></a-form-item>
        <a-form-item label="适用条件"><a-textarea v-model:value="entryForm.applicable_condition" :rows="2" /></a-form-item>
        <a-form-item label="所需材料"><a-textarea v-model:value="entryForm.required_materials" :rows="2" /></a-form-item>
        <a-form-item label="办理步骤"><a-textarea v-model:value="entryForm.process_steps" :rows="3" /></a-form-item>
        <a-form-item label="正文"><a-textarea v-model:value="entryForm.body_md" :rows="6" /></a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="标签">
              <a-select v-model:value="entryForm.tags" mode="tags" style="width: 100%" placeholder="输入后回车" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="关联模板">
              <a-select v-model:value="entryForm.template_ids" mode="multiple" style="width: 100%" option-filter-prop="label">
                <a-select-option v-for="template in activeTemplates" :key="template.id" :value="template.id" :label="template.template_name">
                  {{ template.template_name }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item>
          <a-checkbox v-model:checked="entryForm.ambiguity_flag">模糊 / 高风险内容，学生侧提示转人工</a-checkbox>
        </a-form-item>
        <a-form-item label="人工咨询提示">
          <a-textarea v-model:value="entryForm.manual_consult_hint" :rows="2" />
        </a-form-item>
        <a-form-item>
          <a-space>
            <a-button type="primary" html-type="submit" :loading="entrySubmitting">保存</a-button>
            <a-button @click="resetEntryForm">取消</a-button>
          </a-space>
        </a-form-item>
      </a-form>
      </a-spin>
    </a-drawer>

    <a-drawer
      :open="sourceDrawerOpen"
      :title="editingSourceId ? '编辑知识来源' : '新增知识来源'"
      width="520"
      @close="resetSourceForm"
    >
      <a-form layout="vertical" :model="sourceForm" @finish="onSubmitSource">
        <a-form-item label="来源名称" name="source_name" :rules="[{ required: true, message: '请输入来源名称' }]">
          <a-input v-model:value="sourceForm.source_name" />
        </a-form-item>
        <a-form-item label="来源链接">
          <a-input v-model:value="sourceForm.source_url" placeholder="官方来源必须填写 https://..." />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="发布机构">
              <a-input v-model:value="sourceForm.issuing_org" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="版本">
              <a-input v-model:value="sourceForm.version_label" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="生效日期">
              <a-input v-model:value="sourceForm.effective_date" placeholder="YYYY-MM-DD" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="失效日期">
              <a-input v-model:value="sourceForm.expires_on" placeholder="YYYY-MM-DD" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item>
          <a-space direction="vertical">
            <a-checkbox v-model:checked="sourceForm.is_official">官方来源</a-checkbox>
            <a-checkbox v-model:checked="sourceForm.is_active">启用</a-checkbox>
          </a-space>
        </a-form-item>
        <a-form-item>
          <a-space>
            <a-button type="primary" html-type="submit" :loading="sourceSubmitting">保存</a-button>
            <a-button @click="resetSourceForm">取消</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-drawer>

    <a-drawer :open="templateDrawerOpen" title="上传模板文件" width="520" @close="resetTemplateForm">
      <a-form layout="vertical" :model="templateForm" @finish="onSubmitTemplate">
        <a-form-item label="模板名称" name="template_name" :rules="[{ required: true, message: '请输入模板名称' }]">
          <a-input v-model:value="templateForm.template_name" />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12"><a-form-item label="类型"><a-select v-model:value="templateForm.template_type"><a-select-option value="DOCX">DOCX</a-select-option><a-select-option value="DOC">DOC</a-select-option><a-select-option value="XLSX">XLSX</a-select-option><a-select-option value="PDF">PDF</a-select-option><a-select-option value="OTHER">OTHER</a-select-option></a-select></a-form-item></a-col>
          <a-col :span="12"><a-form-item label="分类"><a-input v-model:value="templateForm.category_code" /></a-form-item></a-col>
        </a-row>
        <a-form-item label="版本"><a-input v-model:value="templateForm.version_label" /></a-form-item>
        <a-form-item label="标签">
          <a-select v-model:value="templateForm.tags" mode="tags" placeholder="输入标签后回车" style="width: 100%" />
        </a-form-item>
        <a-form-item label="适用场景"><a-textarea v-model:value="templateForm.applicable_scenario" :rows="3" /></a-form-item>
        <a-form-item label="文件" required>
          <a-upload :show-upload-list="false" :before-upload="onBeforeTemplateUpload">
            <a-button>选择文件</a-button>
          </a-upload>
          <span class="upload-name">{{ templateFile?.name || '未选择文件' }}</span>
        </a-form-item>
        <a-form-item>
          <a-button type="primary" html-type="submit" :loading="templateSubmitting">上传</a-button>
        </a-form-item>
      </a-form>
    </a-drawer>

    <a-modal v-model:open="revisionModalOpen" title="版本记录" :footer="null" width="720">
      <a-table :columns="revisionColumns" :data-source="revisions" row-key="id" size="small" :pagination="false" :scroll="{ x: 'max-content' }">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'occurred_at'">{{ formatDateTime(record.occurred_at) }}</template>
          <template v-else-if="column.key === 'status'">
            {{ record.status_before || '-' }} -> {{ record.status_after || '-' }}
          </template>
        </template>
      </a-table>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { message, Modal } from 'ant-design-vue'
import {
  BookOutlined,
  CheckCircleOutlined,
  CloseOutlined,
  FileTextOutlined,
  HistoryOutlined,
} from '@ant-design/icons-vue'
import {
  createEntry,
  createSource,
  deprecateEntry,
  deprecateTemplate,
  getEntry,
  getTemplateDownloadLink,
  type KnowledgeEntryDetail,
  listEntries,
  listEntryRevisions,
  listSources,
  listTemplates,
  publishEntry,
  updateEntry,
  updateSource,
  uploadTemplate,
  type EntryPayload,
  type KnowledgeEntryBrief,
  type KnowledgeRevision,
  type KnowledgeSource,
  type KnowledgeTemplate,
} from '@/api/knowledge'

const activeTab = ref('entries')

const entryColumns = [
  { title: '条目', key: 'title' },
  { title: '状态', key: 'status', width: 100 },
  { title: '标签', key: 'tags', width: 180 },
  { title: '来源', key: 'source', width: 260 },
  { title: '版本', dataIndex: 'version_label', key: 'version_label', width: 120 },
  { title: '更新时间', key: 'updated_at', width: 180 },
  { title: '操作', key: 'actions', width: 210 },
]

const templateColumns = [
  { title: '模板', key: 'template_name' },
  { title: '类型', dataIndex: 'template_type', key: 'template_type', width: 100 },
  { title: '分类', dataIndex: 'category_code', key: 'category_code', width: 120 },
  { title: '版本', dataIndex: 'version_label', key: 'version_label', width: 120 },
  { title: '标签', key: 'tags', width: 180 },
  { title: '大小', key: 'file_size', width: 100 },
  { title: '状态', key: 'status', width: 100 },
  { title: '上传时间', key: 'uploaded_at', width: 180 },
  { title: '操作', key: 'actions', width: 160 },
]

const sourceColumns = [
  { title: '来源', key: 'source_name' },
  { title: '发布机构', dataIndex: 'issuing_org', key: 'issuing_org', width: 160 },
  { title: '版本', dataIndex: 'version_label', key: 'version_label', width: 120 },
  { title: '状态', key: 'status', width: 100 },
  { title: '更新时间', key: 'updated_at', width: 180 },
  { title: '操作', key: 'actions', width: 220 },
]

const templatePreviewColumns = [
  { title: '模板名称', key: 'template_name' },
  { title: '类型', dataIndex: 'template_type', key: 'template_type', width: 110 },
  { title: '版本', key: 'version_label', width: 120 },
  { title: '状态', key: 'status', width: 100 },
  { title: '操作', key: 'actions', width: 100 },
]

const revisionColumns = [
  { title: '动作', dataIndex: 'action', key: 'action', width: 120 },
  { title: '状态变化', key: 'status', width: 160 },
  { title: '版本', dataIndex: 'version_label', key: 'version_label', width: 120 },
  { title: '操作者', dataIndex: 'operator_id', key: 'operator_id', width: 100 },
  { title: '说明', dataIndex: 'note', key: 'note' },
  { title: '时间', key: 'occurred_at', width: 180 },
]

const filters = reactive<{ q?: string; status?: string }>({})
const entries = ref<KnowledgeEntryBrief[]>([])
const entryLoading = ref(false)
const entrySubmitting = ref(false)
const entryPagination = reactive({ current: 1, pageSize: 20, total: 0 })

const sources = ref<KnowledgeSource[]>([])
const sourceLoading = ref(false)
const sourceSubmitting = ref(false)
const templates = ref<KnowledgeTemplate[]>([])
const templateLoading = ref(false)
const templateSubmitting = ref(false)
const templatePagination = reactive({ current: 1, pageSize: 20, total: 0 })
const templateFilters = reactive<{ q?: string; category?: string; include_deprecated: boolean }>({ include_deprecated: false })

const entryDrawerOpen = ref(false)
const entryDrawerLoading = ref(false)
const editingEntryId = ref<number | null>(null)
const entryForm = reactive<EditableEntryForm>({
  slug: undefined,
  title: undefined,
  summary: undefined,
  category_code: undefined,
  applicable_condition: undefined,
  required_materials: undefined,
  process_steps: undefined,
  body_md: undefined,
  source_id: undefined,
  version_label: undefined,
  ambiguity_flag: false,
  manual_consult_hint: undefined,
  tags: [],
  template_ids: [],
})

interface EditableEntryForm {
  slug?: string
  title?: string
  summary?: string
  category_code?: string
  applicable_condition?: string
  required_materials?: string
  process_steps?: string
  body_md?: string
  source_id?: number
  version_label?: string
  ambiguity_flag: boolean
  manual_consult_hint?: string
  tags: string[]
  template_ids: number[]
}

const sourceDrawerOpen = ref(false)
const editingSourceId = ref<number | null>(null)
const sourceForm = reactive<EditableSourceForm>({
  source_name: '',
  source_url: '',
  issuing_org: '',
  version_label: '',
  effective_date: '',
  expires_on: '',
  is_official: false,
  is_active: true,
})

interface EditableSourceForm {
  source_name: string
  source_url: string
  issuing_org: string
  version_label: string
  effective_date: string
  expires_on: string
  is_official: boolean
  is_active: boolean
}

const templateDrawerOpen = ref(false)
const templateFile = ref<File | null>(null)
const templateForm = reactive({
  template_name: '',
  template_type: 'DOCX',
  category_code: '',
  applicable_scenario: '',
  version_label: '',
  tags: [] as string[],
})

const revisionModalOpen = ref(false)
const revisions = ref<KnowledgeRevision[]>([])

const activeTemplates = computed(() => templates.value.filter((item) => item.status === 'ACTIVE'))
const activeSources = computed(() => sources.value.filter((item) => item.is_active))
const selectedEntryId = ref<number | null>(null)
const selectedEntry = computed(() => {
  if (selectedEntryId.value == null) return null
  return entries.value.find((item) => item.id === selectedEntryId.value) ?? null
})
const selectedEntryLoading = ref(false)
const selectedEntryDetail = ref<KnowledgeEntryDetail | null>(null)
const entryDetailCache = new Map<number, KnowledgeEntryDetail>()
const selectedEntryTemplateRows = computed(() => selectedEntryDetail.value?.templates ?? [])

const metrics = computed(() => [
  {
    key: 'entries',
    label: '知识条目',
    value: entryPagination.total || entries.value.length,
    sub: '当前筛选结果',
    icon: BookOutlined,
  },
  {
    key: 'published',
    label: '已发布',
    value: entries.value.filter((item) => item.status === 'PUBLISHED').length,
    sub: '当前页发布态',
    icon: CheckCircleOutlined,
  },
  {
    key: 'templates',
    label: '模板文件',
    value: templatePagination.total || templates.value.length,
    sub: '治理附件模板',
    icon: FileTextOutlined,
  },
  {
    key: 'versions',
    label: '版本记录',
      value: revisions.value.length,
      sub: selectedEntry.value ? selectedEntry.value.title : '当前未选条目',
      icon: HistoryOutlined,
    },
  ])

function entryStatusLabel(status: string) {
  return ({ DRAFT: '草稿', PUBLISHED: '已发布', DEPRECATED: '已停用' } as Record<string, string>)[status] || status
}

function entryStatusColor(status: string) {
  return ({ DRAFT: 'default', PUBLISHED: 'green', DEPRECATED: 'red' } as Record<string, string>)[status] || 'default'
}

function formatDateTime(value?: string | null) {
  if (!value) return '-'
  return value.replace('T', ' ').slice(0, 16)
}

function formatSize(bytes?: number | null) {
  if (!bytes) return '-'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

async function reloadEntries() {
  entryLoading.value = true
  try {
    const resp = await listEntries({
      q: filters.q,
      status: filters.status,
      page: entryPagination.current,
      size: entryPagination.pageSize,
    })
    entries.value = resp.data.items
    entryPagination.total = resp.data.meta.total
    syncSelectedEntry()
  } finally {
    entryLoading.value = false
  }
}

async function reloadSources() {
  sourceLoading.value = true
  try {
    const resp = await listSources(true)
    sources.value = resp.data
  } finally {
    sourceLoading.value = false
  }
}

async function reloadTemplates() {
  templateLoading.value = true
  try {
    const resp = await listTemplates({
      q: templateFilters.q,
      category: templateFilters.category,
      include_deprecated: templateFilters.include_deprecated,
      page: templatePagination.current,
      size: templatePagination.pageSize,
    })
    templates.value = resp.data.items
    templatePagination.total = resp.data.meta.total
  } finally {
    templateLoading.value = false
  }
}

function onFilterSubmit() {
  entryPagination.current = 1
  reloadEntries()
}

function onEntryTableChange(pagination: any) {
  entryPagination.current = pagination.current
  entryPagination.pageSize = pagination.pageSize
  reloadEntries()
}

function clearSelectedEntry() {
  selectedEntryId.value = null
  selectedEntryLoading.value = false
  selectedEntryDetail.value = null
}

async function loadEntryDetail(id: number, force = false) {
  if (!force && entryDetailCache.has(id)) {
    return entryDetailCache.get(id) as KnowledgeEntryDetail
  }
  const resp = await getEntry(id)
  entryDetailCache.set(id, resp.data)
  return resp.data
}

async function selectEntry(id: number, force = false) {
  selectedEntryId.value = id
  selectedEntryDetail.value = force ? null : (entryDetailCache.get(id) ?? null)
  selectedEntryLoading.value = true
  try {
    const detail = await loadEntryDetail(id, force)
    if (selectedEntryId.value === id) {
      selectedEntryDetail.value = detail
    }
  } catch {
    if (selectedEntryId.value === id) {
      selectedEntryDetail.value = null
    }
  } finally {
    if (selectedEntryId.value === id) {
      selectedEntryLoading.value = false
    }
  }
}

function syncSelectedEntry() {
  if (selectedEntryId.value == null) return
  const current = entries.value.find((item) => item.id === selectedEntryId.value)
  if (!current) {
    clearSelectedEntry()
    return
  }
  void selectEntry(current.id, true)
}

function entryRowProps(record: KnowledgeEntryBrief) {
  return {
    class: 'selectable-entry-row',
    onClick: () => {
      void selectEntry(record.id)
    },
  }
}

function entryRowClassName(record: KnowledgeEntryBrief) {
  return record.id === selectedEntryId.value
    ? 'selectable-entry-row selected-entry-row'
    : 'selectable-entry-row'
}

function onTemplateTableChange(pagination: any) {
  templatePagination.current = pagination.current
  templatePagination.pageSize = pagination.pageSize
  reloadTemplates()
}

function resetEntryForm() {
  entryDrawerOpen.value = false
  editingEntryId.value = null
  Object.assign(entryForm, {
    slug: undefined,
    title: undefined,
    summary: undefined,
    category_code: undefined,
    applicable_condition: undefined,
    required_materials: undefined,
    process_steps: undefined,
    body_md: undefined,
    source_id: undefined,
    version_label: undefined,
    ambiguity_flag: false,
    manual_consult_hint: undefined,
    tags: [],
    template_ids: [],
  })
}

async function openEntryEditor(id?: number) {
  resetEntryForm()
  if (id) {
    selectedEntryId.value = id
    editingEntryId.value = id
    entryDrawerOpen.value = true
    entryDrawerLoading.value = true
    try {
      const detail = await loadEntryDetail(id)
      if (selectedEntryId.value === id) {
        selectedEntryDetail.value = detail
      }
      Object.assign(entryForm, {
        title: detail.title,
        summary: detail.summary || undefined,
        category_code: detail.category_code || undefined,
        applicable_condition: detail.applicable_condition || undefined,
        required_materials: detail.required_materials || undefined,
        process_steps: detail.process_steps || undefined,
        body_md: detail.body_md || undefined,
        source_id: detail.source?.id,
        version_label: detail.version_label || undefined,
        ambiguity_flag: detail.ambiguity_flag,
        manual_consult_hint: detail.manual_consult_hint || undefined,
        tags: [...detail.tags],
        template_ids: detail.templates.map((item) => item.template_id),
      })
    } finally {
      entryDrawerLoading.value = false
    }
    return
  }
  entryDrawerOpen.value = true
}

async function onSubmitEntry() {
  entrySubmitting.value = true
  try {
    const payload = normalizeEntryPayload(entryForm)
    if (!payload.source_id) {
      message.warning('请选择知识来源；官方来源必须由来源管理显式维护')
      return
    }
    if (editingEntryId.value) {
      await updateEntry(editingEntryId.value, payload)
      entryDetailCache.delete(editingEntryId.value)
      message.success('知识条目已更新')
    } else {
      await createEntry(payload)
      message.success('知识条目已创建')
    }
    resetEntryForm()
    reloadEntries()
  } finally {
    entrySubmitting.value = false
  }
}

function normalizeEntryPayload(form: EditableEntryForm): EntryPayload {
  const payload: EntryPayload = {
    ...form,
    tags: form.tags || [],
    template_ids: form.template_ids || [],
  }
  if (!editingEntryId.value && !payload.slug) {
    message.warning('请输入 slug')
    throw new Error('请输入 slug')
  }
  return payload
}

function onPublishEntry(id: number) {
  Modal.confirm({
    title: '发布知识条目',
    content: '发布后学生端可检索该条目，请确认来源、版本与人工兜底提示已检查。',
    onOk: async () => {
      await publishEntry(id, '管理端发布')
      message.success('已发布')
      reloadEntries()
    },
  })
}

function onDeprecateEntry(id: number) {
  Modal.confirm({
    title: '停用知识条目',
    content: '停用后学生端不可再检索该条目。',
    okType: 'danger',
    onOk: async () => {
      await deprecateEntry(id, '管理端停用')
      message.success('已停用')
      reloadEntries()
    },
  })
}

async function openRevisions(id: number) {
  selectedEntryId.value = id
  const resp = await listEntryRevisions(id)
  revisions.value = resp.data
  revisionModalOpen.value = true
}

function openTemplateDrawer() {
  resetTemplateForm()
  templateDrawerOpen.value = true
}

function resetSourceForm() {
  sourceDrawerOpen.value = false
  editingSourceId.value = null
  Object.assign(sourceForm, {
    source_name: '',
    source_url: '',
    issuing_org: '',
    version_label: '',
    effective_date: '',
    expires_on: '',
    is_official: false,
    is_active: true,
  })
}

function openSourceDrawer(source?: KnowledgeSource | Record<string, any>) {
  resetSourceForm()
  if (source) {
    const sourceRecord = source as KnowledgeSource
    editingSourceId.value = sourceRecord.id
    Object.assign(sourceForm, {
      source_name: sourceRecord.source_name,
      source_url: sourceRecord.source_url || '',
      issuing_org: sourceRecord.issuing_org || '',
      version_label: sourceRecord.version_label || '',
      effective_date: sourceRecord.effective_date || '',
      expires_on: sourceRecord.expires_on || '',
      is_official: sourceRecord.is_official,
      is_active: sourceRecord.is_active,
    })
  }
  sourceDrawerOpen.value = true
}

function normalizeSourcePayload() {
  return {
    source_name: sourceForm.source_name.trim(),
    source_url: sourceForm.source_url.trim() || null,
    issuing_org: sourceForm.issuing_org.trim() || null,
    version_label: sourceForm.version_label.trim() || null,
    effective_date: sourceForm.effective_date.trim() || null,
    expires_on: sourceForm.expires_on.trim() || null,
    is_official: sourceForm.is_official,
    is_active: sourceForm.is_active,
  }
}

async function onSubmitSource() {
  sourceSubmitting.value = true
  try {
    const payload = normalizeSourcePayload()
    if (payload.is_official && !payload.source_url) {
      message.warning('官方来源必须填写来源链接')
      return
    }
    if (editingSourceId.value) {
      await updateSource(editingSourceId.value, payload)
      message.success('知识来源已更新')
    } else {
      await createSource(payload)
      message.success('知识来源已创建')
    }
    resetSourceForm()
    await reloadSources()
  } finally {
    sourceSubmitting.value = false
  }
}

async function onToggleSourceOfficial(source: KnowledgeSource | Record<string, any>) {
  const sourceRecord = source as KnowledgeSource
  if (!sourceRecord.is_official && !sourceRecord.source_url) {
    message.warning('标记官方来源前必须先填写来源链接')
    openSourceDrawer(sourceRecord)
    return
  }
  await updateSource(sourceRecord.id, { is_official: !sourceRecord.is_official })
  message.success(sourceRecord.is_official ? '已取消官方标识' : '已标记为官方来源')
  await reloadSources()
  entryDetailCache.clear()
  await reloadEntries()
}

async function onToggleSourceActive(source: KnowledgeSource | Record<string, any>) {
  const sourceRecord = source as KnowledgeSource
  await updateSource(sourceRecord.id, { is_active: !sourceRecord.is_active })
  message.success(sourceRecord.is_active ? '来源已停用' : '来源已启用')
  await reloadSources()
}

function resetTemplateForm() {
  templateDrawerOpen.value = false
  templateFile.value = null
  Object.assign(templateForm, {
    template_name: '',
    template_type: 'DOCX',
    category_code: '',
    applicable_scenario: '',
    version_label: '',
    tags: [],
  })
}

function onBeforeTemplateUpload(file: File) {
  templateFile.value = file
  if (!templateForm.template_name) templateForm.template_name = file.name.replace(/\.[^.]+$/, '')
  return false
}

async function onSubmitTemplate() {
  if (!templateFile.value) {
    message.warning('请先选择模板文件')
    return
  }
  templateSubmitting.value = true
  try {
    await uploadTemplate({
      file: templateFile.value,
      template_name: templateForm.template_name,
      template_type: templateForm.template_type,
      category_code: templateForm.category_code || undefined,
      applicable_scenario: templateForm.applicable_scenario || undefined,
      version_label: templateForm.version_label || undefined,
      tags: templateForm.tags,
    })
    message.success('模板已上传，学生端常用模板会直接可见')
    resetTemplateForm()
    reloadTemplates()
  } finally {
    templateSubmitting.value = false
  }
}

async function onDeprecateTemplate(id: number) {
  await deprecateTemplate(id)
  message.success('模板已停用')
  reloadTemplates()
}

async function onDownloadTemplate(templateId: number, templateName: string) {
  try {
    const resp = await getTemplateDownloadLink(templateId, 'admin')
    const link = document.createElement('a')
    link.href = resp.data.download_url
    link.target = '_blank'
    link.rel = 'noopener noreferrer'
    document.body.appendChild(link)
    link.click()
    link.remove()
    message.success(`已打开 ${templateName}`)
  } catch {
    message.error('模板下载失败')
  }
}

onMounted(async () => {
  await Promise.all([reloadEntries(), reloadSources(), reloadTemplates()])
})
</script>

<style scoped>
.mb16 { margin-bottom: 16px; }

.knowledge-page {
  padding-right: 394px;
}

.knowledge-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 14px;
  align-items: start;
}

.knowledge-main {
  min-width: 0;
}

.knowledge-filter {
  margin-bottom: 12px;
}

.compact-alert {
  padding: 10px 14px !important;
}

.template-preview-card {
  margin-top: 14px;
}

.knowledge-editor-panel {
  position: fixed;
  top: 58px;
  right: 0;
  bottom: 0;
  z-index: 12;
  width: 380px;
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

.editor-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.editor-panel-head strong {
  color: var(--text);
  font-size: 16px;
}

.editor-panel-head :deep(.ant-btn) {
  color: var(--text-3);
}

.mini-metrics {
  display: none;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 16px;
}

.mini-metrics div {
  min-height: 64px;
  padding: 10px;
  background: #fff7f8;
  border: 1px solid #ffe4e8;
  border-radius: 10px;
}

.mini-metrics :deep(.anticon) {
  color: var(--ruc-red);
  font-size: 14px;
}

.mini-metrics strong {
  display: block;
  margin-top: 6px;
  color: var(--ruc-red);
  font-size: 20px;
  line-height: 1;
}

.mini-metrics span {
  display: block;
  margin-top: 5px;
  color: var(--text-2);
  font-size: 12px;
}

.panel-field {
  display: block;
  margin-bottom: 14px;
}

.panel-field > span {
  display: block;
  margin-bottom: 6px;
  color: var(--text);
  font-size: 13px;
  font-weight: 700;
}

.panel-field > div,
.panel-field > p {
  margin: 0;
  padding: 9px 10px;
  color: var(--text-2);
  background: #fbfcfe;
  border: 1px solid var(--line);
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.6;
}

.panel-field em {
  margin-left: 10px;
  color: var(--text-2);
  font-style: normal;
  font-size: 12px;
}

.panel-status {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.panel-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.cover-uploader {
  display: grid;
  min-height: 112px;
  place-items: center;
  margin: 4px 0 14px;
  padding: 18px;
  color: var(--text-3);
  border: 1px dashed #d8dce3;
  border-radius: 10px;
  text-align: center;
}

.cover-uploader :deep(.anticon) {
  color: var(--text-3);
  font-size: 24px;
}

.cover-uploader span {
  color: var(--text-2);
  font-size: 12px;
}

.cover-uploader small {
  color: var(--text-3);
  font-size: 11px;
}

.panel-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 18px;
}

.table-title { font-weight: 600; color: #1f1f1f; }
.table-secondary { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; color: #8c8c8c; font-size: 12px; margin-top: 4px; }
.muted { color: #bfbfbf; }
.upload-name { margin-left: 12px; color: #595959; }
.table-link { display: block; margin-top: 4px; color: var(--ruc-red); word-break: break-all; }
.source-name { display: block; margin-bottom: 4px; color: var(--text); font-weight: 700; }

:deep(.selectable-entry-row > td) {
  cursor: pointer;
}

:deep(.selected-entry-row > td) {
  background: #fff4f5 !important;
}

@media (max-width: 1320px) {
  .knowledge-page {
    padding-right: 0;
  }

  .knowledge-workspace {
    grid-template-columns: 1fr;
  }

  .knowledge-editor-panel {
    position: static;
    width: auto;
    border: 1px solid var(--line-soft);
    border-radius: 12px;
  }
}
</style>
