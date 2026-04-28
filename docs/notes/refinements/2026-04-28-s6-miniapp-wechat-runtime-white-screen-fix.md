# S6 Miniapp 微信开发者工具白屏修复

- 关联主计划条目：`S6.13`
- 状态：`[x]`
- 日期：`2026-04-28`

## 背景

微信开发者工具导入后出现白屏，控制台同时暴露两类问题：

- `app.json is not found in the project root directory`
- `Cannot read property '_s' of undefined at Object.i [as useAuthStore]`

前者说明导入目录没有指向 `mp-weixin` 构建产物根目录；后者说明页面 `setup` 调用 Pinia store 时，运行期没有可用的 active Pinia instance。

## 范围

- 不改动业务接口、页面路由和视觉设计。
- 保持 `mp-weixin` 仍为 `miniapp` 唯一权威验收口径。
- 兼容两种微信开发者工具导入方式：直接导入构建产物目录，或导入 `miniapp` 根目录后由 `miniprogramRoot` 指向构建产物。

## 修复项

- [x] `miniapp/project.config.json` 新增 `miniprogramRoot = dist/build/mp-weixin/`，避免导入 `miniapp` 根目录时继续在源码根目录寻找 `app.json`。
- [x] `miniapp/src/main.ts` 改为共享单个 Pinia instance，并在模块初始化和 `createApp()` 内显式调用 `setActivePinia(pinia)`。
- [x] `miniapp/vite.config.ts` 将小程序构建目标收口为 `es2018`。
- [x] 新增 `miniapp/src/utils/async.ts`，以本地 `allSettled` helper 替代运行期原生 `Promise.allSettled` 依赖。
- [x] 移除小程序源码中的 `??` 和原生 `Promise.allSettled` 使用，降低微信小程序 JSCore 兼容风险。
- [x] `miniapp/README.md` 补充微信开发者工具导入说明。

## 验证

- [x] `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json`：通过。
- [x] `rg -n "\?\?|Promise\.allSettled|Object\.fromEntries|flatMap|matchAll|\.at\(" miniapp\src --glob "*.ts" --glob "*.vue" -S`：无命中。
- [x] `pnpm -C miniapp build:mp-weixin`：通过，输出 `miniapp/dist/build/mp-weixin`。
- [x] `miniapp/dist/build/mp-weixin/app.json`、`project.config.json`、`pages/index/index.js` 均存在。
- [x] 产物 JS 扫描 `?? / Promise.allSettled / Object.fromEntries / flatMap / matchAll / .at(`：无命中。
- [x] 产物 JS 扫描明显 optional chaining：无命中。
- [x] 产物 `app.js` 已包含 `setActivePinia(n)`，并在 mount 前完成 active Pinia 设置。

## 结论

本轮修复关闭了当前微信开发者工具白屏日志中的两个直接根因。后续若界面仍为空，应优先确认微信开发者工具是否清缓存并重新编译，以及后端 API 是否可访问；后端不可用可能导致数据为空，但不应再导致小程序外壳白屏。

## 变更记录

- `2026-04-28`：创建文件，记录微信开发者工具白屏的根因、修复项与验证结果。
- `2026-04-28`：后续微信开发者工具复核发现独立 `utils/async.js` 模块未注册会导致首页和其他页面注册失败；`miniapp/src/utils/async.ts` 已由 `S6.15` 修复替代，详见 `docs/notes/refinements/2026-04-28-s6-miniapp-runtime-module-registration-fix.md`。
