# 2026-05-19 小程序智能咨询能力核查

- 状态：`[x] 已完成`
- 关联主计划：`S8.1` Miniapp 知识库自助闭环、`S13.4` 官方来源优先实现
- 核查对象：`miniapp` 学生端“知识查询 / 政策查询 / 帮助中心”链路

## 核查目标

核查“小程序端是否实现智能咨询：录入学院/学校常用政策文件和办事指南后，学生可通过关键词搜索或问题描述快速获取答复”。

本次核查不只检查是否存在入口，还重点检查：

1. 小程序端是否存在可访问的搜索/咨询入口；
2. 搜索接口是否真的覆盖正文级字段，而不只是标题；
3. “智能匹配”是否会给出具体答复，还是只返回候选条目；
4. 当前项目默认数据/当前可访问环境中，是否已经具备足够内容让学生搜到具体答案。

## 结论摘要

### 1. 入口与交互链路：已实现

- 小程序首页存在多个入口跳转到知识查询页：
  - `政策查询`
  - `帮助中心`
- 页面路径为 `miniapp/src/pages/knowledge/index.vue`，在 `miniapp/src/pages.json` 中已注册为 `pages/knowledge/index`。
- 页面具备：
  - 关键词搜索框；
  - 分类筛选；
  - 标签二次筛选；
  - “智能匹配”按钮；
  - 知识详情弹层；
  - 模板下载入口；
  - 官方来源展示与链接复制。

### 2. 搜索链路：已实现，且检索范围不只标题

- 小程序调用 `searchKnowledge()` 访问 `/api/v1/knowledge/search`。
- 后端搜索会命中以下字段：
  - `title`
  - `summary`
  - `applicable_condition`
  - `required_materials`
  - `process_steps`
  - `body_md`
- 因此从实现上看，关键词搜索不是“只能搜标题”的浅层检索。

### 3. “智能匹配”能力：部分实现，不是自由问答

- 小程序“智能匹配”会调用 `/api/v1/knowledge/ai-match`。
- 但当前实现明确是“对已检索到的已发布知识条目做重排序”，不是生成式自由回答：
  - `AI_QA_ENABLED=false` 时，走关键词匹配降级；
  - `AI_QA_ENABLED=true` 时，也只是对候选条目做语义重排；
  - 任何模式下都不会编造新答案。
- 因此学生端拿到的首先是“候选条目列表 + 命中原因”，再点开条目详情后，才能看到结构化正文：
  - 适用条件
  - 所需材料
  - 办理步骤
  - `body_md` 正文
  - 人工咨询提示

### 4. 当前默认数据状态：不能保证开箱即答

- 仓库默认种子里只注册了知识分类：
  - `PARTY`
  - `YOUTH_LEAGUE`
  - `SCHOLARSHIP`
  - `ACADEMIC`
  - `CERTIFICATE`
  - `LEAVE`
  - `DAILY_AFFAIRS`
  - `OTHER`
- 但默认种子中没有发现 `KnowledgeEntry` 或 `TemplateAsset` 的正文级知识条目导入。
- 这意味着在“只执行默认 seed”的新环境中，小程序可以打开知识查询页、显示分类和搜索框，但未必能搜到任何具体答复；是否能答，取决于管理员是否在管理端手工创建并发布了知识条目。

## 证据

### 小程序入口与页面

- `miniapp/src/pages.json`
- `miniapp/src/pages/index/index.vue`
- `miniapp/src/pages/knowledge/index.vue`
- `miniapp/src/api/knowledge.ts`

### 后端搜索与智能匹配

- `backend/app/knowledge/router.py`
- `backend/app/knowledge/service.py`
- `backend/app/knowledge/repository.py`
- `backend/app/knowledge/ai_matcher.py`

### 默认数据边界

- `backend/scripts/seed/__init__.py`
- `backend/scripts/seed/knowledge_categories.py`

## 运行态复核说明

- 本次核查期间，本地 `127.0.0.1:8080` 后端一度不可达，无法继续用当前本地环境完成“真实库数据搜索”复核。
- 仓库中登记的临时联调环境 `http://123.57.54.195` 当前返回 `502 Bad Gateway`，也无法作为运行态证据。
- 因此本轮能够确认：
  - 功能代码链路存在；
  - 自动化测试已覆盖“发布条目后搜索与详情可返回具体字段”；
  - 但不能声称“当前默认部署/默认数据下，这些主题已经都能搜到具体答案”。

## 最终判定

- 若问题是“这个小程序有没有实现智能咨询这条功能链路”：`已实现，但属于知识条目检索 + 候选匹配，不是聊天式自由问答。`
- 若问题是“当前项目默认状态下，学生搜奖助学金/入党入团/请假/证明/就业实习/宿舍调整，是否一定能得到具体答案”：`不能保证。当前仓库默认数据没有随种子写入一批已发布知识正文，若后台未手工录入并发布条目，学生端会出现“有入口、有搜索，但搜不到具体答复”的情况。`
