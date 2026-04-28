# Miniapp 小程序主图标资产

- 日期：`2026-04-28`
- 状态：`[x]`
- 关联主计划条目：`S6.20`
- 范围：只新增小程序主图标资产、可复现生成脚本和说明文档；不改业务接口、页面路由、tabBar 配置或微信 AppID。

## 背景

当前 `miniapp/src/static/` 已包含 tabBar 图标和首页视觉资源，但缺少用于微信公众平台上传、项目展示和交付归档的小程序主图标。微信小程序主图标不是 `pages.json` 或 `manifest.json` 中可直接生效的运行时配置项，因此本轮以“正式资产 + 可复现脚本 + 构建带出验证”为交付边界。

## 实施

- [x] 新增 `scripts/miniapp/generate_app_icon.ps1`，使用项目红色品牌基调、白色“信”字主标、书页与连接节点图形生成小程序主图标。
- [x] 生成并纳入 `miniapp/src/static/app-icon.png`、`app-icon-512.png`、`app-icon-144.png` 三个 PNG 资产。
- [x] 更新 `miniapp/README.md`，说明主图标资产路径、生成脚本以及微信公众平台后台上传边界。

## 验证

- [x] 执行 `& .\scripts\miniapp\generate_app_icon.ps1`，成功生成三种尺寸 PNG。
- [x] 执行 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json`，通过。
- [x] 执行 `pnpm -C miniapp build:mp-weixin`，通过，输出 `miniapp/dist/build/mp-weixin`。
- [x] 确认构建产物 `miniapp/dist/build/mp-weixin/static/app-icon.png`、`app-icon-512.png`、`app-icon-144.png` 均已带出。

## 结论

小程序主图标已作为正式静态资产进入 `miniapp/src/static/`，并具备可复现生成脚本。后续如需在微信公众平台更新线上小程序头像，应上传 `miniapp/src/static/app-icon.png`。
