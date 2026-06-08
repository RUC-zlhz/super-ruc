# 2026-06-08 S73 小程序时间格式化 Intl 运行时兼容修复

- 关联主计划条目：`S73.1` ~ `S73.4`
- 状态：`[x]` 已完成
- 输入来源：微信小程序运行时报错 `ReferenceError: Intl is not defined`，堆栈定位到 `formatShanghaiDateTime`。

## 范围

本轮只修复学生端小程序时间格式化运行时兼容问题，不扩大到后端时间字段、Web 管理端时间展示或历史互测问题重判。

## 执行拆分

- [x] `S73.1` 定位根因：`miniapp/src/utils/datetime.ts` 直接调用 `new Intl.DateTimeFormat(...)`，微信小程序部分运行环境没有全局 `Intl`。
- [x] `S73.2` 将上海时间格式化改为纯时间戳与 `UTC+8` 偏移计算，输出稳定的 `YYYY-MM-DD HH:mm` 与 `YYYY-MM-DD`。
- [x] `S73.3` 运行 Miniapp 类型检查、微信小程序构建与产物 `Intl` 残留扫描。
- [x] `S73.4` 提交并推送到 GitHub。

## 验证计划

- [x] Miniapp 类型检查：`.\web\node_modules\.bin\vue-tsc.CMD --noEmit -p miniapp\tsconfig.json` 通过。
- [x] Miniapp 微信构建：`corepack pnpm -C miniapp build:mp-weixin` 通过。
- [x] 产物扫描：`rg -n "Intl|DateTimeFormat" miniapp/dist/build/mp-weixin --glob "!**/*.map"` 无命中，确认运行时代码不再依赖 `Intl`。
