# 文档对齐总入口

> 目的：防止文档孤岛，明确“哪份文档管什么、改一处时还要同步哪些地方、先更新哪里再更新哪里”，让 `docs/`、代码、Dify 资产与比赛材料长期保持一致。

## 一、先看什么

任何新 session、文档维护、范围调整或代码改动前，默认按这个顺序读：

1. `Agent.md`
2. `docs/project_management/task_board.md`
3. `docs/project_management/decision_log.md`
4. 本文档
5. 再进入对应主题的源头文档

如果当前任务是比赛材料，额外优先读：

1. `docs/competition/创AI_申报总纲.md`
2. `docs/competition/README.md`

如果当前任务是产品范围或工程实现，额外优先读：

1. `docs/specs/README.md`
2. `docs/engineering/README.md`

## 二、文档分层

把仓库中的文档分成 6 层理解，避免把不同职责的文档混写：

| 层级 | 目录 / 文件 | 作用 | 是否源头 |
| --- | --- | --- | --- |
| L0 上游输入 | `docs/source_materials/` | 比赛指南、教师原始材料，只读输入 | 是 |
| L1 会话与全局约束 | `Agent.md` | 当前项目状态、规则、关键路径、运行命令 | 是 |
| L2 产品真相 | `docs/specs/` | 当前 MVP 范围、流程、术语、验收标准 | 是 |
| L3 工程真相 | `docs/engineering/` + `development/` + `calc_forest/dify/` | 架构、接口、工作流、代码与真实资产 | 是 |
| L4 项目管理 | `docs/project_management/` | 决策、任务状态、验证记录、会话协议 | 是 |
| L5 对外表达 | `docs/competition/` | 比赛提交口径、视频脚本、证据清单 | 否，需依赖上面各层 |

补充说明：

- `docs/product/` 是 legacy 历史参考，不进入当前主阅读链。
- `docs/research/` 是研究支持材料，不直接定义当前 MVP 真相。

## 三、当前最关键的源头文档

### 1. 全局总控

- `Agent.md`
- `docs/DOC_ALIGNMENT_MAP.md`
- `docs/project_management/task_board.md`
- `docs/project_management/decision_log.md`

### 2. 产品口径源头

- `docs/specs/00_project_brief.md`
- `docs/specs/01_prd.md`
- `docs/specs/02_mvp_scope.md`
- `docs/specs/03_user_flows.md`
- `docs/specs/04_error_taxonomy.md`
- `docs/specs/05_data_contract.md`
- `docs/specs/06_acceptance_criteria.md`

### 3. 工程口径源头

- `docs/engineering/architecture.md`
- `docs/engineering/api_plan.md`
- `docs/engineering/data_model.md`
- `docs/engineering/dify_workflow_plan.md`
- `docs/engineering/frontend_experience_plan.md`
- `development/app/main.py`
- `development/app/services/`
- `calc_forest/dify/README.md`
- `calc_forest/dify/local_build_status.md`

### 4. 比赛口径源头

- `docs/competition/创AI_申报总纲.md`
- `docs/competition/创AI_开发与应用报告_草稿.md`
- `docs/competition/创AI_案例信息表_素材.md`
- `docs/competition/demo_video_script.md`
- `docs/competition/evidence_checklist.md`

## 四、改动触发器：改哪里，就必须检查哪里

这是本文档最核心的部分。

### A. 改了产品范围 / MVP 边界

先改：

- `docs/specs/00_project_brief.md`
- `docs/specs/01_prd.md`
- `docs/specs/02_mvp_scope.md`
- `docs/specs/03_user_flows.md`

然后同步检查：

- `Agent.md`
- `docs/engineering/README.md`
- `docs/engineering/frontend_experience_plan.md`
- `docs/engineering/dify_workflow_plan.md`
- `docs/project_management/task_board.md`
- `docs/project_management/decision_log.md`
- `docs/competition/创AI_申报总纲.md`

### B. 改了错误分类 / 诊断口径

先改：

- `docs/specs/04_error_taxonomy.md`
- `docs/specs/05_data_contract.md`

然后同步检查：

- `development/app/services/diagnosis.py`
- `development/app/schemas.py`
- `development/tests/test_diagnosis.py`
- `docs/engineering/api_plan.md`
- `docs/engineering/data_model.md`
- `docs/competition/创AI_开发与应用报告_草稿.md`

### C. 改了 API / 数据模型 / 返回字段

先改真实实现：

- `development/app/main.py`
- `development/app/schemas.py`
- `development/app/services/`

然后同步检查：

- `docs/specs/05_data_contract.md`
- `docs/engineering/api_plan.md`
- `docs/engineering/data_model.md`
- `Agent.md`
- `calc_forest/dify/README.md`
- `calc_forest/dify/*.yml`
- `calc_forest/dify/local_build_status.md`

### D. 改了 Dify 工作流 / 主演示链路

先改真实资产：

- `calc_forest/dify/*.yml`
- `calc_forest/dify/README.md`
- `calc_forest/dify/local_build_status.md`

然后同步检查：

- `docs/engineering/dify_workflow_plan.md`
- `docs/engineering/architecture.md`
- `docs/competition/创AI_申报总纲.md`
- `docs/competition/demo_video_script.md`
- `docs/competition/evidence_checklist.md`
- `Agent.md`

### E. 改了前端展示主叙事 / 页面结构

先改真实实现或规划：

- `calc_forest/web/`
- `docs/engineering/frontend_experience_plan.md`

然后同步检查：

- `docs/specs/03_user_flows.md`
- `docs/competition/demo_video_script.md`
- `docs/competition/evidence_checklist.md`
- `Agent.md`

### F. 改了比赛申报口径

先改：

- `docs/competition/创AI_申报总纲.md`

然后同步检查：

- `docs/competition/创AI_开发与应用报告_草稿.md`
- `docs/competition/创AI_案例信息表_素材.md`
- `docs/competition/demo_video_script.md`
- `docs/competition/evidence_checklist.md`
- `docs/README.md`
- `Agent.md`
- `docs/project_management/decision_log.md`

### G. 改了目录结构 / 根入口 / 运行命令

先改真实入口：

- `README.md`
- `Agent.md`

然后同步检查：

- `docs/README.md`
- `docs/project_management/task_board.md`
- 本文档
- 受影响子目录的 `README.md`

## 五、按主题找文档，不再迷路

### 1. 我要判断“现在产品到底做什么”

看：

- `Agent.md`
- `docs/specs/00_project_brief.md`
- `docs/specs/02_mvp_scope.md`
- `docs/specs/03_user_flows.md`
- `docs/project_management/decision_log.md`

### 2. 我要判断“接口和代码现在到底是什么样”

看：

- `development/app/main.py`
- `development/app/schemas.py`
- `development/app/services/`
- `docs/specs/05_data_contract.md`
- `docs/engineering/api_plan.md`
- `docs/engineering/data_model.md`

### 3. 我要判断“Dify 现在到底能跑到哪一步”

看：

- `calc_forest/dify/README.md`
- `calc_forest/dify/local_build_status.md`
- `calc_forest/dify/my_calc_forest_dify_night_build.yml`
- `calc_forest/dify/my_calc_forest_dify_formal_v2.yml`
- `docs/engineering/dify_workflow_plan.md`

### 4. 我要判断“比赛该怎么讲”

看：

- `docs/competition/创AI_申报总纲.md`
- `docs/competition/创AI_开发与应用报告_草稿.md`
- `docs/competition/创AI_案例信息表_素材.md`
- `docs/competition/demo_video_script.md`
- `docs/competition/evidence_checklist.md`

### 5. 我要判断“哪些文档只是历史参考，不能当现行真相”

看：

- `docs/product/`
- `docs/research/` 中非结论性材料
- `docs/source_materials/teacher_feedback/` 中未经整理的原始 docx
- `docs/specs/08_forest_growth_system.md`
- `docs/specs/10_multimodal_input.md`
- `docs/project_management/today_*.md`
- `docs/project_management/tonight_*.md`

## 六、推荐更新顺序

为了减少互相打架，默认按这个顺序更新：

1. 上游事实或真实实现
2. `specs/` 产品真相
3. `engineering/` 工程说明
4. `Agent.md`
5. `project_management/` 状态与决策
6. `competition/` 对外表达
7. `docs/README.md` / 各子目录 `README.md` / 本文档入口

一句话版：

```text
先改事实，再改源头，再改说明，最后改对外表达
```

## 七、每次改完至少自查这 8 件事

1. 当前主叙事是否仍和 `Agent.md` 一致。
2. `docs/specs/02_mvp_scope.md` 和代码能力是否一致。
3. `docs/specs/05_data_contract.md` 与真实 API 字段是否一致。
4. `docs/engineering/dify_workflow_plan.md` 与 `calc_forest/dify/*.yml` 是否一致。
5. 比赛材料是否夸大了未实现能力。
6. 森林相关内容是否又被写成当前 MVP 主交付。
7. 是否仍坚持 `pending_teacher_review` 和“LLM 不判算术对错”。
8. 如果改了路径、API、运行方式，是否同步更新了 `Agent.md`、`docs/README.md` 和本文档。

## 八点五、新增外部文档的入库规则

任何新拿到的教师材料、比赛材料、教材整理资料，默认按这个顺序处理：

1. 先放进 `docs/source_materials/` 对应子目录
2. 在对应 `README.md` 里登记来源与用途
3. 判断它属于产品约束、研究资料、知识库素材还是比赛输入
4. 再把提炼结果沉到 `specs/`、`research/`、`calc_forest/dify/knowledge_sources/` 或 `competition/`
5. 不允许直接跳过原始材料区，把外部 docx 当现行规范文档

## 九、当前硬约束

这些约束在所有文档里都不能漂移：

- 当前比赛类别：**教育智能体**
- 当前主入口：**Dify**
- 当前 MVP 主叙事：**教师工作台 + 错因诊断闭环 + 教师审核边界**
- 森林相关内容：**品牌隐喻与成长语气层，不是当前 MVP 主卖点**
- 所有 AI 输出默认：`pending_teacher_review`
- 不让 LLM 判断算术正误
- 只使用合成或脱敏数据

## 十、文档维护责任建议

由你这个“leader”默认按下面方式组织：

- 你负责：范围判断、口径决策、源头文档把关、最终一致性验收
- 下游执行者负责：批量同步、措辞清理、README 串联、证据归档、局部补丁

如果以后继续让下游 agent 干活，默认给它的文档任务应该是：

1. 先读本文档
2. 只在指定写入范围内改
3. 改完汇报“还需要同步哪些文档”
4. 不得把 legacy 文档当 source of truth

## 十一、建议把它当作固定入口

以后遇到下面任一情况，都先回到本文档：

- “这份文档是不是该改？”
- “为什么这里和代码不一致？”
- “比赛材料能不能这么写？”
- “改了 Dify 后还有哪些文档会受影响？”
- “这份文档是不是只是历史资料？”
