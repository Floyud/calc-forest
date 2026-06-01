# Dify Workspace

这是 **我的计算森林** 的 Dify 产品工作区。

在当前《创AI》提交口径下，Dify 是本项目的**主交付入口与主演示链路**。这里保存工作流 DSL、本地验证记录、知识库准备和演示配套资产；算术正确性判断仍由 `calc_forest/backend/` 中的 FastAPI 规则服务负责，最终使用边界仍由教师审核把关。

用途：

- 记录 Dify 工作流搭建清单
- 保存演示输入、截图说明和后续导出资产
- 作为当前教育智能体主入口的可复现证明材料目录

## Positioning

- 主线：教师工作台式智能体工作流
- 主证明点：错因诊断、教师审核、短时反馈、运行日志
- 可选层：树种与鼓励语等品牌语气配置
- 非职责：不让 Dify 直接判定算术对错

## Current Backend Tools

当前 Dify 应优先调用这些本地工具接口。

教师主链路核心接口：

- `POST /api/dify/session-draft`
- `POST /api/diagnose`
- `POST /api/practice/recommend`

可选品牌语气配置接口：

- `GET /api/tree-species`
- `GET /api/encouragements`

它们对应的实现都在 `../../calc_forest/backend/` 下，并且所有运行命令统一使用 `pyt0` 环境。

## Suggested Folder Use

- `workflow_checklist.md`：搭建步骤与节点说明
- `demo_input_402_178.json`：首个演示输入样例
- `my_calc_forest_dify_night_build.yml`：可导入 Dify DSL 文件
- `my_calc_forest_dify_formal_v2.yml`：正式版 V2 多节点工作流 DSL
- `formal_workflow_design.md`：正式版架构说明
- `knowledge_base_setup.md`：知识库接入说明
- `knowledge_sources/`：可直接导入 Dify Knowledge 的轻量源文档
- `scripts/`：本地启动、初始化和导入脚本
- 后续可继续加入截图索引、导出 JSON、知识库草案等内容

## Current Status

- 夜间版：已导入并跑通
- 正式版 V2：已导入并跑通多节点非 LLM 主链路
- 正式版 V3：待补模型 provider 与 Knowledge Retrieval 绑定
- 比赛口径：Dify 保留为教育智能体主入口；FastAPI 负责规则诊断；教师审核负责最终使用边界
