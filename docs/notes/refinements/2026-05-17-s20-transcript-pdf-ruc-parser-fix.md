# S20 成绩单 PDF 解析正确性修复

- 状态：`[x]`
- 日期：`2026-05-17`
- 关联主计划：`S20.1, S20.2, S20.3, S20.4, S20.5`

## 背景

使用 `D:\Downloads\1778947112713.pdf` 复核小程序“学业查看 -> 上传成绩单”时，上传安全边界有效，但解析正确性不足：

- 后端运行依赖未声明 `pypdf`，普通 `uv run --no-sync` 环境会进入“未安装 PDF 文本解析依赖”的降级路径。
- RUC 成绩单文本层将中文课程名拆成单字，且课程没有英文课程代码，旧的课程代码正则无法识别候选课程。
- 真实 PDF 视觉内容包含 `34` 门课程，旧逻辑返回 `0` 条候选。

## 实施项

- [x] `S20.1` 将 `pypdf` 加入后端正式依赖和 `uv.lock`，保证默认后端环境具备 PDF 文本层读取能力。
- [x] `S20.2` 在 `app/report/transcript_pdf.py` 中新增 RUC 成绩单文本层解析分支，支持“学期标题 + 单字课程名 + 学分/成绩/绩点”格式。
- [x] `S20.3` 保留原有课程代码解析兜底，不改变“学生上传只生成教师核验候选、不直接写正式成绩”的边界。
- [x] `S20.4` 新增单元测试覆盖 RUC 成绩单拆字文本与旧课程代码文本，并回跑上传集成边界测试。
- [x] `S20.5` 将 RUC 成绩单学期归一为系统可提交的 `YYYY-FALL / YYYY-SPRING` 格式，并收紧人工核验原文摘要。

## MinerU 评估

- 已查阅 MinerU API 文档：精准 API 需要 Token 并走“申请上传 URL -> 上传文件 -> 轮询结果”的异步流程。
- 尝试使用 MinerU Agent 免 Token 上传接口创建任务成功，但上传到返回的预签名地址返回 `403`，任务停留在 `waiting-file`，因此本轮未把它作为可靠生产依赖。
- 后续若继续接入 MinerU，建议做成教师端或后台任务的可选“增强解析/重新解析”动作，并通过环境变量配置 Token，不写入仓库或日志。

## 验证证据

- 真实 PDF 本地解析：`D:\Downloads\1778947112713.pdf` 可抽取 `1471` 字文本，修复后识别 `34` 条待核验课程候选。
- 单元测试：`UV_CACHE_DIR=D:\Codes\super-ruc\.uv-cache-local` 下执行 `uv run --no-sync --extra dev pytest tests/test_transcript_pdf_analysis.py -q`，结果 `2 passed in 45.91s`。
- 后端静态校验：`uv run --project backend --no-sync --extra dev ruff check app\report\transcript_pdf.py tests\test_transcript_pdf_analysis.py`，结果 `All checks passed!`。
- 后端编译校验：`uv run --project backend --no-sync --extra dev python -m py_compile app\report\transcript_pdf.py tests\test_transcript_pdf_analysis.py`，通过。
- 上传边界集成测试：`UV_CACHE_DIR=D:\Codes\super-ruc\.uv-cache-local` 下执行 `uv run --no-sync --extra dev pytest tests/integration/test_report_contract_flow.py::test_student_transcript_pdf_upload_creates_review_record_without_formal_grades -q`，结果 `1 passed in 70.33s`。
- 小程序类型检查：`.\web\node_modules\.bin\vue-tsc.CMD --noEmit -p miniapp\tsconfig.json`，通过。
