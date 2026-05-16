# S17 可见文案口径统一

- 日期：`2026-05-16`
- 关联主计划：`S17.1, S17.2, S17.3, S17.4`
- 当前状态：`DONE`

## 问题

- Web 管理端和小程序学生端存在若干不准确或不统一的可见文案：
  - 管理端品牌区混用 `教师管理员后台 / 教师管理员管理平台 / 教师管理员管理台`。
  - 荣誉、审批、导入导出页面副标题误写为 `教师荣誉 / 教师业务 / 教师数据`。
  - 小程序学生端应用名、首页入口和页面标题存在 `信息学院综合服务 / 奖助学金 / 宿舍服务 / 缴费记录 / 荣誉榜 / 统一进度 / 学业查看` 等范围不稳或过泛表述。
  - Web HTML 标题和后端 OpenAPI 描述仍使用旧平台名。

## 修复

- [x] `S17.1` 全局检索品牌、平台名、功能入口、页面标题和副标题相关文案，先列出候选让用户确认方向。
- [x] `S17.2` Web 管理端统一为 `信息学院管理后台`，并修正荣誉、审批、导入导出、运营看板等页面副标题。
- [x] `S17.3` 小程序学生端统一为 `信息学院学生服务`，将入口文案收口为当前实现实际覆盖的 `荣誉公示 / 事务办理 / 政策查询 / 学业分析 / 进度中心`。
- [x] `S17.4` 后端可见 API 描述统一为 `中国人民大学信息学院学生综合服务平台 — 后端 API`，并将进度中心错误文案同步为 `进度中心`。

## 验证

- 文案残留扫描：
  - `rg -n "教师管理员|教师业务|教师数据|奖助学金|宿舍服务|缴费记录|党团进度列表|学业查看|统一进度|荣誉榜|学生综合服务与党团管理平台|信息学院综合服务|立学为民|治学报国" web/src web/dist miniapp/src miniapp/dist/build/mp-weixin backend/app` -> 无命中。
- Backend：
  - `uv run --no-sync python -m py_compile app/main.py app/progress/__init__.py app/progress/service.py app/progress/schemas.py app/progress/router.py` -> 通过。
  - `uv run --no-sync ruff check app/main.py app/progress/__init__.py app/progress/service.py app/progress/schemas.py app/progress/router.py` -> `All checks passed`。
- Web：
  - `pnpm -C web build` -> 通过；仅输出 Dart Sass legacy JS API 弃用警告。
- Miniapp：
  - `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` -> 通过。
  - `pnpm -C miniapp build:mp-weixin` -> 通过，产物位于 `miniapp/dist/build/mp-weixin`。

