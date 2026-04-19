# S3 additional-request 对照验收清单

- 日期：`2026-04-19`
- 对照来源：[additional-request.txt](D:/Codes/super-ruc/docs/source/additional-request.txt)
- 关联主计划：`S3A.5, S3B.5`
- 当前状态：`DONE`

## 荣誉展示（FR-017）

### [x] 模块说明与规则边界

- 校级及以上正式荣誉录入/展示：
  - 证据：`backend/app/honor/{schemas,service,repository,router}.py` 已固定荣誉级别、授予单位、文号/证书编号、公示日期、有效期和事迹摘要字段；`backend/tests/integration/test_honor_flow.py` 覆盖公共/管理视图与治理字段。
- 本人授权与学院审核后展示：
  - 证据：公共列表与详情均要求 `consent_flag = true`；未授权条目在公共侧 `404`；对应断言已写入 `backend/tests/integration/test_honor_flow.py`。
- 历史荣誉默认不主动展示：
  - 证据：公共列表默认仅返回当前有效 `ACTIVE` 荣誉；`include_archived=true` 时返回历史项并携带 `is_historical / history_reason`；自动化已覆盖过期、归档、撤销三类状态。
- 管理维护含导入、人工新增、归档/撤销：
  - 证据：`/admin/honors` 与 `/admin/exchange/imports/honor` 均已可用；`backend/tests/integration/test_exchange_flow.py` 已覆盖导入 validate / commit / grouping / error-report。

### [x] 代表用例六

- 学生进入荣誉模块并按类别、学年筛选：
  - 证据：`miniapp/src/pages/honor/index.vue` 已实现类别 chips + 学年选择；`web/src/views/honor/HonorList.vue` 已支持类别、学年、状态筛选。
- 学生查看荣誉详情与事迹摘要：
  - 证据：公共详情 schema 保留 `title / awarded_by / document_no / summary / story_md / acceptance_speech`；`backend/tests/integration/test_honor_flow.py` 已覆盖详情访问与访问计数。
- 历史荣誉标注“仅供参考”：
  - 证据：公共接口提供 `is_historical / history_reason`；Miniapp 页面已按新字段展示历史标识。
- 毕业/历史数据保留查阅入口但不扩展敏感信息：
  - 证据：公共侧 honor schema 本身不返回联系方式等敏感字段；历史条目只保留学籍快照字段。

### [x] 页面与模块验收条目

- 榜单支持类别、学年筛选且结果准确：
  - 证据：后端 `test_honor_flow.py` 已覆盖类别/学年/状态与历史切换；前端构建通过。
- 详情展示获奖者、荣誉名称、授予单位、公示日期、事迹摘要：
  - 证据：公共详情 schema 与前端详情卡片字段已对齐。
- 管理端支持批量导入、单条录入、分类维护、有效期设置、归档/撤销，并记录维护人与更新时间：
  - 证据：Web `HonorList.vue` 与 `web/src/api/honor.ts` 已接通；管理 schema 返回 `updated_by_name / updated_at`，自动化覆盖。

## 学生画像（FR-018）

### [x] 模块说明与责任边界

- 聚合学籍静态字段与动态成长字段：
  - 证据：`ProfileSummary` 与 `ProfileStudentSelfView` 均输出 `student + facts + counters`；动态字段覆盖科研、竞赛、实践、志愿、干部任职。
- 扩展字段标注数据来源、录入人、最后更新时间：
  - 证据：管理侧 `ProfileFactOut` 已补 `source_label / created_by_name / updated_by_name / updated_at / review_comment`。
- 学生仅可查看本人，辅导员/班主任/院领导按 scope 查看：
  - 证据：`profile/service.py` 已按 `CLASS:/MAJOR:` 与 legacy scope 校验搜索、详情、审批、导出；`backend/tests/integration/test_profile_flow.py` 已覆盖 in-scope/out-of-scope 场景。
- 不输出自动评分/排名结论：
  - 证据：当前 profile schema 与页面仅做信息聚合，不含评分、排名字段或逻辑。

### [x] 代表用例七

- 辅导员搜索并进入目标学生画像页：
  - 证据：`GET /admin/profile/students` 与 `GET /admin/profile/{student_id}` 已覆盖 scope 搜索与详情。
- 动态成长信息聚合展示、敏感字段默认最小暴露：
  - 证据：学生自视图隐藏管理元数据；敏感画像事实 `is_sensitive=true` 时学生侧不展示。
- 越权查看拒绝访问并留痕：
  - 证据：`backend/tests/integration/test_profile_flow.py` 已断言详情/审批/快照越权返回 `40321`，并写 `FORBIDDEN` audit。
- 学生本人查看画像并可发起纠错/补录：
  - 证据：`/profile/me`、`/profile/me/corrections`、`/profile/me/facts`、`/profile/me/fact-submissions` 已打通；补录审批通过/驳回均有自动化。

### [x] 页面与模块验收条目

- 辅导员查看所带班级学生全景画像：
  - 证据：scope 搜索和详情自动化通过；Web `StudentProfile.vue` 已接通。
- 扩展字段均标注来源与最后更新时间：
  - 证据：管理端事实列表与快照导出均含治理元数据。
- 学生端隐藏管理元数据，纠错申诉入口可用：
  - 证据：Miniapp `profile/index.vue` 已隐藏管理字段并保留纠错/补录入口；自动化覆盖学生视图字段隔离。
- 非在读学生严格只读：
  - 证据：`require_active_enrollment` 已拦截写操作；`backend/tests/integration/test_profile_flow.py` 已覆盖 `40311` 与只读查询。
- 导出画像快照：
  - 证据：`GET /admin/profile/{student_id}/snapshot.pdf|xlsx` 已自动化验证成功，且 `PDF` 在缺少 GTK 运行时的本地环境下有 fallback。

## 固定收口验证

- `D:\Codes\super-ruc\backend`：`uv run pytest tests/integration -q` -> `48 passed in 117.20s`
- `D:\Codes\super-ruc\web`：`pnpm -C web build` 通过
- `D:\Codes\super-ruc\miniapp`：`pnpm -C miniapp build:mp-weixin` 通过
