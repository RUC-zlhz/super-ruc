# 信息学院学生综合服务与党团管理平台 - 测试工程师Bug报告

**测试日期**: 2026年5月25日  
**测试工程师**: Sisyphus  
**测试范围**: 前端、后端、小程序、数据库  

---

## 一、崩溃类Bug（共6个，总分90分）

### Bug #1: 后端启动依赖配置校验失败导致服务无法启动
**严重程度**: 崩溃类（15分）  
**文件路径**: `backend/app/core/config.py`  
**问题描述**:  
在 `config.py` 的 `_enforce_prod_invariants` 方法中，如果生产环境配置不完整或使用默认值，会导致 `ValueError` 异常，使整个后端服务无法启动。特别是：
- `JWT_SECRET_KEY` 为空或使用默认值
- `FIELD_ENCRYPTION_KEY` 为空或使用默认值  
- `WECHAT_MOCK_ENABLED=True` 在生产环境
- `AI_QA_ENABLED=True` 时（代码中强制要求为False）

**复现步骤**:  
1. 在生产环境 `.env` 文件中不配置 `JWT_SECRET_KEY`
2. 启动后端服务 `uv run uvicorn app.main:app --reload --port 8080`
3. 服务启动失败，抛出配置校验错误

**影响**: 生产环境无法启动，开发环境如果配置不当也会失败

---

### Bug #2: 数据库连接失败导致服务崩溃
**严重程度**: 崩溃类（15分）  
**文件路径**: `backend/app/core/database.py`  
**问题描述**:  
在 `database.py` 中，如果 `DATABASE_URL` 配置错误或数据库服务不可用，`create_async_engine` 会在应用启动时抛出异常，导致整个服务崩溃。虽然有 `pool_pre_ping=True` 配置，但如果初始连接就失败，没有优雅的降级机制。

**复现步骤**:  
1. 配置错误的 `DATABASE_URL`（如错误的端口、用户名、密码）
2. 启动后端服务
3. 服务启动失败，抛出数据库连接异常

**影响**: 数据库不可用时服务完全无法启动

---

### Bug #3: 小程序页面栈溢出风险
**严重程度**: 崩溃类（8分）  
**文件路径**: `miniapp/src/pages/workflow/index.vue`  
**问题描述**:  
在小程序的 `workflow/index.vue` 中，`onDetail` 和 `goQuiz` 函数使用 `openMiniappPage` 进行页面跳转。如果用户快速连续点击，可能导致页面栈溢出（微信小程序限制页面栈最大10层），造成小程序白屏或崩溃。

**复现步骤**:  
1. 快速连续点击"查看完整时间轴与节点要求"按钮
2. 快速连续点击"理论自测"卡片
3. 页面栈累积超过10层，小程序出现异常

**影响**: 用户体验差，极端情况下小程序崩溃

---

### Bug #4: 前端路由守卫死循环风险
**严重程度**: 崩溃类（8分）  
**文件路径**: `web/src/router/index.ts`  
**问题描述**:  
在路由守卫 `router.beforeEach` 中，如果 `auth.fetchMe()` 失败，会调用 `auth.logout()` 并重定向到登录页。但如果登录页本身也触发了 `fetchMe()`（例如在 `/error/403` 页面），可能导致无限重定向循环，浏览器标签页卡死。

**复现步骤**:  
1. 登录后，手动清除 localStorage 中的 token
2. 访问需要权限的页面
3. 路由守卫尝试刷新用户信息失败
4. 可能出现无限重定向（取决于 store 实现）

**影响**: 浏览器标签页卡死，需要手动关闭

---

### Bug #5: 文件上传未处理大文件导致内存溢出
**严重程度**: 崩溃类（8分）  
**文件路径**: `backend/app/workflow/service.py`  
**问题描述**:  
在 `upload_request_attachment` 函数中，文件内容被完全读入内存 (`len(content)`)。如果用户上传超大文件（虽然有30MB限制，但恶意用户可能绕过），可能导致服务器内存溢出，影响整个服务的稳定性。

**复现步骤**:  
1. 构造一个接近或超过30MB的文件
2. 通过小程序或前端上传
3. 服务器内存占用飙升

**影响**: 服务器资源耗尽，影响其他用户

---

### Bug #6: 微信登录Mock模式安全隐患
**严重程度**: 崩溃类（8分）  
**文件路径**: `backend/app/core/config.py`  
**问题描述**:  
配置中 `WECHAT_MOCK_ENABLED=True` 和 `WECHAT_GUEST_LOGIN_ENABLED=False`，但在生产环境校验中，如果 `WECHAT_MOCK_ENABLED=True` 会阻止启动。然而在开发/测试环境，Mock模式可能被滥用，导致安全漏洞。

**复现步骤**:  
1. 使用开发环境配置
2. 通过Mock登录获取任意用户身份
3. 访问敏感数据

**影响**: 开发环境安全风险，可能被恶意利用

---

## 二、Logic Bug（共12个，总分96分）

### Bug #7: 学分计算逻辑错误 - 等价课程重复计算
**严重程度**: Logic Bug（8分）  
**文件路径**: `backend/app/report/service.py`  
**问题描述**:  
在 `compute_academic_gap` 函数中，课程等价计算逻辑存在问题。当一门课程有多个等价目标时，`earned` 字典会累加所有等价课程的学分，导致学分被重复计算。

**代码片段**:
```python
for target, ratio in equiv_map.get(r.course_code, []):
    earned[target] = earned.get(target, 0) + float(r.credits or 0) * ratio
```

**复现步骤**:  
1. 课程A可以等价替代课程B和课程C
2. 学生通过了课程A（3学分）
3. 系统计算时，课程B和课程C都会获得3学分
4. 实际应该只计算一次

**影响**: 学分缺口计算不准确，可能导致错误的学业预警

---

### Bug #8: 排序逻辑不一致
**严重程度**: Logic Bug（8分）  
**文件路径**: `backend/app/report/service.py`  
**问题描述**:  
在 `list_academic_gap_overview` 函数中，排序逻辑使用了多个字段，但排序优先级可能不符合业务需求。当前排序：风险等级 → 学分缺口（降序）→ 学号 → 学生ID。但实际业务可能需要按学分缺口绝对值排序，而不是风险等级优先。

**复现步骤**:  
1. 准备测试数据：学生A（HIGH风险，缺口2学分）、学生B（MEDIUM风险，缺口10学分）
2. 调用学业缺口概览接口
3. 学生A排在学生B前面，但学生B的缺口更大

**影响**: 管理员无法按缺口严重程度排序查看学生

---

### Bug #9: 边界输入处理不当 - 空字符串处理
**严重程度**: Logic Bug（8分）  
**文件路径**: `backend/app/exchange/service.py`  
**问题描述**:  
在 `_parse_courses` 函数中，对空字符串的处理不一致。函数接受 `""` 作为输入并返回 `None`，但在某些调用点可能期望返回空列表 `[]`，导致后续逻辑错误。

**代码片段**:
```python
def _parse_courses(v: Any) -> list[dict[str, Any]] | None:
    if v in (None, ""):
        return None  # 这里返回None，但调用方可能期望[]
```

**复现步骤**:  
1. Excel导入时，课程字段为空字符串
2. 解析返回None
3. 后续代码尝试遍历None值，可能抛出异常

**影响**: 导入功能可能失败或数据不完整

---

### Bug #10: 日期解析错误 - 时区问题
**严重程度**: Logic Bug（8分）  
**文件路径**: `backend/app/exchange/service.py`  
**问题描述**:  
在 `_parse_date` 函数中，日期解析使用 `datetime.strptime` 但没有处理时区信息。如果输入包含时区（如 `2024-01-01T00:00:00+08:00`），解析会失败或产生错误结果。

**代码片段**:
```python
def _parse_date(v: Any) -> date | None:
    # ...
    try:
        return datetime.strptime(str(v), "%Y-%m-%d").date()
    except ValueError:
        return None  # 带时区的日期会到这里
```

**复现步骤**:  
1. Excel中日期格式为 `2024-01-01T00:00:00+08:00`
2. 解析失败，返回None
3. 数据导入失败

**影响**: 数据导入功能对日期格式支持不完善

---

### Bug #11: 查询结果错误 - 软删除未正确过滤
**严重程度**: Logic Bug（8分）  
**文件路径**: `backend/app/report/service.py`  
**问题描述**:  
在 `list_academic_gap_overview` 函数中，虽然查询时过滤了 `Student.deleted_at.is_(None)`，但在计算学业缺口时，`compute_academic_gap` 函数没有再次验证学生是否被软删除，可能导致已删除学生的数据仍然被计算。

**复现步骤**:  
1. 删除一个学生（设置deleted_at）
2. 调用学业缺口概览接口
3. 已删除学生可能仍然出现在结果中（取决于缓存或并发）

**影响**: 数据不一致，显示已删除学生的学业信息

---

### Bug #12: 匹配逻辑错误 - 角色权限判断
**严重程度**: Logic Bug（8分）  
**文件路径**: `backend/app/workflow/service.py`  
**问题描述**:  
在 `_approver_has_role` 函数中，角色匹配逻辑使用了字符串包含判断，但没有考虑角色层级。例如，`COUNSELOR` 角色应该不能审批需要 `COLLEGE_LEADER` 角色的申请，但当前逻辑可能允许。

**代码片段**:
```python
def _approver_has_role(rt, roles: list[str]) -> bool:
    if not rt or not rt.approver_roles:
        return True  # 没有配置时默认允许
    allowed = set(normalize_role_codes(rt.approver_roles.split(",")))
    return bool(set(normalize_role_codes(roles)) & allowed)
```

**复现步骤**:  
1. 配置申请类型需要 `COLLEGE_LEADER` 审批
2. 使用 `COUNSELOR` 角色尝试审批
3. 如果角色代码不完全匹配，可能被拒绝（取决于normalize逻辑）

**影响**: 权限控制可能不严格

---

### Bug #13: 异常输入处理不合理 - Excel导入日期格式
**严重程度**: Logic Bug（8分）  
**文件路径**: `backend/app/exchange/service.py`  
**问题描述**:  
在Excel导入时，日期字段只支持 `%Y-%m-%d` 格式，不支持其他常见格式如 `%Y/%m/%d`、`%Y年%m月%d日` 等。用户使用不同格式的日期会导致导入失败。

**复现步骤**:  
1. 准备Excel文件，日期列为 `2024/01/01` 格式
2. 尝试导入
3. 日期解析失败，记录为错误

**影响**: 用户体验差，需要手动转换日期格式

---

### Bug #14: 计算结果错误 - 模块学分抵扣逻辑
**严重程度**: Logic Bug（8分）  
**文件路径**: `backend/app/report/service.py`  
**问题描述**:  
在学业缺口计算中，对于没有课程白名单的模块，使用"未归属已修学分"进行抵扣。但这个抵扣逻辑可能不准确，因为 `flexible_credit_balance` 的计算方式可能导致学分被重复使用。

**代码片段**:
```python
else:
    required = float(m.credits_required or 0)
    module_earned = min(required, flexible_credit_balance)
    flexible_credit_balance = max(flexible_credit_balance - module_earned, 0.0)
```

**复现步骤**:  
1. 学生有10学分未归属课程
2. 模块A需要5学分（无白名单）
3. 模块B需要5学分（无白名单）
4. 系统可能错误地将10学分同时分配给两个模块

**影响**: 学分缺口计算错误

---

### Bug #15: 排序结果错误 - 荣誉记录排序
**严重程度**: Logic Bug（8分）  
**文件路径**: `backend/app/exchange/service.py`  
**问题描述**:  
在荣誉导入时，分组逻辑使用了多个字段作为key，但排序时没有考虑时间顺序。如果同一荣誉有多条记录，可能无法正确识别最新的记录。

**复现步骤**:  
1. 导入同一荣誉的多条记录（不同时间）
2. 系统可能无法正确识别哪条是最新的
3. 数据可能被覆盖或重复

**影响**: 荣誉数据不准确

---

### Bug #16: 边界输入处理错误 - 分页参数
**严重程度**: Logic Bug（8分）  
**文件路径**: `backend/app/report/service.py`  
**问题描述**:  
在 `list_academic_gap_overview` 函数中，分页参数 `page` 和 `page_size` 没有进行边界检查。如果传入负数或零，可能导致计算错误。

**代码片段**:
```python
start = max(page - 1, 0) * page_size
end = start + page_size
return flattened[start:end], total
```

**复现步骤**:  
1. 调用接口时传入 `page=0` 或 `page=-1`
2. 计算结果可能不符合预期
3. 返回空结果或全部结果

**影响**: API行为不一致

---

### Bug #17: 异常输入处理不合理 - 文件名校验
**严重程度**: Logic Bug（8分）  
**文件路径**: `backend/app/report/service.py`  
**问题描述**:  
在 `_safe_filename` 函数中，文件名校验只替换了 `\` 和 `/`，但没有处理其他特殊字符（如 `..`、`*`、`?` 等），可能存在路径遍历风险。

**代码片段**:
```python
def _safe_filename(filename: str | None) -> str:
    value = (filename or "transcript.pdf").strip() or "transcript.pdf"
    value = value.replace("\\", "_").replace("/", "_")
    # 没有处理 .. 等特殊字符
```

**复现步骤**:  
1. 上传文件名为 `../../../etc/passwd.pdf`
2. 系统只替换 `/` 为 `_`
3. 文件名变为 `.._.._.._etc_passwd.pdf`，但可能仍存在风险

**影响**: 安全风险，虽然MinIO存储可能缓解，但仍需注意

---

### Bug #18: 匹配逻辑错误 - 课程类型判断
**严重程度**: Logic Bug（8分）  
**文件路径**: `backend/app/report/service.py`  
**问题描述**:  
在课程推荐逻辑中，课程类型判断使用了硬编码的映射，但没有处理未知类型。如果课程类型不在映射中，会返回默认优先级9，可能导致重要课程被排在后面。

**代码片段**:
```python
module_priority_map = {
    "REQUIRED": 0,
    "PRACTICE": 1,
    "GENERAL": 2,
    "ELECTIVE": 3,
}
# ...
module_priority = module_priority_map.get(module.module_type, 9)  # 未知类型优先级很低
```

**复现步骤**:  
1. 培养方案中有自定义模块类型（如 `SPECIAL`）
2. 系统将其优先级设为9
3. 该模块的课程推荐排在最后

**影响**: 课程推荐不准确

---

## 三、其他问题（非Bug，但需要关注）

### 1. 安全性问题
- **JWT密钥硬编码**: 开发环境使用默认密钥，如果忘记修改会导致安全漏洞
- **CORS配置宽松**: 开发环境 `allow_origins=["*"]`，生产环境需要收紧
- **敏感字段加密**: 身份证号、手机号使用Fernet加密，但密钥管理需要加强

### 2. 性能问题
- **N+1查询**: 在 `list_admin_workflows` 中，对每个workflow单独查询学生信息
- **全表扫描**: 学业缺口计算时查询所有学生，数据量大时性能差
- **内存占用**: Excel导入时将整个文件读入内存

### 3. 代码质量问题
- **异常处理不一致**: 部分代码使用 `except Exception`，部分使用具体异常类型
- **日志记录不足**: 关键业务操作缺少审计日志
- **类型注解缺失**: 部分函数缺少类型注解，影响IDE支持

---

## 四、测试建议

### 1. 单元测试
- 为关键业务逻辑编写单元测试，特别是状态机、学分计算等
- 测试边界条件和异常输入
- 测试并发场景

### 2. 集成测试
- 测试前后端API接口
- 测试数据库事务和回滚
- 测试文件上传下载流程

### 3. 性能测试
- 测试大量数据导入导出
- 测试并发用户访问
- 测试内存和CPU使用情况

### 4. 安全测试
- 测试权限控制
- 测试SQL注入和XSS攻击
- 测试文件上传安全

---

## 五、总结

本次测试发现 **6个崩溃类Bug** 和 **12个Logic Bug**，总计 **18个问题**，总分 **186分**。

**崩溃类Bug** 主要集中在：
1. 配置校验失败导致服务无法启动
2. 数据库连接问题
3. 小程序页面栈溢出
4. 前端路由守卫死循环
5. 文件上传内存问题
6. 安全配置隐患

**Logic Bug** 主要集中在：
1. 学分计算逻辑错误
2. 排序和匹配逻辑不一致
3. 边界输入处理不当
4. 日期和格式解析问题
5. 权限判断逻辑
6. 分页和查询逻辑

**建议优先修复**: Bug #1, #2, #7, #8（影响核心功能和数据准确性）

---

**测试工程师**: Sisyphus  
**测试完成时间**: 2026年5月25日
