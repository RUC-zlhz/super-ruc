# S25 微信订阅消息模板字段对齐

- 状态：`[x]`
- 主计划引用：`S25.1, S25.4, S25.5, S25.6`
- 日期：`2026-05-20`

## 背景

微信公众平台当前已添加两个可用订阅消息模板：

- 活动日程提醒：`PEiTeRUhzOL3bbYgf3UBWTnSKg_R6j8jrPInZeqvh8s`
- 申请状态变更通知：`5zETE9uyoWXH54hBx7nUYchsb1BJEhBUPiiGkbIJgLU`

这两个模板的字段编号与 S25 首版通用字段 `thing1 / thing2 / time3 / phrase4` 不一致，必须按实际模板字段发送，否则微信接口会拒绝。

## 本次调整

- [x] 活动日程提醒映射为 `thing4=活动名称`、`thing1=活动时间`、`thing2=活动内容`、`thing5=活动地点`、`thing3=温馨提示`。
- [x] 申请状态变更通知映射为 `thing11=申请名称`、`thing2=当前状态`、`time12=申请时间`、`character_string7=工单号`。
- [x] `backend/.env.example` 与临时部署说明写入当前两个模板 ID。
- [x] 后端订阅消息发送测试补充字段编号断言，覆盖申请状态和党团流程提醒两类场景。

## 当前口径

生产环境仍由 `WECHAT_SUBSCRIBE_ENABLED` 控制是否真实发送。启用时必须同时配置微信小程序 `WECHAT_APPID / WECHAT_SECRET`，并将两个模板 ID 写入环境变量。

## 验证记录

- `uv run --extra dev ruff check app/notice/service.py tests/integration/test_notice_flow.py` 通过。
- `uv run --extra dev python -m py_compile app\notice\service.py tests\integration\test_notice_flow.py` 通过。
- `uv run --extra dev pytest tests/integration/test_notice_flow.py::test_wechat_subscribe_send_records_success_and_failure -q -o cache_dir=.tmp/pytest-cache-wechat-template --basetemp=.tmp/pytest-tmp-wechat-template` 因本机测试数据库连接拒绝在 fixture setup 阶段失败，错误为 `ConnectionRefusedError: [WinError 1225] 远程计算机拒绝网络连接。`，未执行到新增字段断言。
