# Engineering

> 相关文档：`../README.md` · `docs/specs/` · `docs/project_management/task_board.md`

工程设计文档。解释架构和实现选择，不包含源代码。

源代码、测试和演示数据在 `calc_forest/backend/`。

## 推荐阅读

| 文档 | 内容 | 适合场景 |
|---|---|---|
| `architecture.md` | ⭐ 系统架构总览 | 了解全貌 |
| `api_plan.md` | API 端点清单 (~75 个) | 开发新功能 |
| `data_model.md` | 数据模型 (33 张表) | 数据库操作 |
| `frontend_experience_plan.md` | 前端实现详情 | 前端开发 |
| `dify_workflow_plan.md` | Dify 工作流设计 | AI 集成 |
| `prompt_registry.md` | Prompt 注册表 | LLM 调用 |
| `evaluation_plan.md` | 测试方案 | 质量保证 |

## 当前定位

- MVP 中心：教师工作台 + 错因诊断闭环 + 教师审核门
- Dify 是主要编排层和竞赛交付入口
- 森林相关资产属于品牌表达层或后续扩展
