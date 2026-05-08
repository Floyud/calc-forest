# Docs

文档侧工作区。这里承接产品定义、工程设计、研究资料、项目管理和比赛材料；实现代码不放在这里。

## Directory Map

| Path | Purpose |
| --- | --- |
| `specs/` | PM-reviewable source of truth for scope, flows, taxonomy, contracts, and acceptance |
| `engineering/` | Architecture, API, data model, prompts, workflow, and evaluation design |
| `research/` | Background research on platforms, pedagogy, policy, and technical options |
| `project_management/` | Task board, session protocol, decision log, and validation notes |
| `competition/` | 《创AI》 submission drafts, scripts, and evidence checklist |
| `source_materials/` | Read-only upstream material from teachers and competition guides |
| `product/` | Legacy product notes kept only for historical reference |
| `../给mom看的/` | Teacher-facing user docs: user manual, feature guide, educational philosophy — written for primary-school math teachers |

## Reading Order

1. `../Agent.md`
2. `project_management/task_board.md`
3. `DOC_ALIGNMENT_MAP.md`
4. `competition/创AI_申报总纲.md` when working on submission materials
5. `specs/README.md`
6. `engineering/README.md`
7. Other subdirectories as needed for the current task

## Rules

- 产品范围以 `specs/` 为准。
- 原始输入材料以 `source_materials/` 为准，默认只读。
- 比赛叙事可以描述愿景，但不能把未实现能力写成已交付功能。
- 当前比赛主口径以 `competition/创AI_申报总纲.md` 为准。
- 当前 MVP 代码、测试和演示数据放在 `../development/`。
- 正式产品侧实现预留在 `../calc_forest/`。
- Dify 产品工作区放在 `../calc_forest/dify/`，但工具 API 真正来源仍是 `../development/`。
- `product/` 目录继续保留为历史参考，不进入当前主阅读链。
- 文档对齐、同步触发器、源头文档映射以 `DOC_ALIGNMENT_MAP.md` 为总入口。
- 新引入的教师原始材料应先进入 `source_materials/teacher_feedback/`，再按内容性质整理到 `specs/`、`research/` 或 Dify 知识源。
