# Miniapp 微信小程序范围约束

- 日期：`2026-04-22`
- 关联主计划：`S0.3, S1.5, S2A.4, S2B.1, S2B.2, S2B.4, S2C.2, S3A.1, S3B.3, S5B.1`
- 当前状态：`DONE`

## 范围

- 将本仓库 `miniapp` 的产品定位明确为“微信小程序学生端”，不是通用 H5 移动站，也不是其他小程序平台的抽象实现。
- 将 `mp-weixin` 明确为 `miniapp` 的唯一权威验收口径；保留 `h5` 仅作为临时开发预览能力，不作为需求实现完成态的判定依据。
- 将微信小程序约束同步回写到权威主计划和 `miniapp/README.md`，避免后续实现继续沿着通用前端语义扩散。

## 非范围

- 不在本轮移除现有 `dev:h5` / `build:h5` 命令，也不重构当前 `uni-app` 技术栈。
- 不在本轮新增微信开放能力接入（如订阅消息、支付、客服、分享链路），除非后续需求明确提出。
- 不在本轮改动已经完成验收的业务闭环逻辑；本轮仅收口范围定义与文档口径。

## 任务清单

- [x] 确认当前 `miniapp` 构建目标与运行时 API 是否以 `mp-weixin` 为主
- [x] 新增本细化文件，固化“微信小程序规范优先”的范围约束
- [x] 在 `docs/notes/current-implementation-plan.md` 登记本细化文件并补充约束说明
- [x] 修正 `miniapp/README.md` 中“主 + H5 兼容 / axios(H5)”等易误导表述
- [x] 实跑 `pnpm -C miniapp build:mp-weixin`，确认当前工作线可生成微信小程序产物与 `app.json`

## 验收条件

- 主计划已明确写出：`miniapp` 以微信小程序规范和 `mp-weixin` 构建结果为准。
- `miniapp/README.md` 不再把 H5 兼容描述为与微信小程序同级的产品目标。
- 当前代码静态排查未发现 `window / document / localStorage / axios / fetch` 等明显 H5 优先实现痕迹。
- 当前工作线已实际执行 `pnpm -C miniapp build:mp-weixin`，并在 `miniapp/dist/build/mp-weixin/` 生成可供微信开发者工具导入的 `app.json` 与 `project.config.json`。

## 风险 / 阻塞

- 当前仓库仍保留 `dev:h5` / `build:h5` 脚本，后续若有人只跑 H5 预览，仍可能误把 H5 行为当成验收依据；需要以后续评审和文档持续约束。
- 本轮为范围澄清，不代表已经逐页完成微信小程序 UX 细则补齐；若后续进入 UI/交互优化，应以微信小程序官方交互和能力边界为准继续审视。

## 变更记录

- `2026-04-22`：创建文件，正式落盘“`miniapp` = 微信小程序前端，`mp-weixin` = 唯一权威验收口径，H5 仅作临时预览”。
- `2026-04-22`：在当前工作线重新实跑 `pnpm -C miniapp build:mp-weixin`，确认 `miniapp/dist/build/mp-weixin/app.json` 已生成，且构建输出明确提示可直接导入微信开发者工具。
