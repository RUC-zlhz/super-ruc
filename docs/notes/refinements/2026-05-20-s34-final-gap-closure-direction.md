# S34 最终缺口闭合方向

- 日期：`2026-05-20`
- 主计划条目：`S34`
- 状态：`[!]`

## 用户确认方向

- 访客登录：保留为开发模式开关。
- 班团骨干工作台：向老师后台的强协同靠拢，但仍保持后端范围校验。
- 学业分析：允许更强的学分缺口结论，并优化展示视觉。
- 通知渠道：接真实微信订阅消息。
- 演示数据：使用真实学院数据。
- 知识问答：只做检索式回答。

## 实施范围

- [x] 后端新增/收口访客登录开发开关，生产环境默认关闭。
- [x] 小程序登录页与个人页只在开发开关开启时展示访客入口。
- [x] 知识问答固定为检索/排序式回答，移除生成式表达。
- [x] 班团骨干工作台继续向老师后台靠拢，补强协同入口与可视化，但保留 scope 校验与审计。
- [x] 学业缺口页和管理端看板补更强的缺口结论表达与视觉层级。
- [!] 微信订阅消息保持真实模板发送链路，补齐配置与演示验证口径。
- [!] 真实学院数据导入口径单独声明，避免将默认种子误当作真实业务数据。

## 约束

- 不修改已稳定的页面结构与排版，除非为实现上述方向所必需。
- 不把推理式回答伪装成检索结果。
- 不把访客态开放给生产默认。

## 验证计划

- [x] 后端静态校验与定向测试：`ruff` 与 `py_compile` 通过；认证集成测试因本机测试库拒连未进入业务断言。
- [x] Web / Miniapp 类型检查或构建：`pnpm -C web build` 与 `pnpm -C miniapp build:mp-weixin` 通过。
- [x] 关键页面回归阅读确认。

## 当前结论

本轮已完成可直接落地的收口：访客登录开发开关、知识检索式回答、班团骨干协同入口与学业展示强化。真实学院数据与微信订阅消息正式联调仍依赖外部配置与数据，因此本细化保留 `[!]` 外部输入阻塞。

## 验证记录

- 后端静态校验：`uv run --extra dev ruff check app/core/config.py app/auth/service.py app/knowledge/service.py app/knowledge/router.py app/knowledge/ai_matcher.py app/report/schemas.py app/report/service.py app/workflow/router.py app/workflow/service.py tests/conftest.py tests/integration/test_auth_flow.py` 通过。
- 后端编译校验：`uv run --extra dev python -m py_compile ...` 通过。
- Web 构建：`pnpm -C web build` 通过。
- Miniapp 微信小程序构建：`pnpm -C miniapp build:mp-weixin` 通过。
- 阻塞验证：`uv run --extra dev pytest tests/integration/test_auth_flow.py -q --basetemp=.tmp/pytest-tmp-s34-auth` 在 fixture setup 阶段因 `localhost:54322/sip_db_test` 连接拒绝失败，未进入业务断言。
