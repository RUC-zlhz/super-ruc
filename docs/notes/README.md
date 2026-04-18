# `docs/notes` 目录说明

本目录同时保存“权威执行计划”“执行证据”和“参考笔记”。为避免后续对话误把参考材料当成当前实施依据，统一约定如下。

## 权威执行文件

- `current-implementation-plan.md`：当前仓库唯一权威的全局实现计划。
- `refinements/*.md`：只有已经在主计划“细化文件登记”表中登记的细化文件，才属于权威执行文件。

## 参考 / 证据文件

以下文件默认作为背景资料、执行证据或历史记录使用，不直接作为新工作的实施依据：

- `fix.md`
- `pending-business-decisions.md`
- `s0-gap-matrix-2026-04-18.md`
- `v15-acceptance-walkthrough.md`
- `v15-completion-plan.md`

如这些文件中的内容需要转化为当前执行计划，必须先整理成新的 refinement 文件，并在 `current-implementation-plan.md` 中登记。

## 回写规则

1. 新产生的可执行计划，不直接落在本目录根部，统一放入 `refinements/`。
2. 每次完成实质性工作后，优先回写 `current-implementation-plan.md` 与对应 refinement。
3. 如某个参考文件开始承载执行任务，必须补一份 refinement，将其“升级”为受控计划，而不是继续让其处于半计划半笔记状态。
