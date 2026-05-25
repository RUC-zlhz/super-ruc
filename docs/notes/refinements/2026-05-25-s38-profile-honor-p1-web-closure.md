# S38 学生画像与荣誉展示 P1 补齐

- 日期：`2026-05-25`
- 关联主计划条目：`S38.1, S38.2, S38.3, S38.4, S38.5`
- 状态：`[x]`

## 输入依据

- 用户新增核查口径：模块三“学生画像与信息管理（P1）”、模块四“奖励荣誉展示（P1）”。
- 微信目录外部补丁文件：`2026-05-25-profile-honor-p1-audit-and-web-closure.md`、`honor.ts`、`HonorList.vue`、`current-implementation-plan(1).md`。

## 范围结论

- 不采用外部 `current-implementation-plan(1).md` 覆盖主计划；当前主计划已有 `S35` 电子证明、`S36` EDR 和 `S37` 党团官方流程模板，本轮登记为 `S38`。
- 学生画像 P1 能力以当前后端、Web 和小程序既有实现核查为主，本轮不新增画像代码。
- 荣誉展示 P1 需要补成真实前后端闭环：个人/集体筛选、展示顺序、封面图、媒体 JSON、获奖人/集体成员维护。

## 核查结论

### 模块三：学生画像与信息管理

- [x] 基础信息管理：后端 `StudentBasic / StudentCreateIn / StudentAcademicInfoPatch` 覆盖学号、姓名、性别、民族、班级、专业、年级、联系方式、政治面貌、入学/毕业年份；Web `UserManage` 与 `StudentProfile` 已提供新增、编辑和画像查看入口。
- [x] 成长信息管理：后端 `ProfileFact` 支持科研、竞赛、实践、志愿服务、干部任职、奖励、惩戒与自定义事实；Web 画像页支持新增、删除、待审核补录处理。
- [x] 批量导入导出：`exchange` 支持学生 Excel 导入、错误报告、提交入库与学生导出；画像页支持 PDF/XLSX 快照导出。
- [x] 多维检索：`/admin/profile/students` 支持关键词、年级、专业、班级、政治面貌、是否毕业、学籍状态筛选；Web 学生管理页已接入。
- [x] 个人档案查看：`/profile/me` 仅学生本人可见，小程序 `profile` 页面消费本人画像与成长记录。
- [x] 字段分级展示：`audit` 字段策略与 `sanitize_student_basic` 已接入，学生侧不暴露管理元数据；完整查看申请与审批链路已存在。

### 模块四：奖励荣誉展示

- [x] 荣誉录入：后端支持管理端录入个人/集体荣誉、类别、级别、授奖单位、文号、公示有效期、简介、事迹、图片/媒体、获奖人，并要求至少一名获奖人或一个集体名称。
- [x] 分类展示：后端、Web 和小程序支持年份、类别、个人/集体、历史展示筛选。
- [x] 榜样宣传：后端字段支持简介、先进事迹、获奖感言、封面图与媒体；Web 补齐封面图和媒体 JSON 维护入口。
- [x] 展示控制：后端支持公开展示 consent、展示顺序 `display_order`、生效/截止日期、归档/撤销；列表按 `display_order ASC, announced_at DESC, id DESC` 排序。

## 本轮代码补齐

- `backend`：新增 `0019_honor_display_order` 迁移、`display_order` 模型/schema 字段、公共/管理列表 `is_collective` 筛选、统一排序、recipients 服务端校验和定向集成测试样例。
- `web`：荣誉 API 类型补齐 `display_order / is_collective`；荣誉管理页新增个人/集体筛选、类型列、展示顺序、封面图 URL、媒体 JSON、获奖人/集体成员编辑器，并阻止非法媒体 JSON 静默保存。
- `miniapp`：荣誉 API 类型补齐 `display_order / is_collective`；荣誉页新增“全部类型 / 个人 / 集体”筛选和个人/集体标识。

## 验证记录

- `uv run --project backend --extra dev ruff check backend/app/honor backend/alembic/versions/0019_honor_display_order_and_collective_filter.py backend/tests/integration/test_honor_flow.py` 通过。
- `uv run --project backend --extra dev python -m py_compile ...` 覆盖 honor 模块、迁移和荣誉集成测试文件，通过。
- `corepack.cmd pnpm -C web exec vue-tsc --noEmit -p tsconfig.json` 通过。
- `.\web\node_modules\.bin\vue-tsc.CMD --noEmit -p miniapp\tsconfig.json` 通过；`corepack.cmd pnpm -C miniapp exec vue-tsc --noEmit -p tsconfig.json` 因 miniapp 未安装本地 `vue-tsc` 命令不可用。
- `corepack.cmd pnpm -C web build` 通过。
- `corepack.cmd pnpm -C miniapp build:mp-weixin` 通过。
- `uv run --project backend --extra dev pytest backend/tests/integration/test_honor_flow.py -q --basetemp=.tmp/pytest-tmp-s37-honor` 因 `localhost:54322/sip_db_test` 连接拒绝在 fixture setup 阶段失败，当前结果为 `4 errors`，未进入业务断言。

## 残余说明

- 后端荣誉集成测试代码已补齐，但当前本机测试数据库未启动；待 `localhost:54322/sip_db_test` 可连接后可直接复跑上述 pytest 命令。
- 本轮仅核查并登记学生画像 P1 现有能力，不额外扩展画像代码。
