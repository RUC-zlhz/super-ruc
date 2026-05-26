# 2026-05-26 S53 小程序开发态本地接口自动回正

- 状态：`[x]` 已完成
- 关联主计划：`S53`
- 依赖：`S51`、`S52`

## 背景

在微信开发者工具中通过调试控制台手动执行：

- `wx.setStorageSync('sip.api_base_url', ...)`
- `wx.removeStorageSync('sip.access_token')`
- `wx.removeStorageSync('sip.refresh_token')`

对首次使用者并不友好，而且部分环境下调试控制台并不提供直接输入体验，导致本地联调经常被旧的远端接口地址或旧 token 卡住。

## 目标

让小程序在开发态默认直接回到本地接口：

1. 不要求开发者手动打开控制台输入 storage 修正命令。
2. 如果历史上存过其他接口地址，开发态自动清掉该覆盖值。
3. 如果历史接口地址与当前开发态本地地址不一致，同时清掉旧 token，避免跨环境 token 残留引发 401。
4. 不影响显式配置的环境变量接口地址，也不影响正式环境。

## 实现

- [x] `S53.1` 在 `miniapp/src/utils/request.ts` 中新增开发态本地接口收口逻辑。
- [x] `S53.2` 当 `import.meta.env.DEV=true` 且未显式配置 `VITE_MINIAPP_API_BASE_URL / VITE_API_BASE_URL` 时，强制使用 `http://127.0.0.1:8080/api/v1`。
- [x] `S53.3` 若检测到 storage 中保留了其他接口地址，则自动移除 `sip.api_base_url`，并同时清掉 `sip.access_token` 与 `sip.refresh_token`。
- [x] `S53.4` 保留环境变量优先级，避免后续显式联调地址被开发态逻辑误覆盖。

## 验证

- `.\web\node_modules\.bin\vue-tsc.CMD --noEmit -p miniapp\tsconfig.json` 通过。

## 结论

当前开发态下，小程序重新编译后会默认连本地后端，无需再依赖微信开发者工具控制台手工修正接口地址；而正式环境和显式环境变量配置不受影响。
