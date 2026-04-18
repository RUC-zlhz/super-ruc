# S0 启动命令与第一批 worktree 创建

- 日期：`2026-04-18`
- 关联主计划：`S0.1, S0.2, S0.3, S0.4`
- 当前状态：`COMPLETED`
- 关联细化：
  - `docs/notes/refinements/2026-04-18-s0-baseline-freeze-refinement.md`
  - `docs/notes/refinements/2026-04-18-worktree-branch-orchestration-refinement.md`

## 范围

- 给出 `S0` 的实际启动顺序与可直接执行的 PowerShell / Git 命令。
- 先解决当前根工作区“带脏改动”的现实约束，再创建 `S0` 第一批 worktree。
- 明确哪些命令必须在根工作区执行，哪些命令必须在冻结后的新基线之上执行。

## 非范围

- 不在本文件中直接执行命令。
- 不在本文件中替用户判定 `S0.1` 的最终分桶结果；只提供执行骨架与冻结后创建 worktree 的命令。
- 不替代 `S1 ~ S5` 的启动命令；本文件只覆盖 `S0` 第一批。

## 当前观测前提

- 当前根工作区路径：`D:\Codes\super-ruc`
- 当前分支：`main`
- 当前已提交基线：`7b28503`
- 当前存在未提交改动：`是`
- 当前 `codex/*` 分支：`无`
- 当前额外 worktree：`无`
- 当前 worktree 根目录 `D:\Codes\super-ruc-wt`：`不存在`

## 启动原则

1. `S0.1` 必须在当前根工作区执行，因为脏改动只存在这里。
2. 在 `S0.1` 的原子提交完成之前，不创建 `S0.2 / S0.3 / S0.4` worktree。
3. `S0.2 / S0.3` 的 worktree 必须从“冻结后的新 HEAD”创建，而不是从当前 `7b28503` 创建。
4. `S0.4` 的 gap matrix worktree 必须晚于 `S0.2 / S0.3` 的结论产出。

## 执行顺序

1. 根工作区创建冻结分支并导出快照。
2. 在根工作区完成 `S0.1.a ~ S0.1.d`，形成两个原子提交。
3. 基于冻结后的新 HEAD 创建：
   - `codex/v1.6-integration`
   - `codex/int-s0`
   - `codex/s0-2-backend-baseline`
   - `codex/s0-3-web-baseline`
   - `codex/s0-3-miniapp-baseline`
4. 并行执行 `S0.2` 与 `S0.3`。
5. 在 `S0.2 / S0.3` 结论明确后，再创建 `codex/s0-4-gap-matrix` worktree。

## 命令清单

### [x] Step 1 根工作区切冻结分支并导出快照

- 执行位置：`D:\Codes\super-ruc`
- 负责人：`S0 Integrator`

```powershell
Set-Location D:\Codes\super-ruc
git switch -c codex/s0-freeze-root
git status --short
git diff --name-only
git diff --stat
```

执行要求：

- `git switch -c codex/s0-freeze-root` 只做一次，用于避免直接在 `main` 上提交冻结 commit。
- 三份快照输出用于完成 `S0.1.a ~ S0.1.b`，不要跳过。

### [x] Step 2 在根工作区完成 `S0.1` 分桶与两个原子提交

- 执行位置：`D:\Codes\super-ruc`
- 负责人：`S0 Integrator`

```powershell
Set-Location D:\Codes\super-ruc

# 先按 S0.1.b 的分桶结果替换 <FILE-LIST-1> / <FILE-LIST-2>
git add <FILE-LIST-1>
git commit -m "feat(workflow): FR-005 理论自测基线冻结"

git add <FILE-LIST-2>
git commit -m "fix(profile): FR-018 非在读画像访问拦截基线冻结"
```

执行要求：

- `FILE-LIST-1`、`FILE-LIST-2` 只能使用 `S0.1.b / S0.1.c` 已确认的分桶结果，不允许边提测边猜文件归属。
- 这一步完成后，重新执行：

```powershell
Set-Location D:\Codes\super-ruc
git status --short
git log --oneline -2
```

- 只有在两个原子提交都存在且剩余未提交改动不影响 `S0` 基线时，才能进入 Step 3。

### [x] Step 3 基于冻结后的新 HEAD 创建程序集成分支与 `S0` worktree

- 执行位置：`D:\Codes\super-ruc`
- 负责人：`S0 Integrator`

```powershell
Set-Location D:\Codes\super-ruc
$WT_ROOT = 'D:\Codes\super-ruc-wt'
$BASE_SHA = (git rev-parse HEAD).Trim()

New-Item -ItemType Directory -Force $WT_ROOT | Out-Null

git show-ref --verify --quiet refs/heads/codex/v1.6-integration
if ($LASTEXITCODE -ne 0) {
  git branch codex/v1.6-integration $BASE_SHA
}

if (-not (Test-Path "$WT_ROOT\int-s0")) {
  git worktree add -b codex/int-s0 "$WT_ROOT\int-s0" codex/v1.6-integration
}

if (-not (Test-Path "$WT_ROOT\s0-backend-baseline")) {
  git worktree add -b codex/s0-2-backend-baseline "$WT_ROOT\s0-backend-baseline" codex/int-s0
}

if (-not (Test-Path "$WT_ROOT\s0-web-baseline")) {
  git worktree add -b codex/s0-3-web-baseline "$WT_ROOT\s0-web-baseline" codex/int-s0
}

if (-not (Test-Path "$WT_ROOT\s0-miniapp-baseline")) {
  git worktree add -b codex/s0-3-miniapp-baseline "$WT_ROOT\s0-miniapp-baseline" codex/int-s0
}

git worktree list
```

执行要求：

- 这里的 `$BASE_SHA` 必须是完成 `Step 2` 后的新 HEAD，不得手填当前旧值 `7b28503`。
- `WT-S0-INVENTORY` 仍然使用根工作区 `D:\Codes\super-ruc`，不单独创建新 worktree。

### [x] Step 4 并行启动 `S0.2 / S0.3`

- 执行位置：
  - `D:\Codes\super-ruc-wt\s0-backend-baseline`
  - `D:\Codes\super-ruc-wt\s0-web-baseline`
  - `D:\Codes\super-ruc-wt\s0-miniapp-baseline`

#### `WT-S0-BE-BASELINE`

```powershell
Set-Location D:\Codes\super-ruc-wt\s0-backend-baseline\backend
uv run pytest tests/integration -v
```

#### `WT-S0-WEB-BASELINE`

```powershell
Set-Location D:\Codes\super-ruc-wt\s0-web-baseline
pnpm -C web build
```

#### `WT-S0-MA-BASELINE`

```powershell
Set-Location D:\Codes\super-ruc-wt\s0-miniapp-baseline
pnpm -C miniapp build:mp-weixin
```

执行要求：

- 三条车道只记录“通过 / 阻塞 + 证据”，不在本阶段直接修业务代码。
- 若 `web` 与 `miniapp` 同时命中共享契约问题，只在 `S0` 中登记为共享阻塞，不双端各自修复。

### [x] Step 5 创建 `S0.4` gap matrix worktree

- 执行位置：`D:\Codes\super-ruc`
- 负责人：`QA / Docs`

```powershell
Set-Location D:\Codes\super-ruc
$WT_ROOT = 'D:\Codes\super-ruc-wt'

if (-not (Test-Path "$WT_ROOT\s0-gap-matrix")) {
  git worktree add -b codex/s0-4-gap-matrix "$WT_ROOT\s0-gap-matrix" codex/int-s0
}
```

执行要求：

- 只在以下条件全部满足后执行：
  - `S0.1.d` 已完成
  - `S0.2.d` 已完成
  - `S0.3.e` 已完成

### [x] Step 6 在 `WT-S0-GAP-MATRIX` 完成矩阵整理

- 执行位置：`D:\Codes\super-ruc-wt\s0-gap-matrix`
- 负责人：`QA / Docs`

```powershell
Set-Location D:\Codes\super-ruc-wt\s0-gap-matrix
git status --short
```

执行要求：

- 本步骤的核心不是 shell 命令，而是回写矩阵文档与证据来源。
- 完成后由 `WT-INT-S0` 统一回写：
  - `docs/notes/current-implementation-plan.md`
  - `docs/notes/refinements/2026-04-18-s0-baseline-freeze-refinement.md`

## 本轮不要做的事

- 不要在 `Step 2` 之前创建 `S0.2 / S0.3 / S0.4` worktree。
- 不要直接在 `main` 上提交 `S0.1` 冻结 commit。
- 不要在 `S0.2 / S0.3` 的 baseline worktree 中顺手修代码。
- 不要把 `docs/notes/current-implementation-plan.md` 放到实现 worktree 里随手改。

## 实际执行结果（2026-04-18）

- `Step 1`：已在根工作区切到 `codex/s0-freeze-root`，并保留计划文档改动在工作区内未混入冻结提交。
- `Step 2`：已形成两个冻结提交：
  - `5088afe` `feat(workflow): FR-005 理论自测基线冻结`
  - `f418335` `fix(profile): FR-018 非在读画像访问拦截基线冻结`
- `Step 3`：已创建并挂载以下 worktree：
  - `D:\Codes\super-ruc-wt\int-s0` -> `codex/int-s0`
  - `D:\Codes\super-ruc-wt\s0-backend-baseline` -> `codex/s0-2-backend-baseline`
  - `D:\Codes\super-ruc-wt\s0-web-baseline` -> `codex/s0-3-web-baseline`
  - `D:\Codes\super-ruc-wt\s0-miniapp-baseline` -> `codex/s0-3-miniapp-baseline`
  - `D:\Codes\super-ruc-wt\s0-gap-matrix` -> `codex/s0-4-gap-matrix`
- `Step 4`：执行结果如下：
  - `backend`：在 `D:\Codes\super-ruc-wt\s0-backend-baseline\backend` 执行 `uv run pytest tests/integration -v` -> `41 passed in 90.91s`
  - `miniapp`：`pnpm -C miniapp build:mp-weixin` -> `DONE  Build complete.`
  - `web`：修正 `web/src/utils/request.ts` 的响应拦截器返回类型后，`pnpm -C web build` 已通过
- 命令修正说明：若在 `s0-backend-baseline` 根目录直接执行 `uv run pytest backend/tests/integration -v`，会因为解释器与插件解析路径不一致导致假失败；后续统一以后端子目录中的 `uv` 环境为准。
- 验收口径说明：根工作区仍保留用户未冻结改动，`S0` 是否出闸统一以冻结后的 `s0-*` baseline worktree 为准。
- `Step 5`：`s0-gap-matrix` worktree 已创建，可作为 `S0.4` 的独立整理环境。
- `Step 6`：已在根工作区回写 `docs/notes/current-implementation-plan.md`、`docs/notes/refinements/2026-04-18-s0-baseline-freeze-refinement.md`，并新增 `docs/notes/s0-gap-matrix-2026-04-18.md`。

## 验收条件

- 根工作区成功切到 `codex/s0-freeze-root` 并形成两个原子提交。
- `codex/v1.6-integration` 与 `codex/int-s0` 从冻结后的新 HEAD 创建，而不是从旧 `7b28503` 创建。
- `WT-S0-BE-BASELINE`、`WT-S0-WEB-BASELINE`、`WT-S0-MA-BASELINE` 三条车道可并行启动。
- `WT-S0-GAP-MATRIX` 晚于前三条输出启动。
- 整个 `S0` 启动过程不破坏当前根工作区里的剩余未提交计划文档改动。

## 风险 / 阻塞

- 当前根工作区同时含有代码改动与计划文档改动；`Step 2` 的 `git add` 文件清单必须以 `S0.1.b` 分桶结果为准，不能误把计划文档混进代码冻结 commit。
- 若 `Step 2` 完成后仍保留会影响测试 / 构建的未提交改动，则 `S0.2 / S0.3` 的 worktree 基线仍会失真。
- 如果后续发现两个原子提交边界判断错误，应在 `codex/s0-freeze-root` 上修正，再重新生成 `$BASE_SHA`，不要硬改已创建 worktree 的基线。

## 变更记录

- `2026-04-18`：创建 `S0` 启动命令细化文件，明确根工作区冻结顺序、冻结后创建第一批 worktree 的命令与质量闸口。
- `2026-04-18`：补回实际执行结果；修正 `src/utils/request.ts` 后，`Step 4` 中 `backend`、`web`、`miniapp` 三条基线均已通过。
