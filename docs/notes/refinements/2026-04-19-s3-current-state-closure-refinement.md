# S3 荣誉与画像二次收口细化

- 日期：`2026-04-19`
- 关联主计划：`S3A.1, S3A.2, S3A.3, S3A.4, S3A.5, S3B.1, S3B.2, S3B.3, S3B.4, S3B.5`
- 当前状态：`DONE`
- 替代关系：本文件是 `S3` 的当前生效收口细化；[2026-04-18-s3-honor-profile-refinement.md](D:/Codes/super-ruc/docs/notes/refinements/2026-04-18-s3-honor-profile-refinement.md) 保留为初版拆分记录，不再作为当前完成态判断依据。

## 目标

- 基于 `S1/S2` 已冻结的 contract，把 `FR-017` 与 `FR-018` 在当前主线收口到“可操作、可回归、可回写”的完成态。
- 本轮不重做 `honor/profile`，只补齐验收缺口、自动化回归和计划落盘。

## 已完成收口

### [x] S3A 荣誉展示

- 后端 `honor` 已拆成公共视图与管理视图两套 schema；公共侧补 `is_historical / history_reason`，管理侧补 `category_name / updated_by_name / updated_at`。
- 管理端类别列表已返回全部类别（含停用），记录编辑切到类别下拉；列表支持类别、学年、状态筛选。
- 公共侧历史口径已固定为 `ARCHIVED` 或 `effective_to < today`；`REVOKED` 与 `consent_flag = false` 均不对公共侧开放。
- `exchange` 已新增 `honor` import type，复用 validate / commit / error-report 两阶段链路；同一荣誉按 canonical identity 分组为一条 `HonorRecord`，按行导入获奖人并回填学籍快照。
- Web / Miniapp 荣誉页已收口到“类别 chips + 学年 + 历史切换”交互；管理侧已接入分类维护、批量导入、历史/维护信息展示。

### [x] S3B 学生画像

- `ProfileSummary.student` 已返回真实 `enrollment_status / enrollment_status_reason / enrollment_status_updated_at`，管理端与学生端停止把 `status` 误用为学籍生命周期。
- 管理端画像事实已补 `source_label / created_by_name / updated_by_name / updated_at / review_comment`，学生端继续隐藏全部管理元数据。
- 学生成长补录已复用 `profile_facts` 落地：学生提交写 `source=STUDENT_SELF, approval_status=PENDING`，管理员在待办队列审批通过/驳回，学生侧可查看处理状态与审核意见。
- 画像查看范围已收口到班级/专业 scope：兼容 `CLASS:<class_code>`、`MAJOR:<major_code>` 及旧 `scope_code == class/major code` 写法；搜索、详情、补录审批、纠错审批、快照导出均执行 scope 校验并在越权时 `403 + audit`。
- 管理端快照导出已支持 `PDF + XLSX`；`PDF` 在缺少 GTK 运行时的 Windows 环境下新增纯 Python fallback，避免导出链路被本地图形依赖阻断。
- Web / Miniapp 画像页已补只读降级、补录状态、快照下载与学生端元数据隔离。

## 自动化验证

- `D:\Codes\super-ruc\backend`：`uv run pytest tests/integration -q` -> `48 passed in 117.20s`
- `D:\Codes\super-ruc\web`：`pnpm -C web build` 通过
- `D:\Codes\super-ruc\miniapp`：`pnpm -C miniapp build:mp-weixin` 通过

## 对照验收

- `additional-request` 对照式验收清单已独立落盘到 [2026-04-19-s3-additional-request-acceptance-checklist.md](D:/Codes/super-ruc/docs/notes/refinements/2026-04-19-s3-additional-request-acceptance-checklist.md)。
- 代表用例六与七的核心链路均已有对应自动化覆盖：
  - `honor`：类别/学年筛选、历史标识、撤销隐藏、访问计数、导入分组与错误报告
  - `profile`：scope 搜索与详情、越权 `403 + audit`、学生补录审批、非在读只读、快照导出

## 备注

- 字段级权限矩阵、全局审计矩阵与更广泛的治理规则仍归 `S4`，本轮只收口 `S3` 直接要求的 scope 与留痕。
- 旧 `S3` refinement 未删除，已保留为初版任务树与历史拆分证据。
