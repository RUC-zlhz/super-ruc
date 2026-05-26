# S48 Miniapp 微信开发者工具告警排查与首页 key 修复

- 关联主计划条目：`S48`
- 状态：`[x]` 已完成
- 日期：`2026-05-26`

## 背景

微信开发者工具日志报告 `utils/request-badge.js` 模块未定义、首页存在重复 `wx:key`，同时伴随 `SharedArrayBuffer` 与 `wx.getSystemInfoSync` 废弃提示。

## 范围

- 核查 `request-badge` 源码与 `mp-weixin` 构建产物是否一致，并在开发者工具缓存仍复现时移除独立模块依赖。
- 扫描最新构建产物中的相对 `require()`，确认是否还有类似缺失模块。
- 核查 `wx:key` 重复来源，并修复小程序首页入口列表的非唯一 key。
- 区分项目源码问题与微信开发者工具 / uni-app vendor 层提示。

## 执行项

- [x] `S48.1` 初步确认 `miniapp/src/utils/request-badge.ts` 与 `miniapp/dist/build/mp-weixin/utils/request-badge.js` 在本地最新构建中存在。
- [x] `S48.2` 为规避微信开发者工具继续加载旧模块索引，将事务徽章 helper 合并进已有 `miniapp/src/api/workflow.ts`，删除独立 `miniapp/src/utils/request-badge.ts`，让请求页不再生成 `../../utils/request-badge.js` require。
- [x] `S48.3` 对 `miniapp/dist/build/mp-weixin` 的 JS 相对 `require()` 做存在性扫描，结果无缺失模块。
- [x] `S48.4` 将首页“重点入口”和“常用服务”的列表 key 从 `item.url` 改为稳定业务 key，避免多个入口共享 `/pages/request/index` 或 `/pages/knowledge/index` 时触发 `wx:key` 重复。
- [x] `S48.5` 区分废弃提示来源：项目源码无直接 `getSystemInfoSync` 调用；当前提示来自 uni-app 生成的 `common/vendor.js`，`SharedArrayBuffer` 属于开发者工具 Chromium 环境提示。

## 验证结果

- `git diff --check -- miniapp/src/pages/index/index.vue` 通过。
- `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` 通过。
- `rg -n ':key="item\.url"|:key="item\.path"' miniapp/src --glob '*.vue'` 无命中。
- `pnpm -C miniapp build:mp-weixin` 通过。
- 清理 `miniapp/dist/build/mp-weixin` 后重新构建，生成产物中已无 `request-badge` 引用。
- 构建后相对 `require()` 存在性扫描输出 `NO_MISSING_RELATIVE_REQUIRE`。

## 结论

`request-badge.js` 报错不是当前源码缺文件，而是微信开发者工具加载了旧模块索引或旧产物。当前代码已移除独立 `request-badge` 模块依赖，修复首页重复 `wx:key`，并确认最新构建产物没有 `request-badge` 引用和缺失相对 `require()`。
