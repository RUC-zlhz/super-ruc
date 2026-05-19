<template>
  <div class="party-stage-page">
    <a-page-header title="党团流程管理" sub-title="配置节点规则、查看学生进展，并闭环管理提醒执行记录" />

    <div class="metric-grid">
      <div v-for="metric in metrics" :key="metric.key" class="metric-tile">
        <span class="metric-icon"><component :is="metric.icon" /></span>
        <div class="metric-label">{{ metric.label }}</div>
        <div class="metric-value">{{ metric.value }}</div>
        <div class="metric-sub">{{ metric.sub }}</div>
      </div>
    </div>

    <a-tabs v-model:activeKey="activeTab">
      <a-tab-pane key="templates" tab="流程模板">
        <div class="toolbar-card">
          <a-space wrap>
            <a-button type="primary" @click="openCreateTemplate">
              <template #icon><PlusOutlined /></template>
              新建模板
            </a-button>
            <a-button :disabled="!selectedTemplatePreview" @click="openEditTemplate(selectedTemplatePreview!)">
              <template #icon><EditOutlined /></template>
              编辑所选模板
            </a-button>
            <a-button @click="refreshTemplates">
              <template #icon><ReloadOutlined /></template>
              刷新
            </a-button>
          </a-space>
        </div>

        <a-card v-if="selectedTemplatePreview" class="template-preview-card" :bordered="false">
          <div class="template-preview-head">
            <div>
              <p class="card-kicker">当前选中模板</p>
              <h3>{{ selectedTemplatePreview.name }}</h3>
              <span>{{ selectedTemplatePreview.code }} · {{ templateKindLabel(selectedTemplatePreview.kind) }}</span>
            </div>
            <a-tag :color="selectedTemplatePreview.is_active ? 'green' : 'default'">
              {{ selectedTemplatePreview.is_active ? '生效中' : '已停用' }}
            </a-tag>
          </div>
          <div class="template-preview-grid">
            <div>
              <span>节点数</span>
              <strong>{{ selectedTemplatePreview.nodes.length }}</strong>
            </div>
            <div>
              <span>启用提醒节点</span>
              <strong>{{ enabledReminderCount }}</strong>
            </div>
            <div>
              <span>最近更新</span>
              <strong>{{ formatTime(selectedTemplatePreview.updated_at) }}</strong>
            </div>
          </div>
          <div class="node-chip-list">
            <div v-for="node in sortedSelectedNodes" :key="node.id" class="node-chip">
              <div>
                <strong>{{ node.sort_order }}. {{ node.name }}</strong>
                <span>{{ node.code }} · {{ triggerRuleLabel(node.trigger_rule) }}</span>
              </div>
              <div class="node-chip-meta">
                <a-tag :color="node.reminder_enabled ? 'gold' : 'default'">
                  {{ node.reminder_enabled ? `${node.reminder_lead_days ?? 0} 天前提醒` : '提醒关闭' }}
                </a-tag>
                <a-tag v-if="node.due_rule_days != null" color="blue">时限 {{ node.due_rule_days }} 天</a-tag>
              </div>
            </div>
          </div>
        </a-card>

        <a-table
          :columns="templateCols"
          :data-source="templates"
          :loading="tplLoading"
          :custom-row="templateRowProps"
          :row-class-name="templateRowClassName"
          row-key="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'kind'">
              {{ templateKindLabel(record.kind) }}
            </template>
            <template v-else-if="column.key === 'rule_summary'">
              {{ reminderRuleSummary(record) }}
            </template>
            <template v-else-if="column.key === 'is_active'">
              <a-tag :color="record.is_active ? 'green' : 'default'">
                {{ record.is_active ? '生效' : '停用' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'updated_at'">
              {{ formatTime(record.updated_at) }}
            </template>
            <template v-else-if="column.key === 'actions'">
              <a-space>
                <a-button type="link" size="small" @click.stop="openEditTemplate(record)">
                  编辑规则
                </a-button>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-tab-pane>

      <a-tab-pane key="students" tab="学生流程">
        <a-form layout="inline" class="filter-card" @finish="reloadStudentFlows">
          <a-form-item label="学号">
            <a-input v-model:value="flowFilters.student_no" placeholder="学号" allow-clear />
          </a-form-item>
          <a-form-item label="模板">
            <a-input v-model:value="flowFilters.template_code" placeholder="模板编码" allow-clear />
          </a-form-item>
          <a-form-item>
            <a-button type="primary" html-type="submit">
              <template #icon><SearchOutlined /></template>
              查询
            </a-button>
          </a-form-item>
          <a-form-item>
            <a-button @click="resetFlowFilters">
              重置
            </a-button>
          </a-form-item>
          <a-form-item v-if="canStartStudentWorkflow" class="toolbar-item-right">
            <a-button type="primary" ghost @click="openStartWorkflowModal">
              <template #icon><PlusOutlined /></template>
              发起学生流程
            </a-button>
          </a-form-item>
        </a-form>

        <a-table
          :columns="flowCols"
          :data-source="flows"
          :loading="flowLoading"
          :pagination="flowPagination"
          row-key="id"
          @change="onFlowTableChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <StatusTag :status="record.current_node_status || 'PENDING'" />
            </template>
            <template v-else-if="column.key === 'due_date'">
              {{ record.due_date || '-' }}
            </template>
          </template>
        </a-table>
      </a-tab-pane>

      <a-tab-pane key="reminders" tab="节点提醒">
        <a-alert
          class="mb16"
          type="success"
          show-icon
          message="提醒规则、提醒记录和运行记录已接入后台。首版默认闭环站内提醒（IN_APP），支持手动触发与自动调度并行使用。"
        />

        <div class="toolbar-card">
          <a-form layout="inline" @finish="reloadReminderWorkspace">
            <a-form-item label="模板">
              <a-input v-model:value="reminderFilters.template_code" placeholder="模板编码" allow-clear />
            </a-form-item>
            <a-form-item label="学号">
              <a-input v-model:value="reminderFilters.student_no" placeholder="学号" allow-clear />
            </a-form-item>
            <a-form-item label="状态">
              <a-select v-model:value="reminderFilters.status" style="width: 160px" allow-clear placeholder="全部状态">
                <a-select-option value="PENDING">待发送</a-select-option>
                <a-select-option value="SENT">已发送</a-select-option>
                <a-select-option value="CANCELLED">已取消</a-select-option>
                <a-select-option value="FAILED">发送失败</a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item>
              <a-button type="primary" html-type="submit">
                <template #icon><SearchOutlined /></template>
                查询
              </a-button>
            </a-form-item>
            <a-form-item>
              <a-button @click="resetReminderFilters">
                重置
              </a-button>
            </a-form-item>
            <a-form-item>
              <a-button type="primary" :loading="reminderActionLoading" @click="generateReminders">
                <template #icon><PlayCircleOutlined /></template>
                立即执行一次提醒
              </a-button>
            </a-form-item>
            <a-form-item>
              <a-button :loading="reminderLoading || runLoading" @click="reloadReminderWorkspace">
                <template #icon><ReloadOutlined /></template>
                刷新工作台
              </a-button>
            </a-form-item>
          </a-form>
        </div>

        <a-card class="run-summary-card" title="最近一次执行结果" :bordered="false">
          <template v-if="latestReminderRun">
            <div class="run-summary-grid">
              <div>
                <span>创建提醒</span>
                <strong>{{ latestReminderRun.created_count }}</strong>
              </div>
              <div>
                <span>发送成功</span>
                <strong>{{ latestReminderRun.sent_count }}</strong>
              </div>
              <div>
                <span>跳过</span>
                <strong>{{ latestReminderRun.skipped_count }}</strong>
              </div>
              <div>
                <span>自动取消</span>
                <strong>{{ latestReminderRun.cancelled_count }}</strong>
              </div>
              <div>
                <span>失败</span>
                <strong>{{ latestReminderRun.failed_count }}</strong>
              </div>
              <div>
                <span>执行方式</span>
                <strong>{{ latestReminderRun.trigger_mode }}</strong>
              </div>
            </div>
            <p class="summary-foot">
              {{ formatTime(latestReminderRun.started_at) }} 开始
              <span v-if="latestReminderRun.finished_at">，{{ formatTime(latestReminderRun.finished_at) }} 完成</span>
              ，渠道 {{ latestReminderRun.channel }}
            </p>
          </template>
          <a-empty v-else description="尚未找到提醒执行记录" />
        </a-card>

        <a-card class="workspace-card" title="提醒记录" :bordered="false">
          <template v-if="reminderSupported">
            <a-table
              :columns="reminderCols"
              :data-source="reminderRecords"
              :loading="reminderLoading"
              :pagination="reminderPagination"
              row-key="id"
              :scroll="{ x: 1280 }"
              @change="onReminderTableChange"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'student'">
                  <div>{{ record.student_name || '-' }}</div>
                  <span class="cell-sub">{{ record.student_no || '-' }}</span>
                </template>
                <template v-else-if="column.key === 'template'">
                  <div>{{ record.template_name }}</div>
                  <span class="cell-sub">{{ record.template_code }}</span>
                </template>
                <template v-else-if="column.key === 'node'">
                  <div>{{ record.node_name }}</div>
                  <span class="cell-sub">{{ record.node_code }}</span>
                </template>
                <template v-else-if="column.key === 'node_status'">
                  <StatusTag :status="record.node_status" />
                </template>
                <template v-else-if="column.key === 'status'">
                  <a-tag :color="reminderStatusColor(record.status)">
                    {{ reminderStatusLabel(record.status) }}
                  </a-tag>
                </template>
                <template v-else-if="column.key === 'sent_at'">
                  {{ formatTime(record.sent_at) }}
                </template>
                <template v-else-if="column.key === 'message'">
                  <div>{{ record.message || '-' }}</div>
                  <span v-if="record.cancel_reason" class="cell-sub">取消原因：{{ record.cancel_reason }}</span>
                  <span v-else-if="record.error_message" class="cell-sub">失败原因：{{ record.error_message }}</span>
                </template>
              </template>
            </a-table>
          </template>
          <a-alert
            v-else
            type="warning"
            show-icon
            message="当前后端未开放提醒记录查询接口，页面暂时无法展示真实提醒清单。"
          />
        </a-card>

        <a-card class="workspace-card" title="最近运行记录" :bordered="false">
          <template v-if="runSupported">
            <a-table
              :columns="runCols"
              :data-source="reminderRuns"
              :loading="runLoading"
              :pagination="runPagination"
              row-key="id"
              :scroll="{ x: 1080 }"
              @change="onRunTableChange"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'status'">
                  <a-tag :color="runStatusColor(record.status)">
                    {{ runStatusLabel(record.status) }}
                  </a-tag>
                </template>
                <template v-else-if="column.key === 'started_at'">
                  {{ formatTime(record.started_at) }}
                </template>
                <template v-else-if="column.key === 'finished_at'">
                  {{ formatTime(record.finished_at) }}
                </template>
              </template>
            </a-table>
          </template>
          <a-alert
            v-else
            type="warning"
            show-icon
            message="当前后端未开放提醒运行记录接口，页面暂时无法展示批次执行轨迹。"
          />
        </a-card>
      </a-tab-pane>
    </a-tabs>

    <a-modal
      :open="showStartWorkflowModal"
      title="发起学生流程"
      width="1040"
      :mask-closable="false"
      :body-style="{ padding: '20px 24px', maxHeight: '78vh', overflowY: 'auto' }"
      @cancel="closeStartWorkflowModal"
    >
      <template #footer>
        <a-space>
          <a-button @click="closeStartWorkflowModal">取消</a-button>
          <a-button
            type="primary"
            :loading="startWorkflowSubmitting"
            :disabled="!selectedStartStudent || !startWorkflowForm.template_code"
            @click="submitStartWorkflow"
          >
            发起流程
          </a-button>
        </a-space>
      </template>

      <a-alert
        class="mb16"
        type="info"
        show-icon
        message="老师发起成功后，学生会在小程序“党团进度 / 进度中心”里看到当前阶段、时间线和下一步待办。"
      />

      <div class="launch-modal-grid">
        <section class="launch-modal-main">
          <a-card class="workspace-card" title="1. 选择流程模板" :bordered="false">
            <a-form layout="vertical">
              <a-form-item label="流程模板" required>
                <a-select
                  v-model:value="startWorkflowForm.template_code"
                  placeholder="请选择一个已启用的流程模板"
                  show-search
                  option-filter-prop="label"
                >
                  <a-select-option
                    v-for="item in launchableTemplates"
                    :key="item.code"
                    :value="item.code"
                    :label="`${item.name}（${item.code}）`"
                  >
                    <div class="template-option">
                      <strong>{{ item.name }}</strong>
                      <span>{{ item.code }} · {{ templateKindLabel(item.kind) }}</span>
                    </div>
                  </a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="备注说明">
                <a-textarea
                  v-model:value="startWorkflowForm.note"
                  :rows="3"
                  placeholder="可填写发起背景、节点说明或老师备注，学生端不会直接展示该备注。"
                />
              </a-form-item>
            </a-form>
          </a-card>

          <a-card class="workspace-card" title="2. 选择学生" :bordered="false">
            <a-form layout="inline" class="launch-search-bar" @finish="onStartStudentSearch">
              <a-form-item label="学号 / 姓名">
                <a-input
                  v-model:value="startWorkflowForm.q"
                  placeholder="支持按学号或姓名搜索"
                  allow-clear
                />
              </a-form-item>
              <a-form-item>
                <a-button type="primary" html-type="submit">
                  <template #icon><SearchOutlined /></template>
                  查询
                </a-button>
              </a-form-item>
              <a-form-item>
                <a-button @click="resetStartStudentSearch">
                  重置
                </a-button>
              </a-form-item>
            </a-form>

            <div class="launch-result-summary">
              <div>
                <strong>{{ startStudentPagination.total }}</strong>
                <span>名候选学生</span>
                <span v-if="startWorkflowForm.q" class="launch-result-keyword">
                  · 关键词“{{ startWorkflowForm.q }}”
                </span>
              </div>
              <div v-if="selectedStartStudent" class="launch-result-selected">
                已选中：{{ selectedStartStudent.full_name }} / {{ selectedStartStudent.student_no }}
              </div>
            </div>

            <a-table
              class="launch-table"
              :columns="startStudentCols"
              :data-source="startStudentCandidates"
              :loading="startStudentLoading"
              :pagination="startStudentPagination"
              row-key="id"
              :custom-row="startStudentRowProps"
              :row-class-name="startStudentRowClassName"
              :scroll="{ x: 780 }"
              @change="onStartStudentTableChange"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'student'">
                  <div>{{ record.full_name }}</div>
                  <span class="cell-sub">{{ record.student_no }}</span>
                </template>
                <template v-else-if="column.key === 'scope'">
                  <div>{{ record.class_code || '-' }}</div>
                  <span class="cell-sub">{{ record.major_code || '-' }}</span>
                </template>
                <template v-else-if="column.key === 'status'">
                  <a-tag :color="record.enrollment_status === 'ACTIVE' ? 'green' : 'default'">
                    {{ record.enrollment_status || record.status || 'UNKNOWN' }}
                  </a-tag>
                </template>
                <template v-else-if="column.key === 'actions'">
                  <a-button
                    type="link"
                    size="small"
                    @click.stop="selectStartStudent(record)"
                  >
                    {{ selectedStartStudent?.id === record.id ? '已选中' : '选择' }}
                  </a-button>
                </template>
              </template>
            </a-table>
          </a-card>
        </section>

        <aside class="launch-modal-side">
          <a-card class="workspace-card" title="3. 发起预览" :bordered="false">
            <div v-if="selectedStartStudent" class="launch-preview">
              <div class="preview-kicker">已选择学生</div>
              <h3>{{ selectedStartStudent.full_name }}</h3>
              <p>{{ selectedStartStudent.student_no }}</p>
              <div class="preview-grid">
                <div>
                  <span>班级</span>
                  <strong>{{ selectedStartStudent.class_code || '-' }}</strong>
                </div>
                <div>
                  <span>专业</span>
                  <strong>{{ selectedStartStudent.major_code || '-' }}</strong>
                </div>
                <div>
                  <span>政治面貌</span>
                  <strong>{{ selectedStartStudent.political_status || '-' }}</strong>
                </div>
                <div>
                  <span>学籍状态</span>
                  <strong>{{ selectedStartStudent.enrollment_status || selectedStartStudent.status || '-' }}</strong>
                </div>
              </div>
            </div>
            <a-empty v-else description="请先从左侧列表选择一位学生" />

            <div class="launch-preview-foot">
              <div>
                <span>流程模板</span>
                <strong>{{ selectedLaunchTemplate?.name || '未选择' }}</strong>
              </div>
              <div>
                <span>模板编码</span>
                <strong>{{ selectedLaunchTemplate?.code || '-' }}</strong>
              </div>
            </div>
          </a-card>

          <a-card class="workspace-card" title="说明" :bordered="false">
            <ul class="launch-tips">
              <li>发起后会立即创建一条进行中的党团流程实例。</li>
              <li>学生端会自动展示当前节点、时间线和下一步待办。</li>
              <li>同一学生在同一模板下已有进行中流程时，系统会阻止重复发起。</li>
            </ul>
          </a-card>
        </aside>
      </div>
    </a-modal>

    <a-drawer
      :open="showTemplateDrawer"
      :title="templateDrawerTitle"
      width="960"
      @close="showTemplateDrawer = false"
    >
      <a-form layout="vertical">
        <div class="drawer-grid">
          <a-form-item label="模板编码" required>
            <a-input v-model:value="tplForm.code" :disabled="editingTemplateId !== null" placeholder="如 PARTY_DEV_MAIN" />
          </a-form-item>
          <a-form-item label="模板名称" required>
            <a-input v-model:value="tplForm.name" placeholder="如 党员发展主流程" />
          </a-form-item>
          <a-form-item label="类型">
            <a-select v-model:value="tplForm.kind">
              <a-select-option value="PARTY">党员发展</a-select-option>
              <a-select-option value="YOUTH_LEAGUE">团学流程</a-select-option>
              <a-select-option value="OTHER">其他</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="版本号">
            <a-input v-model:value="tplForm.version_label" placeholder="如 2026-v1" />
          </a-form-item>
        </div>
        <a-form-item label="模板说明">
          <a-textarea v-model:value="tplForm.description" :rows="3" placeholder="说明这个模板适用于哪些党团流程" />
        </a-form-item>

        <div class="drawer-section-head">
          <div>
            <h3>节点规则</h3>
            <p>节点保存时会一并写入提醒规则，包括提前提醒、重复频率、最大提醒次数和渠道。</p>
          </div>
          <a-button @click="appendNode">
            <template #icon><PlusOutlined /></template>
            新增节点
          </a-button>
        </div>

        <div class="node-editor-list">
          <a-empty v-if="!tplForm.nodes.length" description="请至少配置一个节点" />
          <a-card v-for="(node, index) in tplForm.nodes" :key="node.__key" class="node-editor-card" :bordered="false">
            <template #title>
              <div class="node-editor-title">
                <span>节点 {{ index + 1 }}</span>
                <a-space>
                  <a-tag color="blue">排序 {{ node.sort_order }}</a-tag>
                  <a-button danger type="text" @click="removeNode(index)">
                    <template #icon><DeleteOutlined /></template>
                  </a-button>
                </a-space>
              </div>
            </template>

            <div class="node-editor-grid">
              <a-form-item label="节点编码" required>
                <a-input v-model:value="node.code" placeholder="如 APPLY" />
              </a-form-item>
              <a-form-item label="节点名称" required>
                <a-input v-model:value="node.name" placeholder="如 递交入党申请书" />
              </a-form-item>
              <a-form-item label="排序">
                <a-input-number v-model:value="node.sort_order" :min="1" style="width: 100%" />
              </a-form-item>
              <a-form-item label="阶段分组">
                <a-input v-model:value="node.stage_group" placeholder="如 INITIAL / ACTIVIST" />
              </a-form-item>
              <a-form-item label="触发规则">
                <a-select v-model:value="node.trigger_rule">
                  <a-select-option value="PREV_DONE">上一节点完成后触发</a-select-option>
                  <a-select-option value="ON_APPLY">申请提交后触发</a-select-option>
                  <a-select-option value="MANUAL">人工触发</a-select-option>
                  <a-select-option value="ON_DATE">按日期触发</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="时限天数">
                <a-input-number v-model:value="node.due_rule_days" :min="0" style="width: 100%" />
              </a-form-item>
              <a-form-item label="提前提醒天数">
                <a-input-number v-model:value="node.reminder_lead_days" :min="0" style="width: 100%" />
              </a-form-item>
              <a-form-item label="重复提醒间隔（天）">
                <a-input-number v-model:value="node.repeat_interval_days" :min="0" style="width: 100%" />
              </a-form-item>
              <a-form-item label="最大提醒次数">
                <a-input-number v-model:value="node.max_reminders" :min="1" style="width: 100%" />
              </a-form-item>
              <a-form-item label="提醒渠道">
                <a-select v-model:value="node.reminder_channel">
                  <a-select-option value="IN_APP">站内提醒</a-select-option>
                  <a-select-option value="EMAIL">邮件</a-select-option>
                  <a-select-option value="SMS">短信</a-select-option>
                </a-select>
              </a-form-item>
            </div>

            <a-form-item label="待完成事项">
              <a-textarea v-model:value="node.required_task" :rows="2" placeholder="说明该节点要求学生完成什么动作" />
            </a-form-item>

            <div class="node-switch-row">
              <a-space>
                <span>启用提醒</span>
                <a-switch v-model:checked="node.reminder_enabled" />
              </a-space>
              <a-space>
                <span>终点节点</span>
                <a-switch v-model:checked="node.is_terminal" />
              </a-space>
              <a-space>
                <span>启用节点</span>
                <a-switch v-model:checked="node.is_active" />
              </a-space>
            </div>
          </a-card>
        </div>

        <div class="drawer-actions">
          <a-space>
            <a-button @click="showTemplateDrawer = false">取消</a-button>
            <a-button type="primary" :loading="tplSubmitting" @click="submitTemplate">
              <template #icon><SaveOutlined /></template>
              保存模板与规则
            </a-button>
          </a-space>
        </div>
      </a-form>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import {
  BellOutlined,
  BranchesOutlined,
  DeleteOutlined,
  EditOutlined,
  NodeIndexOutlined,
  PlayCircleOutlined,
  PlusOutlined,
  ReloadOutlined,
  SaveOutlined,
  SearchOutlined,
  TeamOutlined,
} from '@ant-design/icons-vue'
import StatusTag from '@/components/StatusTag.vue'
import { useAuthStore } from '@/store/auth'
import { hasAnyRole } from '@/utils/permission'
import {
  executeWorkflowReminderRun,
  listWorkflowReminderRecords,
  listWorkflowReminderRuns,
  listWorkflowStudents,
  listWorkflowTemplates,
  searchWorkflowStudents,
  startWorkflowStudent,
  saveWorkflowTemplate,
  type ReminderStatus,
  type WorkflowNode,
  type WorkflowNodePayload,
  type WorkflowReminderRecord,
  type WorkflowReminderRun,
  type WorkflowStudentStartPayload,
  type WorkflowStudentBrief,
  type WorkflowTemplate,
  type WorkflowTemplateKind,
  type WorkflowTemplatePayload,
  type WorkflowTriggerRule,
} from '@/api/workflow'
import type { StudentBasic } from '@/api/profile'

type EditableWorkflowNode = {
  __key: string
  code: string
  name: string
  sort_order: number
  stage_group?: string
  required_task?: string
  trigger_rule: WorkflowTriggerRule | string
  due_rule_days?: number
  reminder_lead_days?: number
  reminder_enabled: boolean
  reminder_channel: string
  repeat_interval_days?: number
  max_reminders?: number
  is_terminal: boolean
  is_active: boolean
}

const activeTab = ref('templates')
const auth = useAuthStore()
const templates = ref<WorkflowTemplate[]>([])
const tplLoading = ref(false)
const tplSubmitting = ref(false)
const selectedTemplateId = ref<number | null>(null)
const selectedTemplatePreview = computed(() => {
  if (selectedTemplateId.value == null) return null
  return templates.value.find((item) => item.id === selectedTemplateId.value) ?? null
})
const sortedSelectedNodes = computed(() =>
  [...(selectedTemplatePreview.value?.nodes ?? [])].sort((a, b) => a.sort_order - b.sort_order),
)
const enabledReminderCount = computed(
  () => sortedSelectedNodes.value.filter((node) => node.reminder_enabled).length,
)

const showTemplateDrawer = ref(false)
const editingTemplateId = ref<number | null>(null)
const templateDrawerTitle = computed(() => (editingTemplateId.value ? '编辑流程模板与提醒规则' : '新建流程模板'))
const tplForm = reactive<{
  code: string
  name: string
  kind: WorkflowTemplateKind | string
  description: string
  version_label: string
  nodes: EditableWorkflowNode[]
}>({
  code: '',
  name: '',
  kind: 'PARTY',
  description: '',
  version_label: '',
  nodes: [],
})

const canStartStudentWorkflow = computed(() =>
  hasAnyRole(auth.roleCodes, [
    'SUPER_ADMIN',
    'COLLEGE_LEADER',
    'COUNSELOR',
    'HEAD_TEACHER',
    'YOUTH_LEAGUE_TEACHER',
    'PARTY_BUILD_TEACHER',
  ]),
)
const launchableTemplates = computed(() => templates.value.filter((item) => item.is_active))
const selectedLaunchTemplate = computed(
  () => launchableTemplates.value.find((item) => item.code === startWorkflowForm.template_code) ?? null,
)
const showStartWorkflowModal = ref(false)
const startWorkflowSubmitting = ref(false)
const startStudentLoading = ref(false)
const startStudentCandidates = ref<StudentBasic[]>([])
const selectedStartStudent = ref<StudentBasic | null>(null)
const startStudentPagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
})
const startWorkflowForm = reactive<{
  template_code: string
  q: string
  note: string
}>({
  template_code: '',
  q: '',
  note: '',
})
const startStudentCols = [
  { title: '学号', dataIndex: 'student_no', key: 'student_no', width: 140 },
  { title: '姓名', key: 'student', width: 140 },
  { title: '班级 / 专业', key: 'scope', width: 190 },
  { title: '政治面貌', dataIndex: 'political_status', key: 'political_status', width: 120 },
  { title: '学籍状态', key: 'status', width: 110 },
  { title: '操作', key: 'actions', width: 90 },
]

const flows = ref<WorkflowStudentBrief[]>([])
const flowLoading = ref(false)
const flowFilters = reactive<{ student_no?: string; template_code?: string }>({})
const flowPagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
})

const reminderSupported = ref(true)
const runSupported = ref(true)
const reminderLoading = ref(false)
const runLoading = ref(false)
const reminderActionLoading = ref(false)
const reminderRecords = ref<WorkflowReminderRecord[]>([])
const reminderRuns = ref<WorkflowReminderRun[]>([])
const latestReminderRun = ref<WorkflowReminderRun | null>(null)
const reminderFilters = reactive<{ template_code?: string; student_no?: string; status?: ReminderStatus | string }>({})
const reminderPagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
})
const runPagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
})

const metrics = computed(() => [
  {
    key: 'templates',
    label: '流程模板数',
    value: templates.value.length,
    sub: selectedTemplatePreview.value ? `当前选中 ${selectedTemplatePreview.value.name}` : '请选择一个模板查看详情',
    icon: BranchesOutlined,
  },
  {
    key: 'nodes',
    label: '所选节点数',
    value: sortedSelectedNodes.value.length,
    sub: `${enabledReminderCount.value} 个节点开启提醒`,
    icon: NodeIndexOutlined,
  },
  {
    key: 'flows',
    label: '学生流程数',
    value: flowPagination.total || flows.value.length,
    sub: '当前筛选结果',
    icon: TeamOutlined,
  },
  {
    key: 'reminders',
    label: '最近执行创建',
    value: latestReminderRun.value?.created_count ?? 0,
    sub: latestReminderRun.value ? `最近执行：${formatTime(latestReminderRun.value.started_at)}` : '暂无提醒执行记录',
    icon: BellOutlined,
  },
])

const templateCols = [
  { title: '编码', dataIndex: 'code', key: 'code', width: 150 },
  { title: '名称', dataIndex: 'name', key: 'name', width: 220 },
  { title: '类型', dataIndex: 'kind', key: 'kind', width: 120 },
  { title: '节点数', key: 'node_count', width: 90, customRender: ({ record }: { record: WorkflowTemplate }) => record.nodes.length },
  { title: '提醒规则概览', key: 'rule_summary' },
  { title: '状态', key: 'is_active', width: 90 },
  { title: '最近更新', key: 'updated_at', width: 180 },
  { title: '操作', key: 'actions', width: 120 },
]

const flowCols = [
  { title: '学号', dataIndex: 'student_no', key: 'student_no', width: 140 },
  { title: '姓名', dataIndex: 'student_name', key: 'student_name', width: 120 },
  { title: '模板', dataIndex: 'template_name', key: 'template_name', width: 220 },
  { title: '当前节点', dataIndex: 'current_node_name', key: 'current_node_name' },
  { title: '节点状态', key: 'status', width: 120 },
  { title: '到期日', key: 'due_date', width: 140 },
]

const reminderCols = [
  { title: '提醒日期', dataIndex: 'reminder_date', key: 'reminder_date', width: 120 },
  { title: '学生', key: 'student', width: 150 },
  { title: '模板', key: 'template', width: 220 },
  { title: '节点', key: 'node', width: 220 },
  { title: '节点状态', key: 'node_status', width: 120 },
  { title: '截止日期', dataIndex: 'due_date', key: 'due_date', width: 120 },
  { title: '渠道', dataIndex: 'channel', key: 'channel', width: 100 },
  { title: '发送状态', key: 'status', width: 120 },
  { title: '消息 / 说明', key: 'message' },
  { title: '发送时间', key: 'sent_at', width: 180 },
]

const runCols = [
  { title: '执行时间', key: 'started_at', width: 180 },
  { title: '截止日期', dataIndex: 'as_of_date', key: 'as_of_date', width: 120 },
  { title: '触发方式', dataIndex: 'trigger_mode', key: 'trigger_mode', width: 120 },
  { title: '渠道', dataIndex: 'channel', key: 'channel', width: 100 },
  { title: '状态', key: 'status', width: 120 },
  { title: '创建', dataIndex: 'created_count', key: 'created_count', width: 90 },
  { title: '发送', dataIndex: 'sent_count', key: 'sent_count', width: 90 },
  { title: '跳过', dataIndex: 'skipped_count', key: 'skipped_count', width: 90 },
  { title: '取消', dataIndex: 'cancelled_count', key: 'cancelled_count', width: 90 },
  { title: '失败', dataIndex: 'failed_count', key: 'failed_count', width: 90 },
  { title: '完成时间', key: 'finished_at', width: 180 },
]

function templateKindLabel(kind: string) {
  if (kind === 'PARTY') return '党员发展'
  if (kind === 'YOUTH_LEAGUE') return '团学流程'
  return '其他'
}

function triggerRuleLabel(rule: WorkflowTriggerRule | string) {
  if (rule === 'PREV_DONE') return '上一节点完成后'
  if (rule === 'ON_APPLY') return '申请提交后'
  if (rule === 'MANUAL') return '人工触发'
  if (rule === 'ON_DATE') return '按日期触发'
  return rule
}

function reminderRuleSummary(template: WorkflowTemplate | Record<string, any>) {
  const nodes = template.nodes as WorkflowNode[]
  const enabled = nodes.filter((node: WorkflowNode) => node.reminder_enabled)
  if (!enabled.length) return '所有节点均未开启提醒'
  const leadSet = [...new Set(enabled.map((node: WorkflowNode) => `${node.reminder_lead_days ?? 0} 天前`))]
  return `${enabled.length}/${nodes.length} 个节点开启提醒，常见提前量：${leadSet.slice(0, 2).join('、')}`
}

function reminderStatusLabel(status: string) {
  if (status === 'PENDING') return '待发送'
  if (status === 'SENT') return '已发送'
  if (status === 'CANCELLED') return '已取消'
  if (status === 'FAILED') return '发送失败'
  return status
}

function reminderStatusColor(status: string) {
  if (status === 'SENT') return 'green'
  if (status === 'FAILED') return 'red'
  if (status === 'CANCELLED') return 'default'
  return 'gold'
}

function runStatusLabel(status: string) {
  if (status === 'RUNNING') return '执行中'
  if (status === 'COMPLETED') return '已完成'
  if (status === 'FAILED') return '执行失败'
  return status
}

function runStatusColor(status: string) {
  if (status === 'COMPLETED') return 'green'
  if (status === 'FAILED') return 'red'
  return 'blue'
}

function formatTime(value?: string | null) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

function createNode(partial?: Partial<WorkflowNode>): EditableWorkflowNode {
  return {
    __key: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    code: partial?.code ?? '',
    name: partial?.name ?? '',
    sort_order: partial?.sort_order ?? tplForm.nodes.length + 1,
    stage_group: partial?.stage_group ?? undefined,
    required_task: partial?.required_task ?? undefined,
    trigger_rule: partial?.trigger_rule ?? 'PREV_DONE',
    due_rule_days: partial?.due_rule_days ?? undefined,
    reminder_lead_days: partial?.reminder_lead_days ?? 0,
    reminder_enabled: partial?.reminder_enabled ?? true,
    reminder_channel: partial?.reminder_channel ?? 'IN_APP',
    repeat_interval_days: partial?.repeat_interval_days ?? undefined,
    max_reminders: partial?.max_reminders ?? 1,
    is_terminal: partial?.is_terminal ?? false,
    is_active: partial?.is_active ?? true,
  }
}

function resetTemplateForm() {
  editingTemplateId.value = null
  Object.assign(tplForm, {
    code: '',
    name: '',
    kind: 'PARTY',
    description: '',
    version_label: '',
    nodes: [createNode({ sort_order: 1 })],
  })
}

function openCreateTemplate() {
  resetTemplateForm()
  showTemplateDrawer.value = true
}

function openEditTemplate(template: WorkflowTemplate | Record<string, any>) {
  const normalized = template as WorkflowTemplate
  editingTemplateId.value = template.id
  Object.assign(tplForm, {
    code: normalized.code,
    name: normalized.name,
    kind: normalized.kind,
    description: normalized.description ?? '',
    version_label: normalized.version_label ?? '',
    nodes: normalized.nodes
      .slice()
      .sort((a, b) => a.sort_order - b.sort_order)
      .map((node) => createNode(node)),
  })
  showTemplateDrawer.value = true
}

function refreshTemplates() {
  void loadTemplates()
}

function appendNode() {
  tplForm.nodes.push(
    createNode({
      sort_order: tplForm.nodes.length + 1,
    }),
  )
}

function removeNode(index: number) {
  tplForm.nodes.splice(index, 1)
  tplForm.nodes.forEach((node, i) => {
    if (!node.sort_order || node.sort_order < 1) node.sort_order = i + 1
  })
}

function normalizeNodePayload(node: EditableWorkflowNode): WorkflowNodePayload {
  return {
    code: node.code.trim(),
    name: node.name.trim(),
    sort_order: Number(node.sort_order || 0),
    stage_group: node.stage_group?.trim() || null,
    required_task: node.required_task?.trim() || null,
    trigger_rule: node.trigger_rule,
    due_rule_days: node.due_rule_days ?? null,
    reminder_lead_days: node.reminder_lead_days ?? null,
    reminder_enabled: !!node.reminder_enabled,
    reminder_channel: node.reminder_channel || 'IN_APP',
    repeat_interval_days: node.repeat_interval_days ?? null,
    max_reminders: node.max_reminders ?? null,
    is_terminal: !!node.is_terminal,
    is_active: !!node.is_active,
  }
}

async function submitTemplate() {
  const code = tplForm.code.trim()
  const name = tplForm.name.trim()
  if (!code || !name) {
    message.error('请先填写模板编码和模板名称')
    return
  }
  if (!tplForm.nodes.length) {
    message.error('请至少配置一个节点')
    return
  }
  const normalizedNodes = tplForm.nodes
    .map(normalizeNodePayload)
    .sort((a, b) => a.sort_order - b.sort_order)
  if (normalizedNodes.some((node) => !node.code || !node.name)) {
    message.error('每个节点都需要填写编码和名称')
    return
  }

  tplSubmitting.value = true
  try {
    const payload: WorkflowTemplatePayload = {
      code,
      name,
      kind: tplForm.kind,
      description: tplForm.description.trim() || null,
      version_label: tplForm.version_label.trim() || null,
      nodes: normalizedNodes,
    }
    const resp = await saveWorkflowTemplate(payload)
    message.success('流程模板与提醒规则已保存')
    showTemplateDrawer.value = false
    await loadTemplates(resp.data.id)
  } finally {
    tplSubmitting.value = false
  }
}

async function loadTemplates(preferId?: number) {
  tplLoading.value = true
  try {
    const resp = await listWorkflowTemplates()
    templates.value = resp.data
    if (!templates.value.length) {
      selectedTemplateId.value = null
      return
    }
    if (preferId && templates.value.some((item) => item.id === preferId)) {
      selectedTemplateId.value = preferId
      return
    }
    if (selectedTemplateId.value != null && templates.value.some((item) => item.id === selectedTemplateId.value)) {
      return
    }
    selectedTemplateId.value = templates.value[0].id
  } finally {
    tplLoading.value = false
  }
}

function templateRowProps(record: WorkflowTemplate) {
  return {
    class: 'selectable-template-row',
    onClick: () => {
      selectedTemplateId.value = record.id
    },
  }
}

function templateRowClassName(record: WorkflowTemplate) {
  return record.id === selectedTemplateId.value
    ? 'selectable-template-row selected-template-row'
    : 'selectable-template-row'
}

async function reloadStudentFlows() {
  flowLoading.value = true
  try {
    const resp = await listWorkflowStudents({
      template_code: flowFilters.template_code,
      student_no: flowFilters.student_no,
      page: flowPagination.current,
      size: flowPagination.pageSize,
    })
    flows.value = resp.data.items
    flowPagination.total = resp.data.meta.total
  } finally {
    flowLoading.value = false
  }
}

function resetFlowFilters() {
  flowFilters.student_no = undefined
  flowFilters.template_code = undefined
  flowPagination.current = 1
  reloadStudentFlows()
}

function openStartWorkflowModal() {
  if (!canStartStudentWorkflow.value) return
  if (!launchableTemplates.value.length) {
    message.warning('请先至少启用一个流程模板')
    return
  }
  startWorkflowForm.template_code = selectedTemplatePreview.value?.code ?? launchableTemplates.value[0]?.code ?? ''
  startWorkflowForm.q = ''
  startWorkflowForm.note = ''
  selectedStartStudent.value = null
  startStudentPagination.current = 1
  showStartWorkflowModal.value = true
  void searchStartStudents()
}

function closeStartWorkflowModal() {
  showStartWorkflowModal.value = false
}

async function searchStartStudents() {
  startStudentLoading.value = true
  try {
    const resp = await searchWorkflowStudents({
      q: startWorkflowForm.q || undefined,
      page: startStudentPagination.current,
      size: startStudentPagination.pageSize,
    })
    startStudentCandidates.value = resp.data.items
    startStudentPagination.total = resp.data.meta.total
    const match = selectedStartStudent.value
      ? resp.data.items.find((item) => item.id === selectedStartStudent.value?.id)
      : null
    if (match) {
      selectedStartStudent.value = match
    } else if (resp.data.items.length === 1) {
      selectedStartStudent.value = resp.data.items[0]
    } else if (startWorkflowForm.q) {
      selectedStartStudent.value = null
    }
  } finally {
    startStudentLoading.value = false
  }
}

async function onStartStudentSearch() {
  startStudentPagination.current = 1
  await searchStartStudents()
  if (startStudentPagination.total === 0) {
    message.info('未找到匹配学生，请调整学号或姓名关键词')
    return
  }
  message.success(`已找到 ${startStudentPagination.total} 名候选学生`)
}

function resetStartStudentSearch() {
  startWorkflowForm.q = ''
  startStudentPagination.current = 1
  selectedStartStudent.value = null
  void searchStartStudents()
}

function selectStartStudent(student: StudentBasic | Record<string, any>) {
  selectedStartStudent.value = {
    id: student.id,
    student_no: student.student_no,
    full_name: student.full_name,
    gender: student.gender ?? null,
    grade_code: student.grade_code ?? null,
    major_code: student.major_code ?? null,
    class_code: student.class_code ?? null,
    political_status: student.political_status ?? null,
    enrollment_year: student.enrollment_year ?? null,
    expected_graduation_year: student.expected_graduation_year ?? null,
    status: student.status ?? student.enrollment_status ?? 'UNKNOWN',
    enrollment_status: student.enrollment_status ?? student.status ?? 'UNKNOWN',
    enrollment_status_reason: student.enrollment_status_reason ?? null,
    enrollment_status_updated_at: student.enrollment_status_updated_at ?? null,
  }
}

function startStudentRowProps(record: StudentBasic) {
  return {
    onClick: () => selectStartStudent(record),
  }
}

function startStudentRowClassName(record: StudentBasic) {
  return selectedStartStudent.value?.id === record.id ? 'selected-start-student-row' : ''
}

function onStartStudentTableChange(pagination: any) {
  startStudentPagination.current = pagination.current ?? 1
  startStudentPagination.pageSize = pagination.pageSize ?? startStudentPagination.pageSize
  void searchStartStudents()
}

async function submitStartWorkflow() {
  if (!selectedStartStudent.value) {
    message.warning('请选择一个学生')
    return
  }
  if (!startWorkflowForm.template_code) {
    message.warning('请选择流程模板')
    return
  }
  const payload: WorkflowStudentStartPayload = {
    student_id: selectedStartStudent.value.id,
    template_code: startWorkflowForm.template_code,
    note: startWorkflowForm.note || undefined,
  }
  startWorkflowSubmitting.value = true
  try {
    await startWorkflowStudent(payload)
    message.success(`已为 ${selectedStartStudent.value.full_name} 发起流程，学生端可直接查看进度`)
    showStartWorkflowModal.value = false
    flowFilters.student_no = selectedStartStudent.value.student_no
    flowFilters.template_code = startWorkflowForm.template_code
    flowPagination.current = 1
    activeTab.value = 'students'
    await reloadStudentFlows()
  } finally {
    startWorkflowSubmitting.value = false
  }
}

function onFlowTableChange(pagination: any) {
  flowPagination.current = pagination.current ?? 1
  flowPagination.pageSize = pagination.pageSize ?? flowPagination.pageSize
  reloadStudentFlows()
}

async function loadReminderRecords() {
  reminderLoading.value = true
  try {
    const result = await listWorkflowReminderRecords({
      template_code: reminderFilters.template_code,
      student_no: reminderFilters.student_no,
      status: reminderFilters.status,
      page: reminderPagination.current,
      size: reminderPagination.pageSize,
    })
    reminderSupported.value = result.supported
    reminderRecords.value = result.items
    reminderPagination.total = result.meta.total
  } finally {
    reminderLoading.value = false
  }
}

async function loadReminderRuns() {
  runLoading.value = true
  try {
    const result = await listWorkflowReminderRuns({
      page: runPagination.current,
      size: runPagination.pageSize,
    })
    runSupported.value = result.supported
    reminderRuns.value = result.items
    runPagination.total = result.meta.total
    latestReminderRun.value = result.items[0] ?? latestReminderRun.value
  } finally {
    runLoading.value = false
  }
}

async function reloadReminderWorkspace() {
  await Promise.all([loadReminderRecords(), loadReminderRuns()])
}

function resetReminderFilters() {
  reminderFilters.template_code = undefined
  reminderFilters.student_no = undefined
  reminderFilters.status = undefined
  reminderPagination.current = 1
  reloadReminderWorkspace()
}

async function generateReminders() {
  reminderActionLoading.value = true
  try {
    const result = await executeWorkflowReminderRun({ channel: 'IN_APP' })
    latestReminderRun.value = result.run
    message.success(
      `提醒执行完成：创建 ${result.run.created_count} 条，发送 ${result.run.sent_count} 条，跳过 ${result.run.skipped_count} 条`,
    )
    reminderPagination.current = 1
    runPagination.current = 1
    await reloadReminderWorkspace()
  } finally {
    reminderActionLoading.value = false
  }
}

function onReminderTableChange(pagination: any) {
  reminderPagination.current = pagination.current ?? 1
  reminderPagination.pageSize = pagination.pageSize ?? reminderPagination.pageSize
  loadReminderRecords()
}

function onRunTableChange(pagination: any) {
  runPagination.current = pagination.current ?? 1
  runPagination.pageSize = pagination.pageSize ?? runPagination.pageSize
  loadReminderRuns()
}

watch(activeTab, (tab) => {
  if (tab === 'students') {
    reloadStudentFlows()
  }
  if (tab === 'reminders') {
    reloadReminderWorkspace()
  }
})

onMounted(async () => {
  resetTemplateForm()
  await loadTemplates()
  await Promise.all([reloadStudentFlows(), reloadReminderWorkspace()])
})
</script>

<style scoped>
.party-stage-page {
  display: grid;
  gap: 16px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.metric-tile {
  position: relative;
  overflow: hidden;
  padding: 18px;
  background: linear-gradient(135deg, #fff8f8, #ffffff 60%);
  border: 1px solid #f4d7dc;
  border-radius: 18px;
  box-shadow: 0 16px 28px rgba(108, 18, 32, 0.06);
}

.metric-icon {
  display: inline-grid;
  width: 42px;
  height: 42px;
  place-items: center;
  color: var(--ruc-red);
  background: #ffe7ea;
  border-radius: 999px;
  font-size: 20px;
}

.metric-label {
  margin-top: 14px;
  color: var(--text-3);
  font-size: 12px;
}

.metric-value {
  margin-top: 6px;
  color: var(--text);
  font-family: var(--font-number);
  font-size: 32px;
  line-height: 1.1;
}

.metric-sub {
  margin-top: 8px;
  color: var(--text-2);
  font-size: 12px;
  line-height: 1.6;
}

.toolbar-card,
.filter-card,
.workspace-card,
.run-summary-card,
.template-preview-card {
  margin-bottom: 16px;
}

.toolbar-item-right {
  margin-left: auto;
}

.template-preview-card,
.workspace-card,
.run-summary-card {
  border-radius: 18px;
  box-shadow: 0 16px 28px rgba(108, 18, 32, 0.05);
}

.template-preview-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.card-kicker {
  margin: 0 0 6px;
  color: var(--text-3);
  font-size: 12px;
}

.template-preview-head h3 {
  margin: 0;
  color: var(--text);
  font-size: 22px;
}

.template-preview-head span {
  color: var(--text-2);
  font-size: 13px;
}

.template-preview-grid,
.run-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 18px;
}

.template-preview-grid > div,
.run-summary-grid > div {
  padding: 14px;
  background: #faf7f7;
  border-radius: 14px;
}

.template-preview-grid span,
.run-summary-grid span {
  display: block;
  color: var(--text-3);
  font-size: 12px;
}

.template-preview-grid strong,
.run-summary-grid strong {
  display: block;
  margin-top: 8px;
  color: var(--text);
  font-size: 20px;
}

.node-chip-list {
  display: grid;
  gap: 12px;
  margin-top: 18px;
}

.node-chip {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  background: #fffaf9;
  border: 1px solid #f5e0da;
  border-radius: 14px;
}

.node-chip strong {
  display: block;
  color: var(--text);
  font-size: 14px;
}

.node-chip span {
  color: var(--text-3);
  font-size: 12px;
}

.node-chip-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.summary-foot,
.cell-sub {
  color: var(--text-3);
  font-size: 12px;
}

.summary-foot {
  margin-top: 14px;
}

.cell-sub {
  display: block;
  line-height: 1.6;
}

.drawer-grid,
.node-editor-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 16px;
}

.drawer-section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin: 8px 0 16px;
}

.drawer-section-head h3 {
  margin: 0;
  color: var(--text);
  font-size: 18px;
}

.drawer-section-head p {
  margin: 6px 0 0;
  color: var(--text-3);
  font-size: 12px;
}

.node-editor-list {
  display: grid;
  gap: 16px;
}

.launch-modal-grid {
  display: grid;
  grid-template-columns: minmax(0, 2.2fr) minmax(280px, 1fr);
  gap: 16px;
  align-items: start;
}

.launch-modal-main,
.launch-modal-side {
  display: grid;
  gap: 16px;
}

.launch-search-bar {
  margin-bottom: 14px;
}

.launch-result-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  padding: 10px 12px;
  background: #faf7f7;
  border-radius: 12px;
  color: var(--text-2);
  font-size: 13px;
}

.launch-result-summary strong {
  margin-right: 4px;
  color: var(--text);
  font-size: 16px;
}

.launch-result-keyword,
.launch-result-selected {
  color: var(--text-3);
}

.launch-table {
  overflow: hidden;
}

.template-option {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.template-option strong {
  color: var(--text);
  font-size: 14px;
}

.template-option span {
  color: var(--text-3);
  font-size: 12px;
}

.launch-preview {
  display: grid;
  gap: 12px;
}

.preview-kicker {
  color: var(--text-3);
  font-size: 12px;
}

.launch-preview h3 {
  margin: 2px 0 0;
  color: var(--text);
  font-size: 22px;
}

.launch-preview p {
  margin: 4px 0 0;
  color: var(--text-2);
  font-size: 13px;
}

.preview-grid,
.launch-preview-foot {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.preview-grid > div,
.launch-preview-foot > div {
  padding: 12px;
  background: #faf7f7;
  border-radius: 12px;
}

.preview-grid span,
.launch-preview-foot span {
  display: block;
  color: var(--text-3);
  font-size: 12px;
}

.preview-grid strong,
.launch-preview-foot strong {
  display: block;
  margin-top: 6px;
  color: var(--text);
  font-size: 14px;
}

.launch-tips {
  margin: 0;
  padding-left: 18px;
  color: var(--text-2);
  font-size: 13px;
  line-height: 1.8;
}

.node-editor-card {
  background: #fcfbfb;
  border-radius: 18px;
}

.node-editor-title,
.node-switch-row,
.drawer-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.node-switch-row {
  flex-wrap: wrap;
  padding-top: 8px;
}

.drawer-actions {
  margin-top: 24px;
}

:deep(.selected-template-row > td) {
  background: #fff4f4 !important;
}

:deep(.selected-start-student-row > td) {
  background: #fff8ed !important;
}

.mb16 {
  margin-bottom: 16px;
}

@media (max-width: 1200px) {
  .metric-grid,
  .template-preview-grid,
  .run-summary-grid,
  .launch-modal-grid,
  .drawer-grid,
  .node-editor-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .metric-grid,
  .template-preview-grid,
  .run-summary-grid,
  .launch-modal-grid,
  .drawer-grid,
  .node-editor-grid {
    grid-template-columns: 1fr;
  }

  .template-preview-head,
  .launch-search-bar,
  .launch-result-summary,
  .node-chip,
  .drawer-section-head,
  .node-editor-title,
  .node-switch-row,
  .drawer-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .preview-grid,
  .launch-preview-foot {
    grid-template-columns: 1fr;
  }
}
</style>
