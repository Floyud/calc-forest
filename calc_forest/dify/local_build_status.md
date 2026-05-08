# Local Build Status

## Current Result

- 本地 Dify 已启动：`http://127.0.0.1:18080`
- 本地 FastAPI 工具服务已启动：`http://127.0.0.1:8000`
- Dify 容器访问宿主机 FastAPI 使用：`http://172.17.0.1:8000`

## Night Build Imported App

- Dify App ID: `60fb737f-e51f-4fee-8606-e15a4a44b25c`
- Import status: `completed-with-warnings`
- Imported DSL: `my_calc_forest_dify_night_build.yml`

## Night Build Verified Draft Run

- Workflow run ID: `c8448499-2641-4ffd-b7ed-94977acd0749`
- Status: `succeeded`
- Demo input: `demo_input_402_178.json`

## Verified Output Highlights

- `diagnosis_code`: `E03`
- `teacher_summary`: 已返回
- `student_message`: 已返回
- `encouragement_message`: 已返回
- `session_data.diagnosis.primary_error.code`: `E03`

说明：

- 夜间版仍可返回鼓励语等成长语气字段，但当前提交口径中，这些字段属于可选品牌表达，不是教师端 MVP 主链路的核心证明点。

## Formal V2 Imported App

- Dify App ID: `5435fba0-0196-4cea-84ac-2405ff372818`
- Import status: `completed-with-warnings`
- Imported DSL: `my_calc_forest_dify_formal_v2.yml`

## Formal V2 Verified Draft Run

- Workflow run ID: `25a19b65-0466-4e06-a0f6-5aa8082916b5`
- Status: `succeeded`
- Demo input: `demo_input_402_178.json`

## Formal V2 Verified Output Highlights

- 多节点链路已跑通：`Start -> Code -> HTTP -> Code -> If-Else -> HTTP -> HTTP -> HTTP -> Code -> End`
- `diagnosis_code`: `E03`
- `teacher_summary`: 已返回
- `student_message`: 已返回
- `encouragement_message`: 已返回
- `practice.items`: 已返回
- `tree_species.id`: `cherry`
- 当前正式版 V2 已经同时返回诊断、练习，以及可选成长语气配置字段

## Notes

- 当前夜间版工作流优先使用 `POST /api/dify/session-draft`，避免先依赖 Dify 内部大模型或额外插件。
- 正式版 V2 已拆回更细粒度的 `diagnose + practice + optional tone config + branch + assemble` 多节点版本。
- 若后续需要接入真正的模型与知识库，可在 V2 基础上升级到 `diagnose + practice + knowledge + LLM` 的 V3 版本。
- 通过 Dify draft run API 调试 `Workflow` 时，`text-input` 字段需要按字符串传入；例如 `grade` 要传 `"4"` 而不是数字 `4`。
- 当前《创AI》材料中，Dify 作为教育智能体主入口保留；FastAPI 规则服务仍负责结构化错因诊断，教师审核负责最终使用边界。
