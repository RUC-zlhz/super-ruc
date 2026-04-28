# Miniapp 微信小程序 TabBar 图标修复

- 日期：`2026-04-22`
- 关联主计划：`S0.3, S1.5, S5B.1`
- 当前状态：`DONE`

## 范围

- 修复微信开发者工具编译 `app.json` 时的 tabBar 图标缺失错误。
- 明确当前 `uni-app` 微信小程序构建对 tabBar 图标的有效源码目录是 `miniapp/src/static/`。
- 为 tabBar 图标补一份可重复执行的生成脚本，避免后续继续靠手工补文件。

## 非范围

- 不在本轮改动 tabBar 的页面结构、文案、颜色配置或页面跳转逻辑。
- 不在本轮重做整套品牌视觉系统，仅补齐微信小程序运行必需资源。
- 不在本轮收口其他页面级 UI 细节或交互规范差异。

## 任务清单

- [x] 复核微信开发者工具报错与 `miniapp/src/pages.json` 中的 tabBar 图标配置
- [x] 确认当前仓库缺失 `tab-home* / tab-notice* / tab-profile*` 6 个 PNG 资源
- [x] 新增 `scripts/miniapp/generate_tabbar_icons.ps1`，生成 tabBar 图标
- [x] 将图标生成到 `miniapp/src/static/`，使 `mp-weixin` 构建能复制到微信小程序产物目录
- [x] 实跑 `pnpm -C miniapp build:mp-weixin`，确认 `miniapp/dist/build/mp-weixin/static/` 中存在 6 个图标文件
- [x] 修正 `miniapp/README.md` 中对静态资源目录的描述，避免后续继续放错目录

## 验收条件

- `miniapp/src/pages.json` 中引用的 6 个图标文件在源码目录 `miniapp/src/static/` 中全部存在。
- `pnpm -C miniapp build:mp-weixin` 成功。
- `miniapp/dist/build/mp-weixin/static/` 中存在：
  - `tab-home.png`
  - `tab-home-active.png`
  - `tab-notice.png`
  - `tab-notice-active.png`
  - `tab-profile.png`
  - `tab-profile-active.png`
- 微信小程序产物中的 `app.json` 仍引用 `static/...` 路径，且这些路径在产物目录中可解析。

## 风险 / 阻塞

- 本机在沙箱内执行 `pnpm -C miniapp build:mp-weixin` 仍可能受 `spawn EPERM` 影响；本轮验证通过提权命令完成。
- 当前仅验证了产物文件存在性；若用户本地微信开发者工具仍缓存旧产物，需要重新导入或重新编译 `dist/build/mp-weixin`。

## 变更记录

- `2026-04-22`：创建文件，记录微信小程序 tabBar 图标缺失的真实根因、修复步骤与验证结果。
