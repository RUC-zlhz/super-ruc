# S30 学生主档与微信绑定管理补强

- 日期：`2026-05-19`
- 关联主计划：`S30.1, S30.2, S30.3, S30.4, S30.5`
- 状态：`[x]`

## 背景

S29 已补齐生产默认学生、培养方案导入，以及学生画像页的学籍信息编辑入口。但教师/管理员日常运维还缺少两个直接能力：在后台手工新增学生主档，以及查看和处理学生微信登录绑定。

当前微信绑定由学生小程序登录时自动创建，若学生误绑、换微信或旧微信不再可用，后台必须能够解除旧绑定，让学生重新用学号和校验信息完成绑定。

## 任务清单

- [x] `S30.1` 后端新增学生主档创建接口，沿用画像范围权限，限制 scoped 教师只能在自身管理范围内新增学生。
- [x] `S30.2` 后端扩展学生主档编辑接口，支持修改学号、姓名、性别、年级、专业、班级、政治面貌、入学年份与预计毕业年份，并校验学号唯一性和目标范围权限。
- [x] `S30.3` 后端新增学生微信绑定查看与解绑接口；解绑后旧微信用户失去 `STUDENT` 身份并失效既有 token，学生可重新绑定新微信。
- [x] `S30.4` Web 学生管理页新增“新增学生”“主档”“微信”入口，画像页保留主档编辑入口。
- [x] `S30.5` 完成本地静态/构建验证、生产重建与 smoke。

## 验证记录

- 本地 `uv run --no-sync ruff check app/profile/router.py app/profile/schemas.py app/profile/service.py tests/integration/test_profile_flow.py` 通过。
- 本地 `uv run --no-sync python -m py_compile app/profile/router.py app/profile/schemas.py app/profile/service.py tests/integration/test_profile_flow.py` 通过。
- 本地 `pnpm -C web build` 通过。
- 本地新增集成用例 `test_admin_creates_student_updates_master_data_and_unbinds_wechat` 通过。
- 服务器重建 `backend` / `web` 后，`bash deploy/intranet-prod/scripts/smoke.sh` 通过，`http://10.10.0.13/healthz` 与 `http://10.10.0.13/` 均正常，未登录探测新增学生、主档修改、微信绑定查看和微信解绑接口均返回 `401`。

## 当前口径

- 后台不手工写入任意微信 `openid`；真实绑定仍由学生小程序登录产生。
- 后台负责查看绑定状态和解绑旧绑定；解绑后学生重新登录小程序并输入学号与校验信息即可建立新绑定。
- 绑定解绑是高风险账号操作，必须走后端权限判断和审计留痕。
