# Product Specs

> 相关文档：`../README.md` · `docs/engineering/` · `docs/project_management/task_board.md`

产品规格文档。这是 MVP 功能定义的 source of truth。

这些文件与代码和竞赛材料有意分离。

## Reading Order

1. `00_project_brief.md` — 项目定位与核心价值
2. `01_prd.md` — 产品需求文档
3. `02_mvp_scope.md` — MVP 范围定义（已实现 + 未实现）
4. `03_user_flows.md` — 用户流程
5. `04_error_taxonomy.md` — ⭐ 错因分类体系（E-K/E-H，核心）
6. `05_data_contract.md` — 数据契约（→ `engineering/api_plan.md` 完整清单）
7. `06_acceptance_criteria.md` — 验收标准
8. `07_risks_and_open_questions.md` — 风险与待定问题
9. `09_guidance_system.md` — 分层引导系统
10. `teacher_feedback_digest.md` — 教师反馈摘要
11. `08_forest_growth_system.md` — 森林成长体系（品牌表达层）
12. `10_multimodal_input.md` — 多模态输入（未来扩展）

## 错因编码

`04_error_taxonomy.md` 定义的错因编码是全系统唯一标准：
- 知识类: E-K01 ~ E-K23
- 习惯类: E-H01 ~ E-H21
- 未知: E99

详细类型文件: `knowledge_base/01_error_taxonomy/`（44 个 Markdown 文件）

## 规则

- 产品范围以本目录为准。
- `00` 到 `07` 定义当前 MVP 真相。
- `08` 和 `10` 描述未来扩展，不能覆盖当前 MVP 边界。
- 范围变更时，先更新本目录，再同步 `AGENTS.md`、`engineering/`、`project_management/task_board.md`。
