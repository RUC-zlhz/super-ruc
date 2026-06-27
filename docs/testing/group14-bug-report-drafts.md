# 第 14 组 Bug 报告草稿

- 测试方：第 12 组
- 被测方：第 14 组
- 测试阶段：第一阶段
- 生成时间：`2026-05-28`
- 依据文档：`http://183.174.61.212:8001/uploads/a26b255d5f1f41a1b454c00b2b32278e.pdf`

## BUG-G14-001：平台资料仅提供 PDF，未提供小程序源码包，导致小程序端无法按文档运行

### 基本信息

- Bug 类型：崩溃类 bug
- 所属功能：微信小程序端启动与交付资料完整性
- 严重程度：高
- 正式登记状态：第 12 组已登记第 14 组
- 当前状态：候选，需结合补充 Markdown 决定是否提交；建议提交前补一张平台资料页截图和补充 Markdown 截图

### 问题描述

第 14 组 PDF 使用说明中写明“微信小程序端使用微信开发者工具打开小程序项目进行体验”，并要求在开发者工具中处理域名、TLS、HTTPS 证书校验问题。但第 12 组登录互评平台读取第 14 组资料时，`/api/documents/group/14` 仅返回 1 个 `usage` 类型 PDF 文件，未返回小程序源码包、`project.config.json`、`app.json`、`pages.json`、`manifest.json` 或可导入微信开发者工具的项目目录。用户后续补充的 Markdown 链接提供的是 Web 互测指南和 `http://10.10.0.14/` 浏览器入口，也没有提供小程序源码包。测试方因此无法按 PDF 文档启动微信小程序端。

### 前置条件

1. 第 12 组登录互评平台。
2. 第 12 组已登记第 14 组为第一阶段正式测试对象。
3. 打开第 14 组项目资料页面或调用第 14 组文档接口。

### 复现步骤

1. 登录互评平台。
2. 查看第 14 组项目资料，或请求 `/api/documents/group/14`。
3. 下载平台返回的第 14 组资料。
4. 解包或扫描下载目录，查找微信小程序项目常见入口文件：`project.config.json`、`app.json`、`pages.json`、`manifest.json`、`package.json`。
5. 尝试定位可导入微信开发者工具的小程序项目目录。

### 测试输入

```text
被测组：第 14 组
资料接口：/api/documents/group/14
扫描标记：project.config.json / app.json / pages.json / manifest.json / package.json
```

### 实际输出

```text
平台仅返回 1 个文档：doc_type = usage，url = /uploads/a26b255d5f1f41a1b454c00b2b32278e.pdf。
本地下载和扫描后未发现 project.config.json、app.json、pages.json、manifest.json 或 package.json。
无法定位可导入微信开发者工具的小程序项目目录。
```

### 期望输出

```text
平台应提供第 14 组小程序源码包或可导入微信开发者工具的项目目录，并在使用说明中给出明确导入路径、启动步骤和依赖说明。
若小程序端暂不提供，应在文档中明确说明限制，避免测试方按说明执行但无法启动。
```

### 证据材料

- 文档元数据：`tmp/docs/group14/platform-documents/group14-documents.json`
- 下载 PDF：`tmp/docs/group14/platform-documents/group14-usage.pdf`
- 补充 Markdown：`tmp/docs/group14/platform-documents/group14-extra.md`
- 本地扫描摘要：`tmp/group14-miniapp/SETUP_SUMMARY.md`
- 平台资料页截图：待补充

### 修复建议

1. 在互评平台上传第 14 组微信小程序源码包，至少包含 `project.config.json` 或明确的 UniApp/Taro/原生小程序项目入口。
2. 在使用说明中补充微信开发者工具导入目录、AppID 使用方式、后端地址配置位置和域名校验设置。
3. 如果小程序端不作为本轮互测对象，应在文档“已知限制”中明确说明，避免测试方误判。

### 去重说明

- 是否与其他 bug 同根因：否
- 保留原因：该问题直接阻断小程序端启动与核心功能测试，属于交付资料/运行说明导致无法运行的独立问题。

### 平台提交精简版

```text
Bug 类型：崩溃类 bug
所属功能：微信小程序端启动 / 交付资料完整性

问题描述：
第 14 组 PDF 使用说明中写明“微信小程序端使用微信开发者工具打开小程序项目进行体验”，但第 12 组登录互评平台查看第 14 组资料时，平台仅提供 1 个 usage 类型 PDF 文件，未提供小程序源码包或可导入微信开发者工具的项目目录。后续补充的 Markdown 链接提供的是 Web 互测指南和 http://10.10.0.14/ 浏览器入口，也没有提供小程序源码包，导致测试方无法按 PDF 文档启动微信小程序端。

复现步骤：
1. 使用第 12 组账号登录互评平台。
2. 打开第 14 组项目资料页面。
3. 下载第 14 组提供的全部资料。
4. 在下载内容中查找 project.config.json、app.json、pages.json、manifest.json、package.json 或小程序源码目录。
5. 尝试用微信开发者工具导入小程序项目。

测试输入：
被测组：第 14 组；资料接口：/api/documents/group/14；扫描标记：project.config.json / app.json / pages.json / manifest.json / package.json。

实际输出：
平台资料接口仅返回 1 个 usage PDF：/uploads/a26b255d5f1f41a1b454c00b2b32278e.pdf。补充 Markdown 提供的是 Web 地址 http://10.10.0.14/ 和 demo.* 账号。本地下载和扫描后没有发现 project.config.json、app.json、pages.json、manifest.json 或 package.json，无法定位可导入微信开发者工具的小程序项目目录。

期望输出：
平台应提供第 14 组小程序源码包或可导入微信开发者工具的项目目录，并在使用说明中给出明确导入路径、后端地址配置位置和启动步骤；如果小程序端暂不提供，应在文档中明确说明限制。

证据：
1. 第 14 组资料页截图：待附。
2. 下载后仅有 PDF 的文件列表截图：待附。
3. 本地扫描摘要显示未发现小程序项目标记文件：tmp/group14-miniapp/SETUP_SUMMARY.md。

修复建议：
请补传小程序源码包，至少包含 project.config.json 或明确的 UniApp/Taro/原生小程序项目入口；同时在使用说明中补充微信开发者工具导入目录、AppID 使用方式、后端地址配置位置和域名校验设置。
```

## BUG-G14-002：管理员和教师访问操作日志列表/导出接口均返回 400，操作日志功能不可用

### 基本信息

- Bug 类型：Logic bug
- 所属功能：管理端操作日志
- 严重程度：中
- 测试账号：`demo.admin / demo1234`、`demo.teacher / demo1234`
- 当前状态：建议提交

### 问题描述

第 14 组 Web 互测指南要求在 `/admin/logs` 页面测试“日志列表、条件筛选、分页、导出日志”等功能。前端管理端分包中也会调用 `/logs` 和 `/logs/export`。但使用管理员或教师账号请求操作日志列表、筛选或导出接口时，后端均返回 `400 Bad Request`，提示 `property action should not exist`、`property page should not exist`、`property pageSize should not exist` 等校验错误，导致操作日志列表与导出功能不可用。

### 前置条件

1. 打开服务器地址：`http://10.10.0.14/`。
2. 使用 `demo.admin / demo1234` 或 `demo.teacher / demo1234` 登录。
3. 进入管理端操作日志功能，或直接调用操作日志 API。

### 复现步骤

1. 使用管理员账号登录，获取登录态。
2. 请求 `GET /api/logs?page=1&pageSize=10`。
3. 请求 `GET /api/logs?page=1&pageSize=10&action=LOGIN`。
4. 请求 `GET /api/logs/export`。
5. 使用教师账号重复第 2 至第 4 步。

### 测试输入

```text
账号一：demo.admin / demo1234
账号二：demo.teacher / demo1234
接口一：GET http://10.10.0.14/api/logs?page=1&pageSize=10
接口二：GET http://10.10.0.14/api/logs?page=1&pageSize=10&action=LOGIN
接口三：GET http://10.10.0.14/api/logs/export
```

### 实际输出

```text
HTTP 400 Bad Request
{
  "message": [
    "property action should not exist",
    "property targetType should not exist",
    "property targetId should not exist",
    "property operatorId should not exist",
    "property startDate should not exist",
    "property endDate should not exist",
    "property page should not exist",
    "property pageSize should not exist"
  ],
  "error": "Bad Request",
  "statusCode": 400
}
```

### 期望输出

```text
操作日志列表应返回日志分页数据；筛选参数应被正确接收；导出接口应返回日志文件或明确的空数据导出结果，而不是拒绝前端正常传入的查询字段。
```

### 证据材料

- 接口复现结果：`tmp/docs/group14/web-test-results/logs-bug-repro.json`
- 总体烟测结果：`tmp/docs/group14/web-test-results/smoke-results.json`
- 前端调用依据：`tmp/docs/group14/web14/AdminDashboardPage-Do-HOzQP.js` 中存在 `/logs`、`/logs/export` 调用

### 修复建议

1. 检查后端操作日志查询 DTO 或 ValidationPipe 配置，允许 `action`、`targetType`、`targetId`、`operatorId`、`startDate`、`endDate`、`page`、`pageSize` 等前端实际使用的查询字段。
2. 列表接口和导出接口应复用一致的过滤参数定义，并对空筛选、分页默认值、未知字段分别给出合理处理。
3. 增加管理员和教师账号访问 `/api/logs`、`/api/logs/export` 的回归测试。

### 去重说明

- 是否与其他 bug 同根因：否
- 保留原因：该问题直接影响操作日志列表、筛选、分页和导出功能，属于管理端审计功能不可用的独立逻辑问题。

### 平台提交精简版

```text
Bug 类型：Logic bug
所属功能：管理端操作日志

问题描述：
第 14 组 Web 互测指南要求在 /admin/logs 页面测试日志列表、条件筛选、分页和导出日志。前端管理端代码也会调用 /logs 与 /logs/export。但使用管理员或教师账号请求操作日志列表、筛选或导出时，后端均返回 400 Bad Request，导致操作日志功能不可用。

复现步骤：
1. 打开 http://10.10.0.14/。
2. 使用 demo.admin / demo1234 登录。
3. 请求 GET /api/logs?page=1&pageSize=10。
4. 请求 GET /api/logs?page=1&pageSize=10&action=LOGIN。
5. 请求 GET /api/logs/export。
6. 使用 demo.teacher / demo1234 重复上述请求。

测试输入：
账号：demo.admin / demo1234、demo.teacher / demo1234。
接口：/api/logs?page=1&pageSize=10、/api/logs?page=1&pageSize=10&action=LOGIN、/api/logs/export。

实际输出：
上述接口均返回 HTTP 400，错误信息包括 property action should not exist、property page should not exist、property pageSize should not exist 等。

期望输出：
操作日志列表应返回日志分页数据；筛选参数应被正确接收；导出接口应返回日志文件或明确的空数据导出结果，而不是拒绝前端正常传入的查询字段。

证据：
接口复现结果保存在 tmp/docs/group14/web-test-results/logs-bug-repro.json；前端分包 AdminDashboardPage-Do-HOzQP.js 中存在 /logs 和 /logs/export 调用。

修复建议：
检查后端操作日志查询 DTO 或 ValidationPipe 配置，允许前端实际使用的 action、targetType、targetId、operatorId、startDate、endDate、page、pageSize 等字段；列表和导出接口应复用同一套过滤参数定义。
```

## BUG-G14-003：政策检索接口遇到空字符查询参数返回 500 Internal Server Error

### 基本信息

- Bug 类型：崩溃类 bug
- 所属功能：政策知识库检索
- 严重程度：中
- 测试账号：`demo.student / demo1234`、`demo.admin / demo1234`、`demo.leader / demo1234`
- 当前状态：建议提交

### 问题描述

第 14 组 Web 互测指南要求测试政策检索，并关注异常输入是否有提示。正常查询 `GET /api/policies?keyword=党团` 可以返回政策列表，但当查询参数中包含 URL 编码的空字符 `%00` 时，接口稳定返回 `500 Internal Server Error`。该问题在学生、管理员、领导账号下均可复现，说明后端未对异常查询字符做输入清洗或校验，异常输入会触发服务端内部错误。

### 前置条件

1. 打开服务器地址：`http://10.10.0.14/`。
2. 使用任一可登录账号，例如 `demo.student / demo1234`。
3. 获取登录态后调用政策检索接口。

### 复现步骤

1. 使用学生账号登录，确认登录成功。
2. 请求正常政策检索接口：`GET /api/policies?keyword=党团`。
3. 请求异常政策检索接口：`GET /api/policies?keyword=%00`。
4. 再次请求正常政策检索接口：`GET /api/policies?keyword=党团`，确认服务恢复但异常输入仍会触发 500。
5. 使用管理员或领导账号重复第 2 至第 4 步，可得到同样结果。

### 测试输入

```text
账号：demo.student / demo1234
正常接口：GET http://10.10.0.14/api/policies?keyword=党团
异常接口：GET http://10.10.0.14/api/policies?keyword=%00
```

### 实际输出

```text
正常查询返回 HTTP 200 和政策列表。
异常查询返回 HTTP 500：
{"statusCode":500,"message":"Internal server error"}
```

### 期望输出

```text
接口应对异常字符进行过滤或参数校验，返回空结果、400 Bad Request 或明确的“关键词格式不合法”提示，而不是返回 500 Internal Server Error。
```

### 证据材料

- 最小复现结果：`tmp/docs/group14/web-test-results/policy-null-keyword-bug-repro.json`
- 异常参数深测结果：`tmp/docs/group14/web-test-results/followup-boundary-fuzz-results.json`

### 修复建议

1. 在政策检索入口对 `keyword` 做字符白名单、长度限制和控制字符过滤。
2. 对数据库查询或全文检索层可能不支持的控制字符进行转义或拒绝。
3. 为 `%00`、超长关键词、表情符号等异常输入增加回归测试，确保返回可预期的 4xx 或空结果。

### 去重说明

- 是否与其他 bug 同根因：否
- 保留原因：该问题由政策检索异常输入触发 500，与操作日志参数校验失败和权限问题属于不同功能、不同触发条件。

### 平台提交精简版

```text
Bug 类型：崩溃类 bug
所属功能：政策知识库检索

问题描述：
政策检索接口对异常查询字符缺少校验。正常请求 /api/policies?keyword=党团 返回 200，但当 keyword 为 URL 编码空字符 %00 时，接口稳定返回 500 Internal Server Error。学生、管理员、领导账号均可复现。

复现步骤：
1. 打开 http://10.10.0.14/。
2. 使用 demo.student / demo1234 登录。
3. 请求 GET /api/policies?keyword=党团，返回 200。
4. 请求 GET /api/policies?keyword=%00。
5. 观察接口返回 500；再请求正常关键词可恢复为 200，但该异常输入仍可重复触发 500。

实际输出：
GET /api/policies?keyword=%00 返回 HTTP 500，响应为 {"statusCode":500,"message":"Internal server error"}。

期望输出：
接口应过滤或拒绝控制字符，返回空结果、400 Bad Request 或明确的关键词格式错误提示，而不是服务端内部错误。

证据：
复现结果保存在 tmp/docs/group14/web-test-results/policy-null-keyword-bug-repro.json。

修复建议：
对 keyword 做控制字符过滤、长度限制和查询转义，并增加异常输入回归测试。
```

## BUG-G14-004：领导账号可直接导出管理端政策台账并看到已停用政策

### 基本信息

- Bug 类型：Logic bug
- 所属功能：权限边界 / 政策知识库管理
- 严重程度：中
- 测试账号：`demo.leader / demo1234`
- 当前状态：建议提交；若第 14 组说明领导有政策台账导出权限，则可降级为候选

### 问题描述

第 14 组互测指南中，领导端主要范围是统计概览、终审审批、附件下载、审批台账导出和运行统计；政策知识库的新增、停用、导出政策台账属于管理端 `/admin/policies` 功能。前端路由分包也将 `/admin/policies` 限定为 `teacher`、`admin` 角色。但使用 `demo.leader` 直接调用管理端政策接口时，`GET /api/policies?includeInactive=true` 返回 11 条政策，其中包含 2 条 `INACTIVE` 已停用政策；`GET /api/policies/export` 返回政策台账 Excel 文件，内容包含已停用政策和政策正文摘要。

### 前置条件

1. 打开服务器地址：`http://10.10.0.14/`。
2. 使用领导账号 `demo.leader / demo1234` 登录。
3. 直接调用政策管理相关 API。

### 复现步骤

1. 使用领导账号登录，获取登录态。
2. 请求 `GET /api/policies?includeInactive=true`。
3. 观察返回结果中包含 `status=INACTIVE` 的已停用政策。
4. 请求 `GET /api/policies/export`。
5. 观察接口返回 `200` 和 `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`，可下载政策台账 Excel。
6. 打开 Excel，可看到“状态=已停用”的政策记录和政策摘要字段。

### 测试输入

```text
账号：demo.leader / demo1234
接口一：GET http://10.10.0.14/api/policies?includeInactive=true
接口二：GET http://10.10.0.14/api/policies/export
```

### 实际输出

```text
GET /api/policies?includeInactive=true：HTTP 200，返回 11 条政策，其中包含 2 条 INACTIVE。
GET /api/policies/export：HTTP 200，返回政策台账 Excel，文件中包含“已停用”政策与正文摘要。
```

### 期望输出

```text
领导账号若不具备政策知识库管理权限，应无法访问 includeInactive=true 的管理端政策列表，也不应能导出政策台账。接口应返回 403，或仅返回领导端明确需要的统计数据。
```

### 证据材料

- 深测矩阵：`tmp/docs/group14/web-test-results/followup-permission-export-results.json`
- 领导账号导出的政策台账：`tmp/docs/group14/web-test-results/followup-leader-api_policies_export.xlsx`
- 前端路由依据：`tmp/docs/group14/web14/index-CBayPRXB.js` 中 `/admin/policies` 路由角色为 `teacher`、`admin`
- 互测指南依据：`tmp/docs/group14/platform-documents/group14-extra.md` 中政策台账导出属于管理端测试，领导端仅列出审批台账导出

### 修复建议

1. 后端政策管理接口应与前端路由权限保持一致，导出和包含停用政策的查询仅允许 `admin` 或明确授权的管理角色访问。
2. 将领导端需要的政策数量等统计字段拆分为只读统计接口，不复用管理端全量政策列表和导出接口。
3. 增加 `leader`、`student`、`secretary` 访问 `/api/policies/export` 与 `/api/policies?includeInactive=true` 的权限回归测试。

### 去重说明

- 是否与其他 bug 同根因：否
- 保留原因：该问题属于后端接口权限边界，和操作日志不可用、政策检索 500 分别属于不同缺陷类型。

### 平台提交精简版

```text
Bug 类型：Logic bug
所属功能：权限边界 / 政策知识库管理

问题描述：
领导端互测范围是统计概览、终审审批、附件下载、审批台账导出和运行统计；政策台账导出属于管理端 /admin/policies。前端 /admin/policies 路由也限制为 teacher/admin。但使用 demo.leader 直接请求政策管理 API 时，可以查看 includeInactive=true 的政策列表并导出政策台账 Excel，里面包含已停用政策和政策摘要。

复现步骤：
1. 打开 http://10.10.0.14/。
2. 使用 demo.leader / demo1234 登录。
3. 请求 GET /api/policies?includeInactive=true。
4. 请求 GET /api/policies/export。
5. 打开导出的 Excel，查看“状态”列和政策摘要。

实际输出：
/api/policies?includeInactive=true 返回 200，共 11 条政策，其中包含 2 条 INACTIVE；/api/policies/export 返回 200 和政策台账 Excel，文件中包含“已停用”政策与正文摘要。

期望输出：
领导账号若无政策知识库管理权限，应无法访问包含停用政策的管理端列表，也不应能导出政策台账；接口应返回 403 或仅提供领导端需要的统计数据。

证据：
结果保存在 tmp/docs/group14/web-test-results/followup-permission-export-results.json；导出文件为 tmp/docs/group14/web-test-results/followup-leader-api_policies_export.xlsx。

修复建议：
后端政策管理接口权限应与前端路由一致，导出和 includeInactive 查询仅允许 admin 或明确授权的管理角色；领导端统计应使用单独的统计接口。
```
