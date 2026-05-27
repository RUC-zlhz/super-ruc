# S64 微信订阅消息可达性复测

- 状态：`[x]`
- 主计划引用：`S64.1 ~ S64.4`
- 日期：`2026-05-27`

## 背景

用户要求验证“微信内部消息”的可达性，并明确不是站内信。当前仓库中对应能力是微信小程序订阅消息，不是 `IN_APP` 站内通知。

## 拆分

- [x] `S64.1` 复核 S25 微信订阅消息实现边界，确认链路为小程序订阅授权、后端授权保存、业务触发后调用微信订阅消息发送接口。
- [x] `S64.2` 运行后端定向集成测试，覆盖订阅配置、授权保存、模板字段映射、发送成功记录与微信失败记录。
- [x] `S64.3` 检查本地运行环境是否具备真实微信送达前置配置。
- [x] `S64.4` 明确当前结论：系统内部模拟网关链路可达；真实手机端送达还缺少本地 `WECHAT_APPID / WECHAT_SECRET` 和真实测试用户授权条件，不能在本地直接证明。

## 验证记录

- 已确认小程序端接口：`miniapp/src/api/notice.ts` 提供 `/notices/subscribe-config` 与 `/notices/subscribe-authorizations`；`miniapp/src/pages/notice/index.vue` 调用 `uni.requestSubscribeMessage` 或 `wx.requestSubscribeMessage`。
- 已确认后端实现：`backend/app/notice/service.py` 中 `send_wechat_subscribe_for_delivery` 会在 `WECHAT_SUBSCRIBE_ENABLED`、模板 ID、用户 openid 与 `accept` 授权满足时调用微信订阅消息发送函数，并记录 `WECHAT_SUBSCRIBE` 投递与 attempt。
- 已运行：
  - `uv run --extra dev pytest tests/integration/test_notice_flow.py::test_wechat_subscribe_config_and_authorization_record tests/integration/test_notice_flow.py::test_wechat_subscribe_send_records_success_and_failure -q -o cache_dir=.tmp/pytest-cache-wechat-reachability --basetemp=.tmp/pytest-tmp-wechat-reachability`
  - 结果：`2 passed in 81.04s`
- 本地 `backend/.env` 检查结果：`WECHAT_APPID` 与 `WECHAT_SECRET` 当前为空；未发现本地可直接使用的真实订阅消息凭据。

## 生产复测补充

- 生产主机：`user@10.10.0.13`
- 生产提交：`8604b69d`
- 生产服务：`backend / web / db / redis / minio` 均为 `healthy`，`smoke.sh` 通过。
- 生产配置状态：
  - `WECHAT_SUBSCRIBE_ENABLED=True`
  - `WECHAT_APPID` 已配置
  - `WECHAT_SECRET` 已配置
  - `WECHAT_SUBSCRIBE_REMINDER_TEMPLATE_ID` 已配置
  - `WECHAT_SUBSCRIBE_REQUEST_TEMPLATE_ID` 已配置
- 生产 backend 容器调用微信 `access_token` 接口成功，返回 token 长度 `137`，证明服务器到微信平台 API 真实可达。
- 生产库 `wechat_subscribe_authorizations` 当前 `total=0`、`accept=0`，暂无任何小程序订阅授权记录。
- 生产真实发送尝试：对唯一已绑定微信的学生 `2024201540 / 张念昊` 直接调用微信订阅消息发送接口，返回 `errcode=43101`、`errmsg=user refuse to accept the msg`。这证明 `message/subscribe/send` 真实接口可达，失败原因是微信侧没有该模板的有效用户授权。

## 当前结论

- 不是站内信的微信订阅消息代码级链路目前可达。
- 生产环境已具备真实微信订阅消息凭据、模板和微信 API 出网能力。
- 真实手机端送达测试仍需要：使用绑定 openid 的测试学生账号，在小程序端点击订阅并让微信侧产生有效模板授权，同时本系统授权状态入库为 `accept`；当前生产库没有授权记录，直接调用微信真实发送也返回 `43101 user refuse to accept the msg`。
