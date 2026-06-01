# Docs

> 最后更新：2026-05-19
>
> 相关文档：`../AGENTS.md` · `docs/specs/04_error_taxonomy.md` · `docs/engineering/architecture.md`

文档侧工作区。这里承接产品定义、工程设计、研究资料、项目管理和比赛材料；实现代码不放在这里。

**总入口：`../AGENTS.md`** — 项目架构、命令、约束、文档索引。

## Directory Map

| Path | Purpose | 关键文档 |
|---|---|---|
| `specs/` | ⭐ 产品规格：范围、流程、错因分类、数据契约、验收标准 | `04_error_taxonomy.md` (错因体系) |
| `engineering/` | 工程设计：架构、API、数据模型、Prompt、Dify工作流 | `architecture.md` (系统架构) |
| `competition/` | 《创AI》竞赛材料：演示脚本、申报总纲、电梯演讲 | `创AI_申报总纲.md` (竞赛主口径) |
| `project_management/` | 项目管理：任务看板、决策记录、路线图 | `task_board.md` (当前任务) |
| `research/` | 调研：平台对比、教学研究、政策合规、教师反馈 | `teaching_schedule_and_problem_design.md` |
| `source_materials/` | 只读原始材料（教师反馈PDF、竞赛指南） | README.md |
| `product/` | 历史产品笔记（仅供参考，已合并到 specs/） | — |
| `../knowledge_base/` | Dify 知识库源文件（135+ 文件） | `01_error_taxonomy/` (44 错因类型) |
| `../给mom看的/` | 教师端用户文档 | `小介绍.html` |

## Reading Order

1. `../AGENTS.md` — 项目总入口（架构、命令、约束、文档索引）
2. `specs/04_error_taxonomy.md` — 错因分类体系（E-K/E-H，核心）
3. `engineering/architecture.md` — 系统架构总览
4. `project_management/task_board.md` — 当前任务状态
5. `competition/demo_video_script_v2.md` — 竞赛演示脚本
6. 其他目录按当前任务需要查阅

## 按角色阅读

### 新成员入职

1. `../AGENTS.md` → 项目全貌
2. `specs/00_project_brief.md` → 项目定位
3. `specs/01_prd.md` → 产品需求
4. `specs/02_mvp_scope.md` → MVP 范围
5. `engineering/architecture.md` → 技术架构

### 开发新功能

1. `engineering/architecture.md` → 系统架构
2. `engineering/api_plan.md` → API 端点清单
3. `engineering/data_model.md` → 数据模型
4. `specs/04_error_taxonomy.md` → 错因编码（如涉及诊断）
5. `project_management/task_board.md` → 当前任务

### 竞赛准备

1. `competition/创AI_申报总纲.md` → 申报策略
2. `competition/demo_video_script_v2.md` → 演示脚本
3. `competition/evidence_checklist.md` → 证据清单
4. `competition/elevator_pitch.md` → 电梯演讲

### 教学研究

1. `research/pain_points_primary_math.md` → 痛点分析
2. `research/teaching_schedule_and_problem_design.md` → 教学进度
3. `specs/teacher_feedback_digest.md` → 教师反馈摘要
4. `research/teacher_feedback_curated/` → 教师反馈详情

## Rules

- 产品范围以 `specs/` 为准。
- 原始输入材料以 `source_materials/` 为准，默认只读。
- 比赛叙事可以描述愿景，但不能把未实现能力写成已交付功能。
- 当前比赛主口径以 `competition/创AI_申报总纲.md` 为准。
- `product/` 目录为历史参考，不进入当前主阅读链。
- 新引入的教师原始材料应先进入 `source_materials/teacher_feedback/`，再按内容性质整理。
- 所有文档应在顶部标注最后更新日期和相关文档链接。

## 文档间交叉引用

| 文档 | 引用 |
|---|---|
| `AGENTS.md` | → `docs/README.md`, `docs/specs/04_error_taxonomy.md`, `docs/engineering/architecture.md` |
| `specs/04_error_taxonomy.md` | ← `AGENTS.md`, `engineering/api_plan.md`, `engineering/data_model.md` |
| `engineering/architecture.md` | ← `AGENTS.md`, `engineering/api_plan.md`, `engineering/data_model.md` |
| `engineering/api_plan.md` | → `engineering/architecture.md`, `engineering/data_model.md`, `specs/05_data_contract.md` |
| `engineering/data_model.md` | → `engineering/architecture.md`, `engineering/api_plan.md`, `specs/04_error_taxonomy.md` |
| `specs/02_mvp_scope.md` | → `engineering/architecture.md`, `specs/01_prd.md` |
| `project_management/roadmap.md` | → `project_management/task_board.md`, `engineering/architecture.md` |
