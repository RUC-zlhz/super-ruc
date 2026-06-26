# S78 用户使用说明书与软件测试报告最终提交版出件

- 关联主计划：`S78.1 ~ S78.4`
- 状态：`[x]` 已完成
- 日期：`2026-06-26`
- 主工作区：`D:\Codes\super-ruc`（分支 `feat/s75-perf-uiux`，HEAD `ca3b8de`）

## 范围

- 基于当前最新项目代码（S72~S77 已合并并部署生产）与 `2026-06-26` 生产在线核对事实，
  将《用户使用说明书》与《软件测试报告》从 V1.0 升级为 **V2.0 最终提交版**。
- 通过 `ssh n150` 跳板对 `http://10.10.0.13/` 做在线抽检，作为文档事实基准。
- 复核 `2026-05-26` 测试基线（`bug-report.md`）记录的 14 项 Logic 缺陷整改情况。

## 非范围

- 不修改业务代码、接口契约或部署配置。
- 不在文档中固化个人联系方式或临时私有联系渠道。

## 执行拆分

- [x] `S78.1` 生产在线抽检（经 n150）：根页标题=`信息学院管理后台`、入口资源 `index-Cl5iT-qx.js` 与
  `vue / vendor / antdv` 三个独立 chunk（确认 S75 分包已上线）、`healthz` code=0、
  `knowledge/categories`=9 个分类、`knowledge/search` total=16、`knowledge/{id}` 详情 code=0；
  6 个受保护接口（report/overview、admin/notices、requests 附件下载、workflow/public/templates、
  honors、admin/quiz/questions）未登录均 401；`admin/admin123` 登录探测 401（40100）。
- [x] `S78.2` 缺陷整改复核：按当前 HEAD 代码定位逐项确认 `S50-L01~L14` 14 项 Logic 缺陷均已修复
  （改密 `token_version += 1`、overview/通知/流程搜人按 viewer scope 收口、401 携带 redirect、
  提醒 fetch 接入 401、模拟回执 `isDev` 门禁、详情/批次错误态标记、小程序分页/加载更多补齐）。
- [x] `S78.3` 更新两份出件脚本到 V2.0：`scripts/docs/build_project_user_manual.py`、
  `scripts/docs/build_project_test_report.py`（刷新生产事实、测试基线改为 S77 全量 `146 passed`、
  补充审批附件下载/通知日期校验/小程序下拉刷新/Web 全局加载等已上线能力、缺陷整改复核表）。
- [x] `S78.4` 生成交付件并做页数/版式 QC（Word 导出 PDF + pdftoppm 渲染抽检）。
- [x] `S78.5` 用户提供有效管理员账号（`SUPER_ADMIN`，密码不入库/不入文档）后，经 n150 跳板完成生产
  认证态只读验证：登录 + `/auth/me`（角色 `SUPER_ADMIN`、`must_change_password=false`、token ver 有效）；
  `admin/report/overview`、`admin/report/academic-gap`(total=7)、`admin/notices`(total=9)、
  `admin/honors`(3)/`honors`(2)、`workflow/public/templates`、`admin/quiz/questions`(1)、
  `admin/knowledge/entries`(total=17)/`templates`(4)、`admin/workflow/students/search?q=2024`(total=6)、
  `admin/profile/{id}`、`admin/audit-logs`(total=2163) 均 code=0；改密错误旧密码返回 `40100 旧密码错误`（未误改/未 500）。
  本轮仅只读与失败态探测，未向生产库写测试数据。测试报告新增「3.4 生产认证态只读验证」并相应更新 1.4/2.3/3.1/3.3/5.x。
- [x] `S78.6` 用户授权向生产库写测试数据后，完成认证态写入闭环实测（标注「【生产写入验收-勿用】」并即时清理）：
  - 知识库闭环：建来源(id=16)+条目(id=18,DRAFT)→publish(PUBLISHED)→公开检索 `total=1`（URL-encode 后命中测试 slug，印证 S75 写路径缓存事件失效）→detail 返回来源→deprecate(DEPRECATED)→公开检索 `total=0`（清理生效）。
  - 通知闭环：建通知(id=10,DRAFT)→target-preview `target_count=2`→publish→dispatch 批次 `NB-260626134351-0C0F8D` `target=2/success=2/failed=0` 状态 `COMPLETED`（IN_APP 送达 2 名演示学生）→archive(ARCHIVED) 清理。
  - 生产共 7 名演示学生（均 seed 数据，如 `full_name=test`）；学生侧请假/证明等申请的完整审批写入需学生账号发起，本轮未取得学生账号，留待补验。
  - 测试报告 3.4 升级为「生产认证态读写验证」，新增写入闭环表与说明，并相应更新 2.3/3.1/3.3/5.x；报告页数 11→12。
  - 残留测试数据（已标注、不公开/已归档）：知识条目 18（DEPRECATED）+ 来源 16；通知 10（ARCHIVED）+ 批次 1 条 + 2 名演示学生站内消息。无删除接口，按软态保留。
- [x] `S78.7` 学生端↔教师审批闭环本地全链路 LIVE 实测（生产学生登录走真实微信、mock 已按守卫关闭，无法无头签发学生会话；在线探测伪造 code 返回 40100）：
  - 本机启动 Docker Desktop 后 `docker compose up`（kingbase/redis/minio/mailhog），以真实 HTTP（ASGI）走通：学生微信 mock 登录(绑定 2024999001)→发起在校证明(CERTIFICATE_IN_SCHOOL, DRAFT)→上传附件(实习接收函.pdf)→提交(SUBMITTED)→辅导员认领(IN_REVIEW)→审批通过(APPROVED, 动作链 SUBMIT/CLAIM/APPROVE)→证明 PDF 预览(application/pdf)→学生与辅导员附件认证下载(均 200)→匿名下载 401。
  - 复核：`pytest tests/integration/test_request_flow.py` 本地 Docker 全链路 `20 passed`（草稿→审批、驳回重提、撤回、转线下、终态 REOPEN、附件必填、证明模板引擎、协同角色 scope 等）。
  - 临时演示用例 `test_zzz_student_loop_demo.py` 跑通后已删除，不进正式测试集。
  - 测试报告 3.4 新增「学生端↔教师审批闭环（本地实测）」子节与 9 步表，并更新 2.3/3.1/3.3/5.x；页数 12→13。
- [x] `S78.8` 学生端↔教师审批闭环**生产真机微信端到端实测**（用户提供真机微信并启动微信开发者工具）：
  - 经 `ssh -L 8080:10.10.0.13:80 n150` 隧道把小程序 API 指向生产（host 直连 10.10.0.13 返回 502，仅 n150 路径可用）；
    临时改 `miniapp/.env.local`→`127.0.0.1:8080`、`project.config.json` 加 `urlCheck:false` 并重建 mp-weixin，验证后已全部还原（git 干净）。
  - 在微信开发者工具控制台真实 `wx.login`：伪造 code→生产 `40100`；绑定已占用学生→`40901`；本机微信已绑定→`40902`；
    无参登录→生产签发学生 JWT（角色 STUDENT，user_id=2/student_id=1），**证明生产微信登录配置正确、appid `wxcb6352a74505bc41` 与真机微信匹配、非降级 mock**。
  - 学生（真机微信会话）在生产创建请假申请 `request_id=7`（LEAVE_PERSONAL，标注「【验收测试-勿用】」）→提交 SUBMITTED；
    SUPER_ADMIN 审批被服务正确拒绝（`40304` 无权审批该类型）；遂经 admin 导入创建标注测试辅导员 `TCNSL02`（COUNSELOR），
    辅导员认领 IN_REVIEW→审批 APPROVED（动作链 SUBMIT/CLAIM/APPROVE）；学生端回看 `status=APPROVED` 且见审批意见，闭环成立。
  - 生产标注测试数据（无硬删除接口，留待维护方按标签清理）：请假申请 7（APPROVED）、测试学生 `2024999777`(id8)、测试辅导员 `TCNSL01/TCNSL02`、
    以及早前知识条目 18(DEPRECATED)+来源 16、通知 10(ARCHIVED)。用户真机微信(弹琴)绑定 student_id=1 为既有绑定，非本轮新建。
  - 测试报告 3.4 升级为「生产真机微信 + 本地全量回归」，并更新 2.3/3.1/3.3/5.x；页数维持 13。

## 验收条件 / 结果

- 生成最终交付件：
  - `output/doc/用户使用说明书-信息学院学生综合服务与党团管理平台-v2.0.docx`（及 `.pdf`，`14` 页）
  - `output/doc/软件测试报告-信息学院学生综合服务与党团管理平台-v2.0.docx`（及 `.pdf`，`10` 页）
- 文本抽检：V2.0 / 最终提交版 / 2026-06-26 / ca3b8de / 146 / 下拉刷新 / 附件 等关键事实均已落入；
  无残留 `版本：V1.0` 副标题；变更历史正确保留 V1.0 行并新增 V2.0 行。
- 版式抽检：标题页、总体情况表、缺陷整改表、联系方式表渲染清晰，无重叠/截断/空尾页。

## 备注 / 残留

- n150 是内网访问跳板而非生产 Docker 主机；当前未拿到有效生产账号，认证态成功路径以本地 Docker DB
  全量回归（S77：`146 passed`）覆盖。正式验收建议由部署维护方发放有效账号后补一轮 10.10.0.13 实登抽检。
- V1.0 交付件（`output/doc/*-v1.0.docx`）保留，未删除；出件脚本默认输出已切换到 v2.0。
